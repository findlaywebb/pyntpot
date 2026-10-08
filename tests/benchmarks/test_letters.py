"""Benchmarks for the hand: tracing a face's glyphs cold, and writing names with them warm."""

import pytest
from pytest_benchmark.fixture import BenchmarkFixture

from pyntpot.letters.hand import Hand
from pyntpot.letters.setting import Mark, Setting
from pyntpot.letters.style import FaceStyle, HandStyle

pytestmark = pytest.mark.benchmark

#: A straight synthetic line a long name is written along, in display pixels.
LINE = tuple((10.0 + 8.0 * i, 60.0) for i in range(60))

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
