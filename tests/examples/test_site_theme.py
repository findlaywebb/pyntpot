"""The docs site's theme script: its stylesheet is pinned, readable on both schemes, and its pictures are one file each."""

import re
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from pyntpot.ink import PIGMENTS

from support import REPO_ROOT
from support.examples import run_example

STYLESHEET = REPO_ROOT / "docs" / "stylesheets" / "pyntpot.css"
#: The smallest contrast ratio WCAG AA asks of body text.
MIN_CONTRAST = 4.5
#: The width the pictures are painted at here, in pixels, so each paint stays fast.
SMALL = 96

_BLOCK = re.compile(
    r'(:root|\[data-md-color-scheme="(?:default|slate)"\])\s*\{(.*?)\n\}', re.DOTALL
)
_PROPERTY = re.compile(r"^\s*(--[\w-]+):\s*(.+?);\s*$", re.MULTILINE)


def _scheme(css: str, selector: str) -> dict[str, str]:
    """Return the custom properties a scheme sets over the root's, each `var()` of the root's resolved."""
    blocks = {name: dict(_PROPERTY.findall(body)) for name, body in _BLOCK.findall(css)}
    root = blocks[":root"]
    found: dict[str, str] = {}
    merged = {**root, **blocks[selector]}
    for name, declared in merged.items():
        value = declared
        while (match := re.fullmatch(r"var\((--[\w-]+)\)", value)) is not None:
            value = merged[match.group(1)]
        found[name] = value
    return found


def _luminance(colour: str) -> float:
    """Return the WCAG relative luminance of a `#rrggbb` colour."""
    channels = [int(colour[i : i + 2], 16) / 255 for i in (1, 3, 5)]
    linear = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in channels]
    return float(0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2])


def _contrast(a: str, b: str) -> float:
    """Return the WCAG contrast ratio of two `#rrggbb` colours."""
    hi, lo = sorted((_luminance(a), _luminance(b)), reverse=True)
    return (hi + 0.05) / (lo + 0.05)


#: Each text colour and the colour it is read on, as the scheme's custom property names.
PAIRS = (
    ("--md-default-fg-color", "--md-default-bg-color"),
    ("--md-typeset-a-color", "--md-default-bg-color"),
    ("--md-accent-fg-color", "--md-default-bg-color"),
    ("--md-primary-bg-color", "--md-primary-fg-color"),
    ("--md-code-fg-color", "--md-code-bg-color"),
)
SCHEMES = ('[data-md-color-scheme="default"]', '[data-md-color-scheme="slate"]')


class TestStylesheet:
    """The committed stylesheet is what the script writes, and its text is readable in both schemes."""

    def test_the_committed_file_is_what_the_script_writes(self, tmp_path: Path) -> None:
        """`docs/stylesheets/pyntpot.css` equals the script's `palette` figure, byte for byte."""
        written = run_example("site_theme", tmp_path, figure="palette")
        assert written.read_text() == STYLESHEET.read_text()

    @pytest.mark.parametrize("selector", SCHEMES, ids=["light", "dark"])
    def test_every_text_colour_reads_on_its_ground(self, selector: str) -> None:
        """Each text colour of a scheme has a contrast of at least 4.5 against the colour it sits on."""
        properties = _scheme(STYLESHEET.read_text(), selector)
        for text, ground in PAIRS:
            ratio = _contrast(properties[text], properties[ground])
            assert ratio >= MIN_CONTRAST, f"{selector}: {text} on {ground} is {ratio:.2f}"

    def test_the_palette_names_every_pigment_twice(self) -> None:
        """The stylesheet has one raw and one glazed custom property for each key of `PIGMENTS`."""
        css = STYLESHEET.read_text()
        for key in PIGMENTS:
            assert f"--pyntpot-{key}: {PIGMENTS[key]};" in css
            assert f"--pyntpot-glaze-{key}: #" in css


class TestPictures:
    """Each picture figure writes one image and rejects a figure it does not know."""

    @pytest.mark.parametrize("figure", ["paper", "rule", "header"])
    def test_a_picture_is_the_only_file_written(self, tmp_path: Path, figure: str) -> None:
        """A picture figure writes one PNG of the width asked."""
        path = run_example("site_theme", tmp_path / figure, figure=figure, size=SMALL)
        assert [p.name for p in path.parent.iterdir()] == [f"{figure}.png"]
        with Image.open(path) as image:
            assert image.width == SMALL

    def test_an_unknown_figure_is_refused(self, tmp_path: Path) -> None:
        """A figure outside the four raises `ValueError`."""
        with pytest.raises(ValueError, match="figure must be one of"):
            run_example("site_theme", tmp_path, figure="banner")


def _pixels(path: Path) -> np.ndarray:
    """Return an image file as floats in 0 to 1."""
    with Image.open(path) as image:
        return np.asarray(image.convert("RGB"), dtype=float) / 255


class TestPaintedChrome:
    """The paper tiles, the rule is a stroke on white that keeps its shape, and the header band is dark enough for its text."""

    def test_the_paper_tiles_without_a_seam(self, tmp_path: Path) -> None:
        """Across the tile's edge the paper changes no more than it does between two neighbouring columns inside."""
        paper = _pixels(run_example("site_theme", tmp_path, figure="paper", size=128))
        assert paper.shape[0] == paper.shape[1]
        across = np.abs(paper[:, 0] - paper[:, -1]).mean()
        inside = np.abs(paper[:, 63] - paper[:, 64]).mean()
        assert across <= 1.5 * inside + 1e-3
        assert (
            np.abs(paper[0] - paper[-1]).mean() <= 1.5 * np.abs(paper[63] - paper[64]).mean() + 1e-3
        )

    def test_the_rule_is_a_stroke_on_pure_white(self, tmp_path: Path) -> None:
        """The rule's four corners are pure white, so multiplying it leaves only the stroke, and the stroke is on it."""
        rule = _pixels(run_example("site_theme", tmp_path, figure="rule", size=400))
        corners = [rule[0, 0], rule[0, -1], rule[-1, 0], rule[-1, -1]]
        assert all(np.array_equal(corner, np.ones(3)) for corner in corners)
        assert rule.min() < 0.6

    def test_the_rule_keeps_the_aspect_the_site_shows_it_at(self, tmp_path: Path) -> None:
        """The rule is far wider than tall, and the stylesheet sizes it by height alone, never stretched to the box."""
        rule = _pixels(run_example("site_theme", tmp_path, figure="rule", size=400))
        assert rule.shape[1] / rule.shape[0] > 20
        css = STYLESHEET.read_text()
        assert "left center / auto 100% no-repeat" in css
        assert "100% 100%" not in css

    def test_the_header_band_keeps_the_header_text_readable(self, tmp_path: Path) -> None:
        """Even the lightest pixels of the header band have a contrast of at least 4.5 against the paper colour."""
        band = _pixels(run_example("site_theme", tmp_path, figure="header", size=400))
        paper = _scheme(STYLESHEET.read_text(), SCHEMES[0])["--md-primary-bg-color"]
        linear = np.where(band <= 0.03928, band / 12.92, ((band + 0.055) / 1.055) ** 2.4)
        lightest = np.percentile(linear.reshape(-1, 3) @ [0.2126, 0.7152, 0.0722], 99.5)
        paper_luminance = _luminance(paper)
        assert (paper_luminance + 0.05) / (lightest + 0.05) >= MIN_CONTRAST

    def test_the_header_band_is_not_a_flat_colour(self, tmp_path: Path) -> None:
        """The header band varies along its length and is darker at its lower edge than at its upper."""
        band = _pixels(run_example("site_theme", tmp_path, figure="header", size=400))
        grey = band.mean(axis=2)
        assert grey.mean(axis=0).std() > 0.003
        assert grey[-8:].mean() < grey[:8].mean()


class TestFaces:
    """The body is set in a serif and the hand is kept for headings."""

    def test_the_body_text_is_a_serif_and_the_hand_is_for_headings(self) -> None:
        """The theme's text font is the serif stack, and only headings and the site name take the hand."""
        css = STYLESHEET.read_text()
        assert "--md-text-font: var(--pyntpot-serif);" in css
        assert css.count("font-family: var(--pyntpot-display);") == 1
