"""Every public field and module attribute is documented where the reference reads it (ADR 0068).

A checked class (public, or reached by a public signature) has one non-empty entry per
field in its docstring's `Attributes:` section, in field order (griffe's member order:
the class body, then `__init__` assignments), and no entry for anything that is not a
field. A field is an attribute not starting with `_`, not a property, not a `ClassVar`,
and not pydantic's `model_config`. No comment stays in the class body outside its
methods, but a tool pragma. A checked module attribute has an attribute docstring.

The self-tests write a tiny `pyntpot` package to `tmp_path`. The real tests compare the
run against the pending sets of the per-lane ratchet files, which can only shrink.
"""

import griffe
import pytest

from . import _pending_ink, _pending_letters, _pending_maps, _pending_roads
from ._field_rule import attribute_doc_violations, field_doc_violations, field_docs
from ._public_surface import LAYERS, ROOT, build, load
from support import REPO_ROOT

PENDING = (
    _pending_ink.FIELD_DOCS
    | _pending_letters.FIELD_DOCS
    | _pending_maps.FIELD_DOCS
    | _pending_roads.FIELD_DOCS
)


def core_object(tmp_path, core: str, name: str) -> griffe.Object:
    """Build `pyntpot.ink.core` from `core` and return its member `name`."""
    found = build(tmp_path, {"ink/core.py": core}).get_member(f"ink.core.{name}")
    assert isinstance(found, griffe.Object)
    return found


def class_problems(tmp_path, core: str) -> list[str]:
    """Return the field rule violations of class `C` in `core`."""
    cls = core_object(tmp_path, core, "C")
    assert isinstance(cls, griffe.Class)
    return field_doc_violations(cls)


def test_a_missing_entry_is_reported(tmp_path):
    """A field with no `Attributes:` entry is reported."""
    core = '''\
        class C:
            """A class.

            Attributes:
                x: The first.
            """

            x: int
            y: int
        '''
    assert class_problems(tmp_path, core) == ["pyntpot.ink.core.C.y: missing entry"]


def test_an_empty_entry_is_reported(tmp_path):
    """An entry with no text is reported."""
    core = '''\
        class C:
            """A class.

            Attributes:
                x:
            """

            x: int
        '''
    assert class_problems(tmp_path, core) == ["pyntpot.ink.core.C.x: empty entry"]


def test_entries_out_of_field_order_are_reported(tmp_path):
    """Entries in another order than the fields are reported."""
    core = '''\
        class C:
            """A class.

            Attributes:
                y: The second.
                x: The first.
            """

            x: int
            y: int
        '''
    assert class_problems(tmp_path, core) == ["pyntpot.ink.core.C: entries out of field order"]


def test_a_stale_entry_is_reported(tmp_path):
    """An entry naming no field of the class is reported."""
    core = '''\
        class C:
            """A class.

            Attributes:
                x: The first.
                gone: A field the class no longer has.
            """

            x: int
        '''
    assert class_problems(tmp_path, core) == ["pyntpot.ink.core.C.gone: stale entry"]


def test_a_property_needs_no_entry(tmp_path):
    """A property is documented by its own docstring, not an `Attributes:` entry."""
    core = '''\
        class C:
            """A class.

            Attributes:
                x: The first.
            """

            x: int

            @property
            def doubled(self) -> int:
                """Twice `x`."""
                return 2 * self.x
        '''
    assert class_problems(tmp_path, core) == []


def test_an_init_attribute_needs_an_entry(tmp_path):
    """An attribute assigned in `__init__` is a field and needs an entry."""
    core = '''\
        class C:
            """A class."""

            def __init__(self, seed: int) -> None:
                """Keep the seed."""
                self.seed = seed
        '''
    assert class_problems(tmp_path, core) == ["pyntpot.ink.core.C.seed: missing entry"]


def test_a_hash_colon_comment_in_a_public_class_is_reported(tmp_path):
    """A `#:` comment on a field is not field documentation and is reported."""
    core = '''\
        class C:
            """A class.

            Attributes:
                x: The first.
            """

            #: The first.
            x: int
        '''
    assert class_problems(tmp_path, core) == ["pyntpot.ink.core.C:8: comment in the class body"]


def test_a_trailing_comment_in_a_public_class_is_reported(tmp_path):
    """A trailing comment on a field line is reported."""
    core = '''\
        class C:
            """A class.

            Attributes:
                x: The first.
            """

            x: int  # the first
        '''
    assert class_problems(tmp_path, core) == ["pyntpot.ink.core.C:8: comment in the class body"]


def test_a_comment_inside_a_method_is_allowed(tmp_path):
    """A comment inside a method body, or a tool pragma in the class body, is allowed."""
    core = '''\
        class C:
            """A class.

            Attributes:
                x: The first.
            """

            x: int  # noqa: RUF012

            def twice(self) -> int:
                """Return twice `x`."""
                # Doubling is the whole point.
                return 2 * self.x
        '''
    assert class_problems(tmp_path, core) == []


def test_a_module_constant_without_a_docstring_is_reported(tmp_path):
    """A module attribute with no attribute docstring is reported; one with it passes."""
    core = 'LIMIT = 3\nDOCUMENTED = 4\n"""The documented limit."""\n'
    bare = core_object(tmp_path, core, "LIMIT")
    documented = core_object(tmp_path, core, "DOCUMENTED")
    assert isinstance(bare, griffe.Attribute)
    assert isinstance(documented, griffe.Attribute)
    assert attribute_doc_violations(bare) == ["pyntpot.ink.core.LIMIT: no attribute docstring"]
    assert attribute_doc_violations(documented) == []


@pytest.fixture(scope="module")
def checked() -> dict[str, list[str]]:
    """The real package's field rule violations, computed once (an immutable result)."""
    return field_docs(load(REPO_ROOT / "src", "pyntpot"), (ROOT, *LAYERS))


def test_every_public_field_and_attribute_is_documented(checked):
    """Every checked class and module attribute keeps the field rule, or is pending."""
    new = {path: problems for path, problems in checked.items() if path not in PENDING}
    listing = "\n".join(f"  {p}" for problems in new.values() for p in problems)
    assert not new, f"fields or attributes not documented by the rule:\n{listing}"


def test_every_pending_field_docs_entry_still_violates(checked):
    """The ratchet only shrinks: every pending field docs entry still breaks the rule."""
    stale = PENDING - set(checked)
    assert not stale, f"pending entries that no longer violate; delete them: {sorted(stale)}"
