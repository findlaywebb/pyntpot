"""Banned-term gate: no personal content crosses into the library."""

import re
from pathlib import Path

import pytest

from ._text_scan import scanned_text_files
from support import REPO_ROOT


def _compile(term: str) -> re.Pattern[str]:
    """Compile one list line: a `re:` raw regex or a whole-word plain term."""
    if term.startswith("re:"):
        return re.compile(term.removeprefix("re:"))
    return re.compile(rf"\b{re.escape(term)}\b")


def test_no_banned_terms(pytestconfig: pytest.Config) -> None:
    """No scanned file contains a term from the personal terms file."""
    terms_file = Path(pytestconfig.getini("personal_terms_file")).expanduser()
    if not terms_file.is_file():
        pytest.skip(
            "personal terms file not present; the gate runs only on the maintainer's machine"
        )
    terms = [
        stripped
        for line in terms_file.read_text().splitlines()
        if (stripped := line.strip()) and not stripped.startswith("#")
    ]
    patterns = [(term, _compile(term)) for term in terms]
    found = [
        f"{path.relative_to(REPO_ROOT)}: {term}"
        for path, text in scanned_text_files()
        for term, pattern in patterns
        if pattern.search(text)
    ]
    assert not found, f"banned terms found: {found}"
