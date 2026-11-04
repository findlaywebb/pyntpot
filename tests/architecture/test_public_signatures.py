"""Every name a public signature reaches is itself public, or on the allowlist (ADR 0068).

Read statically with griffe, the way the reference site reads `src`: a public object is
one a layer package exports from the layer that defines it, and the walk starts there.
It reads parameter and return annotations, `Raises:` entries, base classes, public
methods, fields and properties, protocol members and type alias values, through every
wrapper, and walks each `pyntpot` object it reaches by the same rules, once. A reached
`pyntpot` name that is not public is a violation; a reached external name must be in
`ALLOWED`. What the walk cannot read (a string outside `Literal[...]`, an unparsed
`Raises:` entry, an unresolved `pyntpot` path) is a violation, never skipped.

The self-tests write a tiny `pyntpot` package to `tmp_path` and load it with `load`. The
real tests hold the real package to the rule with no exceptions.
"""

from pathlib import Path

import griffe
import pytest

from ._public_surface import (
    ALLOWED,
    LAYERS,
    ROOT,
    build,
    external_names,
    load,
    signature_violations,
)
from support import REPO_ROOT

ALL_LAYERS = (ROOT, *LAYERS)


def ink_violations(tmp_path: Path, core: str, exports: str = "f") -> dict[str, set[str]]:
    """Build `pyntpot.ink.core` from `core`, export `exports` from `pyntpot.ink`, check it."""
    names = exports.split()
    init = f"from pyntpot.ink.core import {', '.join(names)}\n__all__ = {names!r}\n"
    module = build(tmp_path, {"ink/__init__.py": init, "ink/core.py": core})
    return signature_violations(module, ALL_LAYERS)


PRIVATE = "pyntpot.ink.core._Private"


def test_a_private_class_in_a_union_is_reached(tmp_path):
    """A private class inside an `X | Y` parameter annotation is a violation."""
    core = "class _Private: ...\ndef f(x: int | _Private) -> None: ...\n"
    assert set(ink_violations(tmp_path, core)) == {PRIVATE}


def test_a_private_class_in_an_optional_is_reached(tmp_path):
    """A private class inside `Optional[...]` is a violation."""
    core = """\
        from typing import Optional
        class _Private: ...
        def f(x: Optional[_Private]) -> None: ...
        """
    assert set(ink_violations(tmp_path, core)) == {PRIVATE}


def test_a_private_class_in_a_generic_is_reached(tmp_path):
    """A private class inside a generic such as `list[...]` is a violation."""
    core = "class _Private: ...\ndef f(x: list[_Private]) -> None: ...\n"
    assert set(ink_violations(tmp_path, core)) == {PRIVATE}


def test_a_quoted_reference_inside_a_generic_is_reached(tmp_path):
    """A quoted forward reference nested in a generic, `list["_Private"]`, is a violation."""
    core = 'def f(x: list["_Private"]) -> None: ...\nclass _Private: ...\n'
    assert set(ink_violations(tmp_path, core)) == {PRIVATE}


def test_a_constant_in_annotated_metadata_is_reached(tmp_path):
    """A private constant inside a call in `Annotated` metadata is a violation."""
    core = """\
        from typing import Annotated
        from pydantic import Field
        _LIMIT = 3
        def f(x: Annotated[int, Field(max_length=_LIMIT)]) -> None: ...
        """
    assert set(ink_violations(tmp_path, core)) == {"pyntpot.ink.core._LIMIT"}


def test_a_quoted_forward_reference_is_reached(tmp_path):
    """A whole quoted annotation naming a private class is a violation."""
    core = 'def f(x: "_Private") -> None: ...\nclass _Private: ...\n'
    assert set(ink_violations(tmp_path, core)) == {PRIVATE}


def test_a_type_checking_import_is_resolved_to_its_defining_module(tmp_path):
    """A name imported under `TYPE_CHECKING` is reported at the module that defines it."""
    core = """\
        from typing import TYPE_CHECKING
        if TYPE_CHECKING:
            from pyntpot.ink.other import _Hidden
        def f(x: "_Hidden") -> None: ...
        """
    module = build(
        tmp_path,
        {
            "ink/__init__.py": "from pyntpot.ink.core import f\n__all__ = ['f']\n",
            "ink/core.py": core,
            "ink/other.py": "class _Hidden: ...\n",
        },
    )
    assert set(signature_violations(module, ALL_LAYERS)) == {"pyntpot.ink.other._Hidden"}


def test_a_reexported_name_counts_as_public(tmp_path):
    """A class its layer package re-exports is public, so naming it is no violation."""
    core = "class Thing: ...\ndef f(x: Thing) -> Thing: ...\n"
    assert ink_violations(tmp_path, core, exports="f Thing") == {}


def test_a_name_exported_from_another_layer_is_reported(tmp_path):
    """A layer exporting a name another layer defines is reported as misplaced."""
    module = build(
        tmp_path,
        {
            "ink/core.py": "class Thing: ...\n",
            "maps/__init__.py": "from pyntpot.ink.core import Thing\n__all__ = ['Thing']\n",
        },
    )
    found = signature_violations(module, ALL_LAYERS)
    assert found == {"pyntpot.ink.core.Thing": {"exported from pyntpot.maps"}}


def test_a_return_annotation_is_reached(tmp_path):
    """A private class in a return annotation is a violation."""
    core = "class _Private: ...\ndef f() -> _Private: ...\n"
    assert set(ink_violations(tmp_path, core)) == {PRIVATE}


def test_a_public_method_signature_is_reached(tmp_path):
    """A private class in a public method's parameters is a violation."""
    core = "class _Private: ...\nclass C:\n    def m(self, x: _Private) -> None: ...\n"
    assert set(ink_violations(tmp_path, core, exports="C")) == {PRIVATE}


def test_a_property_return_is_reached(tmp_path):
    """A private class in a property's return annotation is a violation."""
    core = """\
        class _Private: ...
        class C:
            @property
            def p(self) -> _Private: ...
        """
    assert set(ink_violations(tmp_path, core, exports="C")) == {PRIVATE}


def test_a_private_base_class_is_reached(tmp_path):
    """A private base class of a public class is a violation."""
    core = "class _Private: ...\nclass C(_Private): ...\n"
    assert set(ink_violations(tmp_path, core, exports="C")) == {PRIVATE}


def test_a_raises_entry_is_reached(tmp_path):
    """A private exception named in a public docstring's `Raises:` is a violation."""
    core = '''\
        class _Private(Exception): ...
        def f() -> None:
            """Do it.

            Raises:
                _Private: Always.
            """
        '''
    assert set(ink_violations(tmp_path, core)) == {PRIVATE}


def test_a_dataclass_field_is_reached_through_init(tmp_path):
    """A dataclass field's private type is reached through the synthesised `__init__`."""
    core = """\
        from dataclasses import dataclass
        class _Private: ...
        @dataclass
        class C:
            x: _Private
        """
    found = ink_violations(tmp_path, core, exports="C")
    assert "pyntpot.ink.core.C.__init__(x)" in found[PRIVATE]


def test_a_protocol_member_is_reached(tmp_path):
    """A private class in a public protocol's member signature is a violation."""
    core = """\
        from typing import Protocol
        class _Private: ...
        class Source(Protocol):
            def get(self) -> _Private: ...
        """
    assert set(ink_violations(tmp_path, core, exports="Source")) == {PRIVATE}


@pytest.mark.parametrize(
    "alias",
    [
        "from typing import TypeAlias\nAlias: TypeAlias = list[_Private]\n",
        "type Alias = list[_Private]\n",
        "Alias = list[_Private]\n",
    ],
    ids=["type-alias-annotation", "pep-695-type", "unannotated-subscript"],
)
def test_a_type_alias_value_is_reached(tmp_path, alias):
    """A private class in a public type alias's value is a violation, in each alias form."""
    core = f"class _Private: ...\n{alias}def f(x: Alias) -> None: ...\n"
    assert set(ink_violations(tmp_path, core, exports="f Alias")) == {PRIVATE}


def test_a_constant_value_is_not_walked(tmp_path):
    """A public constant's value is not a signature, so a call in it reaches nothing."""
    init = (
        "import importlib.metadata\n"
        "__version__ = importlib.metadata.version('pyntpot')\n"
        "__all__ = ['__version__']\n"
    )
    module = build(tmp_path, {"__init__.py": init})
    assert signature_violations(module, ALL_LAYERS) == {}
    assert external_names(module, ALL_LAYERS) == {}


def test_a_private_name_reached_through_a_private_one_is_reached(tmp_path):
    """The walk is transitive: a private name a private class names is a violation too."""
    core = """\
        class _Inner: ...
        class _Outer:
            inner: _Inner
        def f(x: _Outer) -> None: ...
        """
    found = set(ink_violations(tmp_path, core))
    assert found == {"pyntpot.ink.core._Outer", "pyntpot.ink.core._Inner"}


def test_an_unresolved_package_name_is_reported(tmp_path):
    """A reached `pyntpot` name that resolves to nothing fails closed, as a violation."""
    core = "from pyntpot.ink.other import Missing\ndef f(x: Missing) -> None: ...\n"
    module = build(
        tmp_path,
        {
            "ink/__init__.py": "from pyntpot.ink.core import f\n__all__ = ['f']\n",
            "ink/core.py": core,
            "ink/other.py": "",
        },
    )
    found = signature_violations(module, ALL_LAYERS)
    assert found == {"pyntpot.ink.other.Missing": {"pyntpot.ink.core.f(x) (unresolved)"}}


def test_a_parameter_default_is_not_reached(tmp_path):
    """A private constant used only as a parameter default is no violation."""
    core = "_DEFAULT = 3\ndef f(x: int = _DEFAULT) -> None: ...\n"
    assert ink_violations(tmp_path, core) == {}


def test_an_allowed_third_party_name_is_not_reported(tmp_path):
    """An allowlisted external name is reached as external and is no violation."""
    core = "import numpy as np\ndef f(x: np.ndarray) -> None: ...\n"
    module = build(
        tmp_path,
        {
            "ink/__init__.py": "from pyntpot.ink.core import f\n__all__ = ['f']\n",
            "ink/core.py": core,
        },
    )
    assert signature_violations(module, ALL_LAYERS) == {}
    assert set(external_names(module, ALL_LAYERS)) == {"numpy.ndarray"} <= ALLOWED


def test_a_facade_reexport_does_not_make_a_name_public(tmp_path):
    """A name only `pyntpot.__all__` exports is still private where a signature reaches it."""
    module = build(
        tmp_path,
        {
            "__init__.py": "from pyntpot.ink.core import Thing\n__all__ = ['Thing']\n",
            "ink/__init__.py": "from pyntpot.ink.core import f\n__all__ = ['f']\n",
            "ink/core.py": "class Thing: ...\ndef f(x: Thing) -> None: ...\n",
        },
    )
    assert set(signature_violations(module, ALL_LAYERS)) == {"pyntpot.ink.core.Thing"}


def test_a_literal_string_is_not_reached(tmp_path):
    """The string arguments of `Literal[...]` are values, not names: no violation."""
    core = "from typing import Literal\ndef f(x: Literal['wet', 'dry']) -> None: ...\n"
    assert ink_violations(tmp_path, core) == {}


def test_a_string_outside_a_literal_is_reported(tmp_path):
    """A string left in an annotation outside `Literal[...]` fails closed, as a violation."""
    core = "from typing import Annotated\ndef f(x: Annotated[int, 'a wet wash']) -> None: ...\n"
    assert set(ink_violations(tmp_path, core)) == {"string 'a wet wash'"}


@pytest.fixture(scope="module")
def pyntpot_module() -> griffe.Module:
    """The real package, parsed once (an immutable object)."""
    return load(REPO_ROOT / "src", "pyntpot")


def _listing(found: dict[str, set[str]]) -> str:
    return "\n".join(f"  {path}: {', '.join(sorted(found[path]))}" for path in sorted(found))


def test_no_public_signature_names_a_private_name(pyntpot_module):
    """Every `pyntpot` name a public signature reaches is public."""
    found = signature_violations(pyntpot_module, ALL_LAYERS)
    assert not found, f"public signatures reach names that are not public:\n{_listing(found)}"


def test_no_public_signature_names_an_unknown_external_name(pyntpot_module):
    """Every external name a public signature reaches is in `ALLOWED`."""
    found = external_names(pyntpot_module, ALL_LAYERS)
    unknown = {path: where for path, where in found.items() if path not in ALLOWED}
    assert not unknown, f"external names not in ALLOWED:\n{_listing(unknown)}"


def test_every_allowed_name_is_reached(pyntpot_module):
    """No `ALLOWED` entry is stale: each one is reached by some public signature."""
    stale = ALLOWED - set(external_names(pyntpot_module, ALL_LAYERS))
    assert not stale, f"ALLOWED names no public signature reaches: {sorted(stale)}"
