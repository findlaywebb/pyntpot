"""The docs site's theme script: its stylesheet is pinned, readable on both schemes, and its pictures are one file each."""

import re
from pathlib import Path

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
    for name, value in {**root, **blocks[selector]}.items():
        while (match := re.fullmatch(r"var\((--[\w-]+)\)", value)) is not None:
            value = {**root, **blocks[selector]}[match.group(1)]
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

    @pytest.mark.parametrize("figure", ["paper", "rule"])
    def test_a_picture_is_the_only_file_written(self, tmp_path: Path, figure: str) -> None:
        """A picture figure writes one PNG of the width asked."""
        path = run_example("site_theme", tmp_path / figure, figure=figure, size=SMALL)
        assert [p.name for p in path.parent.iterdir()] == [f"{figure}.png"]
        with Image.open(path) as image:
            assert image.width == SMALL

    def test_an_unknown_figure_is_refused(self, tmp_path: Path) -> None:
        """A figure outside the three raises `ValueError`."""
        with pytest.raises(ValueError, match="figure must be one of"):
            run_example("site_theme", tmp_path, figure="banner")
