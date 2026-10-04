"""The import rule between the layered packages and the interim `_port` code.

`ink` never imports `letters`, `maps` or `_port`; `letters` imports only `ink`
from the package. A `maps` module imports `_port` only when it is a pinned
adapter, and an adapter binds `_port` modules, never names from them (except
from `_port.style`). `_port` reaches `maps` only inside a function or under
`if TYPE_CHECKING:`. The checks read the AST of `src/pyntpot`, counting direct
imports only; the cold-import test proves the chains.
"""

import ast
import subprocess
import sys
from collections.abc import Iterator
from pathlib import Path

import pytest

from support import REPO_ROOT

SRC = REPO_ROOT / "src"
PACKAGE = SRC / "pyntpot"

#: Every module a fresh interpreter must import without an import cycle.
MODULES: tuple[str, ...] = (
    "pyntpot.ink",
    "pyntpot.letters",
    "pyntpot.maps",
    "pyntpot.maps.credit",
    "pyntpot._port.paint",
    "pyntpot._port.labels",
    "pyntpot._port.mapcard",
    "pyntpot._port.geo",
    "pyntpot.maps.card",
    "pyntpot.ink.style",
    "pyntpot.ink.brush_style",
    "pyntpot.letters.style",
    "pyntpot.maps.style_groups",
    "pyntpot.maps.track",
    "pyntpot.maps.style",
    "pyntpot.maps.providers.base",
    "pyntpot.ink.polyline",
    "pyntpot.ink.curves",
    "pyntpot.ink.chains",
    "pyntpot.maps.providers.opentopodata",
    "pyntpot.maps.cache",
    "pyntpot.maps.providers.overpass",
    "pyntpot.maps.projection",
    "pyntpot.maps.basemap",
    "pyntpot.maps.plates",
    "pyntpot.maps.pipeline",
    "pyntpot.maps.annotations",
    "pyntpot.maps.lettering",
    "pyntpot.maps.attribution",
    "pyntpot.maps.cli",
)

#: The `maps` modules allowed to import `_port`, binding its modules.
ADAPTERS: tuple[str, ...] = (
    "pyntpot.maps.style_groups",
    "pyntpot.maps.style",
    "pyntpot.maps.pipeline",
    "pyntpot.maps.lettering",
    "pyntpot.maps.attribution",
)

#: The one `_port` module an adapter may import names from.
NAME_IMPORTABLE = "pyntpot._port.style"


def _module_name(path: Path) -> str:
    """Return the dotted module name of a source file under `src`."""
    parts = path.relative_to(SRC).with_suffix("").parts
    return ".".join(parts[:-1] if parts[-1] == "__init__" else parts)


def _modules(package: str) -> list[tuple[str, Path]]:
    """Return (dotted name, path) for every source file in one subpackage."""
    root = PACKAGE / package
    files = sorted(p for p in root.rglob("*.py") if "__pycache__" not in p.parts)
    return [(_module_name(path), path) for path in files]


def _base(node: ast.ImportFrom, module: str, path: Path) -> str:
    """Resolve the module an import-from reads, including relative imports."""
    if not node.level:
        return node.module or ""
    package = module if path.name == "__init__.py" else module.rpartition(".")[0]
    for _ in range(node.level - 1):
        package = package.rpartition(".")[0]
    return f"{package}.{node.module}" if node.module else package


def _targets(node: ast.Import | ast.ImportFrom, module: str, path: Path) -> list[str]:
    """Return the dotted names one import statement reads, one per bound alias."""
    if isinstance(node, ast.Import):
        return [alias.name for alias in node.names]
    base = _base(node, module, path)
    return [f"{base}.{alias.name}" for alias in node.names]


def _imports(path: Path) -> Iterator[ast.Import | ast.ImportFrom]:
    """Yield every import statement in a file, at any nesting level."""
    tree = ast.parse(path.read_text(), filename=str(path))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import | ast.ImportFrom):
            yield node


def _under(name: str, prefix: str) -> bool:
    """Return whether a dotted name is a prefix package or anything inside it."""
    return name == prefix or name.startswith(f"{prefix}.")


def _violations(package: str, allowed: tuple[str, ...]) -> list[str]:
    """Return `module: target` for every `pyntpot` import outside the allowed packages."""
    found: list[str] = []
    for module, path in _modules(package):
        for node in _imports(path):
            for target in _targets(node, module, path):
                inside = _under(target, "pyntpot")
                if inside and not any(_under(target, ok) for ok in allowed):
                    found.append(f"{module}: {target}")
    return found


def _is_type_checking(node: ast.If) -> bool:
    """Return whether an `if` statement tests `TYPE_CHECKING`."""
    test = node.test
    if isinstance(test, ast.Name):
        return test.id == "TYPE_CHECKING"
    return isinstance(test, ast.Attribute) and test.attr == "TYPE_CHECKING"


def _module_level(body: list[ast.stmt]) -> Iterator[ast.stmt]:
    """Yield statements that run at import time, skipping functions and TYPE_CHECKING blocks."""
    for stmt in body:
        yield stmt
        if isinstance(stmt, ast.FunctionDef | ast.AsyncFunctionDef):
            continue
        if isinstance(stmt, ast.If):
            if not _is_type_checking(stmt):
                yield from _module_level(stmt.body)
            yield from _module_level(stmt.orelse)
            continue
        for field in ("body", "orelse", "finalbody"):
            nested = getattr(stmt, field, [])
            yield from _module_level([s for s in nested if isinstance(s, ast.stmt)])
        for handler in getattr(stmt, "handlers", []):
            yield from _module_level(handler.body)


@pytest.mark.parametrize("name", MODULES, ids=MODULES)
def test_each_module_imports_cold(name: str) -> None:
    """A fresh interpreter imports the module without tripping an import cycle."""
    subprocess.run([sys.executable, "-c", f"import {name}"], check=True)


def test_ink_imports_no_other_layer() -> None:
    """No `ink` module imports `letters`, `maps` or `_port`, at any level."""
    assert _violations("ink", ("pyntpot.ink",)) == []


def test_letters_imports_only_ink() -> None:
    """No `letters` module imports anything from `pyntpot` but `ink` and itself."""
    assert _violations("letters", ("pyntpot.ink", "pyntpot.letters")) == []


def test_only_adapters_in_maps_import_port() -> None:
    """No `maps` module outside `ADAPTERS` imports `_port`, at any level."""
    found = [
        f"{module}: {target}"
        for module, path in _modules("maps")
        if module not in ADAPTERS
        for node in _imports(path)
        for target in _targets(node, module, path)
        if _under(target, "pyntpot._port")
    ]
    assert found == []


def test_adapters_bind_port_modules_not_names() -> None:
    """An adapter imports `_port` modules, never names from them, except from `_port.style`."""
    found: list[str] = []
    for module, path in _modules("maps"):
        if module not in ADAPTERS:
            continue
        for node in _imports(path):
            if not isinstance(node, ast.ImportFrom):
                continue
            base = _base(node, module, path)
            if not _under(base, "pyntpot._port") or base == NAME_IMPORTABLE:
                continue
            for alias in node.names:
                bound = PACKAGE / "_port" / alias.name
                is_module = bound.with_suffix(".py").is_file() or bound.is_dir()
                if base != "pyntpot._port" or not is_module:
                    found.append(f"{module}: {base}.{alias.name}")
    assert found == []


def test_port_imports_maps_only_inside_functions() -> None:
    """No `_port` module imports `maps` at module level outside `if TYPE_CHECKING:`."""
    found: list[str] = []
    for module, path in _modules("_port"):
        tree = ast.parse(path.read_text(), filename=str(path))
        for stmt in _module_level(tree.body):
            if not isinstance(stmt, ast.Import | ast.ImportFrom):
                continue
            for target in _targets(stmt, module, path):
                if _under(target, "pyntpot.maps"):
                    found.append(f"{module}: {target}")
    assert found == []
