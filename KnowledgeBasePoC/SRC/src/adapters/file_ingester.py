"""File ingester — saves uploaded files to RAW_DOCS_DIR with timestamp suffix."""
from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)

SUPPORTED_EXTENSIONS = {
    ".cs", ".cpp", ".h", ".ts", ".js",
    ".py", ".md", ".pdf", ".docx", ".json", ".yaml", ".yml"
}


def save_upload(file_bytes: bytes, filename: str, dest_dir: str = None) -> Path:
    """
    Save uploaded file bytes to dest_dir with a timestamp suffix.

    Args:
        file_bytes: Raw bytes of the uploaded file.
        filename: Original filename (used to preserve extension).
        dest_dir: Destination directory. Defaults to RAW_DOCS_DIR.

    Returns:
        Path to the saved file.

    Raises:
        ValueError: If file extension is not supported.
    """
    dest = Path(dest_dir or os.getenv("RAW_DOCS_DIR", "./raw_docs"))
    dest.mkdir(parents=True, exist_ok=True)

    fpath = Path(filename)
    ext = fpath.suffix.lower()
    if ext not in SUPPORTED_EXTENSIONS:
        raise ValueError(
            f"Unsupported file type: {ext}. "
            f"Supported: {', '.join(sorted(SUPPORTED_EXTENSIONS))}"
        )

    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    stem = fpath.stem[:40]  # cap stem length
    dest_filename = f"{stem}_{ts}{ext}"
    dest_path = dest / dest_filename

    dest_path.write_bytes(file_bytes)
    logger.info(f"Saved upload: {dest_path} ({len(file_bytes)} bytes)")
    return dest_path


def fetch_url(url: str, dest_dir: str = None) -> Path:
    """
    Fetch a web page (Confluence, docs site, etc.) and save as Markdown.

    Args:
        url: HTTP/HTTPS URL to fetch.
        dest_dir: Destination directory. Defaults to RAW_DOCS_DIR.

    Returns:
        Path to the saved Markdown file.
    """
    import re
    import urllib.parse

    dest = Path(dest_dir or os.getenv("RAW_DOCS_DIR", "./raw_docs"))
    dest.mkdir(parents=True, exist_ok=True)

    try:
        import httpx
        response = httpx.get(url, follow_redirects=True, timeout=30.0)
        response.raise_for_status()
        content_type = response.headers.get("content-type", "")
        raw = response.text
    except Exception as e:
        raise RuntimeError(f"Failed to fetch {url}: {e}")

    # Convert HTML to Markdown-like text
    text = _html_to_text(raw)

    # Derive filename from URL
    parsed = urllib.parse.urlparse(url)
    slug = re.sub(r"[^a-z0-9]+", "_", parsed.path.lower().strip("/"))[:40] or "page"
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    dest_path = dest / f"{slug}_{ts}.md"
    dest_path.write_text(text, encoding="utf-8")
    logger.info(f"Fetched URL → {dest_path}")
    return dest_path


def _html_to_text(html: str) -> str:
    """Basic HTML to plain text conversion."""
    try:
        from html.parser import HTMLParser

        class MLStripper(HTMLParser):
            def __init__(self):
                super().__init__()
                self.reset()
                self.fed: list[str] = []
                self._in_skip = False

            def handle_starttag(self, tag, attrs):
                if tag in ("script", "style", "nav", "header", "footer"):
                    self._in_skip = True
                if tag in ("h1", "h2", "h3", "h4"):
                    self.fed.append(f"\n## ")
                if tag == "li":
                    self.fed.append("\n- ")
                if tag == "p":
                    self.fed.append("\n")

            def handle_endtag(self, tag):
                if tag in ("script", "style", "nav", "header", "footer"):
                    self._in_skip = False

            def handle_data(self, d):
                if not self._in_skip:
                    self.fed.append(d)

            def get_data(self):
                return "".join(self.fed)

        s = MLStripper()
        s.feed(html)
        return s.get_data()
    except Exception:
        import re
        return re.sub(r"<[^>]+>", " ", html)
