"""Tests for the nib plate: marks are stroked at the surface's scale, in their inks, brushes and washes."""

import math
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from pyntpot.ink.brush_style import BrushStyle
from pyntpot.ink.sheet import Canvas
from pyntpot.ink.style import PaperStyle
from pyntpot.letters.nib import NibSurface, mark_width_px, nib_plate
from pyntpot.letters.setting import Mark
from pyntpot.letters.style import FaceStyle, HandStyle, NibGroups, NibStyle

GROUPS = NibGroups(NibStyle(), FaceStyle(), HandStyle(), BrushStyle(), PaperStyle())


def _surface(w: int, h: int, scale: float) -> NibSurface:
    """A surface of the given render size over middling darkness."""
    return NibSurface(
        Canvas(0.0, 0.0, float(w), float(h), w, h), scale, np.full((h, w), 0.35, np.float32), 6.0
    )


def _marks(k: float, ink: str = "label") -> list[Mark]:
    """Three strokes near the left of the card in one ink, with every point scaled by `k`."""
    lines = [
        [(8.0, 12.0), (20.0, 14.0), (32.0, 12.0)],
        [(8.0, 22.0), (20.0, 24.0), (32.0, 22.0)],
        [(8.0, 32.0), (20.0, 34.0), (32.0, 32.0)],
    ]
    return [Mark([(x * k, y * k) for x, y in line], ink=ink, size=14.0 * k) for line in lines]


class TestPlate:
    """The plate is written with alpha only near the marks, at the surface's own scale."""

    def test_three_marks_write_alpha_near_the_marks(self, tmp_path: Path) -> None:
        """Three marks at scale 1 on 64 by 48 are written with alpha only around them."""
        written = nib_plate(_marks(1.0), _surface(64, 48, 1.0), GROUPS, tmp_path / "a.webp")
        assert written == tmp_path / "a.webp"
        alpha = np.asarray(Image.open(written).getchannel("A"))
        assert alpha[10:36, 4:36].max() > 0
        assert alpha[:, 48:].max() == 0

    def test_a_doubled_scale_puts_the_alpha_at_the_doubled_positions(self, tmp_path: Path) -> None:
        """The same marks at scale 2 on 128 by 96 put the alpha near twice the positions."""
        one = nib_plate(_marks(1.0), _surface(64, 48, 1.0), GROUPS, tmp_path / "a.webp")
        two = nib_plate(_marks(1.0), _surface(128, 96, 2.0), GROUPS, tmp_path / "b.webp")
        assert one is not None
        assert two is not None
        alpha = np.asarray(Image.open(two).getchannel("A"))
        assert one.exists()
        assert alpha[20:72, 8:72].max() > 0
        assert alpha[:, 96:].max() == 0
        # The wash leaves faint alpha everywhere; the ink itself is solid only near the
        # doubled positions, never above row 16, where the halved ones would sit.
        assert alpha[:16].max() < 128, "the marks were shrunk, not enlarged, by the scale"

    def test_nothing_to_draw_writes_nothing(self, tmp_path: Path) -> None:
        """No marks, or only marks too short to stroke, write no file."""
        surface = _surface(64, 48, 1.0)
        assert nib_plate([], surface, GROUPS, tmp_path / "a.webp") is None
        assert nib_plate([Mark([(1.0, 1.0)])], surface, GROUPS, tmp_path / "a.webp") is None
        assert not (tmp_path / "a.webp").exists()


class TestInks:
    """An ink token names one of the nib style's inks; anything else falls back to the label ink."""

    @pytest.mark.parametrize(
        ("token", "colour"),
        [
            ("label", NibStyle().label_ink),
            ("route", NibStyle().label_route_ink),
            ("water", NibStyle().label_water_ink),
            ("in_water", NibStyle().label_in_water_ink),
        ],
        ids=["label", "route", "water", "in-water"],
    )
    def test_a_token_paints_as_the_colour_it_names(
        self, tmp_path: Path, token: str, colour: str
    ) -> None:
        """Marks in an ink token write the same plate as marks in the colour that token names."""
        surface = _surface(64, 48, 1.0)
        named = nib_plate(_marks(1.0, token), surface, GROUPS, tmp_path / "named.webp")
        given = nib_plate(_marks(1.0, colour), surface, GROUPS, tmp_path / "given.webp")
        assert named is not None
        assert given is not None
        assert named.read_bytes() == given.read_bytes()

    @pytest.mark.parametrize(
        "token", ["map", "smudge", "#12345"], ids=["retired-map-token", "unknown-word", "short-hex"]
    )
    def test_an_ink_nobody_chose_falls_back_to_the_label_ink(
        self, tmp_path: Path, token: str
    ) -> None:
        """A mark in an ink that is neither a token nor a #rrggbb colour is written in the label ink."""
        surface = _surface(64, 48, 1.0)
        odd = nib_plate(_marks(1.0, token), surface, GROUPS, tmp_path / "odd.webp")
        label = nib_plate(_marks(1.0, "label"), surface, GROUPS, tmp_path / "label.webp")
        assert odd is not None
        assert label is not None
        assert odd.read_bytes() == label.read_bytes()

    def test_the_label_ink_is_not_the_route_ink(self, tmp_path: Path) -> None:
        """Two different inks write different plates, so the equalities above are not vacuous."""
        surface = _surface(64, 48, 1.0)
        label = nib_plate(_marks(1.0, "label"), surface, GROUPS, tmp_path / "label.webp")
        route = nib_plate(_marks(1.0, "route"), surface, GROUPS, tmp_path / "route.webp")
        assert label is not None
        assert route is not None
        assert label.read_bytes() != route.read_bytes()


#: One stroke well inside a 64 by 48 surface.
STROKE = [(8.0, 12.0), (20.0, 24.0), (32.0, 30.0)]


def _plate(marks: list[Mark], path: Path, groups: NibGroups = GROUPS) -> bytes:
    """The bytes of the plate the marks write on a 64 by 48 surface at scale 1."""
    written = nib_plate(marks, _surface(64, 48, 1.0), groups, path)
    assert written is not None
    return written.read_bytes()


class TestMarks:
    """Which marks are stroked, and with which brush, pen profile and wash."""

    def test_a_two_point_mark_is_stroked(self, tmp_path: Path) -> None:
        """A mark of exactly two points, the fewest a stroke needs, is written."""
        assert nib_plate(
            [Mark([(8.0, 12.0), (32.0, 30.0)])], _surface(64, 48, 1.0), GROUPS, tmp_path / "a.webp"
        )

    def test_a_too_short_mark_is_skipped_not_the_rest(self, tmp_path: Path) -> None:
        """A one-point mark before a real one is skipped, and the real one is still written."""
        alone = _plate([Mark(STROKE)], tmp_path / "a.webp")
        after = _plate([Mark([(1.0, 1.0)]), Mark(STROKE)], tmp_path / "b.webp")
        assert after == alone

    def test_a_glyphs_pen_tilt_turns_the_nib(self, tmp_path: Path) -> None:
        """A glyph tilted by `pen` writes as the untilted glyph does with the nib's angle turned by as much."""
        tilt = 0.4
        turned = NibGroups(
            NibStyle(label_pen_angle_deg=NibStyle().label_pen_angle_deg + math.degrees(tilt)),
            FaceStyle(),
            HandStyle(),
            BrushStyle(),
            PaperStyle(),
        )
        tilted = _plate([Mark(STROKE, pen=tilt)], tmp_path / "a.webp")
        assert tilted == _plate([Mark(STROKE)], tmp_path / "b.webp", turned)
        assert tilted != _plate([Mark(STROKE)], tmp_path / "c.webp")

    def test_a_leader_has_no_pen_profile(self, tmp_path: Path) -> None:
        """Only a glyph's width follows the pen's angle, so a leader's tilt changes nothing."""
        upright = _plate([Mark(STROKE, role="leader")], tmp_path / "a.webp")
        assert _plate([Mark(STROKE, role="leader", pen=0.4)], tmp_path / "b.webp") == upright

    def test_the_role_picks_the_brush(self, tmp_path: Path) -> None:
        """A leader and a pin, two roles of different weights, write different plates."""
        leader = _plate([Mark(STROKE, role="leader")], tmp_path / "a.webp")
        assert _plate([Mark(STROKE, role="pin")], tmp_path / "b.webp") != leader

    def test_a_mark_without_a_wash_writes_a_different_plate(self, tmp_path: Path) -> None:
        """Turning a mark's backing wash off changes what is written under it."""
        washed = _plate([Mark(STROKE)], tmp_path / "a.webp")
        assert _plate([Mark(STROKE, wash=False)], tmp_path / "b.webp") != washed


#: The brush the map paints its labels with: organic, so the bristles drift on a lattice.
ORGANIC = BrushStyle(brush_organic=True, pen_starve=True, stroke_smooth=True)


def _bowl(cx: float, cy: float, rx: float, ry: float) -> list[tuple[float, float]]:
    """A closed oval of 124 points, an "o" as the hand writes it, starting at its foot."""
    turns = np.linspace(0.0, 2.0 * math.pi, 124)
    return [(cx + rx * math.sin(a), cy + ry * math.cos(a)) for a in turns]


class TestCounters:
    """A small closed letter keeps its counter open, whatever the label seed draws."""

    def test_a_small_o_keeps_an_open_counter_across_seeds(self, tmp_path: Path) -> None:
        """A 20 px "o" at scale 2 leaves the middle of its bowl near bare for 400 label seeds."""
        rx, ry = 2.64, 3.72
        surface = _surface(64, 64, 2.0)
        mark = Mark(_bowl(16.0, 16.0, rx, ry), size=20.0, pen=-0.09, wash=False)
        yy, xx = np.mgrid[0:64, 0:64] + 0.5
        core = ((xx - 32.0) / (2.0 * rx)) ** 2 + ((yy - 32.0) / (2.0 * ry)) ** 2 < 0.25
        worst = 0.0
        for seed in range(400):
            groups = NibGroups(NibStyle(), FaceStyle(), HandStyle(seed), ORGANIC, PaperStyle())
            written = nib_plate([mark], surface, groups, tmp_path / "o.webp")
            assert written is not None
            alpha = np.asarray(Image.open(written).getchannel("A"), np.float32) / 255.0
            worst = max(worst, float(alpha[core].mean()))
        assert worst < 0.4, f"the bowl's middle is {worst:.2f} inked: the counter closed"


class TestMarkWidth:
    """A mark's pen width follows its role's weight and its type size."""

    @pytest.mark.parametrize(
        ("role", "size", "outline", "width"),
        [
            ("pin", 20.0, False, 1.275),
            ("pin", 10.0, False, 0.6375),
            ("leader", 20.0, False, 0.612),
            ("glyph", 20.0, False, 1.05),
            ("glyph", 20.0, True, 0.651),
            ("leader", 20.0, True, 0.612),
            ("pin", 0.5, False, 0.06375),
        ],
        ids=["pin", "half-size-pin", "leader", "glyph", "outline-glyph", "outline-leader", "tiny"],
    )
    def test_the_width_is_the_pen_times_the_weight_at_the_size(
        self, role: str, size: float, outline: bool, width: float
    ) -> None:
        """The default nib draws each role at its pinned width in display pixels."""
        assert mark_width_px(NibStyle(), role, size, outline=outline) == pytest.approx(width)
