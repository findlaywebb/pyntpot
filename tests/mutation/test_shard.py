"""Tests for the nightly shards: literal module tables and sources in, patterns out."""

import pytest

from mutation.shard import module_costs, shard_patterns

ONLY_MUTATE = ["src/pyntpot/ink/*", "src/pyntpot/letters/*"]


def _patterns(*modules: str) -> list[str]:
    """Return the sorted two-pattern form of each module."""
    return sorted(pattern for module in modules for pattern in (f"{module}.x_*", f"{module}.xǁ*"))


def test_the_assignment_is_pinned_for_a_literal_table() -> None:
    """Largest first, a cost tie broken by name, and a running-cost tie to the lowest shard."""
    modules = {
        "pyntpot.ink.wash": 300,
        "pyntpot.ink.sheet": 100,
        "pyntpot.ink.polyline": 300,
        "pyntpot.ink.brush": 400,
    }
    assert shard_patterns(modules, 3) == [
        _patterns("pyntpot.ink.brush"),
        _patterns("pyntpot.ink.polyline", "pyntpot.ink.sheet"),
        _patterns("pyntpot.ink.wash"),
    ]


def test_two_shards_take_the_largest_modules_first() -> None:
    """Listed smallest first, the modules are still placed largest first, which balances them."""
    modules = {
        "pyntpot.ink.d": 100,
        "pyntpot.ink.c": 200,
        "pyntpot.ink.b": 300,
        "pyntpot.ink.a": 500,
    }
    assert shard_patterns(modules, 2) == [
        _patterns("pyntpot.ink.a", "pyntpot.ink.d"),
        _patterns("pyntpot.ink.b", "pyntpot.ink.c"),
    ]


def test_one_shard_holds_every_module() -> None:
    """With a count of 1 the single shard has every module's patterns."""
    modules = {"pyntpot.ink.polyline": 355, "pyntpot.letters.hand": 229}
    assert shard_patterns(modules, 1) == [_patterns("pyntpot.ink.polyline", "pyntpot.letters.hand")]


def test_a_package_init_module_gets_the_two_pattern_form() -> None:
    """A package module gets `x_*` and `xǁ*`, never `.*`, which would match its submodules."""
    assert shard_patterns({"pyntpot.ink": 14}, 1) == [["pyntpot.ink.x_*", "pyntpot.ink.xǁ*"]]


@pytest.mark.parametrize("count", [0, 3], ids=["zero", "more-than-modules"])
def test_a_count_that_would_leave_a_shard_empty_raises(count) -> None:
    """No shard may be empty, because `mutmut run` with no pattern tests every mutant."""
    with pytest.raises(ValueError, match="shard count"):
        shard_patterns({"pyntpot.ink.polyline": 355, "pyntpot.letters.hand": 229}, count)


@pytest.mark.parametrize(
    ("path", "source", "expected"),
    [
        (
            "src/pyntpot/ink/polyline.py",
            "def simplify():\n    return 1\n",
            {"pyntpot.ink.polyline": 2},
        ),
        ("src/pyntpot/ink/__init__.py", "def simplify():\n    return 1\n", {"pyntpot.ink": 2}),
        (
            "src/pyntpot/ink/sheet.py",
            "class Sheet:\n    @staticmethod\n    def blank():\n        return 0\n",
            {"pyntpot.ink.sheet": 4},
        ),
        (
            "src/pyntpot/ink/sheet.py",
            "class Sheet:\n    @property\n    def size(self):\n        return 2\n",
            {},
        ),
        (
            "src/pyntpot/ink/palette.py",
            "import functools\n\n\n@functools.cache\ndef palette():\n    return 4\n",
            {},
        ),
        ("src/pyntpot/ink/limits.py", "LIMIT = 3\n", {}),
        ("src/pyntpot/maps/rings.py", "def ring():\n    return 1\n", {}),
        ("src/pyntpot/letters/fonts/OFL.txt", "def ring():\n    return 1\n", {}),
    ],
    ids=[
        "plain-function",
        "package-init",
        "staticmethod",
        "property-only",
        "functools-cache-only",
        "no-function",
        "outside-only-mutate",
        "non-python-under-glob",
    ],
)
def test_module_costs_keep_modules_mutmut_mutates(path, source, expected) -> None:
    """A module counts when a glob matches its `.py` path and it has a function mutmut mutates."""
    assert module_costs({path: source}, ONLY_MUTATE) == expected
