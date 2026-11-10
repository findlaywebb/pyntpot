"""Properties of the reserve and the casing union: identities, the core, the pool and the union."""

import numpy as np
from hypothesis import given
from hypothesis import strategies as st
from hypothesis.extra import numpy as hnp

from pyntpot.ink.effect_casing import casing
from pyntpot.ink.effect_distance import contour_distance, ring_coverage
from pyntpot.ink.effect_reserve import reserve
from pyntpot.ink.effect_types import EFFECT_RANGES, Casing, Reserve
from pyntpot.ink.effect_union import casing_union

from support.properties import UNTIMED

UNIT32 = st.floats(0, 1, width=32)
THRESHOLD = st.floats(0.01, 1)
SIDE = st.integers(8, 32)
_WIDTH = st.floats(*EFFECT_RANGES["width_px"], allow_nan=False, allow_infinity=False)
_POOL = st.floats(*EFFECT_RANGES["pool"], allow_nan=False, allow_infinity=False)
RESERVES = st.builds(Reserve, width_px=_WIDTH, pool=_POOL)
COLOUR = st.integers(0, 0xFFFFFF).map(lambda n: f"#{n:06x}")
CASINGS = st.builds(Casing, width_px=_WIDTH, colour=COLOUR)

Scene = tuple[np.ndarray, np.ndarray, np.ndarray | None]


@st.composite
def scenes(draw: st.DrawFn) -> Scene:
    """A float32 wash, a float32 mask and a paper (`None` or a plate)."""
    h, w = draw(SIDE), draw(SIDE)
    rgb = draw(hnp.arrays(np.float32, (h, w, 3), elements=UNIT32))
    mask = draw(hnp.arrays(np.float32, (h, w), elements=UNIT32))
    paper = draw(st.none() | hnp.arrays(np.float32, (h, w, 3), elements=UNIT32))
    return rgb, mask, paper


def _second_mask(mask: np.ndarray) -> np.ndarray:
    """A second float32 mask: the first, flipped left to right."""
    return np.ascontiguousarray(mask[:, ::-1])


def _bits(a: np.ndarray) -> np.ndarray:
    """The float32 array as its raw words."""
    return a.view(np.uint32)


class TestReserve:
    """A reserve lays the paper, and its pool only deepens."""

    @UNTIMED
    @given(scene=scenes(), zero=st.sampled_from([0.0, -0.0]), pool=_POOL, threshold=THRESHOLD)
    def test_width_zero_is_the_identity(
        self, scene: Scene, zero: float, pool: float, threshold: float
    ) -> None:
        """A reserve of width 0 returns the wash itself."""
        rgb, mask, paper = scene
        out = reserve(
            rgb, mask, Reserve(width_px=zero, pool=pool), threshold=threshold, paper=paper
        )
        assert out is rgb

    @UNTIMED
    @given(scene=scenes(), effect=RESERVES, threshold=THRESHOLD)
    def test_the_core_is_untouched(self, scene: Scene, effect: Reserve, threshold: float) -> None:
        """Wherever the mask is at the threshold, the output equals the wash bit for bit."""
        rgb, mask, paper = scene
        out = reserve(rgb, mask, effect, threshold=threshold, paper=paper)
        core = mask >= np.float32(threshold)
        assert np.array_equal(_bits(out)[core], _bits(rgb)[core])

    @UNTIMED
    @given(scene=scenes(), effect=RESERVES, threshold=THRESHOLD)
    def test_a_whole_ring_is_the_paper_exactly(
        self, scene: Scene, effect: Reserve, threshold: float
    ) -> None:
        """Where the ring's coverage is 1, the output is the paper plate bit for bit, pool or not."""
        rgb, mask, paper = scene
        out = reserve(rgb, mask, effect, threshold=threshold, paper=paper)
        if effect.width_px == 0 or not (mask >= np.float32(threshold)).any():
            return
        d = contour_distance(mask, threshold=threshold, radius=effect.width_px + 2)
        whole = (ring_coverage(d, effect.width_px) == 1.0) & (mask < np.float32(threshold))
        ground = np.ones_like(rgb) if paper is None else paper
        assert np.array_equal(_bits(out)[whole], _bits(ground)[whole])

    @UNTIMED
    @given(scene=scenes(), effect=RESERVES, threshold=THRESHOLD)
    def test_the_pool_never_lightens(self, scene: Scene, effect: Reserve, threshold: float) -> None:
        """The output is at most the zero-pool output, channel by channel."""
        rgb, mask, paper = scene
        plain = reserve(
            rgb, mask, Reserve(width_px=effect.width_px), threshold=threshold, paper=paper
        )
        pooled = reserve(rgb, mask, effect, threshold=threshold, paper=paper)
        assert (pooled <= plain).all()

    @UNTIMED
    @given(scene=scenes(), effect=RESERVES, threshold=THRESHOLD)
    def test_the_pool_never_darkens_bare_paper(
        self, scene: Scene, effect: Reserve, threshold: float
    ) -> None:
        """Where the wash is the ground, the output is the ground for any pool."""
        rgb, mask, paper = scene
        ground = np.ones_like(rgb) if paper is None else paper
        out = reserve(ground.copy(), mask, effect, threshold=threshold, paper=paper)
        assert np.array_equal(_bits(out), _bits(ground))


class TestUnion:
    """A union's ring stays outside every member and agrees with a single ring."""

    @UNTIMED
    @given(scene=scenes(), a=CASINGS, b=CASINGS, threshold=THRESHOLD)
    def test_casing_union_core_and_zero(
        self, scene: Scene, a: Casing, b: Casing, threshold: float
    ) -> None:
        """No pixel under any member's mask changes; members all of width 0 return the wash."""
        rgb, mask, paper = scene
        other = _second_mask(mask)
        one = Casing(width_px=a.width_px, colour=a.colour)
        two = Casing(width_px=b.width_px, colour=a.colour)
        out = casing_union(rgb, [(mask, one), (other, two)], threshold=threshold, paper=paper)
        t = np.float32(threshold)
        inside = (mask >= t) | (other >= t)
        assert np.array_equal(_bits(out)[inside], _bits(rgb)[inside])
        off = Casing(colour=a.colour)
        assert (
            casing_union(rgb, [(mask, off), (other, off)], threshold=threshold, paper=paper) is rgb
        )

    @UNTIMED
    @given(scene=scenes(), a=RESERVES, b=_WIDTH, threshold=THRESHOLD)
    def test_reserve_union_core(self, scene: Scene, a: Reserve, b: float, threshold: float) -> None:
        """No pixel under any reserve member's mask changes."""
        rgb, mask, paper = scene
        other = _second_mask(mask)
        out = casing_union(
            rgb,
            [(mask, a), (other, Reserve(width_px=b, pool=a.pool))],
            threshold=threshold,
            paper=paper,
        )
        t = np.float32(threshold)
        inside = (mask >= t) | (other >= t)
        assert np.array_equal(_bits(out)[inside], _bits(rgb)[inside])

    @UNTIMED
    @given(scene=scenes(), c=CASINGS, r=RESERVES, threshold=THRESHOLD)
    def test_a_union_of_one_is_the_own_ring(
        self, scene: Scene, c: Casing, r: Reserve, threshold: float
    ) -> None:
        """A union of one casing, or one reserve, equals the primitive bit for bit."""
        rgb, mask, paper = scene
        got_c = casing_union(rgb, [(mask, c)], threshold=threshold, paper=paper)
        assert np.array_equal(
            _bits(got_c), _bits(casing(rgb, mask, c, threshold=threshold, paper=paper))
        )
        got_r = casing_union(rgb, [(mask, r)], threshold=threshold, paper=paper)
        assert np.array_equal(
            _bits(got_r), _bits(reserve(rgb, mask, r, threshold=threshold, paper=paper))
        )
