"""Console-based Google Drive OAuth authentication.

For remote machines where the browser redirect to localhost won't work.

Two-step usage:
    Step 1 — get the auth URL:
        uv run python scripts/authenticate_gdrive_console.py

    Step 2 — exchange the code (pass the redirect URL from your browser):
        uv run python scripts/authenticate_gdrive_console.py --code "http://localhost:1/?code=4/0A..."
"""

from __future__ import annotations

import sys
import urllib.parse
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.utils.config import settings  # noqa: E402

REDIRECT_URI = "http://localhost:1"


def _load_client_config() -> tuple[str, str, str, list[str]]:
    """Return (client_id, client_secret, token_uri, scopes)."""
    import json

    creds_path = Path(settings.google_drive.credentials_file)
    if not creds_path.exists():
        print(f"ERROR: Credentials file not found: {creds_path}")  # noqa: T201
        sys.exit(1)

    raw = json.loads(creds_path.read_text())
    # Support both "installed" (desktop) and "web" credential types
    client_config = raw.get("web") or raw.get("installed")
    if not client_config:
        print("ERROR: Credentials file must have 'web' or 'installed' key.")  # noqa: T201
        sys.exit(1)
    return (
        client_config["client_id"],
        client_config["client_secret"],
        client_config["token_uri"],
        settings.google_drive.scopes,
    )


def print_auth_url() -> None:
    """Step 1: print the OAuth URL for the user to visit."""
    client_id, _, _, scopes = _load_client_config()

    params = {
        "client_id": client_id,
        "redirect_uri": REDIRECT_URI,
        "response_type": "code",
        "scope": " ".join(scopes),
        "access_type": "offline",
        "prompt": "consent",
    }
    auth_url = f"https://accounts.google.com/o/oauth2/auth?{urllib.parse.urlencode(params)}"

    print()  # noqa: T201
    print("Step 1: Visit this URL in your browser and grant access:")  # noqa: T201
    print()  # noqa: T201
    print(auth_url)  # noqa: T201
    print()  # noqa: T201
    print("After granting access, the browser will redirect to a URL that won't load.")  # noqa: T201
    print("Copy the FULL URL from the browser address bar, then run:")  # noqa: T201
    print()  # noqa: T201
    print('  uv run python scripts/authenticate_gdrive_console.py --code "PASTE_URL_HERE"')  # noqa: T201


def exchange_code(redirect_url: str) -> None:
    """Step 2: exchange the auth code for tokens and save."""
    client_id, client_secret, token_uri, scopes = _load_client_config()

    folder_id = settings.google_drive.folder_id
    if not folder_id:
        print("ERROR: GOOGLE_DRIVE__FOLDER_ID is not set.")  # noqa: T201
        sys.exit(1)

    # Extract code from redirect URL or treat as raw code
    if redirect_url.startswith("http"):
        parsed = urllib.parse.urlparse(redirect_url)
        qs = urllib.parse.parse_qs(parsed.query)
        code = qs.get("code", [None])[0]
        if not code:
            print("ERROR: No 'code' parameter found in URL.")  # noqa: T201
            sys.exit(1)
    else:
        code = redirect_url

    # Exchange code for tokens
    import httpx

    token_response = httpx.post(
        token_uri,
        data={
            "code": code,
            "client_id": client_id,
            "client_secret": client_secret,
            "redirect_uri": REDIRECT_URI,
            "grant_type": "authorization_code",
        },
    )

    if token_response.status_code != 200:
        print(f"ERROR: Token exchange failed: {token_response.text}")  # noqa: T201
        sys.exit(1)

    token_data = token_response.json()

    from google.oauth2.credentials import Credentials

    creds = Credentials(
        token=token_data["access_token"],
        refresh_token=token_data.get("refresh_token"),
        token_uri=token_uri,
        client_id=client_id,
        client_secret=client_secret,
        scopes=scopes,
    )

    token_path = Path(settings.google_drive.token_file)
    token_path.parent.mkdir(parents=True, exist_ok=True)
    token_path.write_text(creds.to_json())
    print(f"Token saved to {token_path}")  # noqa: T201

    # Quick verification
    from googleapiclient.discovery import build

    service = build("drive", "v3", credentials=creds)
    query = f"'{folder_id}' in parents and trashed = false"
    response = (
        service.files()
        .list(q=query, fields="files(id, name, mimeType, size)", pageSize=10)
        .execute()
    )
    files = response.get("files", [])
    print(f"\nFound {len(files)} files in Drive folder (showing first 10):")  # noqa: T201
    for f in files:
        size = int(f.get("size", 0))
        size_mb = size / (1024 * 1024) if size else 0
        print(f"  {f['name']} ({size_mb:.1f} MB)")  # noqa: T201

    print("\nAuthentication complete.")  # noqa: T201


def main() -> None:
    if "--code" in sys.argv:
        idx = sys.argv.index("--code")
        if idx + 1 >= len(sys.argv):
            print("ERROR: --code requires a URL or code argument.")  # noqa: T201
            sys.exit(1)
        exchange_code(sys.argv[idx + 1])
    else:
        print_auth_url()


if __name__ == "__main__":
    main()
