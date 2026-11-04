"""Tests for the nib plate: marks are stroked at the surface's scale, in their inks, brushes and washes."""

import math
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from pyntpot.ink.brush_style import BrushStyle
from pyntpot.ink.sheet import Canvas
from pyntpot.ink.style import PaperStyle
from pyntpot.letters.nib import (
    NibSurface,
    _backing_wash,
    _sheet,
    mark_width_px,
    nib_brushes,
    nib_plate,
)
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
        # The ink ends near x 70 and the lift fades to nothing a reach (30 px) past it.
        assert alpha[:, 100:].max() == 0
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

    def test_a_washed_mark_beside_an_unwashed_one_keeps_its_own_wash(self, tmp_path: Path) -> None:
        """In one ink, the washed mark's wash is laid as when every mark is washed.

        The washed marks are laid again on their own pad for the wash, from the same
        label seed, so the wash under them matches the all-washed plate there, and the
        unwashed mark far off reads as when no mark is washed.
        """
        top = [(8.0, 8.0), (30.0, 10.0), (52.0, 8.0)]
        low = [(8.0, 120.0), (30.0, 122.0), (52.0, 120.0)]
        surface = _surface(64, 140, 1.0)

        def alpha(marks: list[Mark], name: str) -> np.ndarray:
            written = nib_plate(marks, surface, GROUPS, tmp_path / name)
            assert written is not None
            return np.asarray(Image.open(written).convert("RGBA"), np.int16)[..., 3]

        mixed = alpha([Mark(top), Mark(low, wash=False)], "mixed.webp")
        washed = alpha([Mark(top), Mark(low)], "washed.webp")
        bare = alpha([Mark(top, wash=False), Mark(low, wash=False)], "bare.webp")
        assert not np.array_equal(washed[:40], bare[:40]), "the wash shows under the top mark"
        assert int(np.abs(mixed[:40] - washed[:40]).max()) <= 1
        assert int(np.abs(mixed[90:] - bare[90:]).max()) <= 1


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
            groups = NibGroups(
                NibStyle(), FaceStyle(), HandStyle(label_seed=seed), ORGANIC, PaperStyle()
            )
            written = nib_plate([mark], surface, groups, tmp_path / "o.webp")
            assert written is not None
            alpha = np.asarray(Image.open(written).getchannel("A"), np.float32) / 255.0
            worst = max(worst, float(alpha[core].mean()))
        assert worst < 0.4, f"the bowl's middle is {worst:.2f} inked: the counter closed"


class TestBackingWash:
    """The lift under a name fades out from its ink, with no flat body and no edge of its own."""

    #: Where the name's ink lies on the 200 by 120 surface: one line of "Llyn Llydaw".
    INK = (slice(52, 68), slice(40, 160))

    def _lift(self) -> tuple[np.ndarray, float]:
        """The backing wash's alpha under one line of ink on dark paint, and its reach in pixels."""
        surface = NibSurface(
            Canvas(0.0, 0.0, 200.0, 120.0, 200, 120), 1.0, np.full((120, 200), 0.8, np.float32), 6.0
        )
        cover = np.zeros((120, 200), np.float32)
        cover[self.INK] = 1.0
        _rgb, alpha = _backing_wash(cover, surface, _sheet(surface, GROUPS.paper), GROUPS)
        nib = GROUPS.nib
        return alpha, nib.label_wash_spread * nib.label_size_px

    def test_the_lift_is_strongest_at_the_ink(self) -> None:
        """Half a reach above the ink the lift is under half what it is beside the letters."""
        alpha, reach = self._lift()
        beside = float(alpha[50, 60:140].mean())
        half_out = float(alpha[52 - round(reach / 2), 60:140].mean())
        assert beside > 0.0
        assert half_out < beside / 2, "the lift has a flat body round the name"

    def test_the_lift_has_no_edge(self) -> None:
        """Walking out from the ink the lift never steps by more than a small share of its peak."""
        alpha, _reach = self._lift()
        column = alpha[:52, 60:140].mean(axis=1)
        steps = np.abs(np.diff(column))
        assert float(steps.max()) < 0.1 * float(column.max()), "the lift ends in an edge"

    def test_the_lift_is_gone_two_reaches_out(self) -> None:
        """Nothing of the lift is left two reaches from the ink."""
        alpha, reach = self._lift()
        assert float(alpha[: 52 - round(2 * reach), :].max()) < 0.01

    def test_the_lift_peaks_as_strong_as_the_box_did(self) -> None:
        """The peak lift above the ink is the old box's (0.3365 here) to within five per cent."""
        alpha, _reach = self._lift()
        peak = float(alpha[:52, 60:140].mean(axis=1).max())
        assert peak == pytest.approx(0.3365, rel=0.05), "the name reads fainter than it did"

    def test_the_lift_is_the_pinned_one(self) -> None:
        """Its strength beside the letters, its grain there and its whole weight, pinned."""
        alpha, _reach = self._lift()
        assert float(alpha[50, 60:140].mean()) == pytest.approx(0.301806, rel=1e-3)
        assert float(alpha[50, 60:140].std()) == pytest.approx(0.017055, rel=1e-2)
        assert float(alpha.sum()) == pytest.approx(1376.555, rel=1e-3)


#: Mark layouts on the 96 by 72 card: a block of three lines, one long diagonal, and two
#: short words apart, so the reach is crossed from inside a block, a corner and a gap.
LAYOUTS = {
    "block": [
        [(8.0, 12.0 + 10 * i), (24.0, 14.0 + 10 * i), (40.0, 12.0 + 10 * i)] for i in range(3)
    ],
    "diagonal": [[(10.0, 10.0), (40.0, 30.0), (70.0, 50.0)]],
    "two-words": [[(10.0, 20.0), (26.0, 22.0)], [(56.0, 50.0), (80.0, 48.0)]],
}

#: How far past the reach the feather's blur may carry its last level, in reaches. The
#: blur is a third of the reach wide, so its tail runs a pixel or two over; the floor
#: ends it inside a fifth of a reach on the darkest ground (17.2 px of 18 here). A floor
#: left unscaled by the lift's gain carries it to 18.4 px, past this.
TAIL = 0.2


def _distance_to(mask: np.ndarray) -> np.ndarray:
    """The Euclidean distance of every pixel to the nearest true pixel of `mask`."""
    ys, xs = np.nonzero(mask)
    gy, gx = np.mgrid[0 : mask.shape[0], 0 : mask.shape[1]]
    squared = (gy[..., None] - ys) ** 2 + (gx[..., None] - xs) ** 2
    return np.sqrt(squared.min(axis=-1).astype(np.float64))


class TestNoStrayAlpha:
    """The plate leaves the paper bare once the backing wash has faded out past its reach."""

    @pytest.mark.parametrize("layout", list(LAYOUTS), ids=list(LAYOUTS))
    @pytest.mark.parametrize(
        ("hand_seed", "sheet_seed"),
        [(17, 11), (3, 5), (40, 29)],
        ids=["default", "seeds-3-5", "seeds-40-29"],
    )
    @pytest.mark.parametrize("dark", [0.35, 1.0], ids=["middling-ground", "darkest-ground"])
    def test_no_alpha_level_past_the_fade(
        self, tmp_path: Path, layout: str, hand_seed: int, sheet_seed: int, dark: float
    ) -> None:
        """No pixel further than a reach and its blur's tail from the ink has plate alpha."""
        surface = NibSurface(
            Canvas(0.0, 0.0, 96.0, 72.0, 96, 72), 1.0, np.full((72, 96), dark, np.float32), 6.0
        )
        marks = [Mark(line, size=14.0) for line in LAYOUTS[layout]]
        paper = PaperStyle(sheet_seed=sheet_seed)
        hand = HandStyle(label_seed=hand_seed)
        bare = NibGroups(NibStyle(label_wash=False), FaceStyle(), hand, BrushStyle(), paper)
        washed = NibGroups(NibStyle(), FaceStyle(), hand, BrushStyle(), paper)
        ink_path = nib_plate(marks, surface, bare, tmp_path / "ink.webp")
        plate_path = nib_plate(marks, surface, washed, tmp_path / "plate.webp")
        assert ink_path is not None
        assert plate_path is not None
        ink = np.asarray(Image.open(ink_path).getchannel("A")) > 0.12 * 255
        assert ink.any()
        alpha = np.asarray(Image.open(plate_path).getchannel("A"))
        nib = NibStyle()
        reach = nib.label_wash_spread * nib.label_size_px
        stray = alpha[_distance_to(ink) > reach * (1.0 + TAIL)]
        assert int(stray.max()) == 0, f"{int((stray > 0).sum())} pixels past the fade carry alpha"


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

    def test_a_glyph_is_drawn_with_the_full_pen_unless_asked_for_an_outline(self) -> None:
        """Without `outline` a glyph takes the whole lettering pen, 1.05 px at 20 px."""
        assert mark_width_px(NibStyle(), "glyph", 20.0) == pytest.approx(1.05)

    def test_a_role_without_a_weight_takes_the_leader_pen_unweighted(self) -> None:
        """A role `MARK_WEIGHT` does not name is drawn at the leader pen's own 0.85 px."""
        assert mark_width_px(NibStyle(), "home", 20.0) == pytest.approx(0.85)

    def test_a_style_set_below_one_pixel_scales_from_its_own_size(self) -> None:
        """A nib set at a 0.5 px type size doubles its leader pen at 1 px: 0.85 times 2 times 1.5."""
        nib = NibStyle(label_size_px=0.5)
        assert mark_width_px(nib, "pin", 1.0) == pytest.approx(2.55)

    @pytest.mark.parametrize(
        ("route", "role", "width"),
        [
            ("centreline", "glyph", 2.1),
            ("outline", "glyph", 1.302),
            ("outline", "pin", 2.55),
        ],
        ids=["centreline-glyph", "outline-glyph", "outline-pin"],
    )
    def test_the_brush_is_as_wide_as_the_mark_at_the_scale(
        self, route: str, role: str, width: float
    ) -> None:
        """At scale 2 a 20 px mark's brush is twice its `mark_width_px`, narrowed only on an outline glyph."""
        brush = nib_brushes(NibStyle(), FaceStyle(label_route=route), BrushStyle(), 2.0)
        assert brush(role, 20.0).width == pytest.approx(width)
