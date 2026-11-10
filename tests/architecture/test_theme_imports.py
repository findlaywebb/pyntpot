"""No loader module imports the style: `style.py` imports the loader, so the reverse is a cycle.

The theme loader's modules are `maps/theme_*.py`, and `maps/line_effects.py`, which `style_groups`
and the loader both import. `style.py` imports them, so any of them
that imported `pyntpot.maps.style`, or the `pyntpot.maps` package (whose `__init__` runs
`style.py`), would close an import cycle. `theme_schema` is the exception: it builds the
schema from the model and nothing in `style.py` imports it. A relative import is reported
too, since it can reach the package without naming it.

The check is a plain function returning the offending imports as strings, empty when the
rule holds. The real-tree test holds the package to it; the self-tests plant each import
in `tmp_path` and show the check reporting it.
"""

import ast
from pathlib import Path

import pytest

from support import REPO_ROOT

#: The modules a loader module may not import: the style, and the package that imports it.
FORBIDDEN = frozenset({"pyntpot.maps", "pyntpot.maps.style"})

#: The one loader module allowed to import the style.
ALLOWED = "theme_schema.py"

#: The loader modules whose names do not start with `theme_`.
BY_NAME = ("line_effects.py", "casing_unions.py")


def theme_modules_importing_the_style(maps: Path) -> list[str]:
    """Name every forbidden or relative import in `maps/theme_*.py` as `file:line: module`."""
    found: list[str] = []
    for path in sorted([*maps.glob("theme_*.py"), *(maps / name for name in BY_NAME)]):
        if not path.is_file():
            continue
        if path.name == ALLOWED:
            continue
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if isinstance(node, ast.Import | ast.ImportFrom):
                found.extend(f"{path.name}:{node.lineno}: {name}" for name in _offending(node))
    return found


def _offending(node: ast.Import | ast.ImportFrom) -> list[str]:
    """The forbidden or relative modules the import `node` names."""
    if isinstance(node, ast.Import):
        return [alias.name for alias in node.names if alias.name in FORBIDDEN]
    module = "." * node.level + (node.module or "")
    return [module] if node.level > 0 or module in FORBIDDEN else []


def test_no_loader_module_imports_the_style() -> None:
    """No `maps/theme_*` module but `theme_schema` imports the style or the maps package."""
    assert theme_modules_importing_the_style(REPO_ROOT / "src" / "pyntpot" / "maps") == []


class TestTheCheckFindsAPlantedImport:
    """The check reports each forbidden import planted in a loader module, and nothing else."""

    @pytest.mark.parametrize(
        ("source", "expected"),
        [
            ("from pyntpot.maps.style import Style\n", ["theme_a.py:1: pyntpot.maps.style"]),
            ("from pyntpot.maps import Style\n", ["theme_a.py:1: pyntpot.maps"]),
            ("import pyntpot.maps.style\n", ["theme_a.py:1: pyntpot.maps.style"]),
            ("from . import style\n", ["theme_a.py:1: ."]),
            ("from .style import Style\n", ["theme_a.py:1: .style"]),
            ("from pyntpot.maps.style_groups import CoverStyle\n", []),
        ],
        ids=["from-style", "from-package", "import-style", "relative", "relative-module", "groups"],
    )
    def test_planted_import(self, tmp_path: Path, source: str, expected: list[str]) -> None:
        """A loader module's import of the style or the package is reported; a group import is not."""
        (tmp_path / "theme_a.py").write_text(source, encoding="utf-8")
        assert theme_modules_importing_the_style(tmp_path) == expected

    def test_schema_may_import_the_style(self, tmp_path: Path) -> None:
        """`theme_schema.py` importing the style is allowed."""
        (tmp_path / "theme_schema.py").write_text(
            "from pyntpot.maps.style import Style\n", encoding="utf-8"
        )
        assert theme_modules_importing_the_style(tmp_path) == []

    def test_line_effects_is_checked_by_name(self, tmp_path: Path) -> None:
        """`line_effects.py`, outside the `theme_*` glob, is held to the same rule."""
        (tmp_path / "line_effects.py").write_text(
            "from pyntpot.maps.style import Style\n", encoding="utf-8"
        )
        assert theme_modules_importing_the_style(tmp_path) == [
            "line_effects.py:1: pyntpot.maps.style"
        ]

    def test_other_modules_are_not_checked(self, tmp_path: Path) -> None:
        """A module outside `theme_*` may import the style."""
        (tmp_path / "pipeline.py").write_text(
            "from pyntpot.maps.style import Style\n", encoding="utf-8"
        )
        assert theme_modules_importing_the_style(tmp_path) == []
