"""Tests for the nib plate: marks are stroked at the surface's scale, in their inks, brushes and washes."""

import math
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from pyntpot.ink.brush_style import BrushStyle
from pyntpot.ink.sheet import Canvas
from pyntpot.ink.style import PaperStyle
from pyntpot.letters.hand import Hand
from pyntpot.letters.nib import NibSurface, _pen_profile, nib_plate
from pyntpot.letters.setting import Mark, Setting
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


class TestPenProfile:
    """A glyph stroke's width follows its smoothed direction against the nib."""

    @pytest.mark.parametrize(
        ("heading", "nib", "width"),
        [
            (0.0, math.pi / 2, 1.0),
            (0.0, 0.0, 0.15),
            (math.pi / 6, 0.0, 0.575),
            (math.pi, 0.0, 0.15),
        ],
        ids=["across", "along", "thirty-degrees", "reversed-along"],
    )
    def test_a_straight_stroke_keeps_the_sine_of_its_angle(
        self, heading: float, nib: float, width: float
    ) -> None:
        """A straight stroke keeps `1 - thin` along the nib, all of it across, and the sine between, everywhere."""
        pts = np.array([(0.0, 0.0), (60.0 * math.cos(heading), 60.0 * math.sin(heading))])
        prof = _pen_profile(pts, nib, 0.85, 8.0)
        assert np.allclose(prof, width, atol=1e-6)

    def test_the_samples_are_never_more_than_half_a_window_apart(self) -> None:
        """A stroke 120 px long under an 8 px window is sampled at 31 points, not the fewest 24."""
        pts = np.array([(0.0, 0.0), (120.0, 0.0)])
        assert len(_pen_profile(pts, 0.0, 0.5, 8.0)) == 31
        assert len(_pen_profile(pts, 0.0, 0.5, 80.0)) == 24

    def test_a_short_or_degenerate_stroke_has_full_width(self) -> None:
        """A one-point stroke, or one of no length, keeps its full width at both ends."""
        for pts in (np.array([(3.0, 4.0)]), np.array([(3.0, 4.0), (3.0, 4.0)])):
            prof = _pen_profile(pts, 0.0, 0.85, 8.0)
            assert prof.dtype == np.float32
            assert prof.tolist() == [1.0, 1.0]

    def test_a_corner_is_smoothed_over_the_window(self) -> None:
        """Where a stroke turns from along the nib to across it, the width climbs through the angles between."""
        pts = np.array([(0.0, 0.0), (40.0, 0.0), (40.0, 40.0)])
        prof = _pen_profile(pts, 0.0, 0.85, 8.0)
        assert prof[0] == pytest.approx(0.15, abs=1e-6)
        assert prof[-1] == pytest.approx(1.0, abs=1e-6)
        assert np.all(np.diff(prof) >= -1e-6)
        assert np.abs(np.diff(prof)).max() < 0.5

    @pytest.mark.parametrize("seed", [1, 7, 11], ids=["seed-1", "seed-7", "seed-11"])
    def test_keswick_on_an_upright_nib_has_no_saw_tooth(self, seed: int) -> None:
        """Keswick at 52 px, nib at 90 degrees and thin 0.85, never zigzags wide, thin, wide along a stroke."""
        hand = Hand(FaceStyle(), HandStyle())
        marks = hand.write(Setting("Keswick", 52.0, anchor=(10.0, 80.0)), hand.generator(seed))
        window = 3.4 * 52.0 / NibStyle().label_size_px * 2.0
        zigzags = 0
        for mark in marks:
            pts = np.asarray(mark.pts) * 2.0
            step = np.diff(_pen_profile(pts, math.radians(90.0) + mark.pen, 0.85, window))
            big = np.abs(step) > 0.05
            turn = step[:-1] * step[1:] < 0
            zigzags += int(np.sum(turn[:-1] & turn[1:] & big[:-2] & big[1:-1] & big[2:]))
        assert zigzags == 0

    def test_a_short_corner_turns_through_the_pinned_widths(self) -> None:
        """An L of two 10 px legs under an 8 px tent climbs from 0.15 to 1.0 by the pinned widths."""
        pts = np.array([(0.0, 0.0), (10.0, 0.0), (10.0, 10.0)])
        prof = _pen_profile(pts, 0.0, 0.85, 8.0)
        pinned = [
            0.15, 0.15, 0.15, 0.1519, 0.1657, 0.1918, 0.2293, 0.2803, 0.3484, 0.4382, 0.5523, 0.6826,
            0.8125, 0.8988, 0.9496, 0.9765, 0.99, 0.9963, 0.999, 0.9999, 1.0, 1.0, 1.0, 1.0,
        ]  # fmt: skip
        assert prof.dtype == np.float32
        assert prof.tolist() == pytest.approx(pinned, abs=1e-4)

    def test_a_stroke_as_short_as_the_least_length_has_full_width(self) -> None:
        """A stroke exactly the least length long has no direction, so it keeps its full width."""
        prof = _pen_profile(np.array([(0.0, 0.0), (1e-6, 0.0)]), 0.0, 0.85, 8.0)
        assert prof.dtype == np.float32
        assert prof.tolist() == [1.0, 1.0]
