"""The tutorial scripts in examples/ import only public names.

Public means a name in the `__all__` of `pyntpot`, `pyntpot.ink`, `pyntpot.letters` or
`pyntpot.maps`, read by AST so no package is imported. Besides those, a script imports
only the standard library, numpy and Pillow, and never by relative import, `importlib` or
`__import__`. `EXAMPLES` pins the rung scripts, so the import check cannot pass on an
empty directory; any other script in examples/ is checked without joining the pin.
"""

import ast
import sys
from pathlib import Path

from support import REPO_ROOT
from support.examples import EXAMPLES_DIR

#: The tutorial scripts' stems, one per rung.
EXAMPLES: tuple[str, ...] = (
    "brush_stroke",
    "composition",
    "lettering",
    "nib_line",
    "paper",
    "pigments",
    "route_map",
    "wash",
)

_PUBLIC_MODULES = ("pyntpot", "pyntpot.ink", "pyntpot.letters", "pyntpot.maps")
_THIRD_PARTY = frozenset({"numpy", "PIL", "pyntpot"})


def _module_all(module: str) -> frozenset[str]:
    """Return the string constants of a public module's `__all__` assignment."""
    path = REPO_ROOT / "src" / Path(*module.split(".")) / "__init__.py"
    for node in ast.parse(path.read_text(), filename=str(path)).body:
        match node:
            case (
                ast.Assign(targets=[ast.Name(id="__all__")], value=ast.List(elts=elts))
                | ast.AnnAssign(target=ast.Name(id="__all__"), value=ast.List(elts=elts))
            ):
                return frozenset(
                    e.value
                    for e in elts
                    if isinstance(e, ast.Constant) and isinstance(e.value, str)
                )
            case _:
                continue
    raise AssertionError(f"{path.relative_to(REPO_ROOT)} has no `__all__` list")


def _allowed_top_level(module: str) -> bool:
    """Return whether a module's top-level package is the standard library, numpy, Pillow or pyntpot."""
    top = module.split(".", maxsplit=1)[0]
    return top != "importlib" and (top in sys.stdlib_module_names or top in _THIRD_PARTY)


def _is_bad_from_import(node: ast.ImportFrom, public: dict[str, frozenset[str]]) -> bool:
    """Return whether a `from ... import ...` is relative, private, or outside the allowed packages."""
    if node.level or node.module is None:
        return True
    if node.module.split(".", maxsplit=1)[0] != "pyntpot":
        return not _allowed_top_level(node.module)
    names = public.get(node.module)
    return names is None or any(alias.name not in names for alias in node.names)


def _is_violation(node: ast.AST, public: dict[str, frozenset[str]]) -> bool:
    """Return whether one AST node is an import an example may not make."""
    match node:
        case ast.Import(names=aliases):
            return any(
                a.name.split(".", maxsplit=1)[0] == "pyntpot" or not _allowed_top_level(a.name)
                for a in aliases
            )
        case ast.ImportFrom():
            return _is_bad_from_import(node, public)
        case ast.Call(func=ast.Name(id="__import__") | ast.Attribute(attr="__import__")):
            return True
        case _:
            return False


def test_every_pinned_example_exists() -> None:
    """Each pinned tutorial script is in examples/."""
    missing = [stem for stem in EXAMPLES if not (EXAMPLES_DIR / f"{stem}.py").is_file()]
    assert not missing, f"pinned tutorial scripts missing from examples/: {missing}"


def test_examples_import_only_public_names() -> None:
    """An example imports pyntpot names only from a public module's __all__, and otherwise only the standard library, numpy and Pillow."""
    public = {module: _module_all(module) for module in _PUBLIC_MODULES}
    found: list[str] = []
    for path in sorted(EXAMPLES_DIR.glob("*.py")):
        tree = ast.parse(path.read_text(), filename=str(path))
        found.extend(
            f"{path.relative_to(REPO_ROOT)}:{getattr(node, 'lineno', '?')}"
            for node in ast.walk(tree)
            if _is_violation(node, public)
        )
    assert not found, f"examples import a private or disallowed name: {sorted(found)}"
