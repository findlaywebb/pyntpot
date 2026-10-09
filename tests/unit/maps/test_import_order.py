"""The import rule between the layered packages, and the cold import of every module.

`ink` never imports `letters` or `maps`; `letters` imports only `ink` from the
package. The checks read the AST of `src/pyntpot`, counting direct imports only; the
cold-import test proves the chains. import-linter's layers contract enforces the same
direction over the whole graph.
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
