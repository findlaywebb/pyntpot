"""Benchmarks for the map pipeline over the Lynmouth fixture: fetch, paint, letter and compose.

The fixture providers answer from the shipped payloads, so nothing here touches the
network. Every benchmark paints at `DISPLAY_PX`, below the default card, so one round
stays short.
"""

import itertools
import shutil
from pathlib import Path
from typing import NamedTuple

import pytest
from pytest_benchmark.fixture import BenchmarkFixture

from pyntpot import Basemap, Lettering, Plates, Style, Track, compose, fetch, letter, paint
from pyntpot.maps.cache import Cache

from support.basemaps import class_style
from support.paths import FIXTURE_DIR
from support.providers import FixtureElevation, FixtureFeatures

pytestmark = pytest.mark.benchmark

#: The display width every maps benchmark paints at, in CSS pixels.
DISPLAY_PX = 450


class Lynmouth(NamedTuple):
    """A copy of the fixture: its parsed track, its filled cache, and the style it is painted in."""

    track: Track
    cache: Cache
    style: Style


@pytest.fixture(scope="module")
def lynmouth(tmp_path_factory: pytest.TempPathFactory) -> Lynmouth:
    """The fixture copied once and its track parsed, in the class style at `DISPLAY_PX`."""
    work = tmp_path_factory.mktemp("lynmouth")
    shutil.copytree(FIXTURE_DIR, work, dirs_exist_ok=True)
    style = class_style(display_px=DISPLAY_PX)
    return Lynmouth(Track.from_gpx(work / "track.gpx"), Cache(work), style)


@pytest.fixture(scope="module")
def basemap(lynmouth: Lynmouth) -> tuple[Basemap, Style]:
    """The fixture's basemap, built once from its cached payloads, with the style."""
    return _fetch(lynmouth), lynmouth.style


@pytest.fixture(scope="module")
def painted(basemap: tuple[Basemap, Style], tmp_path_factory: pytest.TempPathFactory) -> Plates:
    """The plates painted once from the basemap, for the stages that follow painting."""
    base, style = basemap
    return paint(base, style, tmp_path_factory.mktemp("plates"))


@pytest.fixture(scope="module")
def lettered(basemap: tuple[Basemap, Style], painted: Plates) -> Lettering:
    """The painted plates lettered once, for composing."""
    base, style = basemap
    return letter(painted, base, None, style)


def _fetch(lynmouth: Lynmouth) -> Basemap:
    """Build the fixture's basemap from its filled cache, calling no provider."""
    return fetch(
        lynmouth.track, lynmouth.cache, FixtureFeatures(), FixtureElevation(), lynmouth.style
    )


def test_fetch(benchmark: BenchmarkFixture, lynmouth: Lynmouth) -> None:
    """Times building the basemap from cached payloads: parsing, projecting and generalising."""
    benchmark(_fetch, lynmouth)


def test_paint(benchmark: BenchmarkFixture, basemap: tuple[Basemap, Style], tmp_path: Path) -> None:
    """Times painting the plates, into a fresh directory each round so no round is skipped."""
    base, style = basemap
    rounds = itertools.count()
    benchmark(lambda: paint(base, style, tmp_path / f"round-{next(rounds)}"))


def test_letter(
    benchmark: BenchmarkFixture, basemap: tuple[Basemap, Style], painted: Plates
) -> None:
    """Times placing and writing the fixture's names over the painted plates."""
    base, style = basemap
    benchmark(letter, painted, base, None, style)


def test_compose(
    benchmark: BenchmarkFixture,
    basemap: tuple[Basemap, Style],
    painted: Plates,
    lettered: Lettering,
) -> None:
    """Times composing the painted, lettered plates into one card, attribution on."""
    base, style = basemap
    benchmark(compose, painted, lettered, base, style)
