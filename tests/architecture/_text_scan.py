"""Shared file walk for the text-level architecture checks (banned terms, coordinates)."""

from collections.abc import Iterator
from pathlib import Path

from support import REPO_ROOT
from support.exemptions import EXEMPTIONS_DIR

_SCANNED = ("src", "tests", "docs", "README.md", "CHANGELOG.md", "GLOSSARY.md", "specs")
_EXCLUDED_NAMES = frozenset({"LICENSE", "CODEOWNERS", "uv.lock"})
_SKIPPED_DIRS = frozenset({"__pycache__", ".hypothesis", ".pytest_cache"})


def scanned_text_files() -> Iterator[tuple[Path, str]]:
    """Yield (path, text) for every scanned non-binary file, skipping exempt ones."""
    for entry in _SCANNED:
        root = REPO_ROOT / entry
        paths = [root] if root.is_file() else sorted(root.rglob("*")) if root.is_dir() else []
        for path in paths:
            if not path.is_file() or path.name in _EXCLUDED_NAMES:
                continue
            if _SKIPPED_DIRS & set(path.parts) or EXEMPTIONS_DIR in path.parents:
                continue
            data = path.read_bytes()
            if b"\0" in data:
                continue
            try:
                yield path, data.decode()
            except UnicodeDecodeError:
                continue
