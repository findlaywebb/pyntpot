"""Tests for one wash: its options, its rims, blooms, separation and fluid modulation."""

import numpy as np
import pytest

from pyntpot.ink.noise import blur, chamfer_distance, smoothstep
from pyntpot.ink.pigment import PIGMENTS, PigmentLayer
from pyntpot.ink.sheet import Sheet, rgb
from pyntpot.ink.style import WashStyle
from pyntpot.ink.wash import WashOptions, flow_edge, fluid_modulate, separated, wash

from support.washes import fluid_fields, two_squares


def density(layer: PigmentLayer) -> np.ndarray:
    """A layer's density, which these tests always give it."""
    assert layer[0] is not None
    return layer[0]


def test_a_wash_given_no_option_is_the_wash_it_always_was():
    """Passing the phase 1 arguments at their inert values changes nothing."""
    sheet, left, _ = two_squares()
    plain = wash(left, sheet, 0.52, 0.20, WashOptions(rim_px=7.0))
    same = wash(
        left,
        sheet,
        0.52,
        0.20,
        WashOptions(rim_px=7.0, wet=None, gran_gamma=0.0, flow=None, blooms=None),
    )
    assert np.array_equal(plain, same)


def test_granulation_settles_in_the_pits_the_dry_brush_breaks_on():
    """Bound to the paper's own height, not to an fbm unrelated to it."""
    sheet = Sheet(200, 300, gran_px=8.0, seed=5, fibre=0.35)
    square_m = np.zeros((200, 300), np.float32)
    square_m[40:160, 60:240] = 1.0
    body = square_m > 0.5
    loose = wash(square_m, sheet, 0.55, 0.22, WashOptions(rim_px=7.0))
    bound = wash(square_m, sheet, 0.55, 0.22, WashOptions(rim_px=7.0, gran_gamma=1.7))

    def follows(d: np.ndarray) -> float:
        a = d[body] - d[body].mean()
        b = sheet.paper[body] - sheet.paper[body].mean()
        return float((a * b).mean() / (a.std() * b.std()))

    # Negative because the pits are where the paper is low and the pigment high.
    assert follows(bound) < follows(loose) - 0.20


def test_two_classes_wet_at_once_bleed_into_each_other_rather_than_butt():
    """A boundary inside the land is not an edge; the outer silhouette still is."""
    sheet, left, right = two_squares()
    union = np.clip(left + right, 0, 1)
    wet = smoothstep(chamfer_distance(union < 0.5) - np.float32(16.0), 16.0)
    assert wet[100, 160] > 0.9, "the seam is inside the wet area"
    assert wet[100, 41] < 0.1, "the outer edge is not"

    def total(wet: np.ndarray | None = None) -> np.ndarray:
        return wash(left, sheet, 0.52, 0.20, WashOptions(rim_px=7.0, wet=wet)) + wash(
            right, sheet, 0.58, 0.26, WashOptions(rim_px=7.0, wet=wet)
        )

    dry = total()
    damp = total(wet)
    seam, band = slice(150, 172), slice(70, 130)

    def step(d: np.ndarray) -> float:
        return float(np.abs(np.diff(d[band, seam], axis=1)).mean())

    assert step(damp) < step(dry) * 0.6
    assert damp[band, seam].max() < dry[band, seam].max() - 0.1
    # The land's own outer edge keeps its rim: the wet area ends before it.
    assert damp[band, 38:48].max() == pytest.approx(dry[band, 38:48].max(), abs=2e-3)


def test_the_flow_rim_is_wider_on_a_bigger_wash():
    """Mask minus blur is one width everywhere; a drying edge is not."""
    sheet = Sheet(260, 400, gran_px=8.0, seed=5)
    depths = {}
    for tag, radius in (("small", 18), ("big", 90)):
        yy, xx = np.ogrid[:260, :400]
        disc = ((yy - 130) ** 2 + (xx - 200) ** 2 < radius * radius).astype(np.float32)
        a = np.clip((blur(disc, 2.4) - 0.5) * 3.2 + 0.5, 0, 1)
        inward = chamfer_distance(~(a > 0.5))
        for name, rim in (
            ("old", np.clip(a - blur(a, 7.0), 0, 1)),
            ("flow", flow_edge(a, sheet, 7.0, 0.125, 0.02, 0.38)),
        ):
            depths[name, tag] = float((rim * inward).sum() / max(rim.sum(), 1e-6))
    grew = depths["flow", "big"] / depths["flow", "small"]
    held = depths["old", "big"] / depths["old", "small"]
    assert grew > held * 1.3
    assert depths["flow", "small"] < depths["old", "small"], "it sits in against the edge"


def test_a_bloom_lifts_the_centre_and_deposits_it_at_the_front():
    """A backrun: lighter inside, a darker crenellated ridge where it stopped."""
    sheet, left, _ = two_squares()
    body = left > 0.5
    core = body & (chamfer_distance(~body) > 12)
    flat = wash(left, sheet, 0.52, 0.20, WashOptions(rim_px=7.0))
    blown = wash(
        left,
        sheet,
        0.52,
        0.20,
        WashOptions(rim_px=7.0, blooms=(np.random.default_rng(3), 3, 0.17, 0.45, 0.45)),
    )
    assert blown[core].std() > flat[core].std() * 1.5
    assert blown[core].min() < flat[core].min() - 0.1, "a lighter centre"
    assert blown[core].max() > flat[core].max() + 0.05, "and a darker ring"
    # Deterministic from the seed it is given, like everything else here.
    again = wash(
        left,
        sheet,
        0.52,
        0.20,
        WashOptions(rim_px=7.0, blooms=(np.random.default_rng(3), 3, 0.17, 0.45, 0.45)),
    )
    assert np.array_equal(blown, again)


def test_a_class_that_is_not_named_stays_the_one_wash_it_was():
    """Only the classes a theme names separate, and only when the flag is on."""
    sheet, left, _ = two_squares(80, 120)
    dens = wash(left, sheet, 0.72, 0.30, WashOptions(rim_px=7.0))
    pig = rgb(PIGMENTS["wood"])
    for style in (WashStyle(), WashStyle(pigment_separation=True)):
        out = separated(dens, "heath", pig, 0.14, sheet, style)
        assert len(out) == 1
        assert out[0][0] is dens


def test_the_heavy_pigment_settles_in_the_tooth_and_the_light_one_floats():
    """Two pigments out of one wash: one in the pits, one over them."""
    sheet, left, _ = two_squares(200, 320)
    dens = wash(left, sheet, 0.72, 0.30, WashOptions(rim_px=7.0))
    style = WashStyle(pigment_separation=True)
    light, heavy = separated(dens, "wood", rgb(PIGMENTS["wood"]), 0.05, sheet, style)
    body = left > 0.5

    def follows(d: np.ndarray) -> float:
        a = d[body] - d[body].mean()
        b = sheet.paper[body] - sheet.paper[body].mean()
        return float((a * b).mean() / (a.std() * b.std()))

    # Negative because the pits are where the paper is low and the pigment high.
    light_d, heavy_d = density(light), density(heavy)
    assert follows(heavy_d) < follows(light_d) - 0.5
    # The wash is redistributed, not added to: the two together are what one was.
    assert (light_d + heavy_d)[body].mean() == pytest.approx(dens[body].mean(), rel=0.06)
    assert heavy[1].tolist() != light[1].tolist(), "and it is a second pigment"
    assert light_d[body].std() < heavy_d[body].std()


def test_the_fluid_pass_modulates_the_washes_and_never_becomes_them():
    """The rule the pass is held to: a failure degrades to today's plate."""
    wet, _, _ = fluid_fields()
    sheet = Sheet(96, 128, gran_px=8.0, seed=5)
    style = WashStyle(fluid_pass=True)
    before = wash(wet, sheet, 0.55, 0.22, WashOptions(rim_px=7.0))
    layers: list[PigmentLayer] = [(before.copy(), rgb(PIGMENTS["wood"]), 0.05)]
    after = density(fluid_modulate(layers, wet, sheet, style)[0])
    body = wet > 0.5
    assert after.min() >= 0.0 and after.max() <= 1.0
    a = after[body] - after[body].mean()
    b = before[body] - before[body].mean()
    assert float((a * b).mean() / (a.std() * b.std())) > 0.8, "still the same wash"
    assert not np.allclose(after[body], before[body]), "but it has been worked"
    # Dry paper is dry paper: away from the wet area nothing is touched at all.
    dry = chamfer_distance(body) > 8
    assert np.array_equal(after[dry], before[dry])


def test_a_sheet_with_nothing_wet_on_it_comes_back_untouched():
    """A pass that has nothing to do hands the plate straight back."""
    sheet = Sheet(64, 64, gran_px=8.0, seed=5)
    layers: list[PigmentLayer] = [(np.zeros((64, 64), np.float32), rgb(PIGMENTS["wood"]))]
    same = fluid_modulate(layers, np.zeros((64, 64), np.float32), sheet, WashStyle(fluid_pass=True))
    assert same is layers
