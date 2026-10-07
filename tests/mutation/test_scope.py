"""Tests for the changed-function scope: literal diffs and sources in, mutmut patterns out."""

import pytest

from mutation.scope import changed_functions

ONLY_MUTATE = ["src/pyntpot/ink/*", "src/pyntpot/letters/*"]
SHEET = "src/pyntpot/ink/sheet.py"

#: A module with a nested function, a method, a staticmethod, a property and a cached
#: function; the line numbers in the hunks below refer to it.
SOURCE = '''\
"""A sheet."""

import functools

LIMIT = 3


def simplify(points):
    def keep(point):
        return point
    return [keep(p) for p in points]


class Sheet:
    def paint(self):
        return 1

    @staticmethod
    def blank():
        return 0

    @property
    def size(self):
        return 2


@functools.cache
def palette():
    return 4
'''


def _diff(path: str, *hunks: str) -> str:
    """Return a `git diff --unified=0` text for one modified file."""
    header = f"diff --git a/{path} b/{path}\nindex 1a2b3c4..5d6e7f8 100644\n"
    return header + f"--- a/{path}\n+++ b/{path}\n" + "".join(hunks)


@pytest.mark.parametrize(
    ("hunk", "expected"),
    [
        (
            "@@ -11 +11 @@\n-    return []\n+    return [keep(p) for p in points]\n",
            ["pyntpot.ink.sheet.x_simplify*"],
        ),
        (
            "@@ -10 +10 @@\n-        return None\n+        return point\n",
            ["pyntpot.ink.sheet.x_simplify*"],
        ),
        (
            "@@ -16 +16 @@\n-        return 0\n+        return 1\n",
            ["pyntpot.ink.sheet.xǁSheetǁpaint*"],
        ),
        (
            "@@ -18 +18 @@\n-    @classmethod\n+    @staticmethod\n",
            ["pyntpot.ink.sheet.xǁSheetǁblank*"],
        ),
        ("@@ -24 +24 @@\n-        return 1\n+        return 2\n", []),
        ("@@ -29 +29 @@\n-    return 3\n+    return 4\n", []),
        ("@@ -5 +5 @@\n-LIMIT = 2\n+LIMIT = 3\n", []),
        ("@@ -10 +9,0 @@\n-        point = point\n", ["pyntpot.ink.sheet.x_simplify*"]),
    ],
    ids=[
        "function-body",
        "nested-function",
        "method",
        "staticmethod-decorator-only",
        "property",
        "functools-cache",
        "module-constant",
        "deletion-only-hunk-in-body",
    ],
)
def test_a_hunk_maps_to_its_top_level_function(hunk, expected) -> None:
    """Each hunk names the function or method around it, or nothing when mutmut has no mutants."""
    assert changed_functions(_diff(SHEET, hunk), {SHEET: SOURCE}, ONLY_MUTATE) == expected


def test_patterns_are_sorted_and_deduplicated() -> None:
    """Two hunks in one function give one pattern, and patterns come back sorted."""
    diff = _diff(
        SHEET,
        "@@ -9 +9 @@\n-    def keep(p):\n+    def keep(point):\n",
        "@@ -11 +11 @@\n-    return []\n+    return [keep(p) for p in points]\n",
        "@@ -16 +16 @@\n-        return 0\n+        return 1\n",
    )
    assert changed_functions(diff, {SHEET: SOURCE}, ONLY_MUTATE) == [
        "pyntpot.ink.sheet.x_simplify*",
        "pyntpot.ink.sheet.xǁSheetǁpaint*",
    ]


def test_a_file_outside_only_mutate_gives_nothing() -> None:
    """A changed file no `only_mutate` glob matches has no pattern, even inside a function."""
    rings = "src/pyntpot/maps/rings.py"
    diff = _diff(rings, "@@ -11 +11 @@\n-    return []\n+    return points\n")
    assert changed_functions(diff, {rings: SOURCE}, ONLY_MUTATE) == []


def test_a_package_init_drops_init_from_the_module() -> None:
    """A function in a package `__init__.py` is named after the package, as mutmut names it."""
    init = "src/pyntpot/ink/__init__.py"
    diff = _diff(init, "@@ -11 +11 @@\n-    return []\n+    return points\n")
    assert changed_functions(diff, {init: SOURCE}, ONLY_MUTATE) == ["pyntpot.ink.x_simplify*"]


def test_a_deleted_file_gives_nothing_and_needs_no_source() -> None:
    """A file whose new side is `/dev/null` is skipped without reading a source for it."""
    diff = (
        "diff --git a/src/pyntpot/ink/tip.py b/src/pyntpot/ink/tip.py\n"
        "deleted file mode 100644\nindex 1a2b3c4..0000000\n"
        "--- a/src/pyntpot/ink/tip.py\n+++ /dev/null\n"
        "@@ -1,2 +0,0 @@\n-def nib():\n-    return 1\n"
    )
    assert changed_functions(diff, {}, ONLY_MUTATE) == []


def test_a_non_python_file_under_a_glob_gives_nothing() -> None:
    """A data file an `only_mutate` glob matches is not mutated, so it has no pattern."""
    notes = "src/pyntpot/letters/fonts/OFL.txt"
    diff = _diff(notes, "@@ -1 +1 @@\n-Copyright\n+Copyright (c)\n")
    assert changed_functions(diff, {}, ONLY_MUTATE) == []


def test_a_changed_line_that_looks_like_a_header_is_not_one() -> None:
    """An added line reading `+++ ...` inside a hunk does not start a new file."""
    diff = _diff(
        SHEET, "@@ -11 +11,2 @@\n-    return []\n+++ b/src/pyntpot/maps/rings.py\n+    x\n"
    )
    assert changed_functions(diff, {SHEET: SOURCE}, ONLY_MUTATE) == [
        "pyntpot.ink.sheet.x_simplify*"
    ]
