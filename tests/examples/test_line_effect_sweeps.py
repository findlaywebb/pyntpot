"""The line effect sweeps run offline, and each sweep's off cell is the plain stroke."""

import numpy as np
import pytest
from PIL import Image

from pyntpot.ink import PenCasing, pen_casing
from pyntpot.ink.effect_types import EFFECT_RANGES

from support import REPO_ROOT
from support.examples import load_example, run_example

FIGURES = ("casing", "glow", "shadow", "pen-casing", "reserve")

#: The values that switch each sweep's effect off through its own primitive: the casing's 0
#: column, and the default (off) effect for the other three.
OFF: dict[str, dict[str, object]] = {
    "casing": {"width_px": 0.0},
    "glow": {},
    "shadow": {},
    "pen-casing": {},
    "reserve": {"width_px": 0.0},
}

#: One real setting of each sweep, not off.
SAMPLE: dict[str, dict[str, object]] = {
    "casing": {"width_px": 3.0},
    "glow": {"spread_px": 4.0, "blur_px": 3.0},
    "shadow": {"offset_px": 3.0, "blur_px": 1.0},
    "pen-casing": {"width_px": 2.0, "edge_px": 1.5},
    "reserve": {"width_px": 3.0, "pool": 0.3},
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


class TestSupersampled:
    """Each sweep is painted at 2x and reduced once, so the file is its 1x size."""

    @pytest.mark.parametrize("figure", FIGURES, ids=FIGURES)
    def test_the_written_image_is_the_registered_width_and_the_grids_height(self, figure, tmp_path):
        """The PNG is the figure's 1x width by the 1x grid's height, though painted at twice that."""
        namespace = _grids()
        path = run_example("line_effect_grids", tmp_path, figure=figure)
        with Image.open(path) as image:
            assert image.size == (namespace["WIDTH_PX"][figure], namespace["_spec"](figure).height)

    @pytest.mark.parametrize("figure", FIGURES, ids=FIGURES)
    def test_a_cell_is_painted_at_twice_its_box(self, figure):
        """A cell comes back at twice the 1x cell's width and height."""
        namespace = _grids()
        spec = namespace["_spec"](figure)
        cell = namespace["paint_cell"](figure, plain=True)
        assert cell.shape == (2 * namespace["CELL_H"][figure], 2 * spec.cell_w, 3)


class TestReserve:
    """A reserve lifts the wash to the paper, and its pool only darkens."""

    def test_a_pooled_cell_is_nowhere_lighter_than_the_unpooled_one(self):
        """On the 2x floats before reduce, each width's 0.3 pool is no lighter than its 0 pool."""
        paint_cell = _grids()["paint_cell"]
        for width in _grids()["RESERVE_WIDTHS_PX"][1:]:
            flat = paint_cell("reserve", width_px=width, pool=0.0)
            pooled = paint_cell("reserve", width_px=width, pool=0.3)
            assert (pooled - flat).max() <= 1e-6, width
            assert (pooled - flat).min() < 0.0, width

    def test_the_reserve_lifts_the_wash_toward_the_paper(self):
        """A reserved cell is no darker than the plain stroke cell."""
        paint_cell = _grids()["paint_cell"]
        plain = paint_cell("reserve", plain=True)
        reserved = paint_cell("reserve", width_px=3.0, pool=0.0)
        assert (reserved - plain).min() >= -1e-6


class TestPenEdges:
    """The thin pen edge line stays unbroken once the 2x paint is reduced."""

    def test_the_thin_edge_has_ink_in_every_column_of_its_span(self):
        """With a 1 px gap and a 0.75 px edge, every column of the line has edge ink of 0.5 or more."""
        namespace = _grids()
        scene = namespace["_scene"]("pen-casing")
        effect = PenCasing(width_px=2.0, edge_px=1.5)
        _, band = pen_casing(scene.wash, scene.density, effect, paper=None)
        reduced = namespace["reduce"](np.repeat(band[..., None], 3, axis=2), 2)[..., 0]
        covered = np.flatnonzero(scene.density.max(axis=0) >= 0.5)
        span = covered[::2][5:-5] // 2
        assert len(span) > 20
        assert (reduced.max(axis=0)[span] >= 0.5).all()


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
            "RESERVE_WIDTHS_PX",
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
