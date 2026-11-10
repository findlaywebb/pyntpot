"""The painter's casing unions and reserves: one ring round a union, the paper laid in its place."""

import dataclasses

import numpy as np
import pytest

from pyntpot.ink import Casing, Colour, Glow, Reserve
from pyntpot.ink.compositing import composite
from pyntpot.ink.effect_distance import contour_distance, ring_coverage
from pyntpot.ink.effect_union import casing_union
from pyntpot.ink.noise import F32, chamfer_distance
from pyntpot.maps.basemap import Road
from pyntpot.maps.effect_pass import lay_stack
from pyntpot.maps.line_effects import EffectStack
from pyntpot.maps.painter.job import PaintJob, PlateStack
from pyntpot.maps.painter.pen import pen_groups
from pyntpot.maps.painter.plates import _wash_plate

from .jobs import tiny_job

CORE = 0.3
WIDTH_PX = 2.0
WHITE = Colour("#ffffff")


def _road(band: str, points: list[tuple[float, float]]) -> Road:
    """A road of `band` through `points`, in card metres."""
    return Road(line=tuple(points), cls=band, band=band, highway="primary", name="", ref="")


def _job(
    tmp_path,
    effects: dict[str, EffectStack] | None = None,
    unions: tuple[tuple[str, ...], ...] = (),
) -> PaintJob:
    """A major road and a lane that cross, the style carrying `effects` and `unions`."""
    major = [(float(x), 120.0 + 0.02 * x) for x in range(10, 310, 20)]
    lane = [(150.0 + 0.02 * y, float(y)) for y in range(10, 235, 15)]
    job = tiny_job(
        tmp_path,
        roads=(_road("major", major), _road("minor", lane)),
        minor_roads=True,
    )
    basemap = dataclasses.replace(
        job.style.basemap, line_effects=effects or {}, casing_unions=unions
    )
    return dataclasses.replace(job, style=job.style.model_copy(update={"basemap": basemap}))


def _plate(job: PaintJob) -> np.ndarray:
    """The wash plate of `job`, painted over a blank stack."""
    return _wash_plate(job, PlateStack.blank(job.shape))


def _casings(width: float = WIDTH_PX) -> dict[str, EffectStack]:
    """A white casing of `width` display pixels on the major road and the lane."""
    stack = EffectStack(effects=(Casing(width_px=width, colour=WHITE),))
    return {"road_major": stack, "lane": stack}


class TestUnionOfCasings:
    """A union lays one ring round the roads together and never inside either."""

    def test_the_footprints_are_untouched_and_only_the_ring_changes(self, tmp_path):
        """Pixels inside either road equal the bare plate; changes lie within the union's ring."""
        bare = _plate(_job(tmp_path / "a"))
        job = _job(tmp_path / "b", _casings(), (("road_major", "lane"),))
        masks = pen_groups(job).road.masks
        foot = (masks["road_major"] >= CORE) | (masks["lane"] >= CORE)
        changed = (bare != _plate(job)).any(axis=2)
        reach = chamfer_distance(foot) <= WIDTH_PX * job.scale + 2.0
        assert changed.any()
        assert not changed[foot].any()
        assert not changed[~reach].any()

    def test_without_a_union_the_lane_ring_shows_inside_the_major_road(self, tmp_path):
        """Separate casings do change pixels inside the major road, which is what a union stops."""
        bare = _plate(_job(tmp_path / "a"))
        job = _job(tmp_path / "b", _casings())
        major = pen_groups(job).road.masks["road_major"] >= CORE
        assert (bare != _plate(job)).any(axis=2)[major].any()

    @pytest.mark.parametrize("kind", ["casing", "reserve"])
    def test_a_union_of_one_equals_no_union(self, tmp_path, kind):
        """One class in a union is laid exactly as the same class with no union."""
        effect = Casing(width_px=WIDTH_PX) if kind == "casing" else Reserve(width_px=WIDTH_PX)
        effects = {"road_major": EffectStack(effects=(effect,))}
        plain = _plate(_job(tmp_path / "a", effects))
        united = _plate(_job(tmp_path / "b", effects, (("road_major",),)))
        assert np.array_equal(plain, united)

    def test_each_member_keeps_its_own_width(self, tmp_path):
        """A wider lane casing reaches farther from the lane than the major road's own."""
        stacks = {
            "road_major": EffectStack(effects=(Casing(width_px=1.0, colour=WHITE),)),
            "lane": EffectStack(effects=(Casing(width_px=4.0, colour=WHITE),)),
        }
        bare = _plate(_job(tmp_path / "a"))
        job = _job(tmp_path / "b", stacks, (("road_major", "lane"),))
        masks = pen_groups(job).road.masks
        changed = (bare != _plate(job)).any(axis=2)
        far_from_major = chamfer_distance(masks["road_major"] >= CORE) > 1.0 * job.scale + 2.0
        assert changed[far_from_major].any()


class TestRingStep:
    """`lay_stack` takes the ring from its caller, or none, or its own."""

    @staticmethod
    def _scene() -> tuple[np.ndarray, np.ndarray]:
        """A grey field and a horizontal line."""
        rgb = np.full((40, 40, 3), 0.5, F32)
        mask = np.zeros((40, 40), F32)
        mask[20, 5:35] = 1.0
        return rgb, mask

    def test_an_empty_ring_skips_the_casing_and_keeps_the_glow(self):
        """With `ring=()` a stack lays its glow alone, as if it held no casing."""
        rgb, mask = self._scene()
        glow = Glow(spread_px=1.0, blur_px=1.0, strength=0.5)
        both = EffectStack(effects=(Casing(width_px=2.0), glow))
        got = lay_stack(rgb, mask, both, scale=1.0, paper=None, ring=())
        want = lay_stack(rgb, mask, EffectStack(effects=(glow,)), scale=1.0, paper=None, ring=None)
        assert np.array_equal(got, want)

    def test_an_empty_ring_on_a_casing_alone_returns_the_array_itself(self):
        """Nothing is laid, so the colour beneath comes back untouched."""
        rgb, mask = self._scene()
        stack = EffectStack(effects=(Casing(width_px=2.0),))
        assert lay_stack(rgb, mask, stack, scale=1.0, paper=None, ring=()) is rgb

    def test_pairs_lay_the_union_with_each_width_scaled(self):
        """Pairs in display pixels are scaled by `scale` and laid as one ring."""
        rgb, mask = self._scene()
        other = np.zeros_like(mask)
        other[5:35, 20] = 1.0
        a, b = Casing(width_px=1.0), Casing(width_px=2.0)
        stack = EffectStack(effects=(a,))
        got = lay_stack(rgb, mask, stack, scale=2.0, paper=None, ring=((mask, a), (other, b)))
        want = casing_union(
            rgb, [(mask, Casing(width_px=2.0)), (other, Casing(width_px=4.0))], paper=None
        )
        assert np.array_equal(got, want)

    def test_a_reserve_is_laid_against_the_paper_plate(self):
        """A reserve in a stack lays the paper plate, not white, where its ring is whole."""
        rgb, mask = self._scene()
        paper = np.full_like(rgb, 0.9)
        stack = EffectStack(effects=(Reserve(width_px=3.0),))
        got = lay_stack(rgb, mask, stack, scale=1.0, paper=paper)
        assert got[17, 20, 0] == pytest.approx(0.9)
        assert np.array_equal(got[20, 20], rgb[20, 20])


class TestReserveInWash:
    """A reserve is the paper in the wash, and the ink laid after it glazes over it."""

    def _setup(self, tmp_path):
        """The cross with a reserve on the major road, its plate, and the road group."""
        stack = {"road_major": EffectStack(effects=(Reserve(width_px=3.0),))}
        job = _job(tmp_path, stack)
        return job, _plate(job), pen_groups(job).road

    def test_the_ring_is_the_ink_glazed_over_bare_paper(self, tmp_path):
        """Where the ring is whole the plate is the road layers glazed over the paper, 1.0."""
        job, plate, group = self._setup(tmp_path)
        width = 3.0 * job.scale
        major = group.masks["road_major"]
        d = contour_distance(major, threshold=CORE, radius=width + 2)
        whole = ring_coverage(d, width) >= 1.0
        paper = np.ones(plate.shape, F32)
        glazed = composite(group.layers, paper, job.style.paper)
        assert whole.any()
        assert np.array_equal(plate[whole], glazed[whole])
        assert not np.array_equal(plate[whole], _plate(_job(tmp_path / "bare"))[whole])

    def test_a_later_line_glazes_over_the_reserve(self, tmp_path):
        """The lane crosses the major road's reserve and is darker than the paper there."""
        job, plate, group = self._setup(tmp_path)
        width = 3.0 * job.scale
        major = group.masks["road_major"]
        d = contour_distance(major, threshold=CORE, radius=width + 2)
        whole = ring_coverage(d, width) >= 1.0
        crossing = whole & (group.masks["lane"] >= CORE)
        assert crossing.any()
        assert np.all(plate[crossing].max(axis=1) < 1.0)
