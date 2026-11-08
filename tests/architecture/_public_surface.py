"""Read pyntpot's public surface with griffe, the way the reference site reads it (ADR 0068).

Shared by `test_public_signatures.py` and `_field_rule.py`. `load` parses a package
statically (no import), resolving `TYPE_CHECKING` imports and quoted annotations.
`public_objects` is the set of canonical paths a layer package exports and defines.
`reached` walks every public object's signature transitively and returns each name it
reaches with where it was reached; `signature_violations` keeps the `pyntpot` names that
are not public, and the names the walk could not read (a string outside `Literal[...]`,
an unparsed `Raises:` entry, an unresolved `pyntpot` path, an unknown expression).

It loads only the package under test, so an alias to a third-party or standard-library
name is never resolved: its target path is the external name, checked against
`ALLOWED`. It does not judge whether a name *should* be public, only whether the rule
holds, and it does not apply the field documentation rule (`_field_rule.py` does).
"""

import ast
import textwrap
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

import griffe

#: The packages a name can be defined in, longest first is not needed: none nests another.
LAYERS: tuple[str, ...] = ("pyntpot.ink", "pyntpot.letters", "pyntpot.maps")
ROOT = "pyntpot"

# The reviewed allowlist of external names a public signature may reach (plan 006, S3).
ALLOWED: frozenset[str] = frozenset(
    {
        # builtins
        "KeyError",
        "RuntimeError",
        "ValueError",
        "bool",
        "dict",
        "float",
        "int",
        "list",
        "str",
        "tuple",
        # collections.abc
        "collections.abc.Callable",
        "collections.abc.Mapping",
        "collections.abc.Sequence",
        # httpx
        "httpx.Client",
        # json
        "json.JSONDecodeError",
        # numpy
        "numpy.ndarray",
        "numpy.random.Generator",
        "numpy.typing.ArrayLike",
        # pathlib
        "pathlib.Path",
        # PIL
        "PIL.Image.Image",
        # pydantic
        "pydantic.BaseModel",
        "pydantic.Field",
        # typing
        "typing.Annotated",
        "typing.Any",
        "typing.Literal",
        "typing.NamedTuple",
        "typing.Protocol",
        "typing.Self",
    }
)

_LITERALS = frozenset({"typing.Literal", "typing_extensions.Literal"})
_PROTOCOLS = frozenset({"typing.Protocol", "typing_extensions.Protocol"})
_TYPE_ALIAS = frozenset({"typing.TypeAlias", "typing_extensions.TypeAlias"})
_PUBLIC_DUNDERS = frozenset({"__init__", "__call__"})
_LOOKUP_ERRORS = (KeyError, ValueError, griffe.AliasResolutionError, griffe.CyclicAliasError)


def build(tmp_path: Path, files: dict[str, str]) -> griffe.Module:
    """Write a tiny `pyntpot` package (file paths relative to it) and load it, for self-tests."""
    root = tmp_path / ROOT
    for package in ("", "ink", "letters", "maps"):
        init = root / package / "__init__.py"
        init.parent.mkdir(parents=True, exist_ok=True)
        init.write_text("__all__ = []\n")
    for name, text in files.items():
        (root / name).write_text(textwrap.dedent(text))
    return load(tmp_path, ROOT)


def load(search_path: Path, package: str) -> griffe.Module:
    """Parse `package` from `search_path` statically, Google docstrings, aliases resolved."""
    loaded = griffe.load(
        package, search_paths=[search_path], docstring_parser="google", resolve_aliases=True
    )
    assert isinstance(loaded, griffe.Module)
    return loaded


def layer_of(path: str) -> str:
    """Return the layer package that `path` lies in, else the root package."""
    for layer in LAYERS:
        if path == layer or path.startswith(f"{layer}."):
            return layer
    return ROOT


def _in_package(path: str) -> bool:
    return path == ROOT or path.startswith(f"{ROOT}.")


def _lookup(module: griffe.Module, path: str) -> griffe.Object | None:
    """Return the loaded object at `path`, followed through aliases, or `None`."""
    try:
        found = module.modules_collection.get_member(path)
        if isinstance(found, griffe.Alias):
            found = found.final_target
    except _LOOKUP_ERRORS:
        return None
    return found if isinstance(found, griffe.Object) else None


def canonical(module: griffe.Module, path: str) -> str:
    """Follow `path` to the object that defines it; an external or unknown path stays."""
    found = _lookup(module, path)
    return found.path if found is not None else path


def _exports(module: griffe.Module, layer: str) -> list[str]:
    found = _lookup(module, layer)
    if not isinstance(found, griffe.Module) or found.exports is None:
        return []
    return [name for name in found.exports if isinstance(name, str)]


def _export_paths(module: griffe.Module, layer: str) -> dict[str, str]:
    """Map each `__all__` name of `layer` to the canonical path of what it binds."""
    return {name: canonical(module, f"{layer}.{name}") for name in _exports(module, layer)}


@dataclass
class Surface:
    """The public objects of a package, and the layer exports that break the rule."""

    public: set[str] = field(default_factory=set)
    misplaced: dict[str, set[str]] = field(default_factory=dict)


def public_surface(module: griffe.Module, layers: tuple[str, ...]) -> Surface:
    """Return each layer's exports that its own defining layer exports, and the misplaced."""
    surface = Surface()
    exported = {layer: _export_paths(module, layer) for layer in {*layers, *LAYERS, ROOT}}
    for layer in layers:
        for path in exported[layer].values():
            home = layer_of(path)
            if exported[home].get(path.rsplit(".", 1)[-1]) == path:
                surface.public.add(path)
            if layer not in (home, ROOT):
                surface.misplaced.setdefault(path, set()).add(f"exported from {layer}")
    return surface


def public_objects(module: griffe.Module, layers: tuple[str, ...]) -> set[str]:
    """Return the canonical paths a layer exports from the layer package that defines them."""
    return public_surface(module, layers).public


@dataclass
class Walk:
    """What a walk reached, and where; and what it could not read, and where."""

    reached: dict[str, set[str]] = field(default_factory=lambda: defaultdict(set))
    unread: dict[str, set[str]] = field(default_factory=lambda: defaultdict(set))


def _is_unread(text: str) -> bool:
    """Say whether a string griffe left in an expression is a string constant or unreadable.

    griffe spells every constant as a string: `None`, `...` and numbers are skipped, and a
    string literal or anything that does not parse to a constant is unread.
    """
    try:
        node = ast.parse(text, mode="eval").body
    except SyntaxError:
        return True
    match node:
        case ast.Constant(value=str()):
            return True
        case ast.Constant():
            return False
        case _:
            return True


def _literal_args(expr: griffe.ExprSubscript) -> list[str | griffe.Expr]:
    inner = expr.slice
    return list(inner.elements) if isinstance(inner, griffe.ExprTuple) else [inner]


def _names_in_subscript(expr: griffe.ExprSubscript, where: str, walk: Walk) -> None:
    """Walk a subscript; the direct string arguments of `Literal[...]` are values, skipped."""
    names_in(expr.left, where, walk)
    left = expr.left
    if (
        isinstance(left, griffe.ExprName | griffe.ExprAttribute)
        and left.canonical_path in _LITERALS
    ):
        for arg in _literal_args(expr):
            if not isinstance(arg, str):
                names_in(arg, where, walk)
    else:
        names_in(expr.slice, where, walk)


def _parts(expr: griffe.Expr) -> list[str | griffe.Expr] | None:
    """Return the sub-expressions of a container expression, or `None` for another kind."""
    match expr:
        case griffe.ExprTuple() | griffe.ExprList():
            return list(expr.elements)
        case griffe.ExprBinOp():
            return [expr.left, expr.right]
        case griffe.ExprCall():
            return [expr.function, *expr.arguments]
        case griffe.ExprKeyword() | griffe.ExprUnaryOp():
            return [expr.value]
        case _:
            return None


def names_in(expr: str | griffe.Expr | None, where: str, walk: Walk) -> None:
    """Record every name `expr` reaches in `walk`, failing closed on what it cannot read."""
    match expr:
        case None:
            return
        case str():
            if _is_unread(expr):
                walk.unread[f"string {expr}"].add(where)
        case griffe.ExprName() | griffe.ExprAttribute():
            walk.reached[expr.canonical_path].add(where)
        case griffe.ExprSubscript():
            _names_in_subscript(expr, where, walk)
        case _:
            parts = _parts(expr)
            if parts is None:
                walk.unread[f"expression {expr}"].add(where)
            for part in parts or []:
                names_in(part, where, walk)


def _is_alias_value(attribute: griffe.Attribute, module: griffe.Module) -> bool:
    """Say whether a module attribute is a type alias, whose value is walked."""
    annotation = attribute.annotation
    if annotation is not None:
        return (
            isinstance(annotation, griffe.ExprName | griffe.ExprAttribute)
            and annotation.canonical_path in _TYPE_ALIAS
        )
    match attribute.value:
        case griffe.ExprSubscript():
            return True
        case griffe.ExprBinOp(operator="|"):
            return True
        case griffe.ExprName() as name:
            return isinstance(_lookup(module, name.canonical_path), griffe.Class)
        case _:
            return False


def _walk_function(function: griffe.Function, walk: Walk) -> None:
    for parameter in function.parameters:
        names_in(parameter.annotation, f"{function.path}({parameter.name})", walk)
    names_in(function.returns, f"{function.path} (return)", walk)
    if function.docstring is None:
        return
    for section in function.docstring.parsed:
        if section.kind is not griffe.DocstringSectionKind.raises:
            continue
        for entry in section.value:
            raised = entry.annotation
            where = f"{function.path} (Raises)"
            if isinstance(raised, griffe.ExprName | griffe.ExprAttribute):
                walk.reached[raised.canonical_path].add(where)
            else:
                walk.unread[f"raises {raised}"].add(where)


def _is_protocol(cls: griffe.Class) -> bool:
    return any(
        isinstance(base, griffe.ExprName | griffe.ExprAttribute)
        and base.canonical_path in _PROTOCOLS
        for base in cls.bases
    )


def _walk_class(cls: griffe.Class, module: griffe.Module, walk: Walk) -> None:
    for base in cls.bases:
        names_in(base, f"{cls.path} (base)", walk)
    protocol = _is_protocol(cls)
    for name, member in cls.members.items():
        if member.is_alias:
            continue
        if not (protocol or not name.startswith("_") or name in _PUBLIC_DUNDERS):
            continue
        if isinstance(member, griffe.Function | griffe.Attribute):
            walk_object(member, module, walk)


def walk_object(obj: griffe.Object, module: griffe.Module, walk: Walk) -> None:
    """Record what one object contributes to the signatures it is part of."""
    match obj:
        case griffe.Function():
            _walk_function(obj, walk)
        case griffe.Class():
            _walk_class(obj, module, walk)
        case griffe.TypeAlias():
            names_in(obj.value, f"{obj.path} (alias)", walk)
        case griffe.Attribute() if isinstance(obj.parent, griffe.Module) and _is_alias_value(
            obj, module
        ):
            names_in(obj.value, f"{obj.path} (alias)", walk)
        case griffe.Attribute():
            names_in(obj.annotation, f"{obj.path} (annotation)", walk)
        case _:
            return


def reached(module: griffe.Module, layers: tuple[str, ...]) -> Walk:
    """Walk every public object, and every `pyntpot` object it reaches, once each."""
    walk = Walk()
    queue = sorted(public_objects(module, layers))
    seen: set[str] = set()
    while queue:
        path = queue.pop()
        if path in seen:
            continue
        seen.add(path)
        found = _lookup(module, path)
        if found is None:
            continue
        walk_object(found, module, walk)
        for name in list(walk.reached):
            target = canonical(module, name)
            if target != name:
                walk.reached[target] |= walk.reached.pop(name)
            if _in_package(target) and target not in seen:
                queue.append(target)
    return walk


def signature_violations(module: griffe.Module, layers: tuple[str, ...]) -> dict[str, set[str]]:
    """Return every reached `pyntpot` name that is not public, and every unread name."""
    surface = public_surface(module, layers)
    walk = reached(module, layers)
    found: dict[str, set[str]] = defaultdict(set)
    for path, where in walk.reached.items():
        if not _in_package(path) or path in surface.public:
            continue
        found[path] |= (
            where if _lookup(module, path) is not None else {f"{w} (unresolved)" for w in where}
        )
    for problems in (walk.unread, surface.misplaced):
        for key, where in problems.items():
            found[key] |= where
    return dict(found)


def external_names(module: griffe.Module, layers: tuple[str, ...]) -> dict[str, set[str]]:
    """Return every reached name outside `pyntpot`, with where it was reached."""
    walk = reached(module, layers)
    return {path: where for path, where in walk.reached.items() if not _in_package(path)}
