"""Signatures quoted in the docs list every parameter of the callable they name.

Reads the real site pages and `README.md` and imports the real public packages.
"""

import importlib
import inspect
import re
from collections.abc import Callable
from pathlib import Path

import pytest

from support import REPO_ROOT
from support.site_pages import prose, site_pages

_PACKAGES = ("pyntpot", "pyntpot.ink", "pyntpot.letters", "pyntpot.maps")
_SPAN = re.compile(r"`(?P<name>[A-Za-z_][\w.]*)\((?P<args>[^`()]+)\)`")
_IDENTIFIER = re.compile(r"[A-Za-z_]\w*")


def _public_callables() -> dict[str, Callable[..., object]]:
    """Return every callable in a public `__all__`, by name."""
    found: dict[str, Callable[..., object]] = {}
    for package in _PACKAGES:
        module = importlib.import_module(package)
        for name in module.__all__:
            member = getattr(module, name)
            if callable(member):
                found.setdefault(name, member)
    return found


def _parameters(member: Callable[..., object]) -> list[str]:
    """Return a callable's parameter names in order, `self` excluded."""
    return [name for name in inspect.signature(member).parameters if name != "self"]


def _quoted_signatures(
    text: str, known: dict[str, Callable[..., object]]
) -> list[tuple[str, list[str]]]:
    """Return `(name, arguments)` for each backticked call of a known callable with bare-identifier arguments."""
    quoted: list[tuple[str, list[str]]] = []
    for span in _SPAN.finditer(prose(text)):
        name = span["name"].rsplit(".", maxsplit=1)[-1]
        arguments = [argument.strip() for argument in span["args"].split(",")]
        if name in known and all(_IDENTIFIER.fullmatch(argument) for argument in arguments):
            quoted.append((name, arguments))
    return quoted


def _pages() -> list[Path]:
    """Return the site pages and the README."""
    return [*site_pages(), REPO_ROOT / "README.md"]


class TestQuotedSignatures:
    """A signature quoted in prose is the whole signature."""

    def test_a_quoted_signature_lists_every_parameter(self) -> None:
        """Every backticked call of a public callable with bare-identifier arguments names all its parameters, in order."""
        known = _public_callables()
        wrong: list[str] = []
        checked = 0
        for page in _pages():
            for name, arguments in _quoted_signatures(page.read_text(encoding="utf-8"), known):
                checked += 1
                if arguments != _parameters(known[name]):
                    wrong.append(f"{page.relative_to(REPO_ROOT)}: `{name}({', '.join(arguments)})`")
        assert checked
        assert not wrong, f"quoted signatures that differ from the code: {wrong}"

    @pytest.mark.parametrize(
        ("text", "flagged"),
        [
            ("`wash(cover, sheet, base, pool)` here.", True),
            ("`wash(cover, sheet, base, pool, options)` here.", False),
            ("`wash(cover=1)` here.", False),
            ("```\nwash(cover)\n```", False),
        ],
        ids=["short", "full", "keyword-skipped", "fenced-skipped"],
    )
    def test_the_check_flags_a_short_signature(self, text: str, flagged: bool) -> None:
        """The extractor finds a short quote and leaves out full, keyword and fenced ones."""
        known = _public_callables()
        quoted = _quoted_signatures(text, known)
        short = [name for name, arguments in quoted if arguments != _parameters(known[name])]
        assert bool(short) is flagged
