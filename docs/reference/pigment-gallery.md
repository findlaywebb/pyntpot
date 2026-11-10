# Pigment gallery

Every pigment of the registry painted, so a colour can be chosen by eye and not by hex. `PIGMENT_REGISTRY` from `pyntpot.ink` holds 25 pigments, the fifteen a map names by role and the ten a painter names by tube; this page shows each as three washes, then how six pairs glaze and what the bundled palettes name. For the tables of every key, see [Pigments](pigments.md).

Every figure is painted on `paper_plate` paper. A wash is the pigment at a density of 0.3, 0.6 or 0.9, glazed by Kubelka-Munk at the pigment's own transparency, so a pigment that covers shows a flatter, duller wash than one that stains. The transparency, and the Colour Index code where the registry records one, are lettered beside each row and repeated in its table. There is no ink bar: the three strengths, glazed, are how the figures show transparency.

## Map pigments

![The fifteen map pigments, one row each: farmland, meadow, orchard, scrub, heath, sand, rock, wetland, built, works, wood, pale, water, relief and rim. Each row holds three washes of the pigment, light to deep from left to right, with its transparency lettered at the right. The land covers are pale greens, tans and greys; wood and water are the deepest.](../images/reference/pigment-gallery-roles.webp)

*Painted by `examples/pigment_gallery.py` (`figure="roles"`), seed 7.* The labels read 0.3, 0.6 and 0.9 across, and the pigment's key down. The right margin letters its transparency. The map's roles are not paint from a tube, so they have no Colour Index code.

| Row | Name | Colour | Transparency | Colour Index |
| --- | --- | --- | --- | --- |
| 1 | `farmland` | `#dfe0b0` | 0.10 | none |
| 2 | `meadow` | `#cfdfae` | 0.09 | none |
| 3 | `orchard` | `#d5dda2` | 0.09 | none |
| 4 | `scrub` | `#c9d5a4` | 0.08 | none |
| 5 | `heath` | `#e0cda2` | 0.14 | none |
| 6 | `sand` | `#ecdfbe` | 0.16 | none |
| 7 | `rock` | `#dcd6c6` | 0.22 | none |
| 8 | `wetland` | `#bfd2cd` | 0.08 | none |
| 9 | `built` | `#ddd3c3` | 0.26 | none |
| 10 | `works` | `#d2cbc0` | 0.28 | none |
| 11 | `wood` | `#a8c286` | 0.05 | none |
| 12 | `pale` | `#d5e0b4` | 0.12 | none |
| 13 | `water` | `#9ec4de` | 0.04 | none |
| 14 | `relief` | `#c9bda4` | 0.30 | none |
| 15 | `rim` | `#c2ad91` | 0.18 | none |

## Painter's pigments

![The ten tube pigments, one row each: ultramarine, cerulean, burnt sienna, raw sienna, yellow ochre, sap green, indigo, perylene maroon, quinacridone rose and Payne's grey. Each row holds three washes, light to deep from left to right, with the transparency and the Colour Index code lettered at the right where there is one.](../images/reference/pigment-gallery-painters.webp)

*Painted by `examples/pigment_gallery.py` (`figure="painters"`), seed 7.* The labels read 0.3, 0.6 and 0.9 across, and the pigment's key down. The right margin letters the transparency, then the Colour Index code; `sap_green`, `indigo` and `paynes_grey` have none.

| Row | Name | Colour | Transparency | Colour Index |
| --- | --- | --- | --- | --- |
| 1 | `ultramarine` | `#2b3d8f` | 0.06 | `PB29` |
| 2 | `cerulean` | `#2a7ab0` | 0.22 | `PB35` |
| 3 | `burnt_sienna` | `#8a3b1c` | 0.20 | `PBr7` |
| 4 | `raw_sienna` | `#b8692a` | 0.18 | `PBr7` |
| 5 | `yellow_ochre` | `#c99a3a` | 0.24 | `PY43` |
| 6 | `sap_green` | `#3f6b2a` | 0.07 | none |
| 7 | `indigo` | `#2c3346` | 0.05 | none |
| 8 | `perylene_maroon` | `#5a1f27` | 0.04 | `PR179` |
| 9 | `quinacridone_rose` | `#b8215e` | 0.05 | `PV19` |
| 10 | `paynes_grey` | `#3b4452` | 0.10 | none |

## Glaze pairs

![Eighteen pairs of overlapping watercolour discs in three rows of six. Each column is one pair, named on two lines above it: cerulean with yellow ochre, cerulean with burnt sienna, ultramarine with yellow ochre, yellow ochre with indigo, yellow ochre with perylene maroon, and cerulean with quinacridone rose. The top row multiplies the two; the middle row glazes the first over the second and the bottom row the second over the first, and the overlap is plainly a different colour in each row: the pigment laid on top shows more of itself.](../images/reference/pigment-gallery-glazes.webp)

*Painted by `examples/pigment_gallery.py` (`figure="glazes"`), seed 7.* Each column is one pair, the first pigment named on the upper line and the second under it. The rows read multiply, A over B and B over A down, where A is the first of the pair. Multiplying is the same in either order. Glazing is not: the pigment laid on top shows more of itself in the overlap, and these six pairs are chosen because the overlap of A over B is clearly a different colour from B over A (measured, a mean CIE76 colour difference of 9 to 17 between the two rows, where about 3 is the least the eye sees). Multiplying also differs from glazing, by 7 to 17.

| Column | First | Second |
| --- | --- | --- |
| 1 | `cerulean` | `yellow_ochre` |
| 2 | `cerulean` | `burnt_sienna` |
| 3 | `ultramarine` | `yellow_ochre` |
| 4 | `yellow_ochre` | `indigo` |
| 5 | `yellow_ochre` | `perylene_maroon` |
| 6 | `cerulean` | `quinacridone_rose` |

## Palettes

![The plain palette: ten swatches in two rows of five. Each is a wash with its alias lettered above and the pigment it names below: blue is ultramarine, sky cerulean, green sap green, brown burnt sienna, orange raw sienna, ochre yellow ochre, red quinacridone rose, maroon perylene maroon, navy indigo and grey Payne's grey.](../images/reference/palettes.webp)

*Painted by `examples/pigment_gallery.py` (`figure="palettes"`), seed 7.* A palette is a named set of aliases; a theme that sets `palette: plain` writes `sky` where it would write `cerulean`. `Palette.names()` lists the bundled palettes and `Palette.named(name).pigments` maps each alias to the pigment it stands for. Each swatch is a 0.6 wash glazed at that pigment's transparency; an alias bound to a bare hex has no transparency of its own and glazes at `PaperStyle.km_transparency`.

| Palette | Alias | Pigment |
| --- | --- | --- |
| `plain` | `blue` | `ultramarine` |
| `plain` | `sky` | `cerulean` |
| `plain` | `green` | `sap_green` |
| `plain` | `brown` | `burnt_sienna` |
| `plain` | `orange` | `raw_sienna` |
| `plain` | `ochre` | `yellow_ochre` |
| `plain` | `red` | `quinacridone_rose` |
| `plain` | `maroon` | `perylene_maroon` |
| `plain` | `navy` | `indigo` |
| `plain` | `grey` | `paynes_grey` |
