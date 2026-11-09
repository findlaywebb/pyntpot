"""Each built-in pigment's hex is written once in `src/`, in the module that holds the registry.

A second literal of any of the 25 hexes is a copy that can drift from the registry. The check
reads the AST of every module under `src/pyntpot` and lists, for each built-in hex, the
modules that hold it as a string constant.
"""

import ast

from pyntpot.ink import PIGMENT_REGISTRY

from support import REPO_ROOT

SRC = REPO_ROOT / "src" / "pyntpot"


def _literals(path) -> set[str]:
    """Return every string constant in one module, lower-cased."""
    tree = ast.parse(path.read_text(), filename=str(path))
    return {
        node.value.lower()
        for node in ast.walk(tree)
        if isinstance(node, ast.Constant) and isinstance(node.value, str)
    }


def test_each_built_in_hex_is_a_literal_in_one_module_only():
    """No hex of a registry pigment appears as a literal outside `ink/pigment_table.py`."""
    holders: dict[str, list[str]] = {str(p.colour): [] for p in PIGMENT_REGISTRY.pigments}
    for path in sorted(SRC.rglob("*.py")):
        found = _literals(path)
        for hex_s, modules in holders.items():
            if hex_s in found:
                modules.append(path.relative_to(SRC).as_posix())
    assert {h: m for h, m in holders.items() if m != ["ink/pigment_table.py"]} == {}
