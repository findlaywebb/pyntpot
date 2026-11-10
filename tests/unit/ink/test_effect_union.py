"""The casing union: one ring round several lines, each member at its own width."""

import numpy as np
import pytest

from pyntpot.ink.colour import Colour
from pyntpot.ink.effect_casing import casing
from pyntpot.ink.effect_reserve import reserve
from pyntpot.ink.effect_types import Casing, Reserve
from pyntpot.ink.effect_union import casing_union
from pyntpot.ink.noise import F32

SIDE = 32


def _bar(rows: slice, cols: slice) -> np.ndarray:
    """A float32 mask with one bar of line."""
    mask = np.zeros((SIDE, SIDE), F32)
    mask[rows, cols] = 1.0
    return mask


def _wash() -> np.ndarray:
    """A flat mid-grey float32 wash."""
    return np.full((SIDE, SIDE, 3), 0.4, F32)


@pytest.fixture
def junction() -> tuple[np.ndarray, np.ndarray]:
    """A wide road and a narrow lane meeting at a T."""
    road = _bar(slice(14, 18), slice(0, SIDE))
    lane = _bar(slice(0, 14), slice(15, 17))
    return road, lane


class TestUnion:
    """The ring surrounds the union and never enters a member."""

    def test_no_ring_inside_either_member(self, junction: tuple[np.ndarray, np.ndarray]) -> None:
        """Every pixel inside either footprint is the wash, though a lane ring would fall there."""
        road, lane = junction
        cas = Casing(width_px=3.0, colour=Colour("#000000"))
        out = casing_union(_wash(), [(road, cas), (lane, cas)])
        inside = (road >= 0.3) | (lane >= 0.3)
        assert (out[inside] == _wash()[inside]).all()
        alone = casing(_wash(), lane, cas)
        assert (alone[road >= 0.3] != 0.4).any()

    def test_the_union_ring_surrounds_the_pair(
        self, junction: tuple[np.ndarray, np.ndarray]
    ) -> None:
        """Beside the lane above the road, and below the road, the wash is cased."""
        road, lane = junction
        cas = Casing(width_px=3.0, colour=Colour("#000000"))
        out = casing_union(_wash(), [(road, cas), (lane, cas)])
        assert out[5, 13, 0] < 0.4
        assert out[20, 5, 0] < 0.4

    def test_each_member_keeps_its_width(self, junction: tuple[np.ndarray, np.ndarray]) -> None:
        """A wider road ring reaches farther than the lane's narrow one."""
        road, lane = junction
        out = casing_union(
            _wash(),
            [
                (road, Casing(width_px=5.0, colour=Colour("#000000"))),
                (lane, Casing(width_px=1.0, colour=Colour("#000000"))),
            ],
        )
        assert out[5, 12, 0] == pytest.approx(0.4)
        assert out[10, 5, 0] < 0.4

    def test_a_union_of_one_is_the_member_own_ring(
        self, junction: tuple[np.ndarray, np.ndarray]
    ) -> None:
        """One casing, or one reserve, equals the primitive bit for bit."""
        road, _ = junction
        cas = Casing(width_px=2.7, colour=Colour("#204060"), strength=0.8)
        assert np.array_equal(casing_union(_wash(), [(road, cas)]), casing(_wash(), road, cas))
        res = Reserve(width_px=2.7, pool=0.6)
        assert np.array_equal(casing_union(_wash(), [(road, res)]), reserve(_wash(), road, res))

    def test_a_reserve_union_lays_the_paper(self, junction: tuple[np.ndarray, np.ndarray]) -> None:
        """A reserve union leaves the paper beside the lane and keeps both cores."""
        road, lane = junction
        res = Reserve(width_px=3.0)
        out = casing_union(_wash(), [(road, res), (lane, res)])
        assert (out[5, 13] == 1.0).all()
        assert (out[road >= 0.3] == 0.4).all()

    def test_width_zero_members_return_the_wash(
        self, junction: tuple[np.ndarray, np.ndarray]
    ) -> None:
        """Members all of width 0 return `rgb` itself."""
        road, lane = junction
        wash = _wash()
        assert casing_union(wash, [(road, Casing()), (lane, Casing())]) is wash


class TestRefusals:
    """A union refuses members that do not agree."""

    def test_empty(self) -> None:
        """No members raises."""
        with pytest.raises(ValueError, match="member"):
            casing_union(_wash(), [])

    def test_mixed_kinds(self, junction: tuple[np.ndarray, np.ndarray]) -> None:
        """A casing and a reserve raise."""
        road, lane = junction
        with pytest.raises(ValueError, match="kind"):
            casing_union(_wash(), [(road, Casing(width_px=1.0)), (lane, Reserve(width_px=1.0))])

    def test_casings_that_differ(self, junction: tuple[np.ndarray, np.ndarray]) -> None:
        """Casings of two colours, or two strengths, raise."""
        road, lane = junction
        with pytest.raises(ValueError, match="colour"):
            casing_union(
                _wash(),
                [
                    (road, Casing(width_px=1.0)),
                    (lane, Casing(width_px=1.0, colour=Colour("#000000"))),
                ],
            )
        with pytest.raises(ValueError, match="strength"):
            casing_union(
                _wash(), [(road, Casing(width_px=1.0)), (lane, Casing(width_px=1.0, strength=0.5))]
            )

    def test_reserves_with_different_pools(self, junction: tuple[np.ndarray, np.ndarray]) -> None:
        """Reserves of two pools raise."""
        road, lane = junction
        with pytest.raises(ValueError, match="pool"):
            casing_union(
                _wash(), [(road, Reserve(width_px=1.0)), (lane, Reserve(width_px=1.0, pool=0.5))]
            )
