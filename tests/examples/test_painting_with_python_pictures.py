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
        assert "(../../features/ink-read-svg-drawings.md)" in text

    @pytest.mark.parametrize("page", ["pictures", "vector-drawing"], ids=["pictures", "vector"])
    def test_each_page_shows_its_registered_image_and_no_dashes(self, page):
        """Each page shows an image under docs/images and has no em or en dash."""
        text = (PAGES / f"{page}.md").read_text()
        assert "../../images/painting-with-python/" in text
        assert not {chr(0x2014), chr(0x2013)} & set(text)
