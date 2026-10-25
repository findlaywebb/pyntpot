<h1 align="center">
  <img src="https://raw.githubusercontent.com/findlaywebb/pyntpot/main/docs/images/word.webp" alt="pyntpot, lettered by hand in dark ink on a washed blue disc with a green wash overlapping it" width="360">
</h1>

Hand-drawn watercolour and pen-and-ink painting for Python, with route maps.

![A hand-painted map of Ambleside and Rydal Water: tawny fell and green wood washes, two blue lakes, the river Rothay in dark blue, and a maroon route looping from Ambleside out to Loughrigg Terrace and back, with the names written by hand](https://raw.githubusercontent.com/findlaywebb/pyntpot/main/docs/images/hero.webp)

*Painted by `examples/place_card.py`: the Ambleside card in its showcase theme, from a fell walk that follows public paths.*

![Five washes of hill in blue-grey, grey-brown and green recede above a streaked blue lake that mirrors them; a small wooded island sits on the water and "Derwentwater" is written below](https://raw.githubusercontent.com/findlaywebb/pyntpot/main/docs/images/painting-with-python/derwentwater.webp)

*Painted by `examples/derwentwater.py`: no map, only the same paper, washes and nib.*

Lay a wash, pull a brush, letter a name.

[![PyPI](https://img.shields.io/pypi/v/pyntpot)](https://pypi.org/project/pyntpot/)
[![Python](https://img.shields.io/pypi/pyversions/pyntpot)](https://pypi.org/project/pyntpot/)
[![CI](https://github.com/findlaywebb/pyntpot/actions/workflows/ci.yml/badge.svg)](https://github.com/findlaywebb/pyntpot/actions/workflows/ci.yml)
[![Licence](https://img.shields.io/pypi/l/pyntpot)](https://github.com/findlaywebb/pyntpot/blob/main/LICENSE)
[![CodSpeed](https://img.shields.io/endpoint?url=https://codspeed.io/badge.json)](https://codspeed.io/findlaywebb/pyntpot)

## What it is

pyntpot paints watercolour and pen-and-ink pictures in Python the way a painter works.
It stretches paper with tooth and foxing, lays washes that pool at their
edges and settle into the grain, pulls brushes that run dry and reload, glazes pigments
over one another, and letters names with a nib. It is a painting engine (`pyntpot.ink`),
hand lettering on top of it (`pyntpot.letters`), and route maps on top of both
(`pyntpot.maps`), the first thing it is used for.

It paints; it does not edit photographs or put a style over an existing picture, and it
is not a web map. A map needs a GPX track and, on the first run, a network connection
to the public map and elevation servers. The engine and the lettering need neither.

- Every image reproduces from its seed: a painting that looks accidental comes out the
  same, byte for byte, from the same seed.
- Every technique cites its source, in [References](https://github.com/findlaywebb/pyntpot/blob/main/docs/explanation/references.md).
- The data providers are asked politely, within their limits, and credited on the card.

## Gallery

Each picture is one rung of the tutorial, and links to its page.

| | | | |
| --- | --- | --- | --- |
| [![A piece of cream paper with a soft grain, a narrow brown edge that wanders a little, and a few small rust specks of foxing](https://raw.githubusercontent.com/findlaywebb/pyntpot/main/docs/images/gallery/paper.webp)](https://github.com/findlaywebb/pyntpot/blob/main/docs/tutorials/paint-a-watercolour.md#stretch-the-paper)<br>`examples/paper.py` | [![A soft blue disc on cream paper, its edge a little darker than its middle](https://raw.githubusercontent.com/findlaywebb/pyntpot/main/docs/images/gallery/wash.webp)](https://github.com/findlaywebb/pyntpot/blob/main/docs/tutorials/paint-a-watercolour.md#lay-a-wash)<br>`examples/wash.py` | [![Two strokes on cream paper: a wet blue one above a drier olive one that breaks into flecks](https://raw.githubusercontent.com/findlaywebb/pyntpot/main/docs/images/gallery/brush-stroke.webp)](https://github.com/findlaywebb/pyntpot/blob/main/docs/tutorials/paint-a-watercolour.md#pull-a-brush)<br>`examples/brush_stroke.py` | [![Two panels, each with a blue disc overlapping a yellow-ochre one, the overlap a different green in each](https://raw.githubusercontent.com/findlaywebb/pyntpot/main/docs/images/gallery/pigments.webp)](https://github.com/findlaywebb/pyntpot/blob/main/docs/tutorials/paint-a-watercolour.md#mix-two-pigments)<br>`examples/pigments.py` |
| [![A dark ink spiral of three turns drawn with a pen nib](https://raw.githubusercontent.com/findlaywebb/pyntpot/main/docs/images/gallery/nib-line.webp)](https://github.com/findlaywebb/pyntpot/blob/main/docs/tutorials/paint-a-watercolour.md#take-up-the-pen)<br>`examples/nib_line.py` | [![The name Ambleside written by hand in dark ink along a gentle wave](https://raw.githubusercontent.com/findlaywebb/pyntpot/main/docs/images/gallery/lettering.webp)](https://github.com/findlaywebb/pyntpot/blob/main/docs/tutorials/paint-a-watercolour.md#letter-a-name)<br>`examples/lettering.py` | [![A blue wash disc with the name Keswick written by hand across it and a wet sienna brush stroke curving under it](https://raw.githubusercontent.com/findlaywebb/pyntpot/main/docs/images/gallery/composition.webp)](https://github.com/findlaywebb/pyntpot/blob/main/docs/tutorials/paint-a-watercolour.md#compose-the-painting)<br>`examples/composition.py` | [![A hand-painted map of Ambleside and Rydal Water with a pink route looping out to Loughrigg Terrace](https://raw.githubusercontent.com/findlaywebb/pyntpot/main/docs/images/gallery/route-map.webp)](https://github.com/findlaywebb/pyntpot/blob/main/docs/tutorials/first-map.md)<br>`examples/route_map.py` |

More pictures, each with its script, are in the [gallery](https://github.com/findlaywebb/pyntpot/blob/main/docs/gallery.md).

## Install

```bash
pip install pyntpot
```

or, in a project managed by uv:

```bash
uv add pyntpot
```

pyntpot needs Python 3.13 or later.

## Quick start

Paint a map from a GPX file with the command line, in three lines:

```bash
pyntpot map route.gpx -o map.png \
  --cache cache/ \
  --contact you@example.org
```

`--contact` is how the operators of the public servers can reach you. The
[command line how-to](https://github.com/findlaywebb/pyntpot/blob/main/docs/how-to/map-from-the-command-line.md) shows the output.

Or paint with the engine in Python, with no network. This lays one wash of water over
the paper. The block is `examples/wash.py` from its imports to the end of `main`, and the
[tutorial](https://github.com/findlaywebb/pyntpot/blob/main/docs/tutorials/paint-a-watercolour.md) explains each line:

<!-- from examples/wash.py -->
```python
import logging
from pathlib import Path

import numpy as np

from pyntpot.ink import (
    PIGMENTS,
    Canvas,
    PaperStyle,
    Sheet,
    composite,
    paper_plate,
    rgb,
    save_image,
    wash,
)

logger = logging.getLogger(__name__)

#: The image's width and height, in pixels.
W, H = 360, 240
#: The size of the paper's granulation noise, in pixels.
GRAN_PX = 8.0
#: The seed of the paper's noise and of the dither the file is written with.
SEED = 11


def main(out_dir: Path) -> Path:
    """Lay a disc of water over the paper, write it into `out_dir` as `wash.png` and return that path."""
    sheet = Sheet(H, W, GRAN_PX, SEED)
    canvas = Canvas(0, 0, W, H, W, H)
    paper = paper_plate(sheet, canvas, PaperStyle(), W)

    yy, xx = np.mgrid[0:H, 0:W]
    disc = ((xx - W / 2) ** 2 + (yy - H / 2) ** 2 <= (0.3 * min(W, H)) ** 2).astype(np.float32)
    density = wash(disc, sheet, 0.6, 0.3)

    out = composite([(density, rgb(PIGMENTS["water"]))], paper, PaperStyle())
    path = out_dir / "wash.png"
    save_image(out, path, seed=SEED)
    logger.info("wrote %s", path)
    return path
```

Then call it. It writes `out/wash.png`:

```python
main(Path("out"))
```

![A soft blue disc on cream paper, its edge a little darker than its middle and its body lightly granular](https://raw.githubusercontent.com/findlaywebb/pyntpot/main/docs/images/tutorials/wash.webp)

*Painted by `examples/wash.py`, seed 11.*

## Crediting the data

A map shows OpenStreetMap data, which is under the Open Database Licence, and
elevations from NASA SRTM, served by OpenTopoData. pyntpot letters the credit on the
card for you, and a map you publish needs it. Turning it off moves the duty to you. See
[Credit the map data](https://github.com/findlaywebb/pyntpot/blob/main/docs/how-to/credit-the-map-data.md) and the
[data policy](https://github.com/findlaywebb/pyntpot/blob/main/docs/explanation/data-policy.md).

## Documentation

- [Start here](https://github.com/findlaywebb/pyntpot/blob/main/docs/index.md): the landing page.
- [Tutorials](https://github.com/findlaywebb/pyntpot/blob/main/docs/tutorials/index.md): paint a watercolour, then a first map, then pictures that are not maps.
- [How-to guides](https://github.com/findlaywebb/pyntpot/blob/main/docs/how-to/index.md): write a theme, work offline, credit the data.
- [Reference](https://github.com/findlaywebb/pyntpot/blob/main/docs/reference/index.md): the command line, every style field, the pigment and brush sheets.
- [Explanation](https://github.com/findlaywebb/pyntpot/blob/main/docs/explanation/index.md): how the wash works, the hand and the nib, the data policy.
- [Gallery](https://github.com/findlaywebb/pyntpot/blob/main/docs/gallery.md): every picture, with its script.
- [Changelog](https://github.com/findlaywebb/pyntpot/blob/main/CHANGELOG.md) and [contributing](https://github.com/findlaywebb/pyntpot/blob/main/CONTRIBUTING.md).

## Status

pyntpot is on 0.x. A minor release may break the API, and a patch release never does.
Painted pixels may change between minor releases, so pin a version if you need the
same picture later.

## Licence

MIT. The vendored Patrick Hand typeface is under the SIL Open Font License 1.1; see
[`LICENSE-FONT`](https://github.com/findlaywebb/pyntpot/blob/main/LICENSE-FONT).
