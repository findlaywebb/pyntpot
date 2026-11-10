"""The essay figures and the cased stroke run offline, and their cells say what the essay says."""

import numpy as np
import pytest
from PIL import Image

from support import REPO_ROOT
from support.examples import load_example, run_example

REASONS = ("glaze-or-rgb", "draw-order")
CELLS = ("plain", "cased", "glow", "shadow")


def _reasons():
    """Return the essay figures' script namespace."""
    return load_example("line_effect_reasons", "example_line_effect_reasons")


def _stroke():
    """Return the cased stroke script's namespace."""
    return load_example("cased_stroke", "example_cased_stroke")


class TestEssayFigures:
    """The essay's two figures and the tutorial's stroke each write one lossless PNG."""

    @pytest.mark.parametrize("figure", REASONS, ids=REASONS)
    def test_a_figure_is_one_image_that_is_not_flat(self, figure, tmp_path):
        """Each essay figure writes one RGB PNG into the directory that is not one flat colour."""
        path = run_example("line_effect_reasons", tmp_path, figure=figure)
        assert list(tmp_path.iterdir()) == [path]
        with Image.open(path) as image:
            assert image.mode == "RGB"
            pixels = np.asarray(image)
        assert (pixels.min(axis=(0, 1)) != pixels.max(axis=(0, 1))).all()

    def test_an_unknown_essay_figure_is_refused(self, tmp_path):
        """A figure the essay does not have is a ValueError, not a blank image."""
        with pytest.raises(ValueError, match="no such figure"):
            run_example("line_effect_reasons", tmp_path, figure="nonesuch")

    def test_the_cased_stroke_is_one_image_that_is_not_flat(self, tmp_path):
        """The tutorial's stroke writes one RGB PNG into the directory that is not one flat colour."""
        path = run_example("cased_stroke", tmp_path)
        assert list(tmp_path.iterdir()) == [path]
        with Image.open(path) as image:
            assert image.mode == "RGB"
            pixels = np.asarray(image)
        assert (pixels.min(axis=(0, 1)) != pixels.max(axis=(0, 1))).all()

    def test_an_unknown_cell_is_refused(self):
        """A cell the cased stroke does not have is a ValueError."""
        with pytest.raises(ValueError, match="no such cell"):
            _stroke()["paint_cell"]("nonesuch")


class TestGlazeOrRgb:
    """A glazed ring barely shows over dark wood, and the same ring laid on RGB does."""

    @pytest.mark.parametrize("column", [0, 1], ids=["casing", "glow"])
    def test_the_rgb_cell_is_lighter_than_the_glazed_cell(self, column):
        """The RGB cell of each effect is lighter on average than its glazed cell, by a margin."""
        paint_cell = _reasons()["paint_cell"]
        glazed = paint_cell("glaze-or-rgb", 0, column)
        laid = paint_cell("glaze-or-rgb", 1, column)
        assert laid.mean() - glazed.mean() > 0.01

    @pytest.mark.parametrize("column", [0, 1], ids=["casing", "glow"])
    def test_the_rgb_ring_is_clearly_lighter_somewhere(self, column):
        """Somewhere in the ring the RGB cell is lighter than the glazed cell by more than a tenth."""
        paint_cell = _reasons()["paint_cell"]
        glazed = paint_cell("glaze-or-rgb", 0, column)
        laid = paint_cell("glaze-or-rgb", 1, column)
        assert (laid - glazed).max() > 0.1


class TestDrawOrder:
    """Cased in turn, a second road's casing cuts the first; with the casings first it does not."""

    def test_the_cells_differ_only_where_a_casing_lightens_a_line(self):
        """Each-stroke-cased is at least as light as casings-first everywhere, and clearly lighter at the fork."""
        paint_cell = _reasons()["paint_cell"]
        each = paint_cell("draw-order", 0, 0)
        first = paint_cell("draw-order", 0, 1)
        assert each.shape == first.shape
        assert (each - first).min() >= -1e-6
        assert (each - first).max() > 0.1


class TestCasedStroke:
    """Each effect moves the stroke's neighbours the way its name says, and the plain cell is the stroke."""

    @pytest.mark.parametrize("name", ["cased", "glow"], ids=["cased", "glow"])
    def test_casing_and_glow_only_lighten(self, name):
        """A casing and a glow are at least as light as the plain cell at every pixel, within float rounding."""
        paint_cell = _stroke()["paint_cell"]
        assert (paint_cell(name) - paint_cell("plain")).min() >= -1e-6

    def test_a_shadow_only_darkens(self):
        """The shadow cell is at least as dark as the plain cell at every pixel, within float rounding."""
        paint_cell = _stroke()["paint_cell"]
        assert (paint_cell("shadow") - paint_cell("plain")).max() <= 1e-6

    @pytest.mark.parametrize("name", CELLS[1:], ids=CELLS[1:])
    def test_an_effect_changes_the_cell(self, name):
        """Each effect's cell is not the plain cell."""
        paint_cell = _stroke()["paint_cell"]
        assert paint_cell(name).tobytes() != paint_cell("plain").tobytes()


class TestEssayHeldValues:
    """The essay scripts hold their own literals and pass no threshold."""

    @pytest.mark.parametrize(
        "stem", ["line_effect_reasons", "cased_stroke"], ids=["reasons", "stroke"]
    )
    def test_the_script_names_no_preset_and_passes_no_threshold(self, stem):
        """The script reads no preset table and no private range, and passes no threshold."""
        source = (REPO_ROOT / "examples" / f"{stem}.py").read_text()
        code = source.split('"""', 2)[2]
        for word in ("BUILT_IN_PRESETS", "LINE_THRESHOLD", "EFFECT_RANGES", "threshold="):
            assert word not in code, word
