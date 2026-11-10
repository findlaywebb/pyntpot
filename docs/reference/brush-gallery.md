# Brush gallery

Every brush id painted, so a brush can be chosen by eye and not by name. A brush id is `<PREFIX><row>-<column>`, such as `MAJ2-a`; see [Brushes](brushes.md) for the form and the treatment values. There are 112 ids, in three figures, one for each group of prefixes.

Every figure is painted on `paper_plate` paper. Its rows are the eight treatments, lettered with their number and kind, from 1 wet to 8 light nib. Its columns are ink colours. Each cell holds an S-shaped stroke 4 pixels wide above one 12 pixels wide, because dryness shows only when a stroke is wide, and has its id lettered beneath. Each table below repeats the figure: the treatment down, the ink column across with its hex, and the ids in their cells.

## RIV, STR and LAN

![Eight rows of strokes in two columns. The left column, lettered RIV = STR, is a blue ink and the right, LAN, a brown one. Down the rows the treatments go from a wet, whole line through gritty and dry strokes that break into flecks, to nibs with a blot where they touch down, to a driest row that is mostly paper showing between specks. Each cell has a narrow stroke over a wide one and its id beneath.](../images/reference/brush-gallery-riv-str-lan.webp)

*Painted by `examples/brush_gallery.py` (`figure="riv-str-lan"`), seed 7.* `RIV` and `STR` are one brush in one ink: neither is a key of `BrushStyle.brush_overrides`, so each cell of the left column is lettered with both ids and holds one painted stroke. The figure holds 16 cells and 24 ids: eight cells of `RIV` and `STR` in one column, and eight of `LAN`.

| Treatment | `a` #255d80 | `a` #6b4423 |
| --- | --- | --- |
| 1 wet | `RIV1-a` `STR1-a` | `LAN1-a` |
| 2 soft | `RIV2-a` `STR2-a` | `LAN2-a` |
| 3 gritty | `RIV3-a` `STR3-a` | `LAN3-a` |
| 4 dry | `RIV4-a` `STR4-a` | `LAN4-a` |
| 5 nib | `RIV5-a` `STR5-a` | `LAN5-a` |
| 6 pen | `RIV6-a` `STR6-a` | `LAN6-a` |
| 7 driest | `RIV7-a` `STR7-a` | `LAN7-a` |
| 8 light nib | `RIV8-a` `STR8-a` | `LAN8-a` |

## MAJ

![Eight rows of strokes in five columns, lettered a to e: a terracotta, an ochre brown, a dark brown, a warm grey and a near-black ink. Each cell has a narrow stroke over a wide one with its MAJ id beneath. The treatments run from wet and whole at the top, through gritty and dry strokes that fleck, to nibs, and a driest row where the paint barely covers the paper.](../images/reference/brush-gallery-maj.webp)

*Painted by `examples/brush_gallery.py` (`figure="maj"`), seed 7.* The five ink columns of `MAJ`, `a` to `e`, with the treatments down.

| Treatment | `a` #b5623f | `b` #8a5a2c | `c` #6b4423 | `d` #7b7266 | `e` #2b2620 |
| --- | --- | --- | --- | --- | --- |
| 1 wet | `MAJ1-a` | `MAJ1-b` | `MAJ1-c` | `MAJ1-d` | `MAJ1-e` |
| 2 soft | `MAJ2-a` | `MAJ2-b` | `MAJ2-c` | `MAJ2-d` | `MAJ2-e` |
| 3 gritty | `MAJ3-a` | `MAJ3-b` | `MAJ3-c` | `MAJ3-d` | `MAJ3-e` |
| 4 dry | `MAJ4-a` | `MAJ4-b` | `MAJ4-c` | `MAJ4-d` | `MAJ4-e` |
| 5 nib | `MAJ5-a` | `MAJ5-b` | `MAJ5-c` | `MAJ5-d` | `MAJ5-e` |
| 6 pen | `MAJ6-a` | `MAJ6-b` | `MAJ6-c` | `MAJ6-d` | `MAJ6-e` |
| 7 driest | `MAJ7-a` | `MAJ7-b` | `MAJ7-c` | `MAJ7-d` | `MAJ7-e` |
| 8 light nib | `MAJ8-a` | `MAJ8-b` | `MAJ8-c` | `MAJ8-d` | `MAJ8-e` |

## TRK

![Eight rows of strokes in six columns, lettered a to f: a dark brown, a terracotta, a grey, an olive, a dusty rose and a near-black ink. Each cell has a narrow stroke over a wide one with its TRK id beneath. The treatments run from wet and whole at the top, through gritty and dry strokes that fleck, to nibs, and a driest row where the paint barely covers the paper.](../images/reference/brush-gallery-trk.webp)

*Painted by `examples/brush_gallery.py` (`figure="trk"`), seed 7.* The six ink columns of `TRK`, `a` to `f`, with the treatments down.

| Treatment | `a` #6b4423 | `b` #b5623f | `c` #7d7468 | `d` #6f6636 | `e` #95584a | `f` #2b2620 |
| --- | --- | --- | --- | --- | --- | --- |
| 1 wet | `TRK1-a` | `TRK1-b` | `TRK1-c` | `TRK1-d` | `TRK1-e` | `TRK1-f` |
| 2 soft | `TRK2-a` | `TRK2-b` | `TRK2-c` | `TRK2-d` | `TRK2-e` | `TRK2-f` |
| 3 gritty | `TRK3-a` | `TRK3-b` | `TRK3-c` | `TRK3-d` | `TRK3-e` | `TRK3-f` |
| 4 dry | `TRK4-a` | `TRK4-b` | `TRK4-c` | `TRK4-d` | `TRK4-e` | `TRK4-f` |
| 5 nib | `TRK5-a` | `TRK5-b` | `TRK5-c` | `TRK5-d` | `TRK5-e` | `TRK5-f` |
| 6 pen | `TRK6-a` | `TRK6-b` | `TRK6-c` | `TRK6-d` | `TRK6-e` | `TRK6-f` |
| 7 driest | `TRK7-a` | `TRK7-b` | `TRK7-c` | `TRK7-d` | `TRK7-e` | `TRK7-f` |
| 8 light nib | `TRK8-a` | `TRK8-b` | `TRK8-c` | `TRK8-d` | `TRK8-e` | `TRK8-f` |
