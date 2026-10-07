"""Properties of `clip_ring`: the clip stays in the box, loses area, and keeps or drops whole rings."""

import math

from hypothesis import given
from hypothesis import strategies as st

from pyntpot.ink.polyline import Pt
from pyntpot.maps.rings import clip_ring, signed_area

from support.properties import UNTIMED

Box = tuple[float, float, float, float]


def _floats(lo: float, hi: float) -> st.SearchStrategy[float]:
    """A finite float in a closed range."""
    return st.floats(lo, hi, allow_nan=False, allow_infinity=False)


def _ring(centre: Pt, radius: float, angles: list[float]) -> list[Pt]:
    """A convex ring: points on a circle at sorted angles."""
    return [(centre[0] + radius * math.cos(t), centre[1] + radius * math.sin(t)) for t in angles]


ANGLES = st.lists(
    st.floats(0, 2 * math.pi, exclude_max=True, allow_nan=False, allow_infinity=False),
    min_size=3,
    max_size=12,
    unique=True,
).map(sorted)
CENTRES = st.tuples(_floats(-200, 200), _floats(-200, 200))
RINGS = st.builds(_ring, CENTRES, _floats(1, 300), ANGLES)


@st.composite
def boxes(draw: st.DrawFn) -> Box:
    """A box from [-250, 250], each side at least 1."""
    xmin = draw(_floats(-250, 249))
    ymin = draw(_floats(-250, 249))
    xmax = draw(_floats(xmin + 1, 250))
    ymax = draw(_floats(ymin + 1, 250))
    return (xmin, ymin, xmax, ymax)


def _box_ring(box: Box) -> list[Pt]:
    """The box's four corners as a ring."""
    xmin, ymin, xmax, ymax = box
    return [(xmin, ymin), (xmax, ymin), (xmax, ymax), (xmin, ymax)]


def _extent(*rings: list[Pt]) -> float:
    """The largest absolute coordinate over some rings."""
    return max(abs(c) for ring in rings for p in ring for c in p)


class TestClipRing:
    """Sutherland-Hodgman against a convex ring keeps what is inside and nothing else."""

    @UNTIMED
    @given(ring=RINGS, box=boxes())
    def test_every_output_point_is_in_the_box(self, ring: list[Pt], box: Box) -> None:
        """Clipped points lie in the box to interpolation rounding."""
        out = clip_ring(ring, box)
        tol = 1e-9 * (1 + _extent(ring, _box_ring(box)))
        xmin, ymin, xmax, ymax = box
        for x, y in out:
            assert xmin - tol <= x <= xmax + tol
            assert ymin - tol <= y <= ymax + tol

    @UNTIMED
    @given(ring=RINGS, box=boxes())
    def test_clipping_never_gains_area(self, ring: list[Pt], box: Box) -> None:
        """The clip's area is at most the ring's and at most the box's."""
        out = clip_ring(ring, box)
        tol = 1e-9 * (1 + abs(signed_area(ring)))
        assert abs(signed_area(out)) <= abs(signed_area(ring)) + tol
        assert abs(signed_area(out)) <= abs(signed_area(_box_ring(box))) + tol

    @UNTIMED
    @given(box=boxes(), angles=ANGLES, share=_floats(0.1, 0.9))
    def test_a_ring_inside_the_box_comes_back_equal(
        self, box: Box, angles: list[float], share: float
    ) -> None:
        """A ring lying strictly inside the box is returned unchanged."""
        xmin, ymin, xmax, ymax = box
        centre = ((xmin + xmax) / 2, (ymin + ymax) / 2)
        ring = _ring(centre, share * min(xmax - xmin, ymax - ymin) / 2, angles)
        assert clip_ring(ring, box) == ring

    @UNTIMED
    @given(ring=RINGS, box=boxes(), side=st.sampled_from(("east", "west", "north", "south")))
    def test_a_ring_clear_of_the_box_clips_to_nothing(
        self, ring: list[Pt], box: Box, side: str
    ) -> None:
        """A ring shifted along one axis until its bounding box clears the box is dropped."""
        xmin, ymin, xmax, ymax = box
        xs = [x for x, _ in ring]
        ys = [y for _, y in ring]
        dx = dy = 0.0
        if side == "east":
            dx = xmax + 1 - min(xs)
        elif side == "west":
            dx = xmin - 1 - max(xs)
        elif side == "north":
            dy = ymax + 1 - min(ys)
        else:
            dy = ymin - 1 - max(ys)
        assert clip_ring([(x + dx, y + dy) for x, y in ring], box) == []
