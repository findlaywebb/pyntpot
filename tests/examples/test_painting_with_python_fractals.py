"""The fern, the tree and the fern family scripts run offline, paint at a small size and keep to their caps."""

import runpy
from typing import Any

import numpy as np
import pytest
from PIL import Image

from support.examples import EXAMPLES_DIR, run_example

#: The width the tests paint at, in pixels.
SMALL = 96


def _namespace(stem: str) -> dict[str, Any]:
    """Load `examples/<stem>.py` without running its main block and return its names."""
    return runpy.run_path(str(EXAMPLES_DIR / f"{stem}.py"), run_name=f"example_{stem}")


CASES: dict[str, tuple[str, dict[str, object]]] = {
    "fern": ("fern", {}),
    "tree": ("trees", {"figure": "tree"}),
    "tree-family": ("trees", {"figure": "family"}),
    "fern-family": ("fern_family", {}),
}


@pytest.mark.parametrize("case", list(CASES), ids=list(CASES))
def test_the_script_writes_one_image_that_is_not_flat(case, tmp_path):
    """The script writes one PNG of the given small width that is not one flat colour."""
    stem, options = CASES[case]
    path = run_example(stem, tmp_path, size=SMALL, **options)
    assert list(tmp_path.iterdir()) == [path]
    with Image.open(path) as image:
        assert image.format == "PNG"
        assert image.mode == "RGB"
        assert image.width == SMALL
        pixels = np.asarray(image)
    low, high = pixels.min(axis=(0, 1)), pixels.max(axis=(0, 1))
    assert (low != high).all(), (low, high)


class TestFern:
    """The Barnsley fern's points and marks."""

    def test_the_points_are_capped_and_stay_inside_the_fern(self):
        """The iterated points number at most 200 000 and lie in the fern's known extent."""
        ns = _namespace("fern")
        points = ns["fern_points"](50_000, 3)
        assert 0 < len(points) <= 200_000
        assert ns["MAX_POINTS"] <= 200_000
        assert ns["MAX_DABS"] <= 400
        assert points[:, 0].min() >= -2.2 and points[:, 0].max() <= 2.7
        assert points[:, 1].min() >= 0.0 and points[:, 1].max() <= 10.0

    def test_the_same_seed_gives_the_same_points(self):
        """Two runs with one seed iterate the same points."""
        fern_points = _namespace("fern")["fern_points"]
        assert np.array_equal(fern_points(2_000, 5), fern_points(2_000, 5))

    def test_the_four_maps_have_probabilities_that_sum_to_one(self):
        """The four affine maps carry Barnsley's probabilities, 1, 85, 7 and 7 per cent."""
        probs = _namespace("fern")["PROBABILITIES"]
        assert tuple(probs) == (0.01, 0.85, 0.07, 0.07)
        assert sum(probs) == pytest.approx(1.0)


class TestFernFamily:
    """The nine perturbed ferns' maps."""

    def test_the_perturbed_maps_keep_the_stem_and_stay_near_barnsleys(self):
        """A perturbed set keeps the stem map and moves every other entry by a few per cent at most."""
        ns = _namespace("fern_family")
        base = ns["MAPS"]
        for seed in range(20):
            maps = ns["perturbed"](base, np.random.default_rng(seed))
            assert np.array_equal(maps[0], base[0])
            assert np.abs(maps[1, :4] - base[1, :4]).max() < 0.08
            assert np.abs(maps[2:, :4] - base[2:, :4]).max() <= 0.06 * np.abs(base[2:, :4]).max()

    def test_two_seeds_give_two_different_ferns(self):
        """Two seeds perturb the maps differently, so the family has no repeated fern."""
        ns = _namespace("fern_family")
        a = ns["perturbed"](ns["MAPS"], np.random.default_rng(1))
        b = ns["perturbed"](ns["MAPS"], np.random.default_rng(2))
        assert not np.array_equal(a, b)

    def test_the_points_stay_inside_the_fitted_cell(self):
        """A fern's points, fitted to a cell, lie inside it."""
        ns = _namespace("fern_family")
        rng = np.random.default_rng(3)
        points = ns["fern_points"](ns["perturbed"](ns["MAPS"], rng), 3_000, rng)
        pixels = ns["_fit"](points, 120, 160)
        assert pixels[:, 0].min() >= 0 and pixels[:, 0].max() <= 120
        assert pixels[:, 1].min() >= 0 and pixels[:, 1].max() <= 160


class TestTrees:
    """The recursive tree's limbs and the family's perturbation."""

    def test_a_child_starts_as_wide_as_its_parent_ends_or_a_little_less(self):
        """Every limb after the trunk is no wider at its foot than the widest limb's end above it, so widths taper by depth."""
        ns = _namespace("trees")
        limbs = ns["grow"](
            np.array([50.0, 150.0]), 40.0, 8.0, ns["Shape"](), np.random.default_rng(2)
        )
        assert limbs[0].depth == 0 and limbs[0].w_start == 8.0
        by_depth = {}
        for limb in limbs:
            by_depth.setdefault(limb.depth, []).append(limb)
        for depth in range(1, ns["DEPTH"] + 1):
            widest_parent_end = max(limb.w_end for limb in by_depth[depth - 1])
            assert max(limb.w_start for limb in by_depth[depth]) <= widest_parent_end + 1e-9

    def test_the_tree_stops_at_its_depth(self):
        """No limb is more than `DEPTH` splits from the trunk, and there are limbs at every depth to it."""
        ns = _namespace("trees")
        limbs = ns["grow"](
            np.array([50.0, 150.0]), 40.0, 8.0, ns["Shape"](), np.random.default_rng(5)
        )
        assert {limb.depth for limb in limbs} == set(range(ns["DEPTH"] + 1))

    def test_the_same_seed_grows_the_same_tree(self):
        """Two runs with one seed grow the same limbs."""
        ns = _namespace("trees")
        runs = [
            ns["grow"](np.array([50.0, 150.0]), 40.0, 8.0, ns["Shape"](), np.random.default_rng(9))
            for _ in range(2)
        ]
        assert all(np.array_equal(a.path, b.path) for a, b in zip(*runs, strict=True))

    def test_a_perturbed_shape_stays_close_to_its_species(self):
        """A seed moves the spread, the ratio and the droop by a few per cent, never to another kind of tree."""
        ns = _namespace("trees")
        base = ns["Shape"]()
        for seed in range(30):
            shape = ns["perturbed"](base, np.random.default_rng(seed))
            assert 0.8 * base.spread <= shape.spread <= 1.25 * base.spread
            assert 0.94 * base.ratio <= shape.ratio <= 1.05 * base.ratio
            assert 0.4 * base.droop <= shape.droop <= 1.7 * base.droop

    def test_fitted_limbs_stand_inside_the_cell(self):
        """A fitted tree has every point inside its cell and its foot near the cell's bottom."""
        ns = _namespace("trees")
        limbs = ns["grow"](np.array([0.0, 0.0]), 40.0, 8.0, ns["Shape"](), np.random.default_rng(4))
        fitted = ns["fitted"](limbs, (160, 120))
        pts = np.vstack([limb.path for limb in fitted])
        assert pts[:, 0].min() >= 0 and pts[:, 0].max() <= 120
        assert pts[:, 1].min() >= 0 and pts[:, 1].max() <= 160
        assert fitted[0].path[0][1] > 0.9 * 160

    def test_an_unknown_figure_is_refused(self, tmp_path):
        """`trees` raises `ValueError` for a figure it does not paint."""
        with pytest.raises(ValueError, match="figure"):
            run_example("trees", tmp_path, size=SMALL, figure="orchard")
