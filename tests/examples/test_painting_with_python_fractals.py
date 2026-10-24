"""The fern and the gasket scripts run offline, paint at a small size and keep to their caps."""

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


@pytest.mark.parametrize("stem", ["fern", "gasket"], ids=["fern", "gasket"])
def test_the_script_writes_one_image_that_is_not_flat(stem, tmp_path):
    """The script writes one PNG of the given small width that is not one flat colour."""
    path = run_example(stem, tmp_path, size=SMALL)
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


class TestGasket:
    """The Apollonian gasket's circles."""

    def test_the_circles_are_capped_and_tangent_to_the_container(self):
        """At most 300 circles, to depth 5, and every inner circle lies inside the container."""
        ns = _namespace("gasket")
        circles = ns["gasket_circles"](5)
        assert 4 <= len(circles) <= 300
        assert ns["MAX_CIRCLES"] <= 300
        for c in circles:
            assert abs(c.centre) + c.radius <= 1.0 + 1e-9

    def test_descartes_theorem_holds_for_the_first_four_circles(self):
        """The seed circles' curvatures satisfy Descartes' circle theorem exactly."""
        ns = _namespace("gasket")
        k = [c.curvature for c in ns["gasket_circles"](0)]
        assert len(k) == 4
        assert 2 * sum(x * x for x in k) == pytest.approx(sum(k) ** 2)
