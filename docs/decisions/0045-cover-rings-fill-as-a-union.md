# 0045 — Cover rings fill as a union: the sixth golden regeneration

Status: accepted

## Context

On the Oxford card Christ Church Meadow (relation 1102976, `leisure=park`, classed
`meadow`) was bare paper, GitHub issue #45. The ring was not lost on its way to the
painter: `polygon_rings` joins it into one closed ring of 174 points, the clip keeps all
174, the simplify leaves 68, and the ring is in `Layers.cover["meadow"]`. Filled alone it
covers about 101,000 render pixels; filled with the rest of the class, the class covered
only about 43,000 of them.

The cause is in `maps/painter/cover.py`, `_label`. A class's rings are filled together by
`fill_cov`, which uses the nonzero winding rule, and the rings come wound as they were
surveyed. The park's ring winds clockwise; inside it way 3662825 (`landuse=meadow`, the
grazed meadow itself, about 18 ha) winds anticlockwise. Their windings cancel, so the nonzero fill
cut the meadow out of the park as a hole, and the theme could not reach it: the pixels were
never labelled `meadow`. The vector layers were already right, because `svg_path.rings_path`
orients each ring before it writes the path.

## Decision

- `_label` winds every ring of a class anticlockwise (`maps.rings.orient`) before the
  nonzero fill, so a class is the union of its rings. The holes of the land cover are not
  read at all (`cover_rings` keeps outer rings only), so no ring of a class is meant to cut
  one.
- The rings are wound after `deform_rings`, not in `cover_rings`. Winding them in the
  basemap reverses about half of them, which moves the base hash and changes the order the
  shared deform generator walks each ring's segments, so every card's outlines would move
  for no reason. Wound in the painter, the basemap, the manifest hash and every deformed
  outline stay as they were; only the fill changes.
- Pinned by `tests/unit/maps/painter/test_cover.py`: a lawn wound against the park around
  it is labelled with the park's class.

## Golden regeneration (the sixth)

Process as ADR 0036. The tolerance bound is not changed, no gate is loosened, and the hash
input does not change; the manifest hash does not move (`340a7f6e260ee1e2-d9c56c0811177b0f`).

### What the fix labels

The label grid (one class per pixel, before any wash) was compared with the old fill on two
fixtures. Almost every changed pixel is a hole filled: bare paper becoming a class.

| Fixture | Pixels | Label changed | Bare to a class | Biggest gain |
|---|---|---|---|---|
| lynmouth (default style) | 2,622,600 | 7,196 | 7,080 | meadow 3,115 |
| oxford (`oxford.toml`) | 2,892,600 | 100,741 | 95,074 | meadow 85,225 |

### Lynmouth compare, against the committed goldens

```
paper.webp: identical yes, differing fraction 0.000000
wash.webp: identical no, differing fraction 0.195877
pen.webp: identical yes, differing fraction 0.000000
labels-centreline.webp: identical no, differing fraction 0.029720
map.png: identical no, differing fraction 0.186743
manifest hash: 340a7f6e260ee1e2-d9c56c0811177b0f here, 340a7f6e260ee1e2-d9c56c0811177b0f in the goldens
```

`labels.txt` is unchanged, and so is `PINNED_LABELS`. The wash moves far past the 0.27% of
pixels whose label changed because of the blooms (ADR 0006, step 3, family b): a wash's
bloom count comes from its own area and every class washes from the one shared bloom
generator, so a class that gains area desynchronises every wash after it. With blooms off
(`wash.blooms = False`) the same two fills differ on 0.010581 of the wash: the filled holes
and the rims and wet edges round them. The labels-centreline plate follows the wash through
the dark grid. `GOLDEN_HASH` is not re-pinned.

The goldens were then regenerated in place with `make_golden.py` and compared with the paint
they came from (`--require-identical all --require-hash equal`): every output byte-identical.

### Docs images

Every docs image and master was repainted with `make_docs_images.py`. The 15 that show a map
moved, and only they; every other entry is byte-identical. Master differing fractions:

| Image | Master | Image | Master |
|---|---|---|---|
| `places/skye.webp` | 0.383801 | `how-to/command-line.webp` | 0.189562 |
| `places/y-fenni.webp` | 0.270483 | `places/oxford.webp` | 0.158995 |
| `gallery/route-map.webp` | 0.137403 | `places/ambleside.webp` | 0.137403 |
| `hero.webp` | 0.121321 | `places/yr-wyddfa.webp` | 0.075773 |
| `social-preview.jpg` | 0.070139 | `map-styles/bold.webp` | 0.042641 |
| `map-styles/winter.webp` | 0.039888 | `how-to/route-ink-grid.webp` | 0.037541 |
| `tutorials/route-map.webp` | 0.036988 | `how-to/route-ink.webp` | 0.036915 |
| `map-styles/sepia.webp` | 0.036257 | | |

Looked at side by side: on Oxford, Christ Church Meadow inside the loop is now meadow green,
and smaller holes elsewhere fill; on Y Fenni the green block north of the loop loses the bare
holes it had; on Skye the land is the same and the sea's blooms sit in different places. The
lettering, the route, the roads and the rivers are unchanged. The place pins and the
map-styles means did not move.

## Consequences

- A class's rings fill as their union whatever way each was surveyed, on the raster card as
  on the vector layers.
- A further regeneration needs its own ADR.

The machine the goldens were regenerated on: the agent's Linux container, Python 3.13, with
the parity stack at its pins. Every docs image that does not show a map repainted
byte-identical there, as did the Lynmouth paper and pen plates.
