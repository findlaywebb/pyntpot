"""Properties of the line effect primitives: the identities and the three invariants of ADR 0070."""

import numpy as np
from hypothesis import given
from hypothesis import strategies as st
from hypothesis.extra import numpy as hnp

from pyntpot.ink.effect_casing import casing
from pyntpot.ink.effect_glow import glow
from pyntpot.ink.effect_pen_casing import pen_casing
from pyntpot.ink.effect_shadow import shadow
from pyntpot.ink.effect_types import EFFECT_RANGES, Casing, Glow, PenCasing, Shadow
from pyntpot.ink.noise import chamfer_distance

from support.properties import UNTIMED

UNIT32 = st.floats(0, 1, width=32)
THRESHOLD = st.floats(0.01, 1)
SIDE = st.integers(8, 40)


def _ranged(name: str) -> st.SearchStrategy[float]:
    """Finite floats over the `EFFECT_RANGES` entry of `name`."""
    lo, hi = EFFECT_RANGES[name]
    return st.floats(lo, hi, allow_nan=False, allow_infinity=False)


COLOUR = st.integers(0, 0xFFFFFF).map(lambda n: f"#{n:06x}")
CASINGS = st.builds(
    Casing, width_px=_ranged("width_px"), strength=_ranged("strength"), colour=COLOUR
)
GLOWS = st.builds(
    Glow, spread_px=_ranged("spread_px"), blur_px=_ranged("blur_px"), strength=_ranged("strength")
)
SHADOWS = st.builds(
    Shadow,
    offset_px=_ranged("offset_px"),
    blur_px=_ranged("blur_px"),
    strength=_ranged("strength"),
    colour=COLOUR,
)
PEN_CASINGS = st.builds(PenCasing, width_px=_ranged("width_px"), edge_px=_ranged("edge_px"))


@st.composite
def scenes(draw: st.DrawFn) -> tuple[np.ndarray, np.ndarray, np.ndarray | None]:
    """A float32 wash, a mask and a paper (`None` or a plate), all in 0 to 1."""
    h, w = draw(SIDE), draw(SIDE)
    rgb = draw(hnp.arrays(np.float32, (h, w, 3), elements=UNIT32))
    mask = draw(hnp.arrays(np.float32, (h, w), elements=UNIT32))
    paper = draw(st.none() | hnp.arrays(np.float32, (h, w, 3), elements=UNIT32))
    return rgb, mask, paper


def _bits(a: np.ndarray) -> np.ndarray:
    """The float32 array as its raw 32-bit words."""
    return a.view(np.uint32)


class TestCasing:
    """The casing identity."""

    @UNTIMED
    @given(scene=scenes(), zero=st.sampled_from([0.0, -0.0]), threshold=THRESHOLD)
    def test_width_zero_is_the_identity_bit_for_bit(
        self, scene: tuple[np.ndarray, np.ndarray, np.ndarray | None], zero: float, threshold: float
    ) -> None:
        """A casing of width 0 or -0 returns the wash bit for bit."""
        rgb, mask, paper = scene
        out = casing(rgb, mask, Casing(width_px=zero), threshold=threshold, paper=paper)
        assert np.array_equal(_bits(out), _bits(rgb))

    @UNTIMED
    @given(scene=scenes(), effect=CASINGS, threshold=THRESHOLD)
    def test_the_output_is_a_float32_plate_in_range(
        self,
        scene: tuple[np.ndarray, np.ndarray, np.ndarray | None],
        effect: Casing,
        threshold: float,
    ) -> None:
        """Any casing gives float32 values in 0 to 1."""
        rgb, mask, paper = scene
        out = casing(rgb, mask, effect, threshold=threshold, paper=paper)
        assert out.dtype == np.float32
        assert out.shape == rgb.shape
        assert out.min() >= 0.0
        assert out.max() <= 1.0


class TestGlow:
    """The glow never darkens."""

    @UNTIMED
    @given(scene=scenes(), effect=GLOWS, threshold=THRESHOLD)
    def test_no_pixel_gets_darker(
        self,
        scene: tuple[np.ndarray, np.ndarray, np.ndarray | None],
        effect: Glow,
        threshold: float,
    ) -> None:
        """For any spread, blur, strength and paper, every channel is at least what it was."""
        rgb, mask, paper = scene
        out = glow(rgb, mask, effect, threshold=threshold, paper=paper)
        assert out.dtype == np.float32
        assert (out >= rgb).all()
        assert out.max() <= 1.0

    @UNTIMED
    @given(scene=scenes(), threshold=THRESHOLD)
    def test_strength_zero_is_the_identity(
        self, scene: tuple[np.ndarray, np.ndarray, np.ndarray | None], threshold: float
    ) -> None:
        """A glow at strength 0 returns the wash bit for bit."""
        rgb, mask, paper = scene
        out = glow(rgb, mask, Glow(spread_px=5.0, blur_px=3.0), threshold=threshold, paper=paper)
        assert np.array_equal(_bits(out), _bits(rgb))


class TestShadow:
    """The shadow never paints over its casting line."""

    @UNTIMED
    @given(
        scene=scenes(),
        effect=SHADOWS,
        azimuth=st.floats(-720, 720, allow_nan=False, allow_infinity=False),
        threshold=THRESHOLD,
    )
    def test_the_line_is_untouched_and_nothing_lightens(
        self,
        scene: tuple[np.ndarray, np.ndarray, np.ndarray | None],
        effect: Shadow,
        azimuth: float,
        threshold: float,
    ) -> None:
        """Where the mask is at the threshold the output equals the wash bit for bit, and none is lighter."""
        rgb, mask, _ = scene
        out = shadow(rgb, mask, effect, azimuth_deg=azimuth, threshold=threshold)
        on_line = mask >= np.float32(threshold)
        assert out.dtype == np.float32
        assert np.array_equal(_bits(out)[on_line], _bits(rgb)[on_line])
        assert (out <= rgb).all()


class TestPenCasing:
    """The pen casing reserve."""

    @UNTIMED
    @given(scene=scenes(), edge=_ranged("edge_px"), threshold=THRESHOLD)
    def test_width_zero_is_the_identity_with_no_edges(
        self,
        scene: tuple[np.ndarray, np.ndarray, np.ndarray | None],
        edge: float,
        threshold: float,
    ) -> None:
        """Width 0 returns the wash bit for bit and zero edges."""
        rgb, mask, paper = scene
        out, edges = pen_casing(
            rgb, mask, PenCasing(edge_px=edge), threshold=threshold, paper=paper
        )
        assert np.array_equal(_bits(out), _bits(rgb))
        assert edges.shape == mask.shape
        assert not edges.any()

    @UNTIMED
    @given(scene=scenes(), effect=PEN_CASINGS, threshold=THRESHOLD)
    def test_the_reserve_is_paper_outside_the_edge_band(
        self,
        scene: tuple[np.ndarray, np.ndarray, np.ndarray | None],
        effect: PenCasing,
        threshold: float,
    ) -> None:
        """Inside the reserve the output is the paper; the edge band lies outside it, 0 or 1."""
        rgb, mask, paper = scene
        out, edges = pen_casing(rgb, mask, effect, threshold=threshold, paper=paper)
        if effect.width_px == 0:
            return
        ground = np.ones_like(rgb) if paper is None else paper
        reserve = chamfer_distance(mask >= threshold) <= effect.width_px
        assert (out[reserve] == ground[reserve]).all()
        assert not edges[reserve].any()
        assert set(np.unique(edges)) <= {0.0, 1.0}
        assert (out[~reserve] == rgb[~reserve]).all()
