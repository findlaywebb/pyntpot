"""The painter's line effects: the base plate lays a basemap class's stack round its own ink."""

import dataclasses
import inspect

import numpy as np
import pytest

from pyntpot.ink import Casing, Glow, Shadow, casing, shadow
from pyntpot.ink.compositing import composite
from pyntpot.ink.noise import F32, chamfer_distance
from pyntpot.ink.sheet import rgb
from pyntpot.maps import relief
from pyntpot.maps.basemap import River, Road
from pyntpot.maps.effect_pass import lay_stack
from pyntpot.maps.line_effects import EffectStack
from pyntpot.maps.painter.job import PaintJob, PlateStack
from pyntpot.maps.painter.pen import paint_pen, pen_groups
from pyntpot.maps.painter.plates import _wash_plate
from pyntpot.maps.painter.ribbon import paint_ribbon
from pyntpot.maps.painter.water import sea_layer

from .jobs import tiny_job

#: The mask value at which a pixel counts as the line, as the ink primitives default it.
CORE = 0.3
WIDTH_PX = 2.0


def _river() -> River:
    """A river across the top of the card."""
    line = tuple((float(x), 40.0 + 0.1 * x) for x in range(10, 300, 20))
    return River(line=line, cls="major", name="Lyn", width_px=5.0, name_width_px=5.0)


def _road(band: str, y: float) -> Road:
    """A road of `band` across the card at about `y` metres."""
    line = tuple((float(x), y - 0.05 * x) for x in range(10, 300, 20))
    return Road(line=line, cls=band, band=band, highway="primary", name="", ref="")


def _job(tmp_path, effects=None, *, km_glazing=True) -> PaintJob:
    """A job with a river, a major road and a lane, the style carrying `effects`."""
    job = tiny_job(
        tmp_path,
        rivers=(_river(),),
        roads=(_road("major", 200.0), _road("minor", 120.0)),
        minor_roads=True,
    )
    style = job.style
    styled = style.model_copy(
        update={
            "basemap": dataclasses.replace(style.basemap, line_effects=effects or {}),
            "paper": dataclasses.replace(style.paper, km_glazing=km_glazing),
        }
    )
    return dataclasses.replace(job, style=styled)


def _ring(mask: np.ndarray, width_px: float) -> np.ndarray:
    """The pixels within `width_px` of the mask's line, and a pixel of slack."""
    return chamfer_distance(mask >= CORE) <= width_px + 1.0


def _plate(job: PaintJob) -> np.ndarray:
    """The wash plate of `job`, painted over a blank stack."""
    return _wash_plate(job, PlateStack.blank(job.shape))


class TestRoadCasingLocality:
    """A set road casing changes the wash only round that road class."""

    def test_km_glazing_is_bit_exact_outside_the_ring_and_changes_inside(self, tmp_path):
        """With Kubelka-Munk glazing the plate is identical outside the ring and differs inside."""
        effects = {"road_major": EffectStack(effects=(Casing(width_px=WIDTH_PX),))}
        off, on = _job(tmp_path / "a"), _job(tmp_path / "b", effects)
        before, after = _plate(off), _plate(on)
        mask = pen_groups(on).road.masks["road_major"]
        ring = _ring(mask, WIDTH_PX * on.scale)
        changed = (before != after).any(axis=2)
        assert changed.any()
        assert not changed[~ring].any()
        assert changed[ring].any()

    def test_no_pixel_changes_near_the_other_road_class(self, tmp_path):
        """The lane's own core stays as it was: the casing is set on the major road alone."""
        effects = {"road_major": EffectStack(effects=(Casing(width_px=WIDTH_PX),))}
        off, on = _job(tmp_path / "a"), _job(tmp_path / "b", effects)
        lane = pen_groups(on).road.masks["lane"] >= CORE
        major = _ring(pen_groups(on).road.masks["road_major"], WIDTH_PX * on.scale)
        far = lane & ~major
        assert far.any()
        changed = (_plate(off) != _plate(on)).any(axis=2)
        assert not changed[far].any()

    def test_multiply_mode_is_within_a_millionth_outside_the_ring(self, tmp_path):
        """With multiply glazing the split reorders a float32 product, so 1e-6 outside."""
        effects = {"road_major": EffectStack(effects=(Casing(width_px=WIDTH_PX),))}
        off = _job(tmp_path / "a", km_glazing=False)
        on = _job(tmp_path / "b", effects, km_glazing=False)
        ring = _ring(pen_groups(on).road.masks["road_major"], WIDTH_PX * on.scale)
        diff = np.abs(_plate(off) - _plate(on))
        assert diff[~ring].max() <= 1e-6
        assert diff[ring].max() > 1e-3


class TestDefaultPath:
    """With no line effects the wash plate is today's single composite."""

    def test_empty_line_effects_equal_one_composite_call(self, tmp_path):
        """`_wash_plate` equals the sea, rim and every ink layer composited at once."""
        job = _job(tmp_path)
        stack = PlateStack.blank(job.shape)
        ground, rim = paint_ribbon(job, stack)
        sea = sea_layer(job, stack)
        assert sea is None
        under = [
            (
                np.clip(rim * job.style.ribbon.rim_strength, 0, 1),
                rgb(job.style.cover.pigments["rim"]),
                job.transp("rim"),
            )
        ]
        expected = composite([*under, *paint_pen(job)], ground, job.style.paper)
        assert np.array_equal(_plate(_job(tmp_path / "again")), expected)


class TestMaskPads:
    """The water mask pads are built only for a class with an effect."""

    def test_no_effect_builds_no_water_mask(self, tmp_path):
        """Without a water effect the group holds layers and no mask."""
        groups = pen_groups(_job(tmp_path))
        assert groups.water.masks == {}
        assert len(groups.water.layers) == 1

    def test_a_water_glow_builds_that_classes_mask_only(self, tmp_path):
        """A glow on the major watercourse builds its mask, with the river drawn in it."""
        effects = {"major": EffectStack(effects=(Glow(spread_px=1.0, blur_px=1.0, strength=0.5),))}
        groups = pen_groups(_job(tmp_path, effects))
        assert set(groups.water.masks) == {"major"}
        assert groups.water.masks["major"].max() > CORE

    def test_the_layers_are_those_paint_pen_returns(self, tmp_path):
        """The groups' layers, joined, are `paint_pen`'s layers, density for density."""
        job = _job(tmp_path)
        groups = pen_groups(job)
        joined = [*groups.water.layers, *groups.road.layers]
        plain = paint_pen(job)
        assert len(joined) == len(plain)
        for (d1, c1, *_), (d2, c2, *_) in zip(joined, plain, strict=True):
            assert d1 is not None
            assert d2 is not None
            assert np.array_equal(d1, d2)
            assert c1.tolist() == c2.tolist()


class TestLayStack:
    """`lay_stack` scales display pixels and takes the hillshade's light."""

    def test_widths_are_scaled_by_the_render_scale(self):
        """A casing of 1 display pixel at scale 3 is a casing of 3 array pixels."""
        rgb = np.full((40, 40, 3), 0.4, F32)
        mask = np.zeros((40, 40), F32)
        mask[20, 10:30] = 1.0
        got = lay_stack(
            rgb, mask, EffectStack(effects=(Casing(width_px=1.0),)), scale=3.0, paper=None
        )
        assert np.array_equal(got, casing(rgb, mask, Casing(width_px=3.0)))

    def test_the_shadow_takes_the_hillshade_azimuth(self):
        """The shadow falls as `DEFAULT_SUN.azimuth` says, and the relief shades with that sun."""
        for fn in (relief.hillshade_png, relief.shade_bands):
            assert inspect.signature(fn).parameters["sun"].default is relief.DEFAULT_SUN
        rgb = np.full((40, 40, 3), 0.9, F32)
        mask = np.zeros((40, 40), F32)
        mask[20, 10:30] = 1.0
        effect = Shadow(offset_px=2.0, blur_px=1.0, strength=0.5)
        got = lay_stack(rgb, mask, EffectStack(effects=(effect,)), scale=1.0, paper=None)
        want = shadow(rgb, mask, effect, azimuth_deg=relief.DEFAULT_SUN.azimuth)
        assert np.array_equal(got, want)

    def test_an_empty_stack_returns_the_array_itself(self):
        """With nothing to lay the colour beneath comes back untouched."""
        rgb = np.full((8, 8, 3), 0.5, F32)
        assert lay_stack(rgb, np.zeros((8, 8), F32), EffectStack(), scale=2.0, paper=None) is rgb


@pytest.mark.parametrize("effect", [Glow(spread_px=1.0, blur_px=1.0, strength=0.5)], ids=["glow"])
def test_a_water_glow_changes_pixels_only_near_the_water(tmp_path, effect):
    """A glow on the major watercourse lifts the wash near the river and nowhere else."""
    on = _job(tmp_path / "b", {"major": EffectStack(effects=(effect,))})
    changed = (_plate(_job(tmp_path / "a")) != _plate(on)).any(axis=2)
    mask = pen_groups(on).water.masks["major"]
    reach = (effect.spread_px + 4 * effect.blur_px) * on.scale + 2.0
    assert changed.any()
    assert not changed[~_ring(mask, reach)].any()
