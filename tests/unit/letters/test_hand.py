"""Tests for the hand: it writes a setting along a line or flat, the same each time for a seed."""

import dataclasses

import pytest

from pyntpot.ink.polyline import Pt
from pyntpot.letters.font import OutlineFont
from pyntpot.letters.hand import Hand
from pyntpot.letters.setting import Align, Mark, Setting
from pyntpot.letters.style import FaceStyle, HandStyle

from support.lettering import open_hand

#: A straight synthetic line a name could be written along, in display pixels.
LINE = tuple((10.0 + 8.0 * i, 60.0) for i in range(30))


@pytest.fixture(scope="module")
def hand() -> Hand:
    """The default hand, opened once: its face is loaded and never changes."""
    return Hand(FaceStyle(), HandStyle())


def _points(marks: list[Mark]) -> list[Pt]:
    """Every point of every mark, in the order written."""
    return [pt for mark in marks for pt in mark.pts]


class TestWrite:
    """The hand writes a setting as marks, deterministically for one generator state."""

    def test_it_writes_a_name_along_a_straight_line(self, hand: Hand) -> None:
        """Grasmere along a straight line gives glyph marks that start near it and run along it."""
        marks = hand.write(Setting("Grasmere", 14.0, path=LINE), hand.generator(1))
        assert marks
        assert {m.role for m in marks} == {"glyph"}
        xs = [x for x, _y in _points(marks)]
        ys = [y for _x, y in _points(marks)]
        assert min(xs) < 25.0
        assert max(xs) > 50.0
        assert all(40.0 < y < 75.0 for y in ys)

    def test_the_same_seed_writes_the_same_marks(self, hand: Hand) -> None:
        """Two generators from one seed write identical marks."""
        setting = Setting("Grasmere", 14.0, path=LINE)
        assert hand.write(setting, hand.generator(7)) == hand.write(setting, hand.generator(7))

    def test_another_seed_writes_different_marks(self, hand: Hand) -> None:
        """A generator from another seed writes a different hand."""
        setting = Setting("Grasmere", 14.0, path=LINE)
        assert hand.write(setting, hand.generator(7)) != hand.write(setting, hand.generator(8))

    def test_a_slant_leans_the_strokes_to_the_right(self, hand: Hand) -> None:
        """A slant of 0.22 gives a positive mean x drift against an upright setting."""
        upright = Setting("Keswick", 20.0, anchor=(40.0, 60.0))
        leaning = dataclasses.replace(upright, slant=0.22)
        drift = []
        for setting in (upright, leaning):
            marks = hand.write(setting, hand.generator(3))
            drift.append(sum(m.pts[-1][0] - m.pts[0][0] for m in marks) / len(marks))
        assert drift[1] - drift[0] > 0.0

    def test_a_wrapped_block_is_narrower_and_taller_than_one_row(self, hand: Hand) -> None:
        """Two rows write a narrower, taller block than the same name on one row."""
        name = "Newlands Valley"
        one = hand.write(Setting(name, 14.0, anchor=(100.0, 60.0)), hand.generator(2))
        two = hand.write(
            Setting(name, 14.0, anchor=(100.0, 60.0), lines=("Newlands", "Valley")),
            hand.generator(2),
        )

        def extent(marks: list[Mark], axis: int) -> float:
            values = [pt[axis] for pt in _points(marks)]
            return max(values) - min(values)

        assert extent(two, 0) < extent(one, 0) * 0.8
        assert extent(two, 1) > extent(one, 1)

    @pytest.mark.parametrize("align", ["start", "middle", "end"], ids=["start", "middle", "end"])
    def test_a_flat_block_sits_on_its_anchor_edge(self, hand: Hand, align: Align) -> None:
        """A flat block starts at, is centred on, or ends at its anchor by its alignment."""
        setting = Setting("Wasdale", 20.0, anchor=(200.0, 60.0), align=align)
        xs = [x for x, _y in _points(hand.write(setting, hand.generator(4)))]
        low, high = min(xs), max(xs)
        if align == "start":
            assert low == pytest.approx(200.0, abs=6.0)
        elif align == "middle":
            assert (low + high) / 2 == pytest.approx(200.0, abs=6.0)
        else:
            assert high == pytest.approx(200.0, abs=6.0)

    def test_the_marks_carry_the_settings_ink_size_and_wash(self, hand: Hand) -> None:
        """Each glyph mark takes its ink, size and wash from the setting."""
        setting = Setting("Derwent", 11.0, path=LINE, ink="water", wash=False)
        marks = hand.write(setting, hand.generator(5))
        assert {(m.ink, m.size, m.wash) for m in marks} == {("water", 11.0, False)}


class TestMeasureAndStroke:
    """The hand measures in its own face and wanders a line it is handed."""

    def test_tracking_widens_a_measure_and_adds_no_padding(self, hand: Hand) -> None:
        """A tracked text is wider than an untracked one, and the width is the face's own."""
        plain = hand.measure("Ullswater", 20.0)[0]
        assert hand.measure("Ullswater", 20.0, 0.24)[0] > plain
        assert plain == hand.font.measure("Ullswater", 20.0)[0]

    def test_a_generator_mixes_the_style_seed(self) -> None:
        """The same caller seed under two style seeds draws two different streams."""
        one = Hand(FaceStyle(), HandStyle(label_seed=1)).generator(9).normal()
        two = Hand(FaceStyle(), HandStyle(label_seed=2)).generator(9).normal()
        assert one != two

    def test_a_stroke_keeps_its_ends_and_is_seeded(self, hand: Hand) -> None:
        """A wandered line keeps both ends and is the same curve for the same generator."""
        line = [(0.0, 0.0), (30.0, 0.0), (60.0, 0.0)]
        first = hand.stroke(line, hand.generator(6), 0.5)
        assert first[0] == line[0]
        assert first[-1] == line[-1]
        assert first == hand.stroke(line, hand.generator(6), 0.5)
        assert first != line

    def test_a_stroke_with_no_amount_is_the_line(self, hand: Hand) -> None:
        """A zero amount returns the line untouched and draws nothing."""
        line = [(0.0, 0.0), (30.0, 5.0)]
        rng = hand.generator(6)
        assert hand.stroke(line, rng, 0.0) == line
        assert rng.normal() == hand.generator(6).normal()


def test_the_face_measures_a_name_instead_of_counting_its_characters():
    """The flat eight pixels a character is what every placement fault came from.

    A real face knows that `Abergavenny` and `Wllllllllll` are not the same
    width, and the default cannot: it counts characters. This is the change
    that moves every label on the plate.
    """
    hand = open_hand()
    assert isinstance(hand.font, OutlineFont)
    narrow = hand.measure("iiiiiiiiiii", 20.0)[0]
    wide = hand.measure("WWWWWWWWWWW", 20.0)[0]
    assert wide > narrow * 1.8, "the face is not measuring, it is counting"
