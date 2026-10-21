"""The import rule between the layered packages, and the cold import of every module.

`ink` never imports `letters` or `maps`; `letters` imports only `ink` from the
package. No module reaches into another module's underscore names: a name another
module imports carries no underscore, checked per defining area (such a name is
module-level, not public API, which is only what an `__all__` lists). The checks read
the AST of `src/pyntpot`, counting direct imports only; the cold-import test proves the
chains. import-linter's layers contract enforces the same direction over the whole
graph.
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
    "pyntpot.maps.card",
    "pyntpot.ink.style",
    "pyntpot.ink.brush_style",
    "pyntpot.letters.style",
    "pyntpot.letters.setting",
    "pyntpot.letters.hand",
    "pyntpot.letters.nib",
    "pyntpot.letters.font",
    "pyntpot.letters.skeleton",
    "pyntpot.letters.trace",
    "pyntpot.maps.style_groups",
    "pyntpot.maps.track",
    "pyntpot.maps.style",
    "pyntpot.maps.providers.base",
    "pyntpot.ink.polyline",
    "pyntpot.ink.curves",
    "pyntpot.ink.chains",
    "pyntpot.ink.noise",
    "pyntpot.ink.sheet",
    "pyntpot.ink.raster",
    "pyntpot.ink.io",
    "pyntpot.ink.paper",
    "pyntpot.ink.pigment",
    "pyntpot.ink.shallow_water",
    "pyntpot.ink.wash",
    "pyntpot.ink.brush",
    "pyntpot.ink.tip",
    "pyntpot.ink.stroke",
    "pyntpot.ink.deposit",
    "pyntpot.ink.stamp",
    "pyntpot.ink.pad",
    "pyntpot.maps.providers.opentopodata",
    "pyntpot.maps.cache",
    "pyntpot.maps.providers.overpass",
    "pyntpot.maps.projection",
    "pyntpot.maps.candidates",
    "pyntpot.maps.candidates.candidate",
    "pyntpot.maps.candidates.roads",
    "pyntpot.maps.candidates.climbs",
    "pyntpot.maps.candidates.places",
    "pyntpot.maps.candidates.landmark_classes",
    "pyntpot.maps.candidates.landmarks",
    "pyntpot.maps.rings",
    "pyntpot.maps.svg_path",
    "pyntpot.maps.track_index",
    "pyntpot.maps.contours",
    "pyntpot.maps.relief",
    "pyntpot.maps.relief_strokes",
    "pyntpot.maps.masks",
    "pyntpot.maps.generalise",
    "pyntpot.maps.rivers",
    "pyntpot.maps.osm_elements",
    "pyntpot.maps.osm",
    "pyntpot.maps.cover",
    "pyntpot.maps.card_geometry",
    "pyntpot.maps.relief_layers",
    "pyntpot.maps.basemap_strokes",
    "pyntpot.maps.layers",
    "pyntpot.maps.vector_layers",
    "pyntpot.maps.candidates.export",
    "pyntpot.maps.basemap",
    "pyntpot.maps.plates",
    "pyntpot.maps.pipeline",
    "pyntpot.maps.annotations",
    "pyntpot.maps.lettering",
    "pyntpot.maps.lettering.label",
    "pyntpot.maps.lettering.span_clear",
    "pyntpot.maps.lettering.placement_costs",
    "pyntpot.maps.lettering.placement_flat",
    "pyntpot.maps.lettering.placement_marks",
    "pyntpot.maps.lettering.placement_window",
    "pyntpot.maps.lettering.placement_lift",
    "pyntpot.maps.lettering.placement_along",
    "pyntpot.maps.lettering.placement_names",
    "pyntpot.maps.lettering.placement",
    "pyntpot.maps.lettering.span_ends",
    "pyntpot.maps.lettering.span_line",
    "pyntpot.maps.lettering.span_sides",
    "pyntpot.maps.lettering.spans",
    "pyntpot.maps.lettering.picks_lines",
    "pyntpot.maps.lettering.picks_settlements",
    "pyntpot.maps.lettering.picks_rivers",
    "pyntpot.maps.lettering.picks_roads",
    "pyntpot.maps.lettering.picks",
    "pyntpot.maps.lettering.pipeline",
    "pyntpot.maps.attribution",
    "pyntpot.maps.compose",
    "pyntpot.maps.strands",
    "pyntpot.maps.lettering_marks",
    "pyntpot.maps.lettering_furniture",
    "pyntpot.maps.lettering_window",
    "pyntpot.maps.cli",
    "pyntpot.maps.painter.job",
    "pyntpot.maps.painter.brushes",
    "pyntpot.maps.painter.water",
    "pyntpot.maps.painter.cover",
    "pyntpot.maps.painter.wood",
    "pyntpot.maps.painter.relief",
    "pyntpot.maps.painter.fluid",
    "pyntpot.maps.painter.pen",
    "pyntpot.maps.painter.ribbon",
    "pyntpot.maps.painter.paper",
    "pyntpot.maps.painter.plates",
    "pyntpot",
)


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


@pytest.mark.parametrize("name", MODULES, ids=MODULES)
def test_each_module_imports_cold(name: str) -> None:
    """A fresh interpreter imports the module without tripping an import cycle."""
    subprocess.run([sys.executable, "-c", f"import {name}"], check=True)


def test_ink_imports_no_other_layer() -> None:
    """No `ink` module imports `letters` or `maps`, at any level."""
    assert _violations("ink", ("pyntpot.ink",)) == []


def test_letters_imports_only_ink() -> None:
    """No `letters` module imports anything from `pyntpot` but `ink` and itself."""
    assert _violations("letters", ("pyntpot.ink", "pyntpot.letters")) == []


#: The defining areas the private-name rule covers, one per renaming slice.
PRIVATE_NAME_AREAS: tuple[str, ...] = ("ink", "letters", "maps", "maps.lettering")


def _area(module: str) -> str:
    """Return the defining area of a module: `ink`, `letters`, `maps.lettering` or `maps`."""
    for area in ("ink", "letters", "maps.lettering"):
        if _under(module, f"pyntpot.{area}"):
            return area
    return "maps" if _under(module, "pyntpot.maps") else ""


def _is_private(name: str) -> bool:
    """Return whether a name is an underscore name, dunders excepted."""
    return name.startswith("_") and not (name.startswith("__") and name.endswith("__"))


def _dotted(node: ast.expr) -> str:
    """Return the dotted name an attribute chain spells, or an empty string."""
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        head = _dotted(node.value)
        return f"{head}.{node.attr}" if head else ""
    return ""


def _from_imports(
    module: str, path: Path, tree: ast.Module, known: set[str]
) -> tuple[dict[str, str], list[tuple[str, str]]]:
    """Return the modules each local name is bound to, and the underscore names imported."""
    bound: dict[str, str] = {}
    found: list[tuple[str, str]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                local = alias.asname or alias.name.partition(".")[0]
                bound[local] = alias.name if alias.asname else local
        elif isinstance(node, ast.ImportFrom):
            base = _base(node, module, path)
            for alias in node.names:
                if f"{base}.{alias.name}" in known:
                    bound[alias.asname or alias.name] = f"{base}.{alias.name}"
                elif _is_private(alias.name) and base in known and base != module:
                    found.append((base, alias.name))
    return bound, found


def _private_reaches(module: str, path: Path, known: set[str]) -> list[tuple[str, str]]:
    """Return (defining module, name) for every underscore name a module takes from another."""
    tree = ast.parse(path.read_text(), filename=str(path))
    bound, found = _from_imports(module, path, tree, known)
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute) and _is_private(node.attr):
            head, _, rest = _dotted(node.value).partition(".")
            owner = ".".join(filter(None, (bound.get(head, ""), rest)))
            if head in bound and owner in known and owner != module:
                found.append((owner, node.attr))
    return found


@pytest.mark.parametrize("area", PRIVATE_NAME_AREAS, ids=PRIVATE_NAME_AREAS)
def test_no_module_imports_another_modules_private_name(area: str) -> None:
    """No module reaches into another module's underscore names."""
    files = sorted(p for p in PACKAGE.rglob("*.py") if "__pycache__" not in p.parts)
    modules = {_module_name(path): path for path in files}
    known = set(modules)
    reaches = [
        f"{module}: {owner}.{name}"
        for module, path in modules.items()
        for owner, name in _private_reaches(module, path, known)
        if _area(owner) == area
    ]
    assert sorted(reaches) == []
