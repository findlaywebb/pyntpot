"""The docs site's own chrome, painted and written by the engine it documents.

Three figures, chosen by `figure=`. `"paper"` paints the cream rag the light scheme's page
sits on: the default paper without its worn border, vignette or foxing, so one picture can
cover any window. `"rule"` paints one wavering stroke of a wet river brush across white paper,
the rule under a page title; the site lays it on the page by multiplying, so only the stroke
shows. `"palette"` writes `pyntpot.css`, the site's stylesheet, with the colours drawn from
`PIGMENTS` as CSS custom properties: each pigment as it is, and the pigment glazed four
times for text and the header on the light scheme. Its contrast is checked by
`tests/examples/test_site_theme.py`.

Public names it uses: from `pyntpot.ink`, `Sheet`, `Canvas`, `PaperStyle`, `BrushStyle`,
`PIGMENTS`, `paper_plate`, `brush_from_id`, `stamp`, `ink_density`, `composite`, `rgb` and
`save_image`.

`main` writes one file per call. For the two pictures it returns the PNG's path; for
`"palette"` it returns the stylesheet's path, which is text, not an image, and is not in the
image registry. Every seed is fixed, so one run writes the same files. It paints no map and
reads no file. Patrick Hand, the face the stylesheet loads for display headings, is the
vendored font, copied to `docs/assets/` with its licence.

Run it with `uv run python examples/site_theme.py out/ --figure rule`.
"""

import argparse
import logging
from dataclasses import replace
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
FIGURES = ("paper", "rule", "palette")
#: The picture widths, in pixels, when `size=` is not given.
WIDTH = {"paper": 960, "rule": 960}
#: The size of the paper's granulation noise, in pixels.
GRAN_PX = 5.0
#: The seed of the paper's noise, the bristles and the dither the file is written with.
SEED = 11
#: The paper's aspect: a window is wider than it is tall.
PAPER_ASPECT = 9 / 16
#: The rule's height as a share of its width.
RULE_ASPECT = 1 / 24
#: How many times a pigment is glazed to make the text and header colours of the light scheme.
GLAZES = 4
#: How much of the `relief` pigment's colour the dark page and the light scheme's ink keep.
DARK_SHARE = 0.14
INK_SHARE = 0.16
#: The brush id and width of the rule's stroke.
RULE_BRUSH = "RIV1-a"

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
}

/* The paper the light scheme's page sits on; the dark scheme has none. */
.md-container {
  background-image: var(--pyntpot-paper-image);
  background-size: cover;
  background-attachment: fixed;
}

/* Display headings and the site name: the hand. Body and code keep the theme's faces. */
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

/* The brush-stroke rule: under a page title and as a thematic break. It multiplies, so only
   the stroke shows on the paper. The dark scheme has a plain line instead. */
.md-typeset h1::after,
.md-typeset hr {
  content: "";
  display: block;
  height: 0.9rem;
  margin: 0.2rem 0 1.2rem;
  border: 0;
  background: var(--pyntpot-rule-image) left center / 100% 100% no-repeat;
  mix-blend-mode: multiply;
}

.md-typeset hr {
  margin: 1.6rem 0;
}

[data-md-color-scheme="slate"] .md-typeset h1::after,
[data-md-color-scheme="slate"] .md-typeset hr {
  height: 0;
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
    r, g, b = (int(round(float(c) * 255)) for c in colour)
    return f"#{r:02x}{g:02x}{b:02x}"


def _rgba(colour: np.ndarray, alpha: float) -> str:
    """Return a colour of three floats in 0 to 1 as a CSS `rgb()` with an alpha."""
    r, g, b = (int(round(float(c) * 255)) for c in colour)
    return f"rgb({r} {g} {b} / {alpha})"


def _paper(white: bool = False) -> PaperStyle:
    """Return the default paper without its worn border, vignette or foxing; white paper for the rule, which the page multiplies."""
    plain = PaperStyle(paper_worn=0.0, paper_vignette=0.0, paper_foxing=0.0)
    return replace(plain, paper_hex="#ffffff") if white else plain


def _paint_paper(width: int) -> np.ndarray:
    """Paint the page's paper `width` pixels wide."""
    height = max(1, round(width * PAPER_ASPECT))
    sheet = Sheet(height, width, GRAN_PX, SEED)
    return paper_plate(sheet, Canvas(0, 0, width, height, width, height), _paper(), width)


def _paint_rule(width: int) -> np.ndarray:
    """Paint one wavering stroke of a river brush across paper `width` pixels wide."""
    height = max(8, round(width * RULE_ASPECT))
    sheet = Sheet(height, width, GRAN_PX, SEED)
    paper = paper_plate(
        sheet, Canvas(0, 0, width, height, width, height), _paper(white=True), width
    )
    x = np.linspace(0.02 * width, 0.98 * width, 240)
    y = height / 2 + 0.16 * height * np.sin(2 * np.pi * 1.5 * x / width)
    brush, ink_hex = brush_from_id(RULE_BRUSH, 0.3 * height, 1.0, BrushStyle())
    acc = np.zeros((height, width), np.float32)
    stamp(acc, np.column_stack([x, y]), brush, np.random.default_rng(SEED))
    return composite([(ink_density(acc, brush, sheet), rgb(ink_hex))], paper, _paper(white=True))


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
        figure: `"paper"`, `"rule"` or `"palette"`.
        size: The picture's width in pixels; ignored by `"palette"`.

    Returns:
        The path of `paper.png`, `rule.png` or, for `"palette"`, `pyntpot.css`.

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
        pixels = _paint_paper(width) if figure == "paper" else _paint_rule(width)
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
