"""The pictures scripts of Painting with Python run offline, paint a whole sheet and read their drawing."""

import re
import runpy
import xml.etree.ElementTree as ET

import numpy as np
import pytest
from PIL import Image

from support import REPO_ROOT
from support.examples import EXAMPLES_DIR, run_example

#: A width small enough for a quick run.
SMALL = 240
FELL = EXAMPLES_DIR / "drawings" / "fell.svg"
PAGES = REPO_ROOT / "docs" / "tutorials" / "painting-with-python"


def _painted(path):
    """Return a finished image's pixels, checking it is an RGB PNG."""
    with Image.open(path) as image:
        assert image.format == "PNG"
        assert image.mode == "RGB"
        return np.asarray(image)


def _dark(pixels):
    """Return how many pixels have every channel under 90, the darkness only a pen lays."""
    return int((pixels.max(axis=2) < 90).sum())


class TestDerwentwater:
    """The Derwentwater view."""

    def test_it_paints_a_picture_of_the_size_asked(self, tmp_path):
        """The script writes one PNG as wide as `size` and 2:3 high, with colour in it."""
        path = run_example("derwentwater", tmp_path, size=SMALL)
        pixels = _painted(path)
        assert pixels.shape == (SMALL * 2 // 3, SMALL, 3)
        assert (pixels.min(axis=(0, 1)) != pixels.max(axis=(0, 1))).all()

    def test_it_leaves_a_margin_of_bare_paper(self, tmp_path):
        """The strip of rows and columns inside the sheet's edge is lighter than the painting."""
        pixels = _painted(run_example("derwentwater", tmp_path, size=SMALL)).astype(float)
        h = pixels.shape[0]
        margin = pixels[h // 4 : 3 * h // 4, int(0.02 * SMALL) : int(0.04 * SMALL)]
        painted = pixels[h // 2 : 3 * h // 4, SMALL // 3 : 2 * SMALL // 3]
        assert margin.mean() > painted.mean() + 30

    def test_the_water_is_bluer_than_the_banks_above_it(self, tmp_path):
        """Below the shore the picture is bluer, against red, than the bank above the shore."""
        pixels = _painted(run_example("derwentwater", tmp_path, size=SMALL)).astype(float)
        h = pixels.shape[0]
        lake = pixels[int(0.66 * h) : int(0.72 * h), SMALL // 4 : 3 * SMALL // 4]
        bank = pixels[int(0.50 * h) : int(0.56 * h), SMALL // 10 : SMALL // 5]
        lake_blue = lake[..., 2].mean() - lake[..., 0].mean()
        bank_blue = bank[..., 2].mean() - bank[..., 0].mean()
        assert lake_blue > bank_blue + 8


class TestSvgDrawing:
    """The vector drawing and the script that reads it."""

    def test_the_drawing_uses_only_the_stated_path_subset(self):
        """Every path in fell.svg is written with M, L, C and Z commands only."""
        paths = ET.parse(FELL).getroot().findall(".//{http://www.w3.org/2000/svg}path")
        assert len(paths) >= 8
        for element in paths:
            commands = set(re.findall(r"[A-Za-z]", element.attrib["d"]))
            assert commands <= set("MLCZ"), (element.attrib.get("id"), commands)

    def test_a_cubic_curve_is_flattened_to_a_fixed_number_of_segments(self):
        """One C command becomes the start plus a fixed count of points, ending on its end point."""
        namespace = runpy.run_path(str(EXAMPLES_DIR / "svg_drawing.py"), run_name="example_svg")
        loops = namespace["parse_path"]("M 0 0 C 0 10 10 10 10 0 L 20 0 Z")
        assert len(loops) == 1
        points, closed = loops[0]
        assert closed
        assert len(points) == 1 + namespace["CURVE_SEGMENTS"] + 1
        assert tuple(points[namespace["CURVE_SEGMENTS"]]) == (10.0, 0.0)
        assert tuple(points[-1]) == (20.0, 0.0)

    def test_it_paints_a_picture_of_the_size_asked(self, tmp_path):
        """The script writes one PNG as wide as `size` and 3:2 high, with colour in it."""
        path = run_example("svg_drawing", tmp_path, size=SMALL)
        pixels = _painted(path)
        assert pixels.shape == (SMALL * 2 // 3, SMALL, 3)
        assert (pixels.min(axis=(0, 1)) != pixels.max(axis=(0, 1))).all()

    @pytest.mark.parametrize("figure", ["flat", "washes", "ink", "painting"])
    def test_each_figure_paints_a_picture_of_the_size_asked(self, tmp_path, figure):
        """Every figure writes one PNG as wide as `size` and 3:2 high, with colour in it."""
        pixels = _painted(run_example("svg_drawing", tmp_path, figure=figure, size=SMALL))
        assert pixels.shape == (SMALL * 2 // 3, SMALL, 3)
        assert (pixels.min(axis=(0, 1)) != pixels.max(axis=(0, 1))).all()

    def test_the_flat_figure_has_no_paper_and_the_others_do(self, tmp_path):
        """The flat figure's corner is pure white; every painted figure's corner is warm paper."""
        corner = np.s_[2:10, 2:10]
        flat = _painted(run_example("svg_drawing", tmp_path, figure="flat", size=SMALL))
        assert (flat[corner] == 255).all()
        for figure in ("washes", "ink", "painting"):
            painted = _painted(run_example("svg_drawing", tmp_path, figure=figure, size=SMALL))
            assert painted[corner][..., 2].mean() < painted[corner][..., 0].mean() - 4, figure

    def test_the_washes_carry_no_ink_and_the_ink_no_wash(self, tmp_path):
        """The washes figure has few dark pixels, the ink figure a pen line of them and no green body, the painting both."""
        washes = _painted(run_example("svg_drawing", tmp_path, figure="washes", size=SMALL))
        ink = _painted(run_example("svg_drawing", tmp_path, figure="ink", size=SMALL))
        painting = _painted(run_example("svg_drawing", tmp_path, figure="painting", size=SMALL))
        fell = np.s_[SMALL // 3 : SMALL // 2, SMALL // 2 : 2 * SMALL // 3]
        assert ink[fell].astype(float).mean() > washes[fell].astype(float).mean() + 15
        assert _dark(washes) * 5 < _dark(ink)
        assert _dark(ink) > 0
        assert _dark(painting) > 0

    def test_the_near_fell_hides_the_far_one(self, tmp_path):
        """Where the main fell lies over the far fell the wash is as green as the main fell elsewhere."""
        washes = _painted(run_example("svg_drawing", tmp_path, figure="washes", size=480)).astype(
            float
        )
        scale = 0.88 * 480 / 600
        dx, dy = (480 - 600 * scale) / 2, (320 - 400 * scale) / 2

        def at(x, y):
            return washes[int(y * scale + dy), int(x * scale + dx)]

        overlap, plain = at(300, 200), at(400, 200)
        assert abs(overlap - plain).max() < 25

    def test_it_rejects_an_unknown_figure(self, tmp_path):
        """A figure outside the four is refused rather than painted as something else."""
        with pytest.raises(ValueError, match="figure"):
            run_example("svg_drawing", tmp_path, figure="oils", size=SMALL)

    def test_it_rejects_a_command_outside_the_subset(self):
        """A path with an arc command is refused rather than half read."""
        namespace = runpy.run_path(str(EXAMPLES_DIR / "svg_drawing.py"), run_name="example_svg")
        with pytest.raises(ValueError, match="command"):
            namespace["parse_path"]("M 0 0 A 5 5 0 0 1 10 0")


class TestPages:
    """The two pages."""

    def test_the_vector_page_says_pyntpot_does_not_read_svg_and_links_the_feature(self):
        """The vector page states that pyntpot reads no SVG and links the feature note."""
        text = (PAGES / "vector-drawing.md").read_text()
        assert "does not read SVG" in text
        assert (
            "(https://github.com/findlaywebb/pyntpot/blob/main/docs/features/ink-read-svg-drawings.md)"
            in text
        )

    def test_the_vector_page_shows_every_step_of_the_drawing(self):
        """The vector page shows the flat drawing, the washes, the inks and the painting."""
        text = (PAGES / "vector-drawing.md").read_text()
        for name in ("svg-flat", "svg-washes", "svg-ink", "svg-drawing"):
            assert f"../../images/painting-with-python/{name}.webp" in text

    @pytest.mark.parametrize("page", ["pictures", "vector-drawing"], ids=["pictures", "vector"])
    def test_each_page_shows_its_registered_image_and_no_dashes(self, page):
        """Each page shows an image under docs/images and has no em or en dash."""
        text = (PAGES / f"{page}.md").read_text()
        assert "../../images/painting-with-python/" in text
        assert not {chr(0x2014), chr(0x2013)} & set(text)
