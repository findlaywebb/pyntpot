"""Purity gates — no clock reads, minted ids, or non-determinism at runtime.

The package is deterministic by contract: timestamps arrive as arguments and
randomness comes from seeded ``random.Random`` instances. Unguarded calls on the
module-level ``random`` object are not permitted.

Matching scope
--------------
Clock calls caught:
  - ``datetime.now(...)`` / ``datetime.utcnow()`` / ``datetime.today()``.
  - ``date.today()``.
  - ``datetime.datetime.now(...)`` chained attribute forms.
  - ``time.time()`` / ``time.monotonic()`` / ``time.perf_counter()`` etc.
Non-determinism calls caught:
  - Any ``random.<attr>(...)`` call where ``attr`` is NOT ``Random``.
Id minting:
  - Any import of ``uuid``.
Exemptions:
  - The clock and random bans skip the files listed in
    ``exemptions/line_budget.txt`` (empty: nothing is exempt).
Scanning:
  Only production code under ``src/pyntpot`` is scanned (not tests).
"""

import ast

from ._ast_checks import CORE_SRC, _violations
from support.exemptions import read_exemption_lines

_CLOCK_ATTRS = {"now", "utcnow", "today"}
_TIME_ATTRS = {"time", "monotonic", "time_ns", "monotonic_ns", "perf_counter"}

_EXEMPT = frozenset(read_exemption_lines("line_budget.txt"))


def _is_clock_name(node: ast.expr) -> bool:
    """Return True if node is a Name or chained Attribute ending in datetime/date."""
    match node:
        case ast.Name(id="datetime" | "date"):
            return True
        case ast.Attribute(value=inner, attr="datetime" | "date"):
            return _is_clock_name(inner)
        case _:
            return False


def test_reads_no_clock() -> None:
    """The package never reads the clock — timestamps arrive as arguments."""

    def is_clock_call(node: ast.AST) -> bool:
        match node:
            case ast.Call(func=ast.Attribute(value=inner, attr=attr)) if (
                attr in _CLOCK_ATTRS and _is_clock_name(inner)
            ):
                return True
            case _:
                return False

    assert not _violations(CORE_SRC, is_clock_call, _EXEMPT), (
        "package reads the clock — timestamps arrive as arguments"
    )


def test_reads_no_time_module() -> None:
    """The package never calls time.time/monotonic/perf_counter."""

    def is_time_call(node: ast.AST) -> bool:
        match node:
            case ast.Call(func=ast.Attribute(value=ast.Name(id="time"), attr=attr)) if (
                attr in _TIME_ATTRS
            ):
                return True
            case _:
                return False

    assert not _violations(CORE_SRC, is_time_call, _EXEMPT), (
        "package calls time module — elapsed / wall time must not originate here"
    )


def test_has_no_module_level_randomness() -> None:
    """The package never calls module-level random functions (seeded random.Random allowed)."""

    def is_random_call(node: ast.AST) -> bool:
        match node:
            case ast.Call(func=ast.Attribute(value=ast.Name(id="random"), attr=attr)) if (
                attr != "Random"
            ):
                return True
            case _:
                return False

    assert not _violations(CORE_SRC, is_random_call, _EXEMPT), (
        "package uses module-level randomness — use random.Random(seed) for seeded instances"
    )


def test_mints_no_ids() -> None:
    """The package never imports uuid — ids arrive as arguments."""

    def is_uuid_import(node: ast.AST) -> bool:
        match node:
            case ast.Import(names=aliases):
                return any(a.name == "uuid" or a.name.startswith("uuid.") for a in aliases)
            case ast.ImportFrom(module=module):
                return module == "uuid" or (module or "").startswith("uuid.")
            case _:
                return False

    assert not _violations(CORE_SRC, is_uuid_import), (
        "package imports uuid — ids arrive as arguments"
    )
