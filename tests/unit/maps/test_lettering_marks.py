"""Tests for the map's translation of placed labels and spans into marks and furniture."""

import dataclasses
import math
from typing import Any

import pytest

from pyntpot.ink.brush import BRUSH_COLOURS
from pyntpot.letters.hand import Hand
from pyntpot.letters.style import FaceStyle, HandStyle
from pyntpot.maps import lettering_marks
from pyntpot.maps.lettering.label import Label, Span
from pyntpot.maps.lettering_window import baseline

from support.basemaps import class_style, river_label
from support.lettering import open_hand

#: A gentle, nearly straight river course, in card pixels.
COURSE = [(float(x), 100.0 + 4.0 * math.sin(x / 90.0)) for x in range(0, 400, 8)]


@pytest.fixture(scope="module")
def hand() -> Hand:
    """The default hand, opened once: its face is loaded and never changes."""
    return Hand(FaceStyle(), HandStyle())


def _flat(**fields: Any) -> Label:
    """A placed flat label with an anchor of its own, overridden by the fields given."""
    base = Label(
        name="Aviemore", kind="landmark", px=120.0, py=90.0, tx=150.0, ty=80.0, size=14.0, flat=True
    )
    return dataclasses.replace(base, **fields)


class TestFurniture:
    """A label draws the furniture its kind is entitled to, and no more."""

    def test_a_label_with_a_leader_yields_one_leader_and_one_pin(self, hand: Hand) -> None:
        """A pinned landmark takes exactly one pin and one leader beside its glyphs."""
        marks = lettering_marks.label_marks(hand, _flat(leader=((120.0, 90.0), (150.0, 72.0))))
        roles = [m.role for m in marks]
        assert roles.count("leader") == 1
        assert roles.count("pin") == 1
        assert roles.count("glyph") > 0

    @pytest.mark.parametrize("kind", ["river", "settlement", "road", "marker"], ids=str)
    def test_a_kind_that_is_its_own_place_takes_no_leader(self, hand: Hand, kind: str) -> None:
        """A river, settlement, road or marker never takes a pin or a leader."""
        marks = lettering_marks.label_marks(
            hand, _flat(kind=kind, size=14.0, leader=((120.0, 90.0), (150.0, 72.0)))
        )
        assert not {"pin", "leader"} & {m.role for m in marks}

    def test_a_town_at_full_size_is_underlined(self, hand: Hand) -> None:
        """A settlement at the default size takes one underline, a smaller one none."""
        big = lettering_marks.label_marks(hand, _flat(kind="settlement", size=20.0))
        small = lettering_marks.label_marks(hand, _flat(kind="settlement", size=14.0))
        assert [m.role for m in big].count("underline") == 1
        assert "underline" not in {m.role for m in small}

    def test_a_home_takes_its_house(self, hand: Hand) -> None:
        """A home label draws its house as one extra mark."""
        marks = lettering_marks.label_marks(hand, _flat(kind="home", size=14.0))
        assert [m.role for m in marks].count("span") == 1


class TestTranslation:
    """A label's kind, tier and lift become the setting the hand writes."""

    def test_a_river_is_set_wide_and_in_water_ink(self, hand: Hand) -> None:
        """A river beside its water leans, is tracked wide and written in the water ink."""
        river = _flat(kind="river", name="Lyn", flat=False, baseline=COURSE, size=14.0)
        marks = lettering_marks.label_marks(hand, river)
        assert {m.ink for m in marks} == {"water"}
        wide = lettering_marks.label_marks(hand, _flat(kind="landmark", name="Lyn"))
        assert wide

    def test_the_same_label_writes_the_same_marks(self, hand: Hand) -> None:
        """A label's marks are the same twice, as its generator is seeded by what names it."""
        label = _flat(leader=((120.0, 90.0), (150.0, 72.0)))
        assert lettering_marks.label_marks(hand, label) == lettering_marks.label_marks(hand, label)

    def test_a_span_writes_its_line_and_ticks(self, hand: Hand) -> None:
        """A span draws one line mark and one tick mark a tick, in its intent's ink."""
        span = Span(
            name="Porlock Hill",
            kind="climb",
            intent="warning",
            line=[(10.0, 10.0), (60.0, 30.0), (110.0, 40.0)],
            ticks=[[(10.0, 5.0), (10.0, 15.0)], [(110.0, 35.0), (110.0, 45.0)]],
        )
        marks = lettering_marks.span_marks(hand, span)
        assert [m.role for m in marks] == ["span", "tick", "tick"]
        assert {m.ink for m in marks} == {lettering_marks.SPAN_INTENT_INK["warning"]}

    def test_the_placers_box_is_half_an_em_wider_than_the_set_width(self, hand: Hand) -> None:
        """The placer's box adds half the size to the face's own width."""
        width, height = hand.measure("Aviemore", 14.0)
        assert lettering_marks.box_size(hand, "Aviemore", 14.0) == (width + 7.0, height)


class TestWindow:
    """A name the placer skipped is set along the best readable window of its line."""

    def test_a_gentle_line_gives_a_window_and_a_hairpin_gives_none(self, hand: Hand) -> None:
        """A name takes a window on a gentle line and is set flat on a hairpin."""
        hairpin = [
            (100.0 + 40.0 * math.cos(a / 9.0), 100.0 + 40.0 * math.sin(a / 9.0))
            for a in range(0, 80)
        ]
        width = hand.measure("Heddon", 14.0)[0]
        gentle = _flat(kind="river", name="Heddon", flat=False, baseline=COURSE, px=200.0)
        tight = _flat(kind="river", name="Heddon", flat=False, baseline=hairpin, px=100.0)
        assert baseline(gentle, width)
        assert baseline(tight, width) is None

    def test_a_window_is_never_upside_down(self) -> None:
        """A line drawn right to left is returned left to right."""
        backwards = [(400.0 - x, y) for x, y in COURSE]
        label = _flat(kind="river", name="Heddon", flat=False, baseline=backwards, px=200.0)
        run = baseline(label, 60.0)
        assert run is not None
        assert run[-1][0] > run[0][0]


def _contrast(a: str, b: str) -> float:
    """WCAG contrast between two hex colours."""

    def lum(hexed: str) -> float:
        v = hexed.lstrip("#")
        out: list[float] = []
        for i in (0, 2, 4):
            c = int(v[i : i + 2], 16) / 255
            out.append(c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4)
        return 0.2126 * out[0] + 0.7152 * out[1] + 0.0722 * out[2]

    hi, lo = sorted((lum(a), lum(b)), reverse=True)
    return (hi + 0.05) / (lo + 0.05)


def test_a_name_on_the_water_takes_its_own_ink():
    """The water ink is the colour of the thing the name is now written on."""
    assert lettering_marks._ink(river_label(40.0)) == "in_water"
    assert lettering_marks._ink(river_label(11.0)) == "water"


def test_the_in_water_ink_beats_a_dark_one_on_the_river():
    """The water is a mid-tone: a dark ink fights it from the wrong side.

    Measured against the major watercourse's own pigment, which is what the
    letters are written over.
    """
    style = class_style()
    river = BRUSH_COLOURS["RIV"]["a"]
    assert _contrast(style.nib.label_in_water_ink, river) > _contrast("#0f1216", river)
    assert _contrast(style.nib.label_in_water_ink, river) > 4.5


def test_a_name_on_the_water_asks_for_no_backing_wash():
    """A pale blob on a river reads as a hole in the water."""
    hand = open_hand()
    wet = lettering_marks.label_marks(hand, river_label(40.0))
    dry = lettering_marks.label_marks(hand, river_label(11.0))
    assert wet and not any(m.wash for m in wet)
    assert dry and all(m.wash for m in dry)
