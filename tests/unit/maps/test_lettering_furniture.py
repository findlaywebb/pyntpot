"""Tests for the furniture beside a name: a pin ring keeps its hole whatever the seed draws."""

from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from pyntpot.ink.sheet import Canvas
from pyntpot.letters.hand import Hand
from pyntpot.letters.nib import NibSurface, mark_width_px, nib_plate
from pyntpot.letters.setting import Mark
from pyntpot.letters.style import HandStyle, NibGroups
from pyntpot.maps.lettering.label import Label
from pyntpot.maps.lettering_furniture import PIN_HOLE_MIN_PX, pin
from pyntpot.maps.style import Style


@pytest.fixture(scope="module")
def style() -> Style:
    """The packaged default style, read once: it is never changed."""
    return Style.default()


class TestPinRing:
    """A pin is a ring the leader points at, never a filled dot."""

    def test_a_pin_ring_keeps_an_open_hole_across_seeds(self, style: Style, tmp_path: Path) -> None:
        """A pin at the shipped type size, weight and brush stays near bare inside for 400 seeds."""
        hand = Hand(style.face, style.hand)
        size = style.nib.label_size_px
        side = 48
        surface = NibSurface(
            Canvas(0.0, 0.0, side, side, side, side),
            2.0,
            np.full((side, side), 0.35, np.float32),
            6.0,
        )
        pen = mark_width_px(style.nib, "pin", size)
        label = Label("Lynton and Exmoor Museum", px=12.0, py=12.0, size=size)
        yy, xx = np.mgrid[0:side, 0:side] + 0.5
        worst = 0.0
        for seed in range(400):
            pts = pin(hand, label, np.random.default_rng(seed), pen)
            xs = [x for x, _y in pts]
            radius = (max(xs) - min(xs)) / 2.0 * surface.scale
            core = (xx - 24.0) ** 2 + (yy - 24.0) ** 2 < (radius / 2.0) ** 2
            groups = NibGroups(style.nib, style.face, HandStyle(seed), style.brush, style.paper)
            mark = Mark(pts, role="pin", size=size, wash=False)
            written = nib_plate([mark], surface, groups, tmp_path / "pin.webp")
            assert written is not None
            alpha = np.asarray(Image.open(written).getchannel("A"), np.float32) / 255.0
            worst = max(worst, float(alpha[core].mean()))
        assert worst < 0.4, f"the ring's middle is {worst:.2f} inked: the pin closed into a dot"

    @pytest.mark.parametrize(
        ("size", "radius"),
        [(11.0, 3.150625), (20.0, 3.4375), (40.0, 6.875)],
        ids=["small-on-the-floor", "shipped", "large-from-the-size"],
    )
    def test_the_ring_sits_half_its_pen_outside_its_hole(
        self, style: Style, size: float, radius: float
    ) -> None:
        """The ring starts, where the wander leaves it, at the pinned radius for its size and pen."""
        hand = Hand(style.face, style.hand)
        pen = mark_width_px(style.nib, "pin", size)
        label = Label("Lynton and Exmoor Museum", px=0.0, py=0.0, size=size)
        pts = pin(hand, label, np.random.default_rng(0), pen)
        assert pts[0] == pytest.approx((radius, 0.0))
        assert pts[0][0] - pen / 2.0 >= PIN_HOLE_MIN_PX

    def test_a_wider_pen_draws_a_wider_ring_round_the_same_hole(self, style: Style) -> None:
        """Doubling the pen moves the ring out by half the extra width, keeping the hole."""
        hand = Hand(style.face, style.hand)
        label = Label("Lynton and Exmoor Museum", px=0.0, py=0.0, size=20.0)
        thin = pin(hand, label, np.random.default_rng(3), 1.0)
        thick = pin(hand, label, np.random.default_rng(3), 2.0)
        assert thick != thin
        assert max(x for x, _y in thick) > max(x for x, _y in thin)
