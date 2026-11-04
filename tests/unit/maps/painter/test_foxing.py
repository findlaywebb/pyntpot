"""The foxing on a real card's sheet: how much of it there is and how big each speck is."""

import dataclasses
import shutil

import numpy as np
import pytest

from pyntpot.ink.paper import paper_plate
from pyntpot.ink.sheet import Sheet
from pyntpot.maps import Cache, Track, fetch
from pyntpot.maps.painter.job import PaintJob
from pyntpot.maps.style import Style

from support.paths import FIXTURE_DIR
from support.providers import FixtureElevation, FixtureFeatures


@pytest.fixture(scope="module")
def job(tmp_path_factory: pytest.TempPathFactory) -> PaintJob:
    """The Lynmouth card's paint job (a 1800 by 1457 render-pixel sheet), built once."""
    work = tmp_path_factory.mktemp("lynmouth")
    shutil.copytree(FIXTURE_DIR, work, dirs_exist_ok=True)
    style = Style.default()
    track = Track.from_gpx(work / "track.gpx")
    basemap = fetch(track, Cache(work), FixtureFeatures(), FixtureElevation(), style)
    return PaintJob.begin(basemap, style, work / "plates")


def speck_extents(mask: np.ndarray) -> list[int]:
    """The longer side of each 4-connected component's bounding box in `mask`."""
    seen = np.zeros_like(mask)
    extents = []
    for start in zip(*np.nonzero(mask), strict=True):
        if seen[start]:
            continue
        seen[start] = True
        stack, found = [start], [start]
        while stack:
            y, x = stack.pop()
            for ny, nx in ((y + 1, x), (y - 1, x), (y, x + 1), (y, x - 1)):
                inside = 0 <= ny < mask.shape[0] and 0 <= nx < mask.shape[1]
                if inside and mask[ny, nx] and not seen[ny, nx]:
                    seen[ny, nx] = True
                    stack.append((ny, nx))
                    found.append((ny, nx))
        ys, xs = zip(*found, strict=True)
        extents.append(int(max(max(ys) - min(ys), max(xs) - min(xs))) + 1)
    return extents


def test_the_foxing_on_a_card_sheet_is_a_few_small_specks(job):
    """On the Lynmouth card's sheet foxed pixels are under 1% and each speck is at most twice the grain."""
    style, canvas, grain = job.style.paper, job.canvas, job.sheet.gran_px

    def plate(**over: float) -> np.ndarray:
        sheet = Sheet(canvas.h, canvas.w, grain, style.sheet_seed)
        return paper_plate(sheet, canvas, dataclasses.replace(style, **over), canvas.w)

    hit = np.abs(plate() - plate(paper_foxing=0.0)).max(axis=2) > 0
    largest = max(speck_extents(hit))
    assert 0.0 < hit.mean() < 0.01
    assert largest <= 2 * grain, f"largest speck {largest} px, grain {grain}"
