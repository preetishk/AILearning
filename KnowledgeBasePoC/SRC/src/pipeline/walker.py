"""File walker — recursively collects source files respecting .gitignore and exclude patterns."""
from __future__ import annotations

import os
from pathlib import Path


# Extensions supported by tree-sitter
CODE_EXTENSIONS = {".cs", ".cpp", ".h", ".ts", ".js", ".py"}
# Extensions for document processing
DOC_EXTENSIONS = {".md", ".txt"}
# Extensions for schema processing
SCHEMA_EXTENSIONS = {".json", ".yaml", ".yml"}
# Extensions requiring OpenKB/adapter
BINARY_EXTENSIONS = {".pdf", ".docx"}

ALL_SUPPORTED = CODE_EXTENSIONS | DOC_EXTENSIONS | SCHEMA_EXTENSIONS | BINARY_EXTENSIONS

DEFAULT_EXCLUDE_DIRS = {
    ".git", ".venv", "venv", "node_modules", "__pycache__",
    ".pytest_cache", "dist", "build", "bin", "obj", ".vs",
    ".idea", ".vscode", "coverage", ".coverage",
}

DEFAULT_EXCLUDE_FILES = {
    ".gitignore", ".gitattributes", "LICENSE", "LICENSE.txt",
}


def walk_dir(
    root: str,
    exts: set[str] = None,
    excludes: set[str] = None,
    path_filter: str = None,
) -> list[Path]:
    """
    Recursively walk root directory and collect files matching given extensions.

    Args:
        root: Directory to walk.
        exts: Set of file extensions to include (e.g. {".cs", ".py"}). Defaults to ALL_SUPPORTED.
        excludes: Extra directory names to exclude.
        path_filter: Optional sub-path filter (e.g. "src/Libraries") — only files under this path.

    Returns:
        Sorted list of matching Path objects.
    """
    root_path = Path(root).resolve()
    if not root_path.exists():
        return []

    target_exts = exts or ALL_SUPPORTED
    exclude_dirs = DEFAULT_EXCLUDE_DIRS | (excludes or set())

    results: list[Path] = []

    for dirpath, dirnames, filenames in os.walk(root_path):
        # Prune excluded dirs in-place
        dirnames[:] = [d for d in dirnames if d not in exclude_dirs and not d.startswith(".")]

        current = Path(dirpath)

        # Apply path_filter
        if path_filter:
            relative = str(current.relative_to(root_path)).replace("\\", "/")
            filter_path = path_filter.strip("/")
            if filter_path and not relative.startswith(filter_path) and filter_path != ".":
                # Allow if we're inside the filter path
                if not relative == filter_path:
                    continue

        for fname in filenames:
            fpath = current / fname
            if fpath.suffix.lower() in target_exts and fname not in DEFAULT_EXCLUDE_FILES:
                results.append(fpath)

    return sorted(results)


def infer_language(path: Path) -> str:
    """Infer the language identifier from a file extension."""
    ext_map = {
        ".cs": "csharp",
        ".cpp": "cpp",
        ".h": "cpp",
        ".ts": "typescript",
        ".js": "javascript",
        ".py": "python",
        ".md": "markdown",
        ".json": "json",
        ".yaml": "yaml",
        ".yml": "yaml",
        ".txt": "text",
        ".pdf": "text",
        ".docx": "text",
    }
    return ext_map.get(path.suffix.lower(), "text")
