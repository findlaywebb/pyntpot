"""Benchmarks for the map pipeline over the Lynmouth fixture: fetch, paint, letter and compose.

The fixture providers answer from the shipped payloads, so nothing here touches the
network. The card is painted at a reduced display width so one round stays short.
"""

import dataclasses
import shutil
from typing import Any, NamedTuple

import pytest
from pytest_benchmark.fixture import BenchmarkFixture

from pyntpot.maps import pipeline
from pyntpot.maps.basemap import Basemap
from pyntpot.maps.cache import Cache
from pyntpot.maps.lettering.pipeline import Lettering, letter
from pyntpot.maps.plates import Plates
from pyntpot.maps.style import Style
from pyntpot.maps.track import Track

from support.paths import FIXTURE_DIR
from support.providers import FixtureElevation, FixtureFeatures

#: The display width the benchmarked card is painted at, in CSS pixels.
DISPLAY_PX = 225


class Fixture(NamedTuple):
    """A copy of the fixture: its track, its filled cache, and the style it is painted in."""

    track: Track
    cache: Cache
    style: Style


class Painted(NamedTuple):
    """The fixture fetched and painted once, in the benchmark style."""

    basemap: Basemap
    plates: Plates
    style: Style


@pytest.fixture(scope="module")
def lynmouth(tmp_path_factory: pytest.TempPathFactory) -> Fixture:
    """The fixture copied once, its track parsed, in the default style at `DISPLAY_PX`."""
    work = tmp_path_factory.mktemp("lynmouth")
    shutil.copytree(FIXTURE_DIR, work, dirs_exist_ok=True)
    base = Style.default()
    style = base.model_copy(update={"card": dataclasses.replace(base.card, display_px=DISPLAY_PX)})
    return Fixture(Track.from_gpx(work / "track.gpx"), Cache(work), style)


@pytest.fixture(scope="module")
def painted(lynmouth: Fixture, tmp_path_factory: pytest.TempPathFactory) -> Painted:
    """The fixture fetched and painted once, for the steps that follow painting."""
    basemap = _fetch(lynmouth)
    plates = pipeline.paint(basemap, lynmouth.style, tmp_path_factory.mktemp("plates"))
    return Painted(basemap, plates, lynmouth.style)


def _fetch(lynmouth: Fixture) -> Basemap:
    """Build the fixture's basemap from its filled cache, calling no provider."""
    return pipeline.fetch(
        lynmouth.track, lynmouth.cache, FixtureFeatures(), FixtureElevation(), lynmouth.style
    )


def test_fetching_the_basemap(benchmark: BenchmarkFixture, lynmouth: Fixture) -> None:
    """Times building the basemap from cached payloads: parsing, projecting and generalising."""
    basemap = benchmark(_fetch, lynmouth)
    assert basemap.layers.route


def test_painting_the_plates(
    benchmark: BenchmarkFixture, lynmouth: Fixture, tmp_path_factory: pytest.TempPathFactory
) -> None:
    """Times painting the paper, wash and pen plates into a fresh directory each round."""
    basemap = _fetch(lynmouth)

    def fresh_directory() -> tuple[tuple[Any, ...], dict[str, Any]]:
        return (basemap, lynmouth.style, tmp_path_factory.mktemp("plates")), {}

    plates = benchmark.pedantic(pipeline.paint, setup=fresh_directory, rounds=1)
    assert plates.strands


def test_lettering_the_card(benchmark: BenchmarkFixture, painted: Painted) -> None:
    """Times placing and writing the fixture's names over the painted plates."""
    lettering = benchmark(letter, painted.plates, painted.basemap, None, painted.style)
    assert lettering.labels


def test_composing_the_card(benchmark: BenchmarkFixture, painted: Painted) -> None:
    """Times composing the painted, lettered plates into one card."""
    lettering: Lettering = letter(painted.plates, painted.basemap, None, painted.style)
    card = benchmark(
        pipeline.compose,
        painted.plates,
        lettering,
        painted.basemap,
        painted.style,
        attribution=True,
    )
    assert card.size[0] > 0
