"""Git repository ingester — clones or updates a repo into RAW_DOCS_DIR."""
from __future__ import annotations

import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)


def clone_repo(url: str, branch: str = "main", dest_dir: str = None,
               force: bool = False) -> Path:
    """
    Clone or update a Git repository.

    Args:
        url: HTTPS or SSH URL of the repository.
        branch: Branch name, tag, or commit SHA to checkout.
        dest_dir: Parent directory for the clone. Defaults to RAW_DOCS_DIR.
        force: If True, delete existing clone and re-clone.

    Returns:
        Path to the cloned repository root.
    """
    try:
        import git
    except ImportError:
        raise ImportError("gitpython is required. Install with: pip install gitpython")

    dest_parent = Path(dest_dir or os.getenv("RAW_DOCS_DIR", "./raw_docs"))
    dest_parent.mkdir(parents=True, exist_ok=True)

    # Derive repo name from URL
    repo_name = url.rstrip("/").split("/")[-1].removesuffix(".git")
    # Sanitize branch name for directory
    safe_branch = branch.replace("/", "_").replace("\\", "_")
    target = dest_parent / f"{repo_name}_{safe_branch}"

    if target.exists() and force:
        import shutil
        shutil.rmtree(target)

    if target.exists():
        # Incremental update: fetch + reset
        try:
            repo = git.Repo(target)
            origin = repo.remotes.origin
            origin.fetch()
            repo.git.checkout(branch)
            repo.git.reset("--hard", f"origin/{branch}")
            logger.info(f"Updated existing clone at {target}")
            return target
        except Exception as e:
            logger.warning(f"Update failed ({e}), re-cloning…")
            import shutil
            shutil.rmtree(target)

    # Fresh clone
    logger.info(f"Cloning {url} branch={branch} → {target}")
    git.Repo.clone_from(
        url,
        str(target),
        branch=branch,
        depth=1,
        multi_options=["--single-branch"],
    )
    logger.info(f"Clone complete: {target}")
    return target
