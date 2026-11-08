"""Benchmarks for the hand: tracing a face's glyphs cold, writing names with them warm, and the nib's widths."""

import math

import numpy as np
import pytest
from pytest_benchmark.fixture import BenchmarkFixture

from pyntpot.ink.brush_style import BrushStyle
from pyntpot.letters.hand import Hand
from pyntpot.letters.nib import nib_brushes
from pyntpot.letters.pen_profile import pen_profile
from pyntpot.letters.setting import Mark, Setting
from pyntpot.letters.style import FaceStyle, HandStyle, NibStyle

from support.flags_off import flags_off

pytestmark = pytest.mark.benchmark

#: A straight synthetic line a long name is written along, in display pixels.
LINE = tuple((10.0 + 8.0 * i, 60.0) for i in range(60))

#: Render pixels per display pixel, as a card paints its lettering.
SCALE = 2.0

#: The two ways a glyph becomes a pen path.
ROUTES = ("centreline", "outline")


@pytest.fixture(scope="module")
def hand() -> Hand:
    """The default hand, opened once and warmed on every glyph the benchmarks write."""
    opened = Hand(FaceStyle(), HandStyle())
    opened.write(Setting("Lynmouth and Lynton", 14.0, path=LINE), opened.generator(0))
    opened.write(Setting("Countisbury Hill", 20.0, anchor=(40.0, 60.0)), opened.generator(0))
    return opened


@pytest.mark.parametrize("route", ROUTES, ids=ROUTES)
def test_writing_a_name_with_a_fresh_hand(benchmark: BenchmarkFixture, route: str) -> None:
    """Times opening a hand and writing a name, tracing every glyph it needs from the face."""

    def run() -> list[Mark]:
        fresh = Hand(FaceStyle(), HandStyle(), route)
        return fresh.write(Setting("Lynmouth and Lynton", 14.0, path=LINE), fresh.generator(1))

    benchmark(run)


def test_writing_a_name_along_a_line(benchmark: BenchmarkFixture, hand: Hand) -> None:
    """Times a warm hand writing a long name along a line, each glyph on its own tangent."""
    setting = Setting("Lynmouth and Lynton", 14.0, path=LINE)
    benchmark(lambda: hand.write(setting, hand.generator(1)))


def test_writing_a_flat_block(benchmark: BenchmarkFixture, hand: Hand) -> None:
    """Times a warm hand writing a flat two-row block from an anchor."""
    setting = Setting("Countisbury Hill", 20.0, anchor=(40.0, 60.0), lines=("Countisbury", "Hill"))
    benchmark(lambda: hand.write(setting, hand.generator(1)))


def test_the_nib_widths_of_a_name(benchmark: BenchmarkFixture, hand: Hand) -> None:
    """Times the broad nib's width profile along every glyph stroke of a long name, at the default nib."""
    marks = hand.write(Setting("Lynmouth and Lynton", 14.0, path=LINE), hand.generator(1))
    nib = NibStyle()
    window = nib_brushes(nib, FaceStyle(), flags_off(BrushStyle), SCALE)("glyph", 14.0).width
    angle = math.radians(nib.label_pen_angle_deg)
    strokes = [(np.asarray(mark.pts) * SCALE, angle + mark.pen) for mark in marks]

    def run() -> list[np.ndarray]:
        return [pen_profile(pts, tilt, nib.label_pen_thin, window) for pts, tilt in strokes]

    benchmark(run)
