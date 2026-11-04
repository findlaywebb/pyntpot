"""Tests for `span_sweep_score` and `sweep_span_scale`: stretches, kept share and the decision."""

import math

import pytest
from fixtures.span_sweep_score import (
    LENGTH_CAPS,
    SCALES,
    STEP_CAPS,
    ScaleRow,
    Verdict,
    coverage,
    decide,
    decisive,
    judge,
    kept_share,
    stretches,
    sweep,
)
from fixtures.sweep_span_scale import FIXTURES, fixture_route

from pyntpot.ink.polyline import Point
from pyntpot.maps.lettering.label import Span
from pyntpot.maps.lettering.span_line import SPAN_OFFSET_CAPS, span_line
from pyntpot.maps.lettering.span_sides import _convex_side

from support.lettering import arc

#: A straight route of 101 points 1 px apart.
STRAIGHT = [(float(x), 0.0) for x in range(101)]


def _leg(a: Point, b: Point, step: float = 2.0) -> list[Point]:
    """The points from `a` (not included) to `b`, about `step` apart."""
    n = max(int(math.dist(a, b) // step), 1)
    return [(a[0] + (b[0] - a[0]) * i / n, a[1] + (b[1] - a[1]) * i / n) for i in range(1, n + 1)]


def _bend_then_strand(y: float) -> list[Point]:
    """A 90 degree bend, then the route on east, down to `y` and back west past the bend's end."""
    route = arc(90.0, r=100.0)
    for a, b in (((200.0, 50.0), (240.0, 50.0)), ((240.0, 50.0), (240.0, y))):
        route += _leg(a, b)
    return route + _leg((240.0, y), (170.0, y))


def _shares(route: list[Point], i1: int) -> dict[int, float | None]:
    """Each side's kept share over the span `0..i1`, measured as `judge` measures it."""
    _, marks = _convex_side(Span(name="Loughrigg", i0=0, i1=i1), route, 14.0)
    return {
        side: kept_share(
            marks[side],
            span_line(route, 0, i1, side, 14.0 * SPAN_OFFSET_CAPS, clear_px=0.0),
            route[: i1 + 1],
        )
        for side in (1, -1)
    }


def _row(scale: float, decisive_n: int, right: int) -> ScaleRow:
    """A sweep row with only the counts the decision reads."""
    return ScaleRow(scale, decisive_n, 0, 0, 0, decisive_n, right)


def _rows(**at: tuple[int, int]) -> list[ScaleRow]:
    """Every swept scale with no decisive stretch, except those given as `s15=(n, right)`."""
    given = {int(k[1:]) / 10: v for k, v in at.items()}
    return [_row(s, *given.get(s, (0, 0))) for s in SCALES]


class TestStretches:
    """The sliding stretches, by arc length in cap heights."""

    def test_a_straight_route_gives_the_pinned_pairs(self):
        """A 100 px route at 1 px a cap gives 43 stretches of 16, every 2."""
        got = stretches(STRAIGHT, 1.0, 16.0, 2.0)
        assert got == [(s, s + 16) for s in range(0, 85, 2)]
        assert len(got) == 43

    def test_length_and_step_are_in_cap_heights(self):
        """At 2 px a cap the same route gives 18 stretches."""
        assert len(stretches(STRAIGHT, 2.0, 16.0, 2.0)) == 18

    def test_a_route_shorter_than_one_stretch_gives_none(self):
        """Fifteen pixels of route hold no 16-pixel stretch."""
        assert stretches(STRAIGHT[:16], 1.0, 16.0, 2.0) == []

    def test_uneven_spacing_starts_at_the_first_index_at_or_past_the_start(self):
        """Each end is the first point at or past its arc length."""
        route = [(float(x), 0.0) for x in (0, 1, 3, 6, 10, 15, 21, 28)]
        assert stretches(route, 1.0, 10.0, 4.0) == [(0, 4), (3, 5), (4, 6), (5, 7)]


class TestCoverage:
    """How much of a stretch a mark spans, signed."""

    def test_a_full_mark_covers_the_whole_stretch(self):
        """A mark the length of the stretch at an offset covers 1.0."""
        mark = [(float(x), 10.0) for x in range(0, 101, 5)]
        assert coverage(mark, STRAIGHT) == pytest.approx(1.0)

    def test_a_middle_half_mark_covers_half(self):
        """A mark over the middle half covers 0.5."""
        assert coverage([(25.0, 10.0), (75.0, 10.0)], STRAIGHT) == pytest.approx(0.5)

    def test_a_backwards_mark_covers_a_negative_share(self):
        """A mark whose last point is before its first along the stretch is negative."""
        assert coverage([(75.0, -10.0), (25.0, -10.0)], STRAIGHT) == pytest.approx(-0.5)

    def test_a_one_point_mark_covers_nothing(self):
        """A single point spans none of the stretch."""
        assert coverage([(50.0, 10.0)], STRAIGHT) == 0.0


class TestKeptShare:
    """The drawn mark's coverage over the same side's unclipped coverage."""

    FULL = ((0.0, 10.0), (100.0, 10.0))
    HALF = ((25.0, 10.0), (75.0, 10.0))
    BACK = ((75.0, 10.0), (25.0, 10.0))

    def test_a_mark_cut_to_its_middle_half_keeps_half(self):
        """A drawn half of an unclipped full mark keeps 0.5."""
        assert kept_share(self.HALF, self.FULL, STRAIGHT) == pytest.approx(0.5)

    @pytest.mark.parametrize(
        ("drawn", "unclipped"),
        [(HALF, BACK), (BACK, FULL), (FULL, HALF)],
        ids=["unclipped-backwards", "drawn-backwards", "keeps-over-a-quarter-more"],
    )
    def test_an_ambiguous_foot_has_no_share(self, drawn, unclipped):
        """Reversed feet, or keeping over 1.25 of the unclipped mark, give None."""
        assert kept_share(drawn, unclipped, STRAIGHT) is None


class TestJudge:
    """Each stretch falls into one case, by the marks the shipped code draws."""

    def test_a_strand_by_the_inside_mark_makes_the_outside_right(self):
        """A later strand trims the inside mark, so the outside keeps more and is right."""
        route = _bend_then_strand(72.0)
        got = judge(Span(name="Loughrigg", i0=0, i1=59), route, 14.0)
        assert got == Verdict("decisive", 1, 1)
        assert got.right
        assert _shares(route, 59) == {
            1: pytest.approx(1.0, rel=1e-9),
            -1: pytest.approx(0.5016262730189113, rel=1e-9),
        }

    def test_a_strand_by_the_outside_mark_makes_the_outside_wrong(self):
        """A later strand trims the outside mark, so the inside keeps more and is better."""
        route = _bend_then_strand(40.0)
        got = judge(Span(name="Loughrigg", i0=0, i1=59), route, 14.0)
        assert got == Verdict("decisive", 1, -1)
        assert not got.right
        assert _shares(route, 59) == {
            1: pytest.approx(0.6052171144238966, rel=1e-9),
            -1: pytest.approx(1.0, rel=1e-9),
        }

    def test_an_isolated_tight_arc_is_even(self):
        """With nothing to clear, both sides keep all of their own mark, whatever the bend."""
        route = arc(120.0, r=16.0)
        got = judge(Span(name="Loughrigg", i0=0, i1=len(route) - 1), route, 14.0)
        assert got == Verdict("even", 1, 0)
        assert _shares(route, len(route) - 1) == {
            1: pytest.approx(1.0, rel=1e-9),
            -1: pytest.approx(1.0, rel=1e-9),
        }

    def test_a_side_with_no_mark_is_excluded(self):
        """A strand along the inside mark's own line leaves that side empty: not scored."""
        bend = arc(90.0, r=100.0)
        inner = [
            (
                200.0 + 83.2 * math.cos(math.radians(270.0 - 90.0 * i / 59)),
                150.0 + 83.2 * math.sin(math.radians(270.0 - 90.0 * i / 59)),
            )
            for i in range(60)
        ]
        route = bend + _leg((200.0, 50.0), inner[0]) + inner
        assert judge(Span(name="Loughrigg", i0=0, i1=59), route, 14.0) == Verdict(
            "empty-mark", 1, 0
        )

    def test_a_straight_stretch_has_no_outside(self):
        """A straight stretch has no outside to judge."""
        assert judge(Span(name="Loughrigg", i0=0, i1=100), STRAIGHT, 14.0) == Verdict(
            "no-outside", 0, 0
        )


class TestDecisive:
    """The kept-share ratio and nothing else."""

    @pytest.mark.parametrize(
        ("a", "b", "side"),
        [(0.8, 0.64, 0), (0.8, 0.63, 1), (0.0, 0.5, -1), (0.0, 0.0, 0)],
        ids=["exactly-the-ratio", "past-the-ratio", "one-side-nothing", "both-nothing"],
    )
    def test_decisive_only_past_a_quarter_better(self, a, b, side):
        """A side is better only when it keeps more than 1.25 times the other."""
        assert decisive(a, b) == side

    def test_the_exact_ratio_case_is_exact_in_floating_point(self):
        """0.64 times 1.25 is exactly 0.8, so the exactly-the-ratio case sits on the line."""
        assert 0.64 * 1.25 == 0.8


class TestSweep:
    """Counting per scale: only the bend's vote is re-read."""

    def test_a_hard_bend_votes_at_every_scale_and_a_straight_at_none(self):
        """The bend's decisive right verdict counts at every scale; the straight never."""
        bend = arc(120.0, r=100.0)
        rows = sweep(
            [(bend, Verdict("decisive", 1, 1)), (STRAIGHT, Verdict("no-outside", 0, 0))],
            14.0,
            SCALES,
        )
        assert [(r.voted, r.decisive, r.right) for r in rows] == [(1, 1, 1)] * len(SCALES)
        assert rows[9].percent_right == 100.0

    def test_no_decisive_stretch_has_no_share(self):
        """A row with no decisive stretch has no share right."""
        assert _row(1.5, 0, 0).percent_right is None


class TestDecide:
    """The decision rule, on pure data."""

    @pytest.mark.parametrize("n", [0, 29], ids=["none", "twenty-nine"])
    def test_too_few_at_the_current_scale_keeps_it_without_comparing(self, n):
        """Under 30 decisive stretches at 1.5 keeps 1.5 and compares nothing."""
        got = decide(_rows(s15=(n, n), s10=(200, 200)), 16.0, 2.0)
        assert (got.scale, got.changed, got.n_current, got.best) == (1.5, False, n, None)

    def test_a_best_inside_the_interval_keeps_the_current_scale(self):
        """A best scale not clearly ahead of 1.5 leaves 1.5."""
        got = decide(_rows(s15=(40, 30), s12=(40, 34)), 16.0, 2.0)
        assert got.best == pytest.approx(1.2)
        assert (got.scale, got.changed) == (1.5, False)

    def test_a_clearly_better_scale_changes_it(self):
        """1.5 below the best's lower bound moves the value, with the pinned bounds."""
        got = decide(_rows(s15=(320, 160), s18=(320, 304)), 16.0, 2.0)
        assert got.changed
        assert got.scale == pytest.approx(1.8)
        assert got.lower == pytest.approx(0.8241461, rel=1e-6)
        assert got.upper == pytest.approx(0.9940358, rel=1e-6)
        assert got.multiple == pytest.approx(1.5)

    def test_ties_go_to_the_larger_count_then_the_smaller_scale(self):
        """Equal shares to one decimal prefer more evidence, then the smaller scale."""
        rows = _rows(s15=(30, 15), s12=(40, 30), s20=(80, 60), s22=(80, 60))
        assert decide(rows, 16.0, 2.0).best == pytest.approx(2.0)

    def test_a_scale_under_the_floor_is_not_eligible(self):
        """A perfect share on 29 stretches is not the best."""
        rows = _rows(s15=(30, 15), s10=(29, 29), s20=(30, 20))
        assert decide(rows, 16.0, 2.0).best == pytest.approx(2.0)

    def test_a_multiple_of_the_offset_is_found_within_a_tolerance(self):
        """1.8 caps is 1.5 offsets and 1.7 is none."""
        win = decide(_rows(s15=(320, 160), s18=(320, 304)), 16.0, 2.0)
        lose = decide(_rows(s15=(320, 160), s17=(320, 304)), 16.0, 2.0)
        assert SCALES[12] == pytest.approx(1.8)
        assert win.multiple == pytest.approx(1.5)
        assert lose.multiple is None


@pytest.mark.golden
def test_the_y_fenni_track_gives_the_pinned_stretch_count():
    """The Y Fenni fixture, projected as its card is, cuts into the pinned stretches."""
    name, theme, margins = next(f for f in FIXTURES if f[0] == "y-fenni")
    route = fixture_route(name, theme, margins)
    assert len(stretches(route, 14.0, LENGTH_CAPS, STEP_CAPS)) == 43
