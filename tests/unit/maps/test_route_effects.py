"""The route's effects at compose: a stack laid round the route on the card, nowhere else."""

import dataclasses

import numpy as np
import pytest
from PIL import Image

from pyntpot.ink import Casing, Colour
from pyntpot.ink.noise import chamfer_distance
from pyntpot.maps import Plates, Style
from pyntpot.maps.compose_steps import painted_map, route
from pyntpot.maps.line_effects import EffectStack
from pyntpot.maps.painter.plates import paint_plates

from .painter.jobs import tiny_job

WIDTH_PX = 3.0
STRANDS = [(5.0, 5.0), (70.0, 50.0), (10.0, 50.0), (70.0, 10.0)]


@pytest.fixture(scope="module")
def plates(tmp_path_factory: pytest.TempPathFactory) -> Plates:
    """The tiny card painted once."""
    out = tmp_path_factory.mktemp("route_effects")
    job = tiny_job(out)
    return paint_plates(job.basemap, job.style, out)


def _card(plates: Plates, ink, *, k: float = 2.0) -> Image.Image:
    """The painted card with the route drawn in `ink`."""
    card = painted_map(plates)
    route(card, plates, STRANDS, ink, k)
    return card


@pytest.mark.parametrize("drawn_as", ["pen", "solid"], ids=["pen", "solid"])
def test_a_route_casing_changes_only_pixels_within_its_ring(plates, drawn_as):
    """The casing alters the card within its ring of the route and leaves the rest bit for bit."""
    base = dataclasses.replace(Style.default().route_ink, drawn_as=drawn_as)
    cased = dataclasses.replace(
        base, effects=EffectStack(effects=(Casing(width_px=WIDTH_PX, colour=Colour("#ffffff")),))
    )
    k = plates.card.render[0] / plates.card.display[0]
    plain = np.asarray(_card(plates, base, k=k))
    laid = np.asarray(_card(plates, cased, k=k))
    bare = np.asarray(painted_map(plates))
    line = (plain != bare).any(axis=2)
    changed = (plain != laid).any(axis=2)
    ring = chamfer_distance(line) <= WIDTH_PX * k + 2.0
    assert changed.any()
    assert not changed[~ring].any()


def test_a_route_casing_never_rewrites_the_pen_plate(plates):
    """The pen plate on disk is the same bytes after a cased route is composed."""
    pen = plates.directory / plates.manifest.files["pen"]
    before = pen.read_bytes()
    ink = dataclasses.replace(
        Style.default().route_ink,
        drawn_as="pen",
        effects=EffectStack(effects=(Casing(width_px=WIDTH_PX),)),
    )
    _card(plates, ink)
    assert pen.read_bytes() == before
