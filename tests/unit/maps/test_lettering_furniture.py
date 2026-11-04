"""Tests for the furniture beside a name: a leader's pin is an open ring facing its leader."""

import itertools
import math

import numpy as np
import pytest

from pyntpot.ink.polyline import Point
from pyntpot.letters.hand import Hand
from pyntpot.letters.nib import mark_width_px
from pyntpot.maps import lettering_marks
from pyntpot.maps.lettering.label import Label
from pyntpot.maps.lettering_furniture import (
    leader,
    leader_angle,
    pin,
    pin_gap_px,
    pin_radius,
)
from pyntpot.maps.style import Style

#: The Lynton and Exmoor Museum's pin, in display pixels on a card.
MUSEUM = (412.0, 268.0)

#: How many directions round the pin a leader is sent in.
TURNS = 72


@pytest.fixture(scope="module")
def style() -> Style:
    """The packaged default style, read once: it is never changed."""
    return Style.default()


@pytest.fixture(scope="module")
def hand(style: Style) -> Hand:
    """The default style's hand, opened once: it is never changed."""
    return Hand(style.face, style.hand)


def _pinned(turn: float, size: float = 20.0, run: float = 40.0) -> Label:
    """The museum's label, its leader running `run` px from the pin in direction `turn`."""
    px, py = MUSEUM
    name = (px + run * math.cos(turn), py + run * math.sin(turn))
    return Label(name="Lynton and Exmoor Museum", px=px, py=py, size=size, leader=(MUSEUM, name))


def _furniture(hand: Hand, style: Style, label: Label) -> tuple[list[Point], list[Point]]:
    """The pin's and the leader's points as `label_marks` draws them for the default nib."""
    marks = lettering_marks.label_marks(hand, label, style.nib)
    ring = [m.pts for m in marks if m.role == "pin"]
    line = [m.pts for m in marks if m.role == "leader"]
    assert len(ring) == len(line) == 1
    return ring[0], line[0]


def _gap_bisector(ring: list[Point]) -> float:
    """The direction from the pin's centre to the middle of the chord across its gap."""
    (x0, y0), (x1, y1) = ring[0], ring[-1]
    return math.atan2((y0 + y1) / 2 - MUSEUM[1], (x0 + x1) / 2 - MUSEUM[0])


def _turn_apart(a: float, b: float) -> float:
    """The smallest angle between two directions, in radians."""
    return abs((a - b + math.pi) % math.tau - math.pi)


def _segment_gap(p: Point, a: Point, b: Point) -> float:
    """The distance from a point to a segment."""
    dx, dy = b[0] - a[0], b[1] - a[1]
    t = ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / ((dx * dx + dy * dy) or 1.0)
    t = min(max(t, 0.0), 1.0)
    return math.hypot(p[0] - a[0] - t * dx, p[1] - a[1] - t * dy)


def _clearance(line: list[Point], ring: list[Point]) -> float:
    """The closest the leader's centreline comes to the arc's, checked both ways."""
    one = min(_segment_gap(p, a, b) for p in line for a, b in itertools.pairwise(ring))
    two = min(_segment_gap(p, a, b) for p in ring for a, b in itertools.pairwise(line))
    return min(one, two)


class TestOpenPin:
    """A leader's pin is a ring with a gap, turned so the leader comes in through it."""

    @pytest.mark.parametrize("size", [11.0, 20.0, 40.0], ids=["small", "shipped", "large"])
    def test_the_gap_faces_the_leader_at_every_angle(
        self, hand: Hand, style: Style, size: float
    ) -> None:
        """Over 72 leader directions the gap is centred where the leader leaves the ring."""
        for i in range(TURNS):
            turn = i * math.tau / TURNS - math.pi
            ring, line = _furniture(hand, style, _pinned(turn, size))
            crossing = leader_angle(line, MUSEUM, pin_radius(_pinned(turn, size)))
            assert _turn_apart(_gap_bisector(ring), crossing) < 1e-6

    @pytest.mark.parametrize("size", [11.0, 20.0, 40.0], ids=["small", "shipped", "large"])
    def test_a_leader_bent_little_leaves_its_ring_towards_its_name(
        self, hand: Hand, size: float
    ) -> None:
        """Over 72 directions a leader drawn from one fixed generator leaves the ring within 20 degrees of its name."""
        # The generator is the leader's own, not the label's: in `label_marks` the name's
        # glyphs draw from the label's generator first, so the bend it leaves the leader
        # moves with any change to how the letters are stroked.
        for i in range(TURNS):
            turn = i * math.tau / TURNS - math.pi
            label = _pinned(turn, size)
            assert label.leader is not None
            line = leader(hand, label.leader, np.random.default_rng(0))
            crossing = leader_angle(line, MUSEUM, pin_radius(label))
            assert _turn_apart(crossing, turn) < math.radians(20.0)

    @pytest.mark.parametrize("size", [11.0, 20.0, 40.0], ids=["small", "shipped", "large"])
    def test_the_leader_passes_through_the_gap_clear_of_the_arc(
        self, hand: Hand, style: Style, size: float
    ) -> None:
        """Over 72 directions the leader's ink and the arc's ink never touch, with a bristle's 0.55 px jitter spare."""
        leader_px = mark_width_px(style.nib, "leader", size)
        ring_px = mark_width_px(style.nib, "pin", size)
        touch = (leader_px + ring_px) / 2 + 0.55
        worst = math.inf
        for i in range(TURNS):
            ring, line = _furniture(hand, style, _pinned(i * math.tau / TURNS, size))
            worst = min(worst, _clearance(line, ring))
        assert worst > touch, f"the leader comes {worst:.2f} px from the arc"

    def test_the_leader_runs_from_the_pins_centre_to_the_name(self, hand: Hand) -> None:
        """The leader starts on the ring's centre, inside it, and ends on its name."""
        label = _pinned(0.0)
        assert label.leader is not None
        line = leader(hand, label.leader, np.random.default_rng(0))
        assert line[0] == pytest.approx(MUSEUM)
        assert line[-1] == pytest.approx((452.0, 268.0))

    def test_the_gap_is_the_leaders_pen_two_ring_pens_and_the_bristles(self, style: Style) -> None:
        """At the shipped size the gap is 0.612 + 2 x 1.275 + 1.1 px across."""
        leader_px = mark_width_px(style.nib, "leader", 20.0)
        ring_px = mark_width_px(style.nib, "pin", 20.0)
        assert pin_gap_px(leader_px, ring_px) == pytest.approx(4.262)

    def test_the_arcs_ends_are_the_gap_apart(self, hand: Hand) -> None:
        """The wander keeps the arc's ends, so the chord across the gap is the width asked for."""
        ring = pin(hand, _pinned(1.0), np.random.default_rng(5), gap_at=1.0, gap_px=3.162)
        (x0, y0), (x1, y1) = ring[0], ring[-1]
        assert math.hypot(x1 - x0, y1 - y0) == pytest.approx(3.162)

    def test_an_open_ring_is_pinned(self, hand: Hand) -> None:
        """An east-facing gap at the shipped size starts and ends the arc at the pinned points."""
        ring = pin(hand, _pinned(0.0), np.random.default_rng(0), gap_at=0.0, gap_px=3.162)
        assert len(ring) == 12
        assert ring[0] == pytest.approx((414.3109390, 269.581))
        assert ring[-1] == pytest.approx((414.3109390, 266.419))

    def test_a_gap_wider_than_the_ring_leaves_half_of_it(self, hand: Hand) -> None:
        """A gap wider than the ring's diameter opens it to a half circle, not past it."""
        ring = pin(hand, _pinned(0.0), np.random.default_rng(0), gap_at=0.0, gap_px=50.0)
        assert ring[0] == pytest.approx((MUSEUM[0], MUSEUM[1] + 2.8))
        assert ring[-1] == pytest.approx((MUSEUM[0], MUSEUM[1] - 2.8))


class TestClosedPin:
    """A pin given no gap is the closed ring of fourteen sides."""

    def test_a_pin_without_a_gap_closes(self, hand: Hand) -> None:
        """With no gap direction the ring ends where it starts, after fourteen sides."""
        ring = pin(hand, _pinned(0.0), np.random.default_rng(0))
        assert len(ring) == 15
        assert ring[0] == pytest.approx(ring[-1])
        assert ring[0] == pytest.approx((414.8, 268.0))

    def test_a_gap_of_no_width_closes(self, hand: Hand) -> None:
        """A gap direction with no width draws the same closed ring as no gap at all."""
        label = _pinned(0.0)
        shut = pin(hand, label, np.random.default_rng(2))
        assert pin(hand, label, np.random.default_rng(2), gap_at=1.0, gap_px=0.0) == shut

    def test_a_name_without_a_leader_takes_no_pin(self, hand: Hand, style: Style) -> None:
        """A label with no leader draws neither a ring nor a leader beside its name."""
        px, py = MUSEUM
        label = Label(name="Lynton and Exmoor Museum", px=px, py=py, size=20.0)
        marks = lettering_marks.label_marks(hand, label, style.nib)
        assert not {"pin", "leader"} & {m.role for m in marks}


class TestDeterminism:
    """The same pinned label draws the same pin and leader."""

    def test_the_same_label_draws_the_same_pin_and_leader(self, hand: Hand, style: Style) -> None:
        """Two draws of one label give identical rings and leaders."""
        label = _pinned(2.0)
        assert _furniture(hand, style, label) == _furniture(hand, style, label)

    def test_a_pin_from_the_same_seed_is_the_same(self, hand: Hand) -> None:
        """One seed and one gap give the same arc twice."""
        label = _pinned(0.5)
        one = pin(hand, label, np.random.default_rng(9), gap_at=0.5, gap_px=3.0)
        two = pin(hand, label, np.random.default_rng(9), gap_at=0.5, gap_px=3.0)
        assert one == two

    def test_the_pin_and_leader_marks_are_pinned(self, hand: Hand, style: Style) -> None:
        """The pin and leader marks for a north-east leader keep their pinned ends."""
        marks = [
            m
            for m in lettering_marks.label_marks(hand, _pinned(-math.pi / 4), style.nib)
            if m.role in {"pin", "leader"}
        ]
        assert [m.role for m in marks] == ["pin", "leader"]
        ring, line = marks[0].pts, marks[1].pts
        assert len(ring) == 11
        assert ring[0] == pytest.approx((414.4496701, 266.6438597))
        assert ring[-1] == pytest.approx((410.2728206, 265.7961735))
        assert line[0] == pytest.approx(MUSEUM)
        assert line[-1] == pytest.approx((440.2842712, 239.7157288))
