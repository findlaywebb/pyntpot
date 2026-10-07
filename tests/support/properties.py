"""Shared Hypothesis settings for the property tests.

`UNTIMED` switches off Hypothesis's per-example deadline. A wall-clock deadline is a
flake source on shared runners and under mutmut's trampolines, and these tests prove
invariants, not speed. Every `@given` test is decorated `@UNTIMED`.
"""

from hypothesis import settings

UNTIMED = settings(deadline=None)
