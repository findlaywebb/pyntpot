"""The sea from the coastline chains of a card: open chains and closed island rings."""

import math

from pyntpot.ink.polyline import Pt
from pyntpot.maps.sea import sea_from_coast

CLIP = (-5000.0, -5000.0, 5000.0, 5000.0)


def _circle(cx: float, cy: float, r: float, *, anticlockwise: bool = True, n: int = 48) -> list[Pt]:
    """A closed ring of n points, first point repeated at the end."""
    sign = 1 if anticlockwise else -1
    pts = [
        (
            cx + r * math.cos(sign * 2 * math.pi * k / n),
            cy + r * math.sin(sign * 2 * math.pi * k / n),
        )
        for k in range(n)
    ]
    return [*pts, pts[0]]


def _is_sea(p: Pt, rings: list[list[Pt]]) -> bool:
    """A point is sea when an odd number of the rings hold it (they nest, never cross)."""
    inside = 0
    for ring in rings:
        hit = False
        for i in range(len(ring)):
            (x1, y1), (x2, y2) = ring[i], ring[(i + 1) % len(ring)]
            if (y1 > p[1]) != (y2 > p[1]) and p[0] < x1 + (p[1] - y1) * (x2 - x1) / (y2 - y1):
                hit = not hit
        inside += hit
    return inside % 2 == 1


def _mainland_south() -> list[Pt]:
    """An open coast along y = -3000, land to the south (on its left, walking west)."""
    return [(-5000.0 + 250.0 * k, -3000.0 + 40.0 * math.sin(k)) for k in range(40, -1, -1)]


class TestClosedRings:
    """Closed coastline rings are islands: the sea is everywhere outside them."""

    def test_one_island_is_land_and_the_rest_of_the_card_is_sea(self) -> None:
        """An anticlockwise ring in the card leaves sea at the corners and land at its centre."""
        rings = sea_from_coast([_circle(0.0, 0.0, 1500.0)], CLIP)
        assert rings
        assert _is_sea((-4000.0, 4000.0), rings)
        assert _is_sea((2000.0, 0.0), rings)
        assert not _is_sea((0.0, 0.0), rings)
        assert not _is_sea((1000.0, 500.0), rings)

    def test_an_island_and_an_islet_are_both_land(self) -> None:
        """Two separate rings each cut their own hole, and the water between them is sea."""
        rings = sea_from_coast(
            [_circle(-1500.0, 0.0, 1200.0), _circle(2800.0, 1000.0, 500.0)], CLIP
        )
        assert not _is_sea((-1500.0, 0.0), rings)
        assert not _is_sea((2800.0, 1000.0), rings)
        assert _is_sea((1000.0, 0.0), rings)
        assert _is_sea((2800.0, -2500.0), rings)

    def test_a_ring_wound_the_wrong_way_still_gives_land_inside(self) -> None:
        """A clockwise island, as a badly wound payload draws it, is still the land."""
        rings = sea_from_coast([_circle(0.0, 0.0, 1500.0, anticlockwise=False)], CLIP)
        assert not _is_sea((0.0, 0.0), rings)
        assert _is_sea((-4000.0, 4000.0), rings)


class TestOpenChains:
    """Open chains that cross the card close round its edge on the land side."""

    def test_a_single_open_chain_gives_the_sea_side_only(self) -> None:
        """Land to the south of the chain, sea to the north."""
        rings = sea_from_coast([_mainland_south()], CLIP)
        assert len(rings) == 1
        assert _is_sea((0.0, 3000.0), rings)
        assert not _is_sea((0.0, -4000.0), rings)

    def test_an_open_mainland_and_an_island_leave_sea_between_them(self) -> None:
        """The mainland coast and an island ring both cut the sea."""
        rings = sea_from_coast([_mainland_south(), _circle(0.0, 1000.0, 800.0)], CLIP)
        assert _is_sea((3000.0, 3000.0), rings)
        assert _is_sea((0.0, -1500.0), rings)
        assert not _is_sea((0.0, 1000.0), rings)
        assert not _is_sea((0.0, -4500.0), rings)

    def test_two_chains_round_one_strip_of_land_keep_it_land(self) -> None:
        """A land strip entering at the west and leaving at the east is land; both sides are sea."""
        south = [(float(x), -2000.0 + 30.0 * math.sin(x / 400.0)) for x in range(-5000, 5001, 250)]
        north = [(float(x), 2000.0 + 30.0 * math.sin(x / 400.0)) for x in range(5000, -5001, -250)]
        rings = sea_from_coast([south, north], CLIP)
        assert _is_sea((0.0, 4000.0), rings)
        assert _is_sea((0.0, -4000.0), rings)
        assert not _is_sea((0.0, 0.0), rings)

    def test_no_chains_is_no_sea(self) -> None:
        """A card without a coast has no sea."""
        assert sea_from_coast([], CLIP) == []
