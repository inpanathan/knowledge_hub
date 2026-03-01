"""Book metadata extraction from multiple file formats.

Extracts title, author, ISBN, publisher, page count, language,
description, and table of contents from PDF, EPUB, DOCX, and text files.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from src.utils.logger import get_logger

logger = get_logger(__name__)

# ISBN patterns (ISBN-10 and ISBN-13)
_ISBN_PATTERN = re.compile(
    r"(?:ISBN[-: ]?(?:13|10)?[-: ]?)?"
    r"(?=[0-9X]{10}$|(?=(?:[0-9]+[-\s]){3})[-\s0-9X]{13}$"
    r"|97[89][0-9]{10}$|(?=(?:[0-9]+[-\s]){4})[-\s0-9]{17}$)"
    r"(?:97[89][-\s]?)?[0-9]{1,5}[-\s]?[0-9]+[-\s]?[0-9]+[-\s]?[0-9X]",
    re.MULTILINE,
)

_ISBN_SIMPLE = re.compile(r"(?:ISBN[-:\s]*)((?:97[89][-\s]?)?[0-9][-0-9\s]{8,15}[0-9X])", re.I)


def extract_metadata(file_path: Path) -> dict[str, Any]:
    """Extract book metadata from a supported file.

    Returns a dict with keys: title, author, isbn, publisher, publication_year,
    language, page_count, description, table_of_contents.
    Missing fields are returned as empty string / None / [].
    """
    suffix = file_path.suffix.lower()

    extractors = {
        ".pdf": _extract_pdf_metadata,
        ".epub": _extract_epub_metadata,
        ".docx": _extract_docx_metadata,
        ".txt": _extract_txt_metadata,
        ".md": _extract_txt_metadata,
    }

    extractor = extractors.get(suffix, _extract_fallback_metadata)
    try:
        metadata = extractor(file_path)
    except Exception as e:
        logger.warning(
            "metadata_extraction_failed",
            file=str(file_path),
            format=suffix,
            error=str(e),
        )
        metadata = _extract_fallback_metadata(file_path)

    # Ensure all expected keys exist
    defaults: dict[str, Any] = {
        "title": file_path.stem,
        "author": "",
        "isbn": "",
        "publisher": "",
        "publication_year": None,
        "language": "",
        "page_count": None,
        "description": "",
        "table_of_contents": [],
    }
    for key, default in defaults.items():
        if key not in metadata or not metadata[key]:
            metadata[key] = default

    return metadata


def _extract_pdf_metadata(file_path: Path) -> dict[str, Any]:
    """Extract metadata from a PDF file using pypdf."""
    from pypdf import PdfReader

    reader = PdfReader(str(file_path))
    meta: dict[str, Any] = dict(reader.metadata) if reader.metadata else {}

    result: dict[str, Any] = {
        "title": (meta.get("/Title") or "").strip() or file_path.stem,
        "author": (meta.get("/Author") or "").strip(),
        "description": (meta.get("/Subject") or "").strip(),
        "publisher": (meta.get("/Creator") or "").strip(),
        "page_count": len(reader.pages),
        "language": "",
        "isbn": "",
        "publication_year": None,
        "table_of_contents": [],
    }

    # Try to extract ISBN from first few pages
    isbn = _scan_pages_for_isbn(reader, max_pages=3)
    if isbn:
        result["isbn"] = isbn

    # Extract table of contents from PDF outline
    try:
        outline = reader.outline
        if outline:
            result["table_of_contents"] = _flatten_outline(outline)
    except Exception:
        pass

    return result


def _extract_epub_metadata(file_path: Path) -> dict[str, Any]:
    """Extract metadata from an EPUB file using ebooklib."""
    try:
        from ebooklib import epub
    except ImportError as e:
        logger.warning("ebooklib_not_installed", error=str(e))
        return _extract_fallback_metadata(file_path)

    book = epub.read_epub(str(file_path), options={"ignore_ncx": True})

    def _get_dc(field: str) -> str:
        items = book.get_metadata("DC", field)
        if items:
            return str(items[0][0]).strip()
        return ""

    title = _get_dc("title") or file_path.stem
    author = _get_dc("creator")
    publisher = _get_dc("publisher")
    language = _get_dc("language")
    description = _get_dc("description")

    # ISBN from identifier
    isbn = ""
    identifiers = book.get_metadata("DC", "identifier")
    for ident_tuple in identifiers:
        ident_val = str(ident_tuple[0])
        if "isbn" in ident_val.lower() or re.match(r"^97[89]", ident_val):
            isbn = re.sub(r"[^0-9X]", "", ident_val.upper())
            break

    # Publication year from date
    publication_year = None
    date_str = _get_dc("date")
    if date_str:
        year_match = re.search(r"(\d{4})", date_str)
        if year_match:
            publication_year = int(year_match.group(1))

    # Table of contents
    toc: list[str] = []
    try:
        for item in book.toc:
            if hasattr(item, "title"):
                toc.append(item.title)
            elif isinstance(item, tuple) and len(item) >= 1:
                section = item[0]
                if hasattr(section, "title"):
                    toc.append(section.title)
    except Exception:
        pass

    return {
        "title": title,
        "author": author,
        "isbn": isbn,
        "publisher": publisher,
        "publication_year": publication_year,
        "language": language,
        "page_count": None,
        "description": description,
        "table_of_contents": toc,
    }


def _extract_docx_metadata(file_path: Path) -> dict[str, Any]:
    """Extract metadata from a DOCX file using python-docx."""
    from docx import Document

    doc = Document(str(file_path))
    props = doc.core_properties

    publication_year = None
    if props.created:
        publication_year = props.created.year

    return {
        "title": (props.title or "").strip() or file_path.stem,
        "author": (props.author or "").strip(),
        "isbn": "",
        "publisher": "",
        "publication_year": publication_year,
        "language": (props.language or "").strip(),
        "page_count": None,
        "description": (props.subject or "").strip(),
        "table_of_contents": [],
    }


def _extract_txt_metadata(file_path: Path) -> dict[str, Any]:
    """Extract minimal metadata from a text/markdown file."""
    title = file_path.stem.replace("_", " ").replace("-", " ").title()

    # Try to read first line as title
    try:
        with open(file_path, encoding="utf-8", errors="replace") as f:
            first_line = f.readline().strip()
        if first_line and len(first_line) < 200:
            # Strip markdown heading markers
            clean = re.sub(r"^#+\s*", "", first_line).strip()
            if clean:
                title = clean
    except Exception:
        pass

    return {
        "title": title,
        "author": "",
        "isbn": "",
        "publisher": "",
        "publication_year": None,
        "language": "",
        "page_count": None,
        "description": "",
        "table_of_contents": [],
    }


def _extract_fallback_metadata(file_path: Path) -> dict[str, Any]:
    """Fallback metadata using only the filename."""
    return {
        "title": file_path.stem.replace("_", " ").replace("-", " ").title(),
        "author": "",
        "isbn": "",
        "publisher": "",
        "publication_year": None,
        "language": "",
        "page_count": None,
        "description": "",
        "table_of_contents": [],
    }


def extract_cover_image(
    file_path: Path,
    covers_dir: Path,
    book_id: str,
) -> str:
    """Extract cover image and save to covers_dir/<book_id>.jpg.

    Returns the saved cover path, or empty string if not extractable.
    Currently supports EPUB cover extraction. PDF cover deferred to Phase 2.
    """
    suffix = file_path.suffix.lower()
    covers_dir.mkdir(parents=True, exist_ok=True)

    if suffix == ".epub":
        return _extract_epub_cover(file_path, covers_dir, book_id)

    return ""


def _extract_epub_cover(file_path: Path, covers_dir: Path, book_id: str) -> str:
    """Extract cover image from an EPUB file."""
    try:
        from ebooklib import epub
    except ImportError:
        return ""

    try:
        book = epub.read_epub(str(file_path), options={"ignore_ncx": True})

        # Try to find cover image
        cover_image = None
        for item in book.get_items():
            if item.get_type() == 6:  # ITEM_COVER
                cover_image = item
                break

        if cover_image is None:
            # Fallback: look for items with "cover" in the name
            for item in book.get_items():
                name = (item.get_name() or "").lower()
                if "cover" in name and any(
                    name.endswith(ext) for ext in (".jpg", ".jpeg", ".png", ".gif")
                ):
                    cover_image = item
                    break

        if cover_image is None:
            return ""

        # Determine extension from the item name
        item_name = cover_image.get_name() or "cover.jpg"
        ext = Path(item_name).suffix or ".jpg"
        cover_path = covers_dir / f"{book_id}{ext}"
        cover_path.write_bytes(cover_image.get_content())

        logger.info("cover_extracted", book_id=book_id, path=str(cover_path))
        return str(cover_path)
    except Exception as e:
        logger.warning("cover_extraction_failed", book_id=book_id, error=str(e))
        return ""


def _scan_pages_for_isbn(reader: Any, max_pages: int = 3) -> str:
    """Scan the first N pages of a PDF for an ISBN."""
    for i in range(min(max_pages, len(reader.pages))):
        try:
            text = reader.pages[i].extract_text() or ""
            match = _ISBN_SIMPLE.search(text)
            if match:
                isbn = re.sub(r"[\s-]", "", match.group(1))
                return isbn
        except Exception:
            continue
    return ""


def _flatten_outline(outline: list[Any], depth: int = 0) -> list[str]:
    """Flatten a PDF outline into a list of chapter title strings."""
    titles: list[str] = []
    for item in outline:
        if isinstance(item, list):
            titles.extend(_flatten_outline(item, depth + 1))
        elif hasattr(item, "title"):
            prefix = "  " * depth
            titles.append(f"{prefix}{item.title}")
    return titles
