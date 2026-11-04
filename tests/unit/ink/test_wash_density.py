"""What one wash lays: its density pinned per option, the bounds it keeps, and its inert cases."""

import numpy as np
import pytest

from pyntpot.ink.sheet import Sheet
from pyntpot.ink.washing import Flow, WashOptions, wash

H, W = 96, 128

#: A wet area rising from none at the west edge to all at the east edge.
RAMP = np.broadcast_to(np.linspace(0.0, 1.0, W, dtype=np.float32), (H, W)).copy()

#: Pinned washes of `block()`: the options, then the density's sum and its sum weighted by `RAMP`.
PINNED = {
    "plain": (WashOptions(), 5065.252971042364, 2563.7900270126565),
    "flow": (
        WashOptions(flow=Flow(exp=0.125, ref_frac=0.02, frac=0.5)),
        5089.052347640716,
        2576.7148532057913,
    ),
    "pits": (WashOptions(gran_gamma=0.8), 5088.881457488167, 2601.1916614141523),
    "wet": (WashOptions(wet=RAMP), 4941.125304561367, 2481.9219769336623),
}


def block() -> tuple[Sheet, np.ndarray]:
    """A sheet and a block of cover over most of it, so every paper field shows in the wash."""
    cover = np.zeros((H, W), np.float32)
    cover[8:88, 10:118] = 1.0
    return Sheet(H, W, gran_px=6.0, seed=7), cover


class TestWashDensity:
    """The density `wash` lays, pinned, and the range it is held to."""

    @pytest.mark.parametrize("name", PINNED, ids=PINNED.keys())
    def test_each_option_lays_the_pinned_density(self, name: str) -> None:
        """Edge, rim, granulation, wet area and the final softening all show in the pinned sums."""
        options, total, weighted = PINNED[name]
        sheet, cover = block()
        dens = wash(cover, sheet, 0.52, 0.20, options)
        assert float(dens.sum(dtype=np.float64)) == pytest.approx(total, rel=1e-7)
        assert float((dens * RAMP).sum(dtype=np.float64)) == pytest.approx(weighted, rel=1e-7)

    @pytest.mark.parametrize(
        ("base", "pool", "options"),
        [(1.0, 1.0, WashOptions()), (0.52, 0.20, WashOptions(uneven=3.0))],
        ids=["past-one", "below-zero"],
    )
    def test_the_density_stays_in_zero_to_one(
        self, base: float, pool: float, options: WashOptions
    ) -> None:
        """Settings that push the density past one or below zero are clipped to exactly that range."""
        sheet, cover = block()
        dens = wash(cover, sheet, base, pool, options)
        assert float(dens.min()) == 0.0
        assert float(dens.max()) == 1.0

    def test_no_cover_lays_zeros_of_the_covers_shape(self) -> None:
        """An empty cover gives a zero density of the cover's own shape and type."""
        sheet, _ = block()
        dens = wash(np.zeros((H, W), np.float32), sheet, 0.52, 0.20)
        assert dens.shape == (H, W)
        assert dens.dtype == np.float32
        assert not dens.any()

    def test_a_bleed_at_the_blur_floor_is_no_bleed(self) -> None:
        """A bleed of 0.4 px is too small to blur, so it leaves the wash bit for bit unbled."""
        sheet, cover = block()
        floor = wash(cover, sheet, 0.52, 0.20, WashOptions(wet=RAMP, bleed_px=0.4))
        none = wash(cover, sheet, 0.52, 0.20, WashOptions(wet=RAMP, bleed_px=0.0))
        assert np.array_equal(floor, none)
