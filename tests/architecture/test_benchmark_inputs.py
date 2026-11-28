"""No benchmark builds a phase-flagged style group directly: it would time whatever the default look is.

`PaperStyle`, `WashStyle` and `BrushStyle` default to the default look (ADR 0069), so a
benchmark that calls one directly, with or without arguments, silently times a different
configuration whenever the look changes. A benchmark builds them through `flags_off`
instead, with the flags it times turned on by name, so it measures what its docstring says.
`brush_from_id` takes `style=None` to mean `BrushStyle()` (ADR 0073), which would get round
that rule, so a benchmark's `brush_from_id` call must pass `style=` too, and not
`style=None`.

The check is a plain function returning the offending calls as strings, empty when the rule
holds. The real-tree test holds `tests/benchmarks/` to it; the self-tests plant each call in
`tmp_path` and show the check reporting it.
"""

import ast
from pathlib import Path

import pytest

from support import REPO_ROOT

#: The style groups whose defaults are the default look, and so move with it.
FLAGGED_GROUPS = frozenset({"PaperStyle", "WashStyle", "BrushStyle"})


def default_look_calls(root: Path) -> list[str]:
    """Name every direct group call, and every `brush_from_id` call without `style=` or with `style=None`, under `root`.

    The `brush_from_id` rule: its `style=None` default means `BrushStyle()`, the default look.
    """
    found: list[str] = []
    for path in sorted(root.rglob("*.py")):
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            name = func.id if isinstance(func, ast.Name) else getattr(func, "attr", None)
            if name in FLAGGED_GROUPS:
                found.append(f"{path.relative_to(root)}:{node.lineno}: {name}")
            elif name == "brush_from_id":
                styles = [k.value for k in node.keywords if k.arg == "style"]
                if not styles or (isinstance(styles[0], ast.Constant) and styles[0].value is None):
                    found.append(f"{path.relative_to(root)}:{node.lineno}: {name} without style=")
    return found


def test_no_benchmark_builds_a_flagged_group_directly() -> None:
    """Every benchmark builds the flagged groups through `flags_off` and gives `brush_from_id` a real `style=`.

    `brush_from_id` with no `style=`, or `style=None`, times the default look as `BrushStyle()` does.
    """
    assert default_look_calls(REPO_ROOT / "tests" / "benchmarks") == []


class TestTheCheckFindsAPlantedCall:
    """The check reports each direct group call planted in a benchmark, and nothing else."""

    @pytest.mark.parametrize(
        ("source", "expected"),
        [
            ("BrushStyle()\n", ["test_a.py:1: BrushStyle"]),
            ("PaperStyle(km_glazing=True)\n", ["test_a.py:1: PaperStyle"]),
            ("style.WashStyle()\n", ["test_a.py:1: WashStyle"]),
            ("replace(BrushStyle(), ink_starve=True)\n", ["test_a.py:1: BrushStyle"]),
            ("flags_off(BrushStyle, ink_starve=True)\n", []),
            ("NibStyle()\n", []),
            ("brush_from_id('RIV1-a', 3.0)\n", ["test_a.py:1: brush_from_id without style="]),
            (
                "brush_from_id('RIV1-a', 3.0, scale=2.0)\n",
                ["test_a.py:1: brush_from_id without style="],
            ),
            (
                "brush_from_id('RIV1-a', 3.0, style=None)\n",
                ["test_a.py:1: brush_from_id without style="],
            ),
            ("brush_from_id('RIV1-a', 3.0, style=flags_off(BrushStyle))\n", []),
        ],
        ids=[
            "no-argument",
            "with-argument",
            "attribute",
            "replaced",
            "flags-off",
            "other-group",
            "brush-default-style",
            "brush-scale-only",
            "brush-style-none",
            "brush-with-style",
        ],
    )
    def test_planted_call(self, tmp_path: Path, source: str, expected: list[str]) -> None:
        """A direct call of a flagged group is reported; `flags_off` and other groups are not."""
        (tmp_path / "test_a.py").write_text(source, encoding="utf-8")
        assert default_look_calls(tmp_path) == expected
