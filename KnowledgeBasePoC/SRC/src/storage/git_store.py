"""GitStore: commit wiki pages to the central git repository."""
from __future__ import annotations

import os
from pathlib import Path
from datetime import datetime, timezone


class GitStore:
    """Manages the central Git wiki repository."""

    def __init__(self, wiki_dir: str = None):
        self.wiki_dir = Path(wiki_dir or os.getenv("WIKI_DIR", "./wiki"))
        self.wiki_dir.mkdir(parents=True, exist_ok=True)
        (self.wiki_dir / "concepts").mkdir(exist_ok=True)
        (self.wiki_dir / "summaries").mkdir(exist_ok=True)

    def commit_wiki_page(self, page_path: str, content: str) -> None:
        """Write a wiki page to disk. Optionally commit with git if repo exists."""
        target = self.wiki_dir / page_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        # Try git commit if the wiki_dir is a git repo
        try:
            import git
            repo = git.Repo(self.wiki_dir, search_parent_directories=True)
            repo.index.add([str(target)])
            repo.index.commit(f"Update wiki page: {page_path}")
        except Exception:
            pass  # Not a git repo or git not configured — file write is sufficient

    def read_wiki_page(self, page_path: str) -> str:
        """Read a wiki page content."""
        target = self.wiki_dir / page_path
        if target.exists():
            return target.read_text(encoding="utf-8")
        return ""

    def list_concept_pages(self) -> list[Path]:
        """List all concept pages in wiki/concepts/."""
        concepts_dir = self.wiki_dir / "concepts"
        if not concepts_dir.exists():
            return []
        return list(concepts_dir.glob("*.md"))

    def list_summary_pages(self) -> list[Path]:
        """List all summary pages in wiki/summaries/."""
        summaries_dir = self.wiki_dir / "summaries"
        if not summaries_dir.exists():
            return []
        return list(summaries_dir.glob("*.md"))
