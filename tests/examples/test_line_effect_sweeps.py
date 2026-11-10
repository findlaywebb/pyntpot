"""The line effect sweeps run offline, and each sweep's off cell is the plain stroke."""

import numpy as np
import pytest
from PIL import Image

from pyntpot.ink.effect_types import EFFECT_RANGES

from support import REPO_ROOT
from support.examples import load_example, run_example

FIGURES = ("casing", "glow", "shadow", "pen-casing")

#: The values that switch each sweep's effect off through its own primitive: the casing's 0
#: column, and the default (off) effect for the other three.
OFF: dict[str, dict[str, object]] = {
    "casing": {"width_px": 0.0},
    "glow": {},
    "shadow": {},
    "pen-casing": {},
}

#: One real setting of each sweep, not off.
SAMPLE: dict[str, dict[str, object]] = {
    "casing": {"width_px": 3.0},
    "glow": {"spread_px": 4.0, "blur_px": 3.0},
    "shadow": {"offset_px": 3.0, "blur_px": 1.0},
    "pen-casing": {"width_px": 2.0, "edge_px": 1.5},
}


def _grids():
    """Return the sweep script's namespace."""
    return load_example("line_effect_grids", "example_line_effect_grids")


class TestFigures:
    """Each figure writes one lossless PNG, and a figure the script does not have is refused."""

    @pytest.mark.parametrize("figure", FIGURES, ids=FIGURES)
    def test_a_figure_is_one_image_that_is_not_flat(self, figure, tmp_path):
        """Each figure writes one RGB PNG into the directory that is not one flat colour."""
        path = run_example("line_effect_grids", tmp_path, figure=figure)
        assert list(tmp_path.iterdir()) == [path]
        with Image.open(path) as image:
            assert image.mode == "RGB"
            pixels = np.asarray(image)
        assert (pixels.min(axis=(0, 1)) != pixels.max(axis=(0, 1))).all()

    def test_an_unknown_figure_is_refused(self, tmp_path):
        """A figure the sweeps do not have is a ValueError, not a blank image."""
        with pytest.raises(ValueError, match="no such figure"):
            run_example("line_effect_grids", tmp_path, figure="nonesuch")


class TestOffCells:
    """A sweep's off cell is painted through its primitive and is the plain stroke, byte for byte."""

    @pytest.mark.parametrize("figure", FIGURES, ids=FIGURES)
    @pytest.mark.parametrize("at", [(0, 0), (130, 70)], ids=["origin", "offset"])
    def test_each_sweeps_off_cell_is_the_plain_stroke(self, figure, at):
        """The off cell and the separately painted plain stroke are the same float32 bytes."""
        paint_cell = _grids()["paint_cell"]
        off = paint_cell(figure, at=at, **OFF[figure])
        plain = paint_cell(figure, at=at, plain=True)
        assert off.dtype == plain.dtype == np.float32
        assert off.shape == plain.shape
        assert off.ndim == 3 and off.shape[2] == 3
        assert off.tobytes() == plain.tobytes()

    @pytest.mark.parametrize("figure", FIGURES, ids=FIGURES)
    def test_a_real_setting_is_not_the_plain_stroke(self, figure):
        """A swept value other than off changes the cell, so the byte comparison is not vacuous."""
        namespace = _grids()
        values = SAMPLE[figure]
        painted = namespace["paint_cell"](figure, **values)
        plain = namespace["paint_cell"](figure, plain=True)
        assert painted.tobytes() != plain.tobytes()


class TestGlow:
    """A glow only lifts toward the paper."""

    def test_no_glow_cell_is_darker_than_the_plain_stroke(self):
        """Every cell of the glow sweep is at least as light as the plain stroke, within float rounding."""
        namespace = _grids()
        plain = namespace["paint_cell"]("glow", plain=True)
        for spread in namespace["SPREADS_PX"]:
            for blur in namespace["GLOW_BLURS_PX"]:
                cell = namespace["paint_cell"]("glow", spread_px=spread, blur_px=blur)
                assert (cell - plain).min() >= -1e-6, (spread, blur)


class TestShadow:
    """The shadow falls south-east, away from the light in the north-west."""

    def test_the_shadow_falls_to_the_south_east_of_the_line(self):
        """The darkening a shadow adds has its centre of mass right of and below the line's."""
        namespace = _grids()
        plain = namespace["paint_cell"]("shadow", plain=True)
        cell = namespace["paint_cell"]("shadow", offset_px=5.0, blur_px=1.0)
        added = (plain - cell).sum(axis=2).clip(0.0)
        assert added.sum() > 0
        yy, xx = np.mgrid[0 : added.shape[0], 0 : added.shape[1]]
        line = namespace["stroke_density"]("shadow")
        assert (added * xx).sum() / added.sum() > (line * xx).sum() / line.sum()
        assert (added * yy).sum() / added.sum() > (line * yy).sum() / line.sum()


class TestHeldValues:
    """The sweeps' held values are the script's own literals."""

    def test_the_script_names_no_preset_and_passes_no_threshold(self):
        """The script reads no preset table and no private range, and passes no threshold."""
        for stem in ("line_effect_grids", "line_effect_scenes"):
            source = (REPO_ROOT / "examples" / f"{stem}.py").read_text()
            code = source.split('"""', 2)[2]
            for word in ("BUILT_IN_PRESETS", "LINE_THRESHOLD", "EFFECT_RANGES", "threshold="):
                assert word not in code, (stem, word)

    def test_every_swept_value_is_inside_its_documented_range(self):
        """Each swept axis stays within 0 to 16 pixels, the range a theme may set."""
        namespace = _grids()
        axes = (
            "WIDTHS_PX",
            "SPREADS_PX",
            "GLOW_BLURS_PX",
            "OFFSETS_PX",
            "SHADOW_BLURS_PX",
            "GAPS_PX",
            "EDGES_PX",
        )
        for axis in axes:
            low, high = EFFECT_RANGES["width_px"]
            assert all(low <= value <= high for value in namespace[axis]), axis


class TestSweepGrid:
    """`sweep_grid` lays each painted cell in its box and refuses one of the wrong size."""

    def test_a_cell_lands_in_its_box_and_the_paper_is_left_alone(self):
        """The painted cell fills its box, the gap keeps the paper, and the input is unchanged."""
        sweep_grid = load_example("labelled_grid", "example_labelled_grid")["sweep_grid"]
        paper = np.full((20, 30, 3), 0.5, np.float32)
        boxes = [[(2, 3, 10, 6), (16, 3, 10, 6)]]
        out = sweep_grid(paper, boxes, lambda r, c, box: np.full((6, 10, 3), c, np.float32))
        assert (out[3:9, 2:12] == 0).all() and (out[3:9, 16:26] == 1).all()
        assert out[0, 0, 0] == np.float32(0.5) and (paper == 0.5).all()

    def test_a_cell_of_the_wrong_size_is_refused(self):
        """A cell that is not its box's size raises ValueError."""
        sweep_grid = load_example("labelled_grid", "example_labelled_grid")["sweep_grid"]
        with pytest.raises(ValueError, match="its box is"):
            sweep_grid(
                np.zeros((9, 9, 3), np.float32),
                [[(0, 0, 4, 4)]],
                lambda r, c, b: np.zeros((3, 3, 3)),
            )
