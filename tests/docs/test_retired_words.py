"""No site page, `README.md`, example, source or test file uses a word `GLOSSARY.md` has retired.

Reads the retired words from the real `GLOSSARY.md` and scans the real site pages, the
README, every `.py`, `.toml`, `.yaml` and `.md` file under `examples/`, and every `.py` file under
`src/` and `tests/` except `tests/docs/` and `tests/support/glossary.py`, which quote
retired words as data. A word matches
case-insensitively as a whole phrase with an optional plural `s`, its spaces matching any
run of whitespace (so a phrase wrapped across lines still matches), after backticks are
removed (so a quoted retired word still counts).
"""

import re
from pathlib import Path

import pytest

from support import REPO_ROOT
from support.glossary import parse
from support.site_pages import site_pages

_GLOSSARY = REPO_ROOT / "GLOSSARY.md"
_EXAMPLES = REPO_ROOT / "examples"
_SUFFIXES = frozenset({".py", ".toml", ".yaml", ".md"})
_SOURCE = REPO_ROOT / "src"
_TESTS = REPO_ROOT / "tests"
#: Test code that quotes retired words as data, so the scan leaves it out.
_QUOTING = (_TESTS / "docs", _TESTS / "support" / "glossary.py")


def retired_pattern(word: str) -> re.Pattern[str]:
    """Return the pattern a retired word matches: whole phrase, optional plural, any whitespace run between words."""
    phrase = r"\s+".join(re.escape(part) for part in word.split())
    return re.compile(rf"\b{phrase}s?\b", re.IGNORECASE)


def uses(text: str, word: str) -> list[int]:
    """Return the 1-based lines of `text`, backticks removed, on which a use of `word` starts."""
    plain = text.replace("`", "")
    return [
        plain.count("\n", 0, found.start()) + 1 for found in retired_pattern(word).finditer(plain)
    ]


def _scanned_files() -> list[Path]:
    """Return the site pages, the README, the example files and the source and test code the scan reads."""
    examples = sorted(
        path for path in _EXAMPLES.rglob("*") if path.is_file() and path.suffix in _SUFFIXES
    )
    source = sorted(_SOURCE.rglob("*.py"))
    tests = sorted(
        path
        for path in _TESTS.rglob("*.py")
        if not any(path == quoting or path.is_relative_to(quoting) for quoting in _QUOTING)
    )
    return [*site_pages(), REPO_ROOT / "README.md", *examples, *source, *tests]


class TestTheMatcher:
    """The phrase matcher itself, on inline text."""

    @pytest.mark.parametrize(
        ("text", "word", "expected"),
        [
            ("the label plate is", "label plate", [1]),
            ("two Label Plates", "label plate", [1]),
            ("the label\n  plate", "label plate", [1]),
            ("the `callout` key", "callout", [1]),
            ("a\nlabelled plate", "label plate", []),
            ("recallout", "callout", []),
        ],
        ids=["plain", "plural-and-case", "wrapped", "backticked", "other-word", "inside-a-word"],
    )
    def test_uses(self, text: str, word: str, expected: list[int]) -> None:
        """A retired word is found as a whole phrase, plural or wrapped or quoted, and nowhere else."""
        assert uses(text, word) == expected


class TestTheRetiredWords:
    """The real glossary's retired words against the real pages and examples."""

    def test_the_glossary_retires_words(self) -> None:
        """The glossary lists retired words, so the scan below cannot pass on none."""
        assert parse(_GLOSSARY.read_text()).retired

    def test_no_page_or_example_uses_a_retired_word(self) -> None:
        """No site page, README, example file, or source or test code outside the quoting files contains a retired word."""
        words = [retired.word for retired in parse(_GLOSSARY.read_text()).retired]
        found = [
            f"{path.relative_to(REPO_ROOT)}:{line}: {word!r}"
            for path in _scanned_files()
            for word in words
            for line in uses(path.read_text(), word)
        ]
        assert not found, f"retired words in use (see GLOSSARY.md's Retired words): {found}"
