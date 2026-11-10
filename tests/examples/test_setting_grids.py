"""The setting grids run offline, and every swept setting changes the picture it sweeps."""

from itertools import pairwise

import numpy as np
import pytest
from golden.make_docs_images import fixture_options
from PIL import Image

from pyntpot.ink import BrushStyle, brush_from_id

from support.examples import load_example, run_example

FIGURES = ("pool", "granulation", "dryness")
#: How many columns and rows each figure sweeps, from the script's own tuples.
SHAPES = {"pool": (4, 2), "granulation": (4, 3), "dryness": (4, 3)}
#: The least mean difference between neighbouring cells that a painter can see, in 0 to 1.
VISIBLE = 0.002
#: The least mean CIE76 difference between neighbouring relief cells that reads by eye.
RELIEF_DELTA_E = 3.0


def _lab(srgb: np.ndarray) -> np.ndarray:
    """Convert an sRGB array of 0 to 1 to CIE L*a*b* (D65)."""
    linear = np.where(srgb > 0.04045, ((srgb + 0.055) / 1.055) ** 2.4, srgb / 12.92)
    to_xyz = np.array(
        [
            [0.4124564, 0.3575761, 0.1804375],
            [0.2126729, 0.7151522, 0.0721750],
            [0.0193339, 0.1191920, 0.9503041],
        ]
    )
    xyz = (linear @ to_xyz.T) / np.array([0.95047, 1.0, 1.08883])
    f = np.where(xyz > 216 / 24389, np.cbrt(xyz), (24389 / 27 * xyz + 16) / 116)
    return np.stack(
        [116 * f[..., 1] - 16, 500 * (f[..., 0] - f[..., 1]), 200 * (f[..., 1] - f[..., 2])], -1
    )


def _grids():
    """Return the setting grids script's namespace."""
    return load_example("setting_grids", "example_setting_grids")


class TestFigures:
    """Each figure writes one lossless PNG, and a figure the script does not have is refused."""

    @pytest.mark.parametrize("figure", FIGURES, ids=FIGURES)
    def test_a_figure_is_one_image_that_is_not_flat(self, figure, tmp_path):
        """Each figure writes one RGB PNG into the directory that is not one flat colour."""
        path = run_example("setting_grids", tmp_path, figure=figure)
        assert list(tmp_path.iterdir()) == [path]
        with Image.open(path) as image:
            assert image.mode == "RGB"
            pixels = np.asarray(image)
        assert (pixels.min(axis=(0, 1)) != pixels.max(axis=(0, 1))).all()

    def test_an_unknown_figure_is_refused(self, tmp_path):
        """A figure the grids do not have is a ValueError, not a blank image."""
        with pytest.raises(ValueError, match="no such figure"):
            run_example("setting_grids", tmp_path, figure="nonesuch")

    @pytest.mark.parametrize("figure", FIGURES, ids=FIGURES)
    def test_each_figure_sweeps_as_many_cells_as_it_letters(self, figure):
        """The names the figure letters are as many as the cells it paints, across and down."""
        made = _grids()["layout"](figure)
        assert (len(made.columns), len(made.rows)) == SHAPES[figure]


class TestEverySettingShows:
    """No neighbouring cells of a sweep are alike: each step of each swept setting is visible."""

    @pytest.mark.parametrize("figure", FIGURES, ids=FIGURES)
    def test_neighbouring_columns_differ_visibly(self, figure):
        """Each cell differs from the one beside it by more than a painter could miss."""
        paint_cell = _grids()["paint_cell"]
        cols, rows = SHAPES[figure]
        for row in range(rows):
            for col in range(cols - 1):
                left, right = paint_cell(figure, row, col), paint_cell(figure, row, col + 1)
                assert np.abs(left - right).mean() > VISIBLE, (figure, row, col)

    @pytest.mark.parametrize("figure", FIGURES, ids=FIGURES)
    def test_neighbouring_rows_differ_visibly(self, figure):
        """Each cell differs from the one below it by more than a painter could miss."""
        paint_cell = _grids()["paint_cell"]
        cols, rows = SHAPES[figure]
        for col in range(cols):
            for row in range(rows - 1):
                above, below = paint_cell(figure, row, col), paint_cell(figure, row + 1, col)
                assert np.abs(above - below).mean() > VISIBLE / 4, (figure, row, col)


class TestDryness:
    """The dryness grid sets its treatment through `override="major"`, which `brush_from_id` reads."""

    def test_the_override_key_reaches_the_brush(self):
        """With `override="major"` the swept dryness is the brush's; without it the id's own prefix is read."""
        style = BrushStyle(brush_overrides={"major": {"dry": 0.9}})
        swept, _ = brush_from_id("MAJ2-c", 12.0, 1.0, style, override="major")
        unread, _ = brush_from_id("MAJ2-c", 12.0, 1.0, style)
        assert swept.dry == 0.9
        assert unread.dry != 0.9

    def test_the_grid_sweeps_the_dryness_the_pages_letter(self):
        """The script reads the `major` override and sweeps the four dryness values the page letters."""
        script = _grids()
        assert script["OVERRIDE"] == "major"
        assert script["DRYNESS"] == (0.1, 0.4, 0.7, 0.9)


class TestReliefGrid:
    """The relief grid paints the Ambleside fixture at four strengths from a copy of its cache."""

    @pytest.mark.golden
    def test_the_grid_is_one_image_that_is_not_flat(self, tmp_path):
        """The figure writes only its RGB PNG into the output directory, and it is not one flat colour."""
        options = fixture_options("ambleside", tmp_path / "cache")
        path = run_example("relief_grid", tmp_path / "out", **options)

        assert list(path.parent.iterdir()) == [path]
        with Image.open(path) as image:
            assert image.mode == "RGB"
            pixels = np.asarray(image)
        assert (pixels.min(axis=(0, 1)) != pixels.max(axis=(0, 1))).all()

    @pytest.mark.golden
    def test_neighbouring_cells_differ_visibly(self, tmp_path):
        """Each relief cell differs from the one beside it by at least 3 mean CIE76 delta E over the window."""
        script = load_example("relief_grid", "example_relief_grid")
        options = fixture_options("ambleside", tmp_path / "cache")
        strengths = script["STRENGTHS"]
        cell_w = (
            script["GRID_W"] - script["LEFT"] - script["PAD"] - script["GAP"] * (len(strengths) - 1)
        ) // len(strengths)
        cells = script["paint_cells"](cell_w=cell_w, **options)
        labs = [_lab(np.asarray(cell.convert("RGB"), np.float64) / 255) for cell in cells]
        for strength, (left, right) in zip(strengths[1:], pairwise(labs), strict=True):
            delta_e = np.sqrt(((left - right) ** 2).sum(axis=-1)).mean()
            assert delta_e >= RELIEF_DELTA_E, (strength, delta_e)
