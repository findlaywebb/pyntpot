"""The brush and pigment galleries run offline, paint what they list and write one image each."""

import numpy as np
import pytest
from PIL import Image

from pyntpot.ink import PAINTERS_PIGMENTS, PIGMENT_REGISTRY, PIGMENTS

from support.examples import load_example, run_example

#: A small width, so a figure paints quickly.
SMALL = 360

BRUSH_FIGURES = ("riv-str-lan", "maj", "trk")
PIGMENT_FIGURES = ("roles", "painters", "glazes", "palettes")


def _pigment_gallery():
    """Return the pigment gallery script's namespace."""
    return load_example("pigment_gallery", "example_pigment_gallery")


def _darkness(cell: np.ndarray) -> float:
    """Return how dark a painted cell is: one minus its mean luminance."""
    return float(1.0 - (cell @ np.array([0.2126, 0.7152, 0.0722], np.float32)).mean())


class TestBrushGallery:
    """The brush gallery paints each of its figures as one image of the width asked for."""

    @pytest.mark.parametrize("figure", BRUSH_FIGURES, ids=BRUSH_FIGURES)
    def test_a_figure_is_one_image_of_its_width(self, figure, tmp_path):
        """Each figure writes one PNG of the width asked for that is not one flat colour."""
        path = run_example("brush_gallery", tmp_path, figure=figure, size=SMALL)
        assert list(tmp_path.iterdir()) == [path]
        with Image.open(path) as image:
            assert image.mode == "RGB"
            assert image.width == SMALL
            pixels = np.asarray(image)
        assert (pixels.min(axis=(0, 1)) != pixels.max(axis=(0, 1))).all()

    def test_an_unknown_figure_is_refused(self, tmp_path):
        """A figure the gallery does not have is a ValueError, not a blank image."""
        with pytest.raises(ValueError, match="no such figure"):
            run_example("brush_gallery", tmp_path, figure="nonesuch", size=SMALL)

    def test_the_riv_str_lan_figure_paints_two_columns_of_eight(self):
        """RIV and STR share one column, so the first figure holds 16 cells and 24 ids."""
        namespace = load_example("brush_gallery", "example_brush_gallery")
        cells = namespace["cell_ids"]("riv-str-lan")
        assert [len(row) for row in cells] == [2] * 8
        assert len(namespace["figure_ids"]("riv-str-lan")) == 24
        assert cells[0][0] == ("RIV1-a", "STR1-a")
        assert cells[7][1] == ("LAN8-a",)


class TestPigmentGallery:
    """The pigment gallery paints each of its figures as one image of the width asked for."""

    @pytest.mark.parametrize("figure", PIGMENT_FIGURES, ids=PIGMENT_FIGURES)
    def test_a_figure_is_one_image_of_its_width(self, figure, tmp_path):
        """Each figure writes one PNG of the width asked for that is not one flat colour."""
        path = run_example("pigment_gallery", tmp_path, figure=figure, size=SMALL)
        assert list(tmp_path.iterdir()) == [path]
        with Image.open(path) as image:
            assert image.mode == "RGB"
            assert image.width == SMALL
            pixels = np.asarray(image)
        assert (pixels.min(axis=(0, 1)) != pixels.max(axis=(0, 1))).all()

    def test_an_unknown_figure_is_refused(self, tmp_path):
        """A figure the gallery does not have is a ValueError, not a blank image."""
        with pytest.raises(ValueError, match="no such figure"):
            run_example("pigment_gallery", tmp_path, figure="nonesuch", size=SMALL)

    def test_the_two_wash_figures_paint_every_registry_pigment_once(self):
        """The roles and painters figures together hold each registry pigment, in registry order."""
        rows = _pigment_gallery()["wash_rows"]
        names = (*rows("roles", SMALL).names, *rows("painters", SMALL).names)
        assert names == PIGMENT_REGISTRY.names()
        assert names == (*PIGMENTS, *PAINTERS_PIGMENTS)

    @pytest.mark.parametrize("figure", ("roles", "painters"), ids=("roles", "painters"))
    def test_the_pigment_gallery_washes_darken_with_strength(self, figure):
        """For every registry pigment the 0.9 wash is darker than the 0.6, and the 0.6 than the 0.3."""
        namespace = _pigment_gallery()
        assert namespace["STRENGTHS"] == (0.3, 0.6, 0.9)
        painted = namespace["wash_rows"](figure, SMALL)
        for name, row in zip(painted.names, painted.boxes, strict=True):
            tones = [_darkness(painted.image[y : y + h, x : x + w]) for (x, y, w, h) in row]
            assert tones[0] < tones[1] < tones[2], (name, tones)

    def test_the_glaze_figure_lays_each_pair_of_the_registry(self):
        """Every pigment a glaze pair names is in the registry, and no pair names one twice."""
        pairs = _pigment_gallery()["GLAZE_PAIRS"]
        assert len(pairs) == 6
        for first, second in pairs:
            assert first in PIGMENT_REGISTRY
            assert second in PIGMENT_REGISTRY
            assert first != second
