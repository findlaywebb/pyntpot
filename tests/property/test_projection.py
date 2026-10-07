"""Properties of the local projection: it inverts, and it anchors the track where it says."""

import pytest
from hypothesis import given
from hypothesis import strategies as st

from pyntpot.maps.projection import Projection, track_projection

from support.properties import UNTIMED

LAT = st.floats(51.19, 51.26, allow_nan=False, allow_infinity=False)
LNG = st.floats(-3.88, -3.80, allow_nan=False, allow_infinity=False)
METRES = st.floats(-1e4, 1e4, allow_nan=False, allow_infinity=False)


class TestProjection:
    """`inverse` undoes `__call__` over the Lynmouth box."""

    @UNTIMED
    @given(
        lat0=LAT,
        ref=st.tuples(LAT, LNG),
        shift=st.tuples(METRES, METRES),
        target=st.tuples(LAT, LNG),
    )
    def test_inverse_undoes_the_projection(
        self,
        lat0: float,
        ref: tuple[float, float],
        shift: tuple[float, float],
        target: tuple[float, float],
    ) -> None:
        """Projecting a coordinate and inverting it gives the coordinate back."""
        proj = Projection(lat0, ref[0], ref[1], shift[0], shift[1])
        assert proj.inverse(*proj(*target)) == pytest.approx(target, abs=1e-9)


class TestTrackProjection:
    """`track_projection` fixes the origin from the track or from the route."""

    @UNTIMED
    @given(pairs=st.lists(st.tuples(LAT, LNG), min_size=2, max_size=50))
    def test_no_route_puts_the_minimum_at_zero(self, pairs: list[tuple[float, float]]) -> None:
        """Without a route the smallest projected x and y are both zero."""
        _, pts = track_projection([a for a, _ in pairs], [b for _, b in pairs])
        assert min(x for x, _ in pts) == pytest.approx(0.0, abs=1e-6)
        assert min(y for _, y in pts) == pytest.approx(0.0, abs=1e-6)

    @UNTIMED
    @given(
        pairs=st.lists(st.tuples(LAT, LNG), min_size=2, max_size=50),
        route=st.lists(st.tuples(METRES, METRES), min_size=1, max_size=5),
    )
    def test_a_route_sets_the_first_point(
        self, pairs: list[tuple[float, float]], route: list[tuple[float, float]]
    ) -> None:
        """With a route the first projected point is the route's first point."""
        _, pts = track_projection([a for a, _ in pairs], [b for _, b in pairs], route)
        assert pts[0] == pytest.approx(route[0], abs=1e-6)
