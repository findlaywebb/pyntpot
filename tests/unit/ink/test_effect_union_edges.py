"""The casing union's refusals by message, its tie at the threshold and its reserve reach."""

import numpy as np
import pytest

from pyntpot.ink.colour import Colour
from pyntpot.ink.effect_reserve import reserve
from pyntpot.ink.effect_types import Casing, Reserve
from pyntpot.ink.effect_union import Member, casing_union
from pyntpot.ink.noise import F32

SIDE = 24


def _mask(level: float = 1.0) -> np.ndarray:
    """A float32 mask with a vertical bar of `level`."""
    mask = np.zeros((SIDE, SIDE), F32)
    mask[:, 10:12] = level
    return mask


def _wash() -> np.ndarray:
    """A flat mid-grey float32 wash."""
    return np.full((SIDE, SIDE, 3), 0.4, F32)


class TestRefusalMessages:
    """Each refusal names its reason in full."""

    @pytest.mark.parametrize(
        ("members", "message"),
        [
            ([], "a casing union needs at least one member"),
            (
                [(_mask(), Casing(width_px=1.0)), (_mask(), Reserve(width_px=1.0))],
                "a casing union takes all casings or all reserves: the kind differs",
            ),
            (
                [
                    (_mask(), Casing(width_px=1.0)),
                    (_mask(), Casing(width_px=1.0, colour=Colour("#000000"))),
                ],
                "casings in one union must share a colour",
            ),
            (
                [
                    (_mask(), Casing(width_px=1.0)),
                    (_mask(), Casing(width_px=1.0, strength=0.5)),
                ],
                "casings in one union must share a strength",
            ),
            (
                [(_mask(), Reserve(width_px=1.0)), (_mask(), Reserve(width_px=1.0, pool=0.5))],
                "reserves in one union must share a pool",
            ),
        ],
        ids=["empty", "kind", "colour", "strength", "pool"],
    )
    def test_the_message(self, members: list[Member], message: str) -> None:
        """The error text is the whole reason."""
        with pytest.raises(ValueError, match=f"^{message}$"):
            casing_union(_wash(), members)


class TestUnionEdges:
    """A union treats the threshold and the pool's reach as the primitives do."""

    @pytest.mark.parametrize(
        "member",
        [
            (_mask(0.3), Casing(width_px=2.0, colour=Colour("#000000"))),
            (_mask(0.3), Reserve(width_px=2.0)),
        ],
        ids=["casing", "reserve"],
    )
    def test_a_pixel_exactly_at_the_threshold_is_untouched(self, member: Member) -> None:
        """A bar of exactly 0.3 keeps its wash under a union."""
        out = casing_union(_wash(), [member])
        assert (out[:, 10:12] == 0.4).all()
        assert (out[:, 12] != 0.4).all()

    def test_a_reserve_union_pools_as_the_reserve_does(self) -> None:
        """A one-member union of a pooled reserve round a dot equals `reserve` bit for bit."""
        mask = np.zeros((SIDE, SIDE), F32)
        mask[12, 12] = 1.0
        res = Reserve(width_px=3.0, pool=1.0)
        assert np.array_equal(casing_union(_wash(), [(mask, res)]), reserve(_wash(), mask, res))
