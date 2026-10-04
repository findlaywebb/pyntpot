# 0006 — Golden regeneration

Status: proposed

## Context

The golden plates in `tests/golden/lynmouth/` were painted by the pre-port code. Three
changes the port needs move what those goldens record: the base hash takes its final
form (the typed basemap's canonical text and the base style digest, in place of a
hand-kept payload key list and the digest of every painter field), the seam between the
basemap and the painter stops rounding geometry to a tenth of a metre, and duplicated
polyline helpers are merged. The hash moves for certain; pixels may move by a bounded
amount.

Regenerating after each change would let a bug become golden unseen, and regenerating
never would leave the goldens describing code that no longer exists. So the changes land
inside one regeneration window: a run of commits, each compared against the output of
the commit before it on the same machine, with the goldens regenerated once at its end.

## Decision

Each step of the window is one commit. Before it is committed, the Lynmouth fixture is
painted and compared with the previous step's output, under gate options that say what
the step may move. A step whose compare fails is not committed. The committed goldens are
compared too, as the cumulative record, but that compare is not a gate. The tolerance
bound in `tests/golden/test_parity.py` (`MAX_DIFFERING_FRACTION = 0.005`,
`MAX_CHANNEL_DELTA = 2`) is not changed.

The hash input is final from the first step: compact sorted-key JSON of the card's box,
display grid, render grid and both scales and every `Layers` field, with every float
written to three decimals and negative zero written as zero. The manifest hash is the
first 16 hex digits of its SHA-256, a hyphen, and the style's base digest.

### Steps

| Step | Commit | Expected | Gate options |
|---|---|---|---|
| 0 | `020c3ff` | baseline, made on the window's starting commit | none |
| 1 | `Hash plates from the typed basemap and the style groups` | all five outputs byte-identical to step 0; the hash differs | `--require-identical all --require-hash differ` |
| 2 | `Read lettering geometry from the basemap and settle the manifest` | all five outputs byte-identical to step 1; the hash equal; `labels.txt` written for the first time | `--require-identical all --require-hash equal` |
| 3 | `Keep basemap geometry as full-precision point lists` | each output within the bound of step 2; the hash differs; `labels.txt` equal | `--max-fraction 0.005 --require-hash differ --require-labels-equal` |
| 4 | `Merge the ring and chain joiners` | all five outputs byte-identical to step 3; the hash equal; `labels.txt` equal | `--require-identical all --require-hash equal --require-labels-equal` |
| 5 | `Merge the arc-length helpers` | all five outputs byte-identical to step 4; the hash equal; `labels.txt` equal | `--require-identical all --require-hash equal --require-labels-equal` |
| 6 | none: no two normal helpers compute the same quantity, so nothing was merged | no commit and no compare | none |

Step 1 wires the grouped style into the painter: the flat painter style, the effective
basemap options and the route ink all come from the packaged default theme, and the base
digest goes into the hash. It also changes the painter's consumer-only `label_font`
default to the vendored face; nothing in the painter reads it.

Step 1 compare, against step 0 (the gate):

```
paper.webp: identical yes, differing fraction 0.000000
wash.webp: identical yes, differing fraction 0.000000
pen.webp: identical yes, differing fraction 0.000000
labels-centreline.webp: identical yes, differing fraction 0.000000
map.png: identical yes, differing fraction 0.000000
manifest hash: 87624a4cd49063df-e5a5f1b4b3ca2177 here, c034e1a4d60bad70-77dce82bec370944 in step 0
```

Step 1 compare, against the committed goldens (cumulative record):

```
paper.webp: identical no, differing fraction 0.000000
wash.webp: identical no, differing fraction 0.000000
pen.webp: identical yes, differing fraction 0.000000
labels-centreline.webp: identical no, differing fraction 0.000000
map.png: identical no, differing fraction 0.000000
manifest hash: 87624a4cd49063df-e5a5f1b4b3ca2177 here, c034e1a4d60bad70-77dce82bec370944 in the goldens
```

The four outputs that are not byte-identical to the committed goldens were already so on
the starting commit, in this environment; they are within the channel bound everywhere.

Step 2 moves the lettering's inputs from the manifest to the basemap: the places, the
candidates and the named lines a label is set along are read from the basemap the plates
were painted from, and the route is the basemap's own track rather than a second
projection of the recorded points. The manifest takes its final shape. These keys are
removed: `id`, `route0`, `places`, `candidates`, `label_geom`, `labels_hash`, `sources`,
`timing`. These sixteen remain, final: `hash`, `files`, `sizes`, `bytes`, `card`,
`display`, `render`, `mpp`, `mpp_display`, `ribbon_m`, `span_m`, `wet_px`, `gran_px`,
`dark`, `wood_px`, `water_px`.

Step 2 compare, against step 1 (the gate):

```
paper.webp: identical yes, differing fraction 0.000000
wash.webp: identical yes, differing fraction 0.000000
pen.webp: identical yes, differing fraction 0.000000
labels-centreline.webp: identical yes, differing fraction 0.000000
map.png: identical yes, differing fraction 0.000000
manifest hash: 87624a4cd49063df-e5a5f1b4b3ca2177 here, 87624a4cd49063df-e5a5f1b4b3ca2177 in step 1
```

Step 2 compare, against the committed goldens (cumulative record):

```
paper.webp: identical no, differing fraction 0.000000
wash.webp: identical no, differing fraction 0.000000
pen.webp: identical yes, differing fraction 0.000000
labels-centreline.webp: identical no, differing fraction 0.000000
map.png: identical no, differing fraction 0.000000
manifest hash: 87624a4cd49063df-e5a5f1b4b3ca2177 here, c034e1a4d60bad70-77dce82bec370944 in the goldens
```

The window's pinned label list, `labels.txt` as step 2 wrote it (the placed label names,
in placement order). Every later step must write the same list:

```
Lynton
Barbrook
East Lyn
East Lyn
A39
B3234
Saint Mary the Virgin
Hollerday Hill
Lyn Valley Art and Craft Centre
start
```

### Step 3

Step 3 stops the seam between the basemap and the painter rounding geometry to a tenth of
a metre. `journal_layers` hands the painter its route, cover, lakes, sea and coastline at
full precision, and the elevation patch corners unrounded; `paint.parse_d` goes, as does
the route offset the lettering used to pin the card onto the painter's rounded route
(`Card.offset`), and `named_lines` no longer rounds its points. The vector map's own
output is unchanged: `basemap()` still writes 0.1 m path data, and `journal_layers` still
reads roads, water areas and rivers through `geo.parse_path`.

Step 3 compare, against step 2 (the gate):

```
paper.webp: identical yes, differing fraction 0.000000
wash.webp: identical no, differing fraction 0.207338
pen.webp: identical no, differing fraction 0.000225
labels-centreline.webp: identical no, differing fraction 0.042485
map.png: identical no, differing fraction 0.193396
manifest hash: 340a7f6e260ee1e2-e5a5f1b4b3ca2177 here, 87624a4cd49063df-e5a5f1b4b3ca2177 in step 2
```

`labels.txt` is equal to step 2's. The wash, the labels-centreline plate and the map
exceed the per-step bound of 0.005, so the gate failed and the step was not committed
until the drift was explained.

Step 3 compare, against the committed goldens (cumulative record):

```
paper.webp: identical no, differing fraction 0.000000
wash.webp: identical no, differing fraction 0.207337
pen.webp: identical no, differing fraction 0.000225
labels-centreline.webp: identical no, differing fraction 0.042485
map.png: identical no, differing fraction 0.193396
manifest hash: 340a7f6e260ee1e2-e5a5f1b4b3ca2177 here, c034e1a4d60bad70-77dce82bec370944 in the goldens
```

Visible differences in `map.png`, step 3 beside step 2:

- The pale blooms in the sea sit in different places: the tall column of blooms north of
  Lynton is gone, and a row of smaller blooms now runs along the coast.
- The mottling of the land cover wash differs in pattern, most visibly the darker green
  patches in the middle of the loop and south of it.
- The lettering, the route, the roads, the rivers and the coastline look the same.

**Why it moved.** Each point moves by at most 0.05 m, a small fraction of a render pixel.
The drift comes entirely from three families of discrete threshold decision, each of
which feeds a random generator shared down a sequence, so one flipped decision changes
everything drawn after it from that generator:

- **a. Deform rounds.** `deform_ring` stops deforming a ring when the median segment is
  shorter than its minimum. One generator is shared by every cover ring, so once the
  first ring ends with a different round count, the later rings' midpoints and medians
  change too: 57 rings end with a different round count.
- **b. Bloom placement.** `bloom` picks its candidate centres by rank in raster order
  among the pixels above an alpha threshold, then takes the argmax among them; the bloom
  radius, its clipping at the edge and the bloom count (from the rounded square root of
  the area) set how much the shared `bloom_rng` consumes. A sub-pixel change to a coast
  or cover edge changes the rank count, so the same draws land on pixels several columns
  away, and the shared generator then desynchronises every later wash, the sea included.
- **c. Lettering.** `Hand._label_marks` seeds each label from its position rounded to a
  tenth of a pixel. The A39 label sits 0.0016 px from a rounding boundary, and both the
  removed card offset and the removed `named_lines` rounding push it across; its new
  seed changes its stroke count in `stamp`, and the whole map-ink group shares one
  label generator. One along-line label also changes window in `_place_along`'s argmin.
  The rest of the labels-centreline drift is downstream of the wash: `label_plate` reads
  the painter's darkness grid through `_dark_field` for the ink tint and the backing wash.

**Proof.** Each family was neutralised in a diagnostic copy only: (a) the round count
computed on the 0.1 m ring and forced on the full-precision one, (b) the step-2 bloom
centre, radius and post-draw generator state replayed for each bloom, (c) the card pin and
the `named_lines` rounding restored. Differing fraction against step 2:

| Variant | paper | wash | pen | labels-centreline | map |
|---|---|---|---|---|---|
| step 3 as committed | 0 | 0.207338 | 0.000225 | 0.042485 | 0.193396 |
| a only (wash only) | 0 | 0.097679 | 0.000225 | | |
| b only (wash only) | 0 | 0.088510 | 0.000225 | | |
| a + b | 0 | 0.002286 | 0.000225 | 0.008066 | 0.004086 |
| a + b + pin | 0 | 0.002286 | 0.000225 | 0.007752 | 0.003818 |
| a + b + pin + `named_lines` rounding | 0 | 0.002286 | 0.000225 | 0.000002 | 0.001737 |

With all three neutralised every output is within 0.005 and `labels.txt` is equal
throughout. What remains is continuous: edge antialiasing in the wash and the map, and a
route that moves by at most 0.05 m in the pen.

**Conclusion.** The step-3 drift is fully explained, with no behaviour defect: every
mechanism is legitimate amplification of a sub-pixel change through a discrete decision
and a shared generator. Removing the card offset is itself a correctness fix, since step
2 shifted all lettering by the route's rounding residual. The fragility of shared
generators is recorded in `docs/issues/shared-generators.md`.

Accepted by the maintainer as the one exception in the window; the per-step bound and the
parity tolerance are unchanged.

### Step 4

Step 4 merges the two greedy pool joiners. The multipolygon ring joiner and the traced
contour joiner were the same loop: take the last piece from the pool, grow it at either
end by the first piece in pool order whose end meets it, and stop when nothing meets it
or it has closed. They are now one function, `join_chains(lines, tol)`, which copies its
pieces and drops nothing. The ring joiner's callers (a relation's outer and inner rings,
at a tolerance of 1 m, and the coastline, at 2 m) keep only chains of more than three
points themselves, as the ring joiner did; the contour caller passes its tolerance of
1e-6 explicitly.

Step 4 compare, against step 3 (the gate):

```
paper.webp: identical yes, differing fraction 0.000000
wash.webp: identical yes, differing fraction 0.000000
pen.webp: identical yes, differing fraction 0.000000
labels-centreline.webp: identical yes, differing fraction 0.000000
map.png: identical yes, differing fraction 0.000000
manifest hash: 340a7f6e260ee1e2-e5a5f1b4b3ca2177 here, 340a7f6e260ee1e2-e5a5f1b4b3ca2177 in step 3
```

`labels.txt` is equal to step 3's.

Step 4 compare, against the committed goldens (cumulative record):

```
paper.webp: identical no, differing fraction 0.000000
wash.webp: identical no, differing fraction 0.207337
pen.webp: identical no, differing fraction 0.000225
labels-centreline.webp: identical no, differing fraction 0.042485
map.png: identical no, differing fraction 0.193396
manifest hash: 340a7f6e260ee1e2-e5a5f1b4b3ca2177 here, c034e1a4d60bad70-77dce82bec370944 in the goldens
```

Kept apart, as different algorithms:

- `join_strokes` finds a meeting end through a grid of cells rather than in pool order,
  and grows the whole tail and then the whole head without stopping when the chain
  closes. At a junction where two pieces both meet a chain's end it can take a different
  one: a pinned test in `tests/unit/ink/test_chains.py` gives the two joiners different
  chains on the same three pieces, so no merge was tried.
- `chain_lines` takes two ends to meet when they are within the tolerance on each axis
  rather than by distance, and concatenates the arrays whole, so a shared end appears
  twice; the pinned tolerance tests show both differences.
- `joined` is `chain_lines` over point lists, at the lettering's tolerance of 8 px, and
  differs from `join_chains` and `join_strokes` as `chain_lines` does.

### Step 5

Step 5 merges the arc-length helpers. The lettering's running length and the route's
metres covered were the same running sum, the second dividing each step by the scale;
they are now one function, `cumulative_length(line, scale=1.0)`, with the second's body,
and dividing by the default scale of 1.0 is exact. The two total-length helpers were the
same sum of the same distances in the same order, one walking pairs and one walking
indices; they are now one, `length`.

Step 5 compare, against step 4 (the gate):

```
paper.webp: identical yes, differing fraction 0.000000
wash.webp: identical yes, differing fraction 0.000000
pen.webp: identical yes, differing fraction 0.000000
labels-centreline.webp: identical yes, differing fraction 0.000000
map.png: identical yes, differing fraction 0.000000
manifest hash: 340a7f6e260ee1e2-e5a5f1b4b3ca2177 here, 340a7f6e260ee1e2-e5a5f1b4b3ca2177 in step 4
```

`labels.txt` is equal to step 4's.

Step 5 compare, against the committed goldens (cumulative record):

```
paper.webp: identical no, differing fraction 0.000000
wash.webp: identical no, differing fraction 0.207337
pen.webp: identical no, differing fraction 0.000225
labels-centreline.webp: identical no, differing fraction 0.042485
map.png: identical no, differing fraction 0.193396
manifest hash: 340a7f6e260ee1e2-e5a5f1b4b3ca2177 here, c034e1a4d60bad70-77dce82bec370944 in the goldens
```

### Step 6

Step 6 would have merged the polyline normal helpers that compute the same quantity. No
two of them do, so nothing was merged and the step has no commit and no compare. Each
keeps a docstring line saying how it differs from the others:

- `normal_at` is the unit left normal at a point, differenced across the points one
  either side, falling back to (0, 1) on a degenerate run.
- `normals` is the unit left normal at every point, differenced across the points three
  either side, so it is smoothed along the run, and a zero run gives a zero normal
  rather than a fallback: a different quantity from `normal_at` at any bend.
- `tangent_at` is the unit direction of travel, not a normal, falling back to (1, 0).
- `unit_normal` is the unit right normal of one given segment, and None rather than a
  fallback when the segment is degenerate: opposite in sign to `normal_at`, and taken
  along a segment rather than across a point's neighbours.

### Hashes

- Old manifest hash (the committed goldens): `c034e1a4d60bad70-77dce82bec370944`.
- New manifest hash after step 1: `87624a4cd49063df-e5a5f1b4b3ca2177`, whose suffix is
  the default style's pinned base digest.
- Manifest hash after step 2: `87624a4cd49063df-e5a5f1b4b3ca2177`, unchanged.
- Manifest hash after step 3: `340a7f6e260ee1e2-e5a5f1b4b3ca2177`.
- Manifest hash after step 4: `340a7f6e260ee1e2-e5a5f1b4b3ca2177`, unchanged.
- Manifest hash after step 5: `340a7f6e260ee1e2-e5a5f1b4b3ca2177`, unchanged.

## Consequences

- Inside the window the golden-marked tests are known stale: the manifest-hash parity test
  fails until the goldens are regenerated. The paper and pen cases still pass in
  tolerance; from step 3 the wash, labels-centreline and map cases fail too.
- The hash no longer depends on any hand-kept key list, and a last-bit difference in a
  machine's maths library cannot move it.
- A lettering-only or route-ink style change no longer moves the base hash.
