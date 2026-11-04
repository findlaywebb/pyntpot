"""Apply the field documentation rule to the public surface (ADR 0068).

Shared by `test_field_docs.py`. `field_doc_violations` checks one class: every field has
exactly one non-empty `Attributes:` entry, in field order, with no stale or duplicate
entries and no comment in the class body outside its methods. `attribute_doc_violations`
checks a module attribute or type alias for an attribute docstring. `field_docs` runs both
over the public objects and the names the signature walk reaches.

It reads the griffe objects `_public_surface.py` loads and does not walk signatures or
decide what is public itself.
"""

import ast
import io
import textwrap
import tokenize

import griffe

from ._public_surface import _lookup, public_objects, signature_violations

_CLASS_VARS = frozenset({"typing.ClassVar", "typing_extensions.ClassVar"})
_PRAGMAS = ("# type:", "# noqa", "# pragma")


def _is_field(name: str, member: griffe.Object | griffe.Alias) -> bool:
    if name.startswith("_") or name == "model_config" or member.is_alias:
        return False
    if not isinstance(member, griffe.Attribute) or "property" in member.labels:
        return False
    annotation = member.annotation
    if isinstance(annotation, griffe.ExprSubscript):
        annotation = annotation.left
    return not (
        isinstance(annotation, griffe.ExprName | griffe.ExprAttribute)
        and annotation.canonical_path in _CLASS_VARS
    )


def _attribute_entries(cls: griffe.Class) -> list[tuple[str, str]]:
    if cls.docstring is None:
        return []
    return [
        (entry.name, entry.description.strip())
        for section in cls.docstring.parsed
        if section.kind is griffe.DocstringSectionKind.attributes
        for entry in section.value
    ]


def _comment_lines(cls: griffe.Class) -> list[int]:
    """Return the line numbers of non-pragma comments in a class body outside its methods."""
    source = textwrap.dedent("\n".join(cls.lines))
    node = ast.parse(source).body[0]
    methods = [
        range(min([d.lineno for d in item.decorator_list] + [item.lineno]), item.end_lineno + 1)
        for item in getattr(node, "body", [])
        if isinstance(item, ast.FunctionDef | ast.AsyncFunctionDef) and item.end_lineno
    ]
    found = []
    for token in tokenize.generate_tokens(io.StringIO(source).readline):
        line = token.start[0]
        if token.type != tokenize.COMMENT or token.string.startswith(_PRAGMAS):
            continue
        if not any(line in method for method in methods):
            found.append(line + (cls.lineno or 1) - 1)
    return found


def field_doc_violations(cls: griffe.Class) -> list[str]:
    """Return each way a class's `Attributes:` section or body breaks the field rule."""
    fields = [name for name, member in cls.members.items() if _is_field(name, member)]
    entries = _attribute_entries(cls)
    named = [name for name, _ in entries]
    found = [f"{cls.path}.{name}: missing entry" for name in fields if name not in named]
    found += [f"{cls.path}.{name}: empty entry" for name, text in entries if not text]
    found += [f"{cls.path}.{name}: stale entry" for name in named if name not in fields]
    found += [f"{cls.path}.{name}: duplicate entry" for name in set(named) if named.count(name) > 1]
    listed = [name for name in named if name in fields]
    if listed != [name for name in fields if name in listed]:
        found.append(f"{cls.path}: entries out of field order")
    found += [f"{cls.path}:{line}: comment in the class body" for line in _comment_lines(cls)]
    return found


def attribute_doc_violations(attr: griffe.Attribute | griffe.TypeAlias) -> list[str]:
    """Return the violation of a module attribute with no attribute docstring, if any."""
    if attr.docstring is None or not attr.docstring.value.strip():
        return [f"{attr.path}: no attribute docstring"]
    return []


def field_docs(module: griffe.Module, layers: tuple[str, ...]) -> dict[str, list[str]]:
    """Return the checked classes and module attributes that break the rule, with why."""
    checked = public_objects(module, layers) | set(signature_violations(module, layers))
    found: dict[str, list[str]] = {}
    for path in sorted(checked):
        obj = _lookup(module, path)
        if isinstance(obj, griffe.Class):
            problems = field_doc_violations(obj)
        elif isinstance(obj, griffe.TypeAlias) or (
            isinstance(obj, griffe.Attribute) and isinstance(obj.parent, griffe.Module)
        ):
            problems = attribute_doc_violations(obj)
        else:
            problems = []
        if problems:
            found[path] = problems
    return found
