"""Tests for the nib plate: marks are stroked onto a surface of the given scale."""

from pathlib import Path

import numpy as np
from PIL import Image

from pyntpot.ink.brush_style import BrushStyle
from pyntpot.ink.sheet import Canvas
from pyntpot.ink.style import PaperStyle
from pyntpot.letters.nib import NibSurface, plate
from pyntpot.letters.setting import Mark
from pyntpot.letters.style import FaceStyle, HandStyle, NibGroups, NibStyle

GROUPS = NibGroups(NibStyle(), FaceStyle(), HandStyle(), BrushStyle(), PaperStyle())


def _surface(w: int, h: int, scale: float) -> NibSurface:
    """A surface of the given render size over middling darkness."""
    return NibSurface(
        Canvas(0.0, 0.0, float(w), float(h), w, h), scale, np.full((h, w), 0.35, np.float32), 6.0
    )


def _marks(k: float) -> list[Mark]:
    """Three strokes near the left of the card, with every point scaled by `k`."""
    lines = [
        [(8.0, 12.0), (20.0, 14.0), (32.0, 12.0)],
        [(8.0, 22.0), (20.0, 24.0), (32.0, 22.0)],
        [(8.0, 32.0), (20.0, 34.0), (32.0, 32.0)],
    ]
    return [Mark([(x * k, y * k) for x, y in line], size=14.0 * k) for line in lines]


class TestPlate:
    """The plate is written with alpha only near the marks, at the surface's own scale."""

    def test_three_marks_write_alpha_near_the_marks(self, tmp_path: Path) -> None:
        """Three marks at scale 1 on 64 by 48 are written with alpha only around them."""
        written = plate(_marks(1.0), _surface(64, 48, 1.0), GROUPS, tmp_path / "a.webp")
        assert written == tmp_path / "a.webp"
        alpha = np.asarray(Image.open(written).getchannel("A"))
        assert alpha[10:36, 4:36].max() > 0
        assert alpha[:, 48:].max() == 0

    def test_a_doubled_scale_puts_the_alpha_at_the_doubled_positions(self, tmp_path: Path) -> None:
        """The same marks at scale 2 on 128 by 96 put the alpha near twice the positions."""
        one = plate(_marks(1.0), _surface(64, 48, 1.0), GROUPS, tmp_path / "a.webp")
        two = plate(_marks(1.0), _surface(128, 96, 2.0), GROUPS, tmp_path / "b.webp")
        assert one is not None
        assert two is not None
        alpha = np.asarray(Image.open(two).getchannel("A"))
        assert one.exists()
        assert alpha[20:72, 8:72].max() > 0
        assert alpha[:, 96:].max() == 0

    def test_nothing_to_draw_writes_nothing(self, tmp_path: Path) -> None:
        """No marks, or only marks too short to stroke, write no file."""
        surface = _surface(64, 48, 1.0)
        assert plate([], surface, GROUPS, tmp_path / "a.webp") is None
        assert plate([Mark([(1.0, 1.0)])], surface, GROUPS, tmp_path / "a.webp") is None
        assert not (tmp_path / "a.webp").exists()
