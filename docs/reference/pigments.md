# Pigments

A pigment is a colour a wash or a mark lays, named by its key. This page lists every key of `PIGMENTS` and `TRANSPARENCY` from `pyntpot.ink`. The same pigments are in `PIGMENT_REGISTRY`, which also holds each one's Colour Index code.

![The fifteen map pigments, one row each: farmland, meadow, orchard, scrub, heath, sand, rock, wetland, built, works, wood, pale, water, relief and rim. Each row holds three washes of the pigment, light to deep from left to right, with its transparency lettered at the right. The land covers are pale greens, tans and greys; wood and water are the deepest.](../images/reference/pigment-gallery-roles.webp)

*Painted by `examples/pigment_gallery.py` (`figure="roles"`), seed 7.* The labels read 0.3, 0.6 and 0.9 across, and the pigment's key down. Each row is a pigment of the table below, in its order, as three washes glazed by Kubelka-Munk at the pigment's own transparency. The [pigment gallery](pigment-gallery.md) shows the painter's pigments, how pairs glaze and the bundled palettes the same way.

## Entries

`PIGMENTS` maps each key to the colour a full-strength wash of that pigment transmits, as `#rrggbb`. `TRANSPARENCY` maps each key to what the pigment shows over black as a share of what it shows over white. Near 0 is a staining glaze that lets the layer under it through; near 1 is a covering body colour. Only Kubelka-Munk glazing (`PaperStyle.km_glazing`) reads the transparency; multiply ignores it.

| Row | Key | Colour | Transparency | Colour Index |
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

## Where the keys are used

- The cover classes `farmland`, `meadow`, `orchard`, `scrub`, `heath`, `sand`, `rock`, `wetland`, `built`, `works` and `wood` are the land cover classes the basemap paints.
- `pale` is the single wash laid instead of the classes when `land_cover` is off.
- `water`, `relief` and `rim` colour the water, the relief and the pooled edge inside a wash's tear.
- `CoverStyle.pigments` holds these keys, each a colour with its transparency, a `CoverPigment`; a theme writes an entry as a reference or as `{pigment, transparency}`. See [Style fields](style-fields.md).

## Colour Index

The Colour Index column is the pigment's Colour Index generic code, such as `PB29` for ultramarine, or `none` when the pigment has none. It is metadata: it names no lookup key and changes no colour. The map's fifteen roles are not paint from a tube, so they have no code. A pigment of your own can carry one; see [Write a theme](../how-to/write-a-theme.md).

## What the table does not hold

An unnamed pigment takes `PaperStyle.km_transparency`. The inks are not pigments: a mark's colour comes from its brush id. See [Brushes](brushes.md).

## Painter's pigments

`PAINTERS_PIGMENTS` and `PAINTERS_TRANSPARENCY` are a second pair of tables beside `PIGMENTS` and `TRANSPARENCY`, keyed by the tube a painter names instead of by map role, with the same meaning: a colour as `#rrggbb`, and a transparency in 0 to 1. No map style reads them; they are for painting with the engine directly, and the figure above does not show them. The [pigment gallery](pigment-gallery.md) paints them as three washes each.

| Key | Colour | Transparency | Colour Index |
| --- | --- | --- | --- |
| `ultramarine` | `#2b3d8f` | 0.06 | `PB29` |
| `cerulean` | `#2a7ab0` | 0.22 | `PB35` |
| `burnt_sienna` | `#8a3b1c` | 0.20 | `PBr7` |
| `raw_sienna` | `#b8692a` | 0.18 | `PBr7` |
| `yellow_ochre` | `#c99a3a` | 0.24 | `PY43` |
| `sap_green` | `#3f6b2a` | 0.07 | none |
| `indigo` | `#2c3346` | 0.05 | none |
| `perylene_maroon` | `#5a1f27` | 0.04 | `PR179` |
| `quinacridone_rose` | `#b8215e` | 0.05 | `PV19` |
| `paynes_grey` | `#3b4452` | 0.10 | none |
