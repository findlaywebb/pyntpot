"""The docs site's API reference shows every public name once, and its nav names real pages.

Read statically, so no build runs: each page under `docs/reference/` for a public module
(`pyntpot`, `pyntpot.ink`, `pyntpot.letters`, `pyntpot.maps`) holds one mkdocstrings directive
for the module itself, with `members: false` so it renders only the module's docstring, and one
directive per public name, `::: pyntpot.<layer>.<module>.<name>` or `::: pyntpot.<layer>.<name>`.
Every name in the four `__all__` lists must be the last part of exactly one such directive,
and a directive for any other name is a name that is not public. `mkdocs.yml`'s nav lists only
pages that exist, and lists the four pages.
"""

import ast
import re
from collections import Counter
from pathlib import Path

import pytest

from support import REPO_ROOT

#: The public modules and the reference page that renders each.
PAGES: dict[str, str] = {
    "pyntpot": "pyntpot.md",
    "pyntpot.ink": "ink.md",
    "pyntpot.letters": "letters.md",
    "pyntpot.maps": "maps.md",
}
REFERENCE = REPO_ROOT / "docs" / "reference"
MKDOCS = REPO_ROOT / "mkdocs.yml"
_DIRECTIVE = re.compile(r"^::: ([\w.]+)\n((?:[ ]{4}.*\n?)*)", re.MULTILINE)
_NAV_PAGE = re.compile(r"^\s*(?:[^:#\n]+:\s*)?-?\s*([\w/.-]+\.md)\s*$", re.MULTILINE)


def _module_all(module: str) -> list[str]:
    """Return the string constants of a public module's `__all__` list, read by AST."""
    path = REPO_ROOT / "src" / Path(*module.split(".")) / "__init__.py"
    for node in ast.parse(path.read_text(), filename=str(path)).body:
        match node:
            case ast.AnnAssign(target=ast.Name(id="__all__"), value=ast.List(elts=elts)):
                return [str(e.value) for e in elts if isinstance(e, ast.Constant)]
            case _:
                continue
    raise AssertionError(f"{path.relative_to(REPO_ROOT)} has no `__all__` list")


def _directives(page: str) -> list[tuple[str, str]]:
    """Return one reference page's mkdocstrings directives as (dotted path, option text)."""
    return [(m[0], m[1]) for m in _DIRECTIVE.findall((REFERENCE / page).read_text())]


def _is_module_file(parts: list[str]) -> bool:
    """Return whether dotted parts name a module or package of `src/`."""
    base = REPO_ROOT / "src" / Path(*parts)
    return base.with_suffix(".py").is_file() or (base / "__init__.py").is_file()


def test_every_public_name_is_rendered_once() -> None:
    """Each name in the four `__all__` lists is the last part of exactly one name directive, and no other name is."""
    public = {name for module in PAGES for name in _module_all(module)}
    rendered: Counter[str] = Counter()
    for module, page in PAGES.items():
        for path, _options in _directives(page):
            if path != module:
                rendered[path.rsplit(".", maxsplit=1)[1]] += 1
    assert not public - set(rendered), (
        f"public names with no directive: {sorted(public - set(rendered))}"
    )
    assert not set(rendered) - public, (
        f"directives for names that are not public: {sorted(set(rendered) - public)}"
    )
    assert not {n for n, c in rendered.items() if c > 1}, (
        f"rendered twice: {sorted(n for n, c in rendered.items() if c > 1)}"
    )


@pytest.mark.parametrize(("module", "page"), PAGES.items(), ids=list(PAGES))
class TestPage:
    """One reference page: the module directive, then directives that point into the module."""

    def test_the_module_directive_renders_no_members(self, module: str, page: str) -> None:
        """The page opens with a directive for the module that sets `members: false`, so no name is rendered twice."""
        first_path, options = _directives(page)[0]
        assert first_path == module
        assert "members: false" in options

    def test_each_name_directive_points_into_the_module(self, module: str, page: str) -> None:
        """A name directive's path is under the module, and every part before the name is a module of `src/`."""
        listed = set(_module_all(module))
        for path, _options in _directives(page)[1:]:
            parts = path.split(".")
            assert parts[: len(module.split("."))] == module.split("."), (
                f"{path} is not under {module}"
            )
            assert _is_module_file(parts[:-1]), f"{path}: {'.'.join(parts[:-1])} is not a module"
            assert parts[-1] in listed, f"{path} is not in {module}'s `__all__`"


class TestNav:
    """`mkdocs.yml` lists pages that exist, and the four API pages."""

    def test_every_nav_page_exists(self) -> None:
        """Each Markdown file the nav names is under `docs/`."""
        nav = MKDOCS.read_text().split("\nnav:\n", maxsplit=1)[1]
        pages = _NAV_PAGE.findall(nav)
        assert pages, "the nav names no page"
        missing = [p for p in pages if not (REPO_ROOT / "docs" / p).is_file()]
        assert not missing, f"nav pages that do not exist: {missing}"

    def test_the_api_pages_are_in_the_nav(self) -> None:
        """The four API reference pages are in the nav."""
        nav = MKDOCS.read_text().split("\nnav:\n", maxsplit=1)[1]
        for page in PAGES.values():
            assert f"reference/{page}" in nav
