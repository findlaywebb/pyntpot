"""Every `pyntpot` name the docs import, attribute to a package or spell as a dotted path is real.

The pages are the site's pages and `README.md`. Three claims are checked against the
installed package: each `from pyntpot... import ...` in a fenced `python` block imports;
each prose claim that a backticked name is "from" a backticked `pyntpot` module names a
name in that module's `__all__`; and each backticked dotted `pyntpot.…` path in prose
resolves with `support.site_pages.resolve_dotted`. Nothing here runs a code block.
"""

import ast
import importlib
import re
from pathlib import Path

from support import REPO_ROOT
from support.site_pages import fenced_blocks, prose, resolve_dotted, site_pages

_FROM_IMPORT = re.compile(r"^[ \t]*from[ \t]+pyntpot[\w.]*[ \t]+import\b.*$", re.MULTILINE)
_FROM_CLAIM = re.compile(r"`(?P<name>\w+)`,?[ \t]+from[ \t]+`(?P<module>pyntpot[\w.]*)`")
_CODE_SPAN = re.compile(r"`(?P<span>[^`\n]+)`")
_DOTTED = re.compile(r"^(?P<path>pyntpot(?:\.\w+)+)(?:\(.*\))?$")


def _pages() -> list[Path]:
    """Return the pages these checks read: every site page, then `README.md`."""
    return [*site_pages(), REPO_ROOT / "README.md"]


def _name(page: Path) -> str:
    """Return a page's path relative to the repo root, for a failure message."""
    return page.relative_to(REPO_ROOT).as_posix()


def _import_statements(code: str) -> list[str]:
    """Return each `from pyntpot... import ...` statement in `code`, a parenthesised list joined onto one line."""
    statements: list[str] = []
    for found in _FROM_IMPORT.finditer(code):
        statement = found.group().strip()
        if "(" in statement and ")" not in statement:
            rest = code[found.end() :]
            statement += rest[: rest.index(")") + 1]
        statements.append(" ".join(statement.split()))
    return statements


def _import_problem(statement: str) -> str | None:
    """Return why one `from ... import ...` statement fails, or `None` when it imports."""
    node = ast.parse(statement).body[0]
    assert isinstance(node, ast.ImportFrom)
    assert node.module is not None
    try:
        module = importlib.import_module(node.module)
    except ImportError as exc:
        return f"{node.module} does not import: {exc}"
    missing: list[str] = []
    for alias in node.names:
        if alias.name == "*" or hasattr(module, alias.name):
            continue
        try:
            importlib.import_module(f"{node.module}.{alias.name}")
        except ModuleNotFoundError:
            missing.append(alias.name)
    return f"{node.module} has no {', '.join(missing)}" if missing else None


def _dotted_paths(text: str) -> list[str]:
    """Return each backticked dotted `pyntpot.…` path in `text`'s prose, a trailing call dropped."""
    paths: list[str] = []
    for span in _CODE_SPAN.finditer(prose(text)):
        found = _DOTTED.match(span["span"])
        if found is not None:
            paths.append(found["path"])
    return paths


def test_every_import_in_a_code_block_resolves() -> None:
    """Each `from pyntpot... import ...` in a fenced `python` block names a module that imports and names it has."""
    checked = 0
    wrong: list[str] = []
    for page in _pages():
        for block in fenced_blocks(page.read_text()):
            if block.lang != "python":
                continue
            for statement in _import_statements(block.code):
                checked += 1
                problem = _import_problem(statement)
                if problem is not None:
                    wrong.append(f"{_name(page)}:{block.line}: {statement}: {problem}")
    assert checked, "no page has a `from pyntpot... import` in a python block"
    assert not wrong, "\n".join(wrong)


def test_every_from_claim_names_an_exported_name() -> None:
    """Each prose claim that `Name` is from `pyntpot.x` names a module whose `__all__` holds `Name`."""
    checked = 0
    wrong: list[str] = []
    for page in _pages():
        for found in _FROM_CLAIM.finditer(prose(page.read_text())):
            checked += 1
            name, module_name = found["name"], found["module"]
            try:
                exported = getattr(importlib.import_module(module_name), "__all__", ())
            except ImportError:
                exported = ()
            if name not in exported:
                wrong.append(f"{_name(page)}: `{name}`, from `{module_name}`: not in its __all__")
    assert checked, "no page claims a name is from a pyntpot module"
    assert not wrong, "\n".join(wrong)


def test_every_dotted_pyntpot_path_resolves() -> None:
    """Each backticked dotted `pyntpot.…` path in prose names an importable module or an attribute of one."""
    checked = 0
    wrong: list[str] = []
    for page in _pages():
        for path in _dotted_paths(page.read_text()):
            checked += 1
            try:
                resolve_dotted(path)
            except (LookupError, ImportError) as exc:
                wrong.append(f"{_name(page)}: `{path}`: {exc}")
    assert checked, "no page names a dotted pyntpot path"
    assert not wrong, "\n".join(wrong)


def test_a_parenthesised_import_is_read_as_one_statement() -> None:
    """A `from ... import (` list spread over lines is joined into one statement, names in order."""
    code = "x = 1\nfrom pyntpot.ink import (\n    Sheet,\n    wash,\n)\nfrom pyntpot.maps import Style\n"
    assert _import_statements(code) == [
        "from pyntpot.ink import ( Sheet, wash, )",
        "from pyntpot.maps import Style",
    ]


def test_a_dotted_path_drops_its_trailing_call() -> None:
    """A backticked dotted path is read without its call, and a fenced block's paths are not prose."""
    text = "Use `pyntpot.maps.Style.default()` and `pyntpot`.\n\n```python\n`pyntpot.ink.x`\n```\n"
    assert _dotted_paths(text) == ["pyntpot.maps.Style.default"]
