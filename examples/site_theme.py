"""The docs site's own chrome, painted and written by the engine it documents.

Four figures, chosen by `figure=`. `"paper"` paints the cream rag the light scheme's page
sits on: the default paper without its worn border, vignette or foxing, made seamless so the
page repeats it at its own size, whatever the window. `"rule"` paints one wavering, tapering
stroke of a river brush on pure white, the rule under a page title; the site lays it on the
page at its own aspect by multiplying, so only the stroke shows. `"header"` paints the band
behind the site's header: a deep water wash that is darker along its lower edge, where the
wash pooled, and uneven along its length; the site repeats it sideways. `"palette"` writes `pyntpot.css`, the site's stylesheet, with the colours drawn from
`PIGMENTS` as CSS custom properties: each pigment as it is, and the pigment glazed four
times for text and the header on the light scheme. Its contrast is checked by
`tests/examples/test_site_theme.py`.

Public names it uses: from `pyntpot.ink`, `Sheet`, `Canvas`, `PaperStyle`, `BrushStyle`,
`PIGMENTS`, `paper_plate`, `brush_from_id`, `stamp`, `ink_density`, `composite`, `rgb` and
`save_image`.

`main` writes one file per call. For the three pictures it returns the PNG's path; for
`"palette"` it returns the stylesheet's path, which is text, not an image, and is not in the
image registry. Every seed is fixed, so one run writes the same files. It paints no map and
reads no file. Patrick Hand, the face the stylesheet loads for display headings, is the
vendored font, copied to `docs/assets/` with its licence. Body text uses the system serif
stack, which needs no file.

Run it with `uv run python examples/site_theme.py out/ --figure rule`.
"""

import argparse
import logging
from pathlib import Path
from string import Template

import numpy as np

from pyntpot.ink import (
    PIGMENTS,
    BrushStyle,
    Canvas,
    PaperStyle,
    Sheet,
    brush_from_id,
    composite,
    ink_density,
    paper_plate,
    rgb,
    save_image,
    stamp,
)

logger = logging.getLogger(__name__)

#: The figures `main` paints or writes.
FIGURES = ("paper", "rule", "header", "palette")
#: The picture widths, in pixels, when `size=` is not given.
WIDTH = {"paper": 512, "rule": 1600, "header": 1600}
#: The size of the paper's granulation noise, in pixels.
GRAN_PX = 5.0
#: The seed of the paper's noise, the bristles and the dither the file is written with.
SEED = 11
#: The rule's height as a share of its width.
RULE_ASPECT = 60 / 1600
#: The header band's height as a share of its width.
HEADER_ASPECT = 120 / 1600
#: How many times the water pigment is glazed in the band, at its lightest and its darkest.
HEADER_GLAZE = (3.5, 5.0)
#: How many times a pigment is glazed to make the text and header colours of the light scheme.
GLAZES = 4
#: How much of the `relief` pigment's colour the dark page and the light scheme's ink keep.
DARK_SHARE = 0.14
INK_SHARE = 0.16
#: The rule's brush id, and its width as a share of the rule's height.
RULE_BRUSH = "RIV4-a"
RULE_BRUSH_SHARE = 0.4

STYLESHEET = Template("""\
/* Written by examples/site_theme.py (figure="palette"); do not edit by hand.
   The colours are the PIGMENTS of pyntpot.ink: --pyntpot-<key> as the pigment is,
   --pyntpot-glaze-<key> the pigment glazed $glazes times, for text and the header. */

@font-face {
  font-family: "Patrick Hand";
  font-style: normal;
  font-weight: 400;
  font-display: swap;
  src: url("../assets/PatrickHand-Regular.ttf") format("truetype");
}

:root {
$pigments
  --pyntpot-paper: $paper;
  --pyntpot-ink: $ink;
  --pyntpot-night: $night;
  --pyntpot-display: "Patrick Hand", "Segoe Print", "Comic Sans MS", cursive;
  --pyntpot-serif: Charter, "Sitka Text", Cambria, "Iowan Old Style", Georgia, serif;
  --md-text-font: var(--pyntpot-serif);
}

[data-md-color-scheme="default"] {
  --md-default-bg-color: var(--pyntpot-paper);
  --md-default-fg-color: var(--pyntpot-ink);
  --md-default-fg-color--light: $ink_light;
  --md-default-fg-color--lighter: $ink_lighter;
  --md-default-fg-color--lightest: $ink_lightest;
  --md-primary-fg-color: var(--pyntpot-glaze-water);
  --md-primary-bg-color: var(--pyntpot-paper);
  --md-accent-fg-color: var(--pyntpot-glaze-wood);
  --md-typeset-a-color: var(--pyntpot-glaze-water);
  --md-code-bg-color: $code_light;
  --md-code-fg-color: var(--pyntpot-ink);
  --pyntpot-paper-image: url("../images/site/paper.webp");
  --pyntpot-rule-image: url("../images/site/rule.webp");
  --pyntpot-header-image: url("../images/site/header.webp");
}

[data-md-color-scheme="slate"] {
  --md-default-bg-color: var(--pyntpot-night);
  --md-default-fg-color: var(--pyntpot-paper);
  --md-default-fg-color--light: $paper_light;
  --md-default-fg-color--lighter: $paper_lighter;
  --md-default-fg-color--lightest: $paper_lightest;
  --md-primary-fg-color: var(--pyntpot-glaze-water);
  --md-primary-bg-color: var(--pyntpot-paper);
  --md-accent-fg-color: var(--pyntpot-wood);
  --md-typeset-a-color: var(--pyntpot-water);
  --md-code-bg-color: $code_dark;
  --md-code-fg-color: var(--pyntpot-paper);
  --pyntpot-paper-image: none;
  --pyntpot-rule-image: none;
  --pyntpot-header-image: none;
}

/* The paper the light scheme's page sits on, repeated at its own size so the tooth stays
   crisp at every width; the dark scheme has none. */
.md-container {
  background-image: var(--pyntpot-paper-image);
  background-size: 512px 512px;
  background-repeat: repeat;
}

/* The header is a painted wash, not a flat bar: the band repeats sideways at its own aspect
   over the glazed water colour, which shows alone on the dark scheme. */
.md-header {
  background-color: var(--md-primary-fg-color);
  background-image: var(--pyntpot-header-image);
  background-size: auto 100%;
  background-repeat: repeat-x;
}

/* Body text in a book serif; the hand is for the headings, code keeps the theme's monospace.
   The serif sits a little larger than the theme's sans, which it would otherwise undersize. */
.md-typeset {
  font-size: 0.85rem;
  line-height: 1.7;
}

.md-typeset code,
.md-typeset pre {
  font-size: 0.85em;
}

/* Display headings and the site name: the hand. */
.md-typeset h1,
.md-typeset h2,
.md-header__title .md-ellipsis:first-child {
  font-family: var(--pyntpot-display);
  font-weight: 400;
  letter-spacing: 0.01em;
}

.md-typeset h1 {
  color: var(--md-default-fg-color);
  font-size: 2.6em;
}

.md-typeset h2 {
  font-size: 1.9em;
}

/* The brush-stroke rule: under a page title and as a thematic break. It keeps its own aspect,
   starting at the left, and multiplies, so only the stroke shows on the paper. The dark scheme
   has a plain line instead. */
.md-typeset h1::after,
.md-typeset hr {
  content: "";
  display: block;
  height: 1.5rem;
  margin: -0.3rem 0 0.8rem;
  border: 0;
  background: var(--pyntpot-rule-image) left center / auto 100% no-repeat;
  mix-blend-mode: multiply;
}

.md-typeset hr {
  margin: 1.2rem 0;
}

[data-md-color-scheme="slate"] .md-typeset h1::after,
[data-md-color-scheme="slate"] .md-typeset hr {
  height: 0;
  margin: 0.4rem 0 1.2rem;
  border-top: 2px solid var(--pyntpot-water);
  opacity: 0.6;
  mix-blend-mode: normal;
}

/* The painted figures sit on the page like prints. */
.md-typeset img {
  border-radius: 2px;
}
""")


def _hex(colour: np.ndarray) -> str:
    """Return a colour of three floats in 0 to 1 as `#rrggbb`."""
    r, g, b = (round(float(c) * 255) for c in colour)
    return f"#{r:02x}{g:02x}{b:02x}"


def _rgba(colour: np.ndarray, alpha: float) -> str:
    """Return a colour of three floats in 0 to 1 as a CSS `rgb()` with an alpha."""
    r, g, b = (round(float(c) * 255) for c in colour)
    return f"rgb({r} {g} {b} / {alpha})"


def _paper() -> PaperStyle:
    """Return the default paper without its worn border, vignette or foxing."""
    return PaperStyle(paper_worn=0.0, paper_vignette=0.0, paper_foxing=0.0)


def _seamless(pixels: np.ndarray) -> np.ndarray:
    """Return `pixels` made to tile: each axis crossfaded with itself rolled by half, the seam at the weight's zero.

    The weights are a sine and a cosine, so the noise keeps its spread across the blend.
    """
    for axis in (0, 1):
        length = pixels.shape[axis]
        t = (np.arange(length) + 0.5) / length
        weight = np.sin(np.pi * t)
        shape = [1, 1, 1]
        shape[axis] = length
        near = np.sin(np.pi / 2 * weight).reshape(shape)
        far = np.cos(np.pi / 2 * weight).reshape(shape)
        mean = pixels.mean(axis=axis, keepdims=True)
        rolled = np.roll(pixels, length // 2, axis=axis)
        pixels = mean + (pixels - mean) * near + (rolled - mean) * far
    return np.clip(pixels, 0.0, 1.0)


def _paint_paper(width: int) -> np.ndarray:
    """Paint the page's paper `width` pixels square, so that it tiles."""
    sheet = Sheet(width, width, GRAN_PX, SEED)
    plate = paper_plate(sheet, Canvas(0, 0, width, width, width, width), _paper(), width)
    return _seamless(plate)


def _paint_rule(width: int) -> np.ndarray:
    """Paint one wavering stroke of a river brush on pure white, touched down and tapering out, `width` pixels wide."""
    height = max(8, round(width * RULE_ASPECT))
    sheet = Sheet(height, width, GRAN_PX, SEED)
    x = np.linspace(0.02 * width, 0.98 * width, 240)
    y = height / 2 + 0.16 * height * np.sin(2 * np.pi * 1.5 * x / width)
    brush, ink_hex = brush_from_id(RULE_BRUSH, RULE_BRUSH_SHARE * height, 1.0, BrushStyle())
    t = np.linspace(0.0, 1.0, 64)
    taper = np.minimum(np.minimum(t / 0.05, (1.0 - t) / 0.4), 1.0) ** 0.7 * 0.8 + 0.2
    acc = np.zeros((height, width), np.float32)
    stamp(acc, np.column_stack([x, y]), brush, np.random.default_rng(SEED), wprof=taper)
    white = np.ones((height, width, 3))
    return composite([(ink_density(acc, brush, sheet), rgb(ink_hex))], white, _paper())


def _smooth_noise(shape: tuple[int, int], cell: float, rng: np.random.Generator) -> np.ndarray:
    """Return unit-spread noise of `shape` with features about `cell` pixels across, by low-passing white noise."""
    spectrum = np.fft.rfft2(rng.standard_normal(shape))
    fy = np.fft.fftfreq(shape[0])[:, None]
    fx = np.fft.rfftfreq(shape[1])[None, :]
    spectrum *= np.exp(-((fx * cell) ** 2 + (fy * cell) ** 2) * 2.0)
    noise = np.fft.irfft2(spectrum, shape)
    return noise / noise.std()


def _paint_header(width: int) -> np.ndarray:
    """Paint the header band, `width` pixels wide: a water wash, uneven along its length and pooled along its lower edge."""
    height = max(8, round(width * HEADER_ASPECT))
    rng = np.random.default_rng(SEED)
    low, high = HEADER_GLAZE
    along = 0.5 + 0.5 * np.tanh(1.4 * _smooth_noise((height, width), 0.12 * width, rng))
    grain = _smooth_noise((height, width), GRAN_PX, rng)
    rows = np.linspace(0.0, 1.0, height)[:, None]
    pool = 0.25 * np.clip((rows - 0.8) / 0.2, 0.0, 1.0) ** 2
    glaze = low + (high - low) * along + 0.12 * grain + pool
    sheet = Sheet(height, width, GRAN_PX, SEED)
    paper = paper_plate(sheet, Canvas(0, 0, width, height, width, height), _paper(), width)
    return np.clip(paper * rgb(PIGMENTS["water"]) ** glaze[..., None], 0.0, 1.0)


def stylesheet() -> str:
    """Return the site's stylesheet, its colours drawn from `PIGMENTS`."""
    paper = rgb(_paper().paper_hex)
    relief = rgb(PIGMENTS["relief"])
    ink, night = relief * INK_SHARE, relief * DARK_SHARE
    lines = []
    for key, value in PIGMENTS.items():
        lines.append(f"  --pyntpot-{key}: {value};")
        lines.append(f"  --pyntpot-glaze-{key}: {_hex(rgb(value) ** GLAZES)};")
    return STYLESHEET.substitute(
        glazes=GLAZES,
        pigments="\n".join(lines),
        paper=_hex(paper),
        ink=_hex(ink),
        night=_hex(night),
        ink_light=_rgba(ink, 0.7),
        ink_lighter=_rgba(ink, 0.32),
        ink_lightest=_rgba(ink, 0.12),
        paper_light=_rgba(paper, 0.75),
        paper_lighter=_rgba(paper, 0.32),
        paper_lightest=_rgba(paper, 0.12),
        code_light=_hex(0.85 * paper + 0.15 * relief),
        code_dark=_hex(0.9 * night + 0.1 * paper),
    )


def main(out_dir: Path, figure: str = "paper", size: int | None = None) -> Path:
    """Paint or write one figure of the site's theme into `out_dir` and return its path.

    Args:
        out_dir: The directory the file is written into.
        figure: `"paper"`, `"rule"`, `"header"` or `"palette"`.
        size: The picture's width in pixels; ignored by `"palette"`.

    Returns:
        The path of `paper.png`, `rule.png`, `header.png` or, for `"palette"`, `pyntpot.css`.

    Raises:
        ValueError: When `figure` is not one of `FIGURES`.
    """
    if figure not in FIGURES:
        raise ValueError(f"figure must be one of {FIGURES}, not {figure!r}")
    out_dir.mkdir(parents=True, exist_ok=True)
    if figure == "palette":
        path = out_dir / "pyntpot.css"
        path.write_text(stylesheet())
    else:
        width = size or WIDTH[figure]
        pixels = {"paper": _paint_paper, "rule": _paint_rule, "header": _paint_header}[figure](
            width
        )
        path = out_dir / f"{figure}.png"
        save_image(pixels, path, seed=SEED)
    logger.info("wrote %s", path)
    return path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Paint or write one figure of the site's theme.")
    parser.add_argument("out_dir", type=Path, help="the directory the file is written into")
    parser.add_argument("--figure", choices=FIGURES, default="paper", help="the figure to write")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)
    main(args.out_dir, figure=args.figure)
