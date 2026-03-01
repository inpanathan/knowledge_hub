"""Unit tests for book metadata extraction."""

from __future__ import annotations

from pathlib import Path

from src.data.book_metadata import extract_metadata


def test_extract_txt_metadata(tmp_dir: Path) -> None:
    """Text files use the first line as title."""
    txt_file = tmp_dir / "sample_book.txt"
    txt_file.write_text("My Sample Book Title\nLine two\nLine three\n")

    meta = extract_metadata(txt_file)
    assert meta["title"] == "My Sample Book Title"
    assert meta["author"] == ""
    assert meta["table_of_contents"] == []


def test_extract_markdown_metadata(tmp_dir: Path) -> None:
    """Markdown files strip heading markers from the first line."""
    md_file = tmp_dir / "notes.md"
    md_file.write_text("# My Notes Title\nSome content\n")

    meta = extract_metadata(md_file)
    assert meta["title"] == "My Notes Title"


def test_extract_fallback_metadata(tmp_dir: Path) -> None:
    """Unknown formats use filename-based fallback."""
    unknown = tmp_dir / "my_great_book.xyz"
    unknown.write_text("data")

    meta = extract_metadata(unknown)
    assert "My Great Book" in meta["title"]
    assert meta["author"] == ""
    assert meta["isbn"] == ""


def test_extract_metadata_ensures_all_keys(tmp_dir: Path) -> None:
    """All expected keys are present in the result."""
    txt_file = tmp_dir / "test.txt"
    txt_file.write_text("Hello\n")

    meta = extract_metadata(txt_file)
    expected_keys = {
        "title",
        "author",
        "isbn",
        "publisher",
        "publication_year",
        "language",
        "page_count",
        "description",
        "table_of_contents",
    }
    assert expected_keys.issubset(set(meta.keys()))


def test_extract_txt_long_first_line_uses_filename(tmp_dir: Path) -> None:
    """If first line is too long (>200 chars), fall back to filename."""
    txt_file = tmp_dir / "short_name.txt"
    txt_file.write_text("x" * 250 + "\n")

    meta = extract_metadata(txt_file)
    # Should use filename-based title since first line is too long
    assert meta["title"] == "Short Name"


def test_extract_metadata_handles_empty_file(tmp_dir: Path) -> None:
    """Empty file should not crash, uses filename fallback."""
    empty = tmp_dir / "empty_book.txt"
    empty.write_text("")

    meta = extract_metadata(empty)
    assert meta["title"] == "Empty Book"
