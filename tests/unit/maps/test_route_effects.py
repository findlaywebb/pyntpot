"""The route's effects at compose: a stack laid round the route on the card, nowhere else."""

import dataclasses

import numpy as np
import pytest
from PIL import Image

from pyntpot.ink import Casing, Colour, Reserve
from pyntpot.ink.effect_distance import contour_distance, ring_coverage
from pyntpot.ink.noise import F32, chamfer_distance
from pyntpot.maps import Plates, Style
from pyntpot.maps.compose_steps import painted_map, route
from pyntpot.maps.line_effects import EffectStack
from pyntpot.maps.painter.plates import paint_plates
from pyntpot.maps.route_effects import lay, pen_mask

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


class TestPenMask:
    """The pen route mask is the alpha's density above a noise floor."""

    @staticmethod
    def _alpha(values: list[int]) -> Image.Image:
        """An `L` image of one row holding `values`."""
        return Image.fromarray(np.array([values], np.uint8), "L")

    def test_sub_floor_alphas_give_zeros(self):
        """Alphas under 8 of 255, Lanczos ringing and lossy noise, are no line at all."""
        got = pen_mask(self._alpha([0, 1, 4, 7]))
        assert got.dtype == F32
        assert not got.any()

    def test_alphas_at_or_above_the_floor_are_kept_exactly(self):
        """8 and above are the density, `alpha / 255` in float32, with no threshold."""
        values = [8, 9, 77, 128, 255]
        got = pen_mask(self._alpha(values))
        assert np.array_equal(got[0], np.array(values, F32) / F32(255.0))


def test_a_route_reserve_is_the_paper_plate_where_its_ring_is_whole(plates):
    """On the composed card the reserve ring equals the paper plate where it lies whole."""
    k = plates.card.render[0] / plates.card.display[0]
    pen = Image.open(plates.directory / plates.manifest.files["pen"]).convert("RGBA")
    mask = pen_mask(pen.getchannel("A"))
    stack = EffectStack(effects=(Reserve(width_px=WIDTH_PX),))
    card = painted_map(plates)
    paper = Image.open(plates.paths["paper"]).convert("RGB")
    got = np.asarray(lay(card, mask, stack, scale=k, paper=paper))
    width = WIDTH_PX * k
    whole = ring_coverage(contour_distance(mask, threshold=0.3, radius=width + 2), width) >= 1.0
    assert whole.any()
    assert np.array_equal(got[whole], np.asarray(paper)[whole])
    assert not np.array_equal(got[whole], np.asarray(card)[whole])


def test_a_route_reserve_is_laid_under_the_route_ink(plates):
    """Through `route`, the ink is laid over the reserve, so the line itself stays drawn."""
    ink = dataclasses.replace(
        Style.default().route_ink,
        drawn_as="pen",
        effects=EffectStack(effects=(Reserve(width_px=WIDTH_PX),)),
    )
    plain = dataclasses.replace(ink, effects=EffectStack())
    k = plates.card.render[0] / plates.card.display[0]
    laid = np.asarray(_card(plates, ink, k=k))
    bare = np.asarray(_card(plates, plain, k=k))
    pen = Image.open(plates.directory / plates.manifest.files["pen"]).convert("RGBA")
    line = pen_mask(pen.getchannel("A")) >= 0.3
    assert (laid != bare).any()
    assert np.array_equal(laid[line], bare[line])
