# 0036 — Fourth golden regeneration: the engine fixes of revision round 1

Status: accepted

## Context

Revision round 1 (P7.V) found seven faults in the engine that the golden images show: a
water multipolygon's islands filled solid, a leader line cut through a placed label, the
centreline skeleton drawing strokes twice, shops and unrecorded museums offered as
landmarks, a square blot at the start of a wide pen stroke, a pen route that did not keep
its doubled-back legs apart, and a paper whose grey vignette and smudges the maintainer
asked to replace. Each fix moves pixels past `MAX_DIFFERING_FRACTION`, so each needs a
golden regeneration with an ADR, run as ADRs 0006, 0025 and 0031 were.

## Decision

### The process

The process is the one of ADR 0031: the Lynmouth fixture is painted and compared with the
committed goldens under gate options that say what may move, the moved images are looked
at, the labels are diffed, and the goldens are regenerated once at the end and compared
with the paint they came from.

- The tolerance bound in `tests/golden/test_parity.py` (`MAX_DIFFERING_FRACTION = 0.005`,
  `MAX_CHANNEL_DELTA = 2`) is not changed, and no gate is loosened.
- The hash input does not change. The manifest hash moves only in its style half, from the
  paper fix (below).
- The Lynmouth compare is run first, against the committed goldens, and recorded; the
  goldens are then regenerated in place with `make_golden.py` and compared with that paint
  (`--require-identical all --require-hash equal`).
- The place pins (`tests/golden/test_places.py`), the map-styles means
  (`tests/golden/test_map_styles.py`), the smoke lock, `GOLDEN_HASH` and every docs image
  with its master are re-measured on the merged code and re-pinned from that run.

### The parallel-coding deviation

The plan says each of these slices regenerates the goldens it moves, in sequence. They were
coded in parallel instead, each in its own worktree, and none regenerated anything. The
machine has four cores and an exact golden run takes about 27 minutes, so seven slices that
each ran a compare, a regeneration and the exact run in turn would have spent hours of the
round on the same repaint, and the repaint is not the evidence: each slice instead recorded
its own Lynmouth attribution (which outputs its fix moved, and by what fraction, on a base
without the others) in the run log, with its draft section of this ADR. This slice
(P7.V7c) did the one regeneration, on the merged code, and checks the union of those
attributions against it. What is lost is the per-step "committed state is green" record
between the seven fixes; what is kept is that every fix was proved by its own failing unit
test first and attributed on its own base.

Outcome of the first compare, merged code against the committed goldens (differing
fraction per output, past the channel bound):

| paper | wash | pen | labels-centreline | map | Hash | `labels.txt` |
|---|---|---|---|---|---|---|
| 0.999990 | 0.000645 | 0.000887 | 0.107045 | 0.970524 | `340a7f6e260ee1e2-e5a5f1b4b3ca2177` to `340a7f6e260ee1e2-d9c56c0811177b0f`, differs | two names replaced |

That is the union of the slices' attributions: paper moves only with the paper fix (P7.V7b),
the wash only with the pool fix (P7.V6), the pen with P7.V6 and P7.V7 (0.000120 and 0.000876
singly), labels-centreline with P7.V4, P7.V5, P7.V6 and P7.V7b, and the map with all of them
but P7.V2 and P7.V3, which Lynmouth does not show.

### P7.V2. Water areas keep their islands

A water multipolygon's inner rings are islands. The lake fill carries them as holes wound
against the outer rings, so the nonzero fill leaves them dry; the river-width measure treats
a point inside an island as not in water, and measures a river's banks to the nearest ring
edge of any ring, so a channel beside an island is as wide as the water it runs in, not as the
lake's outer envelope. `Harvest.lake_holes` collects the rings, `osm.py` writes
`rings_path(lakes, lake_holes)`, `rivers._in_water` is a nonzero winding sum and
`rivers._banks_at` takes the nearest crossing of any ring. Bays keep ignoring inner rings.
The vector export reads the same path and gains the holes.

Moved: every card whose payload holds a holed water relation, which is Oxford's Cherwell (14
inner rings, 41.1 of 49.2 ha), and no other. Lynmouth does not move (its payload holds no
holed water). The Oxford card shows the braided Cherwell in place of one solid blue blot
about 600 render px across, and its labels: the Cherwell is lettered twice (on two strands),
and "Thames" moves to the south west bank.

### P7.V3. A leader never crosses a placed label

`_place_flat` costed a candidate's box against placed boxes but not the line joining it to
its mark, so a chapel's leader could cut the "K" of "Keswick". A candidate now pays
`LEADER_CROSS_LABEL_COST` (90, equal to `ROAD_CROSS_COST`) for each placed box its leader
passes through, in the flat placer and in the swap pass's `_seat_cost`, so `_swap_seats`
cannot put a label back across. It is a price, not a ban: where every seat crosses, the
cheapest still wins. Leaderless names (spans, settlements, rivers, roads, markers) are not
charged.

Moved: the positions of leadered labels on cards where a leader used to cross a label. No
place's set of names changes because of it, and Lynmouth does not move.

### P7.V4. The skeleton draws each stroke once

The thinned skeleton was sound; the walk that turned it into chains was not. `_walk` stepped
over a junction node and drew a stroke again from the far side (k, m, n and K stems), started
a branch twice from a staircase junction, carried on past its own start node round a loop
(d, g, a) and stopped mid-stroke at a dead-end corner pixel. `_walk` now ends at any node
beside it and at its own start node once round a loop, `_step` takes the pixel that touches
the walk least, `_again` drops a walk whose run is already drawn, `_loops` drops leftover
staircase corners, and `trace._flank` drops a flank longer than `FLANK_LONGEST` (3.0
half-widths), which is the stem's other side, not an arm. Strokes that run on through a
junction are one stroke (`letters/junction.py`, `join_through`), a spur that carries on from
another branch is kept, and a flank starts on its stem and is dropped under 2.2 half-widths.
`RASTER_EM`, `FLANK_MIN` and the junction merge were not changed, and no single-line font was
needed.

Moved: every lettered golden (the hand's draws are made per stroke, so fewer strokes shift
every later draw): on Lynmouth `labels-centreline.webp` and `map.png`, and the lettered
docs images and masters. Labels do not change. Known and not fixed:
`docs/issues/letters-terminal-tails-pruned.md` (D, Q and 3 lose their terminal tails; 8 keeps
a 0.047 em bridge).

### P7.V5. Landmark ranking

Shops and brands are never offered (`other`); a `tourism=museum` the wider record does not
know is a `sight` (tier 2) and a recorded one stays an `attraction`; castles are `building`
(tier 1); inside a tier a recorded thing (any of `wikidata`, `wikipedia`, `heritage`,
`listed_status`; never `brand:wikidata`) ranks first, so `landmark_rank` is `(tier, not
recorded, distance / reach)`. `osm_elements.LANDMARK_TAG_KEYS` gains the four record keys and
`shop`, `brand`, `brand:wikidata`. The fixtures already held the keys; nothing was
re-recorded. Why: the Keswick card lettered a gift shop as a museum and the Lynmouth card an
art and craft centre.

Moved: the names of the landmarks on every card with automatic picks. The changes to the
place pins are in "Label changes" below, and on Lynmouth `Hollerday Hill` and
`Lyn Valley Art and Craft Centre` (a shop) give way to `Lynton and Exmoor Museum` and
`Living Waters Lynton United Reformed Church`.

### P7.V6. The pool fades to nothing at its edge

`ink/deposit.py pool` cut its Gaussian at two radii, leaving a square blot at the start of a
wide pen stroke (13.5% of the centre at the side midpoint of the span). It is cut at
`ceil(3 r)` (1.1%). The `pen` smoke hash moved when the fix landed and the `wash` smoke
hash did not (the smoke box's wash brushes never reach a wide pool), so
`tests/golden/smoke/wash.webp` is unchanged. The ink benchmarks did not slow (within noise,
none over 15%).

Moved: small fractions of the wash, the pen, labels-centreline and map (about 0.0006,
0.0001, 0.0011 and 0.0006 on Lynmouth); the blots at stroke starts are slightly wider and
softer with no square edge.

### P7.V7. The pen route keeps its legs apart

The pen plate is a base plate and the route inks are in `digest()` only (ADRs 0005 and
0027), so the pen reads base-group fields only. `paint_route_pen` separates the route by its
own `route_pen_width_px * STRAND_GAP_WIDTHS * scale` before it lays the pen, whatever the
ride ink. `strands.strand_gap_px(style)` gives `pipeline.paint` the pen's gap when the pen
plate is the route shown (the route pen is on and the ride ink's style is `"pen"`), else the
ride ink's, so the lettering and the solid route read the line the pen painted.

Moved: the pen plate of every card with a doubled-back track (on Lynmouth 0.000876 of
`pen.webp`, in a box where the track doubles back). Composed images move only where the ride
ink is a pen, which none of the shipped themes sets.

### P7.V7b. The paper's edge and foxing

The grey vignette and broad grey smudges are replaced, by default, with a narrow warm edge
and small rust specks: `PaperStyle.paper_edge` is `"warm"` or `"classic"` (default
`"warm"`, not in `DIGEST_OMITS_AT_DEFAULT`, named in `default.toml`'s `[paper]`).
`"classic"` is the old arithmetic, pinned by a hash taken from the base. `"warm"` draws the
same two fields from the sheet in the same order (the generator ends in the same state,
tested, so later fields keep their values), narrows the vignette to `w * 0.08 * (0.5 + n26)`,
darkens the worn border and the vignette through `PAPER_EDGE_TINT`, and foxes with the top
`FOX_SPECK_AREA` (0.3%) of `sheet.gran` by rank, weighted `0.4 + 0.6 * n120`, tinted
`PAPER_FOX_TINT`. `pigment_swatches`, `brush_sheet`, `wash_stages` and `nib_stages` pass
`paper_foxing=0.0` (reference and explanation figures carry no foxing).
`DocsImage.quality` is threaded through `make_docs_images.py`'s `_encode` for the budget rule
below.

Moved: the default style's full and base digests (`25ae6fee082ebff5` to
`d7997015c8df9b37`, `e5a5f1b4b3ca2177` to `d9c56c0811177b0f`), so the manifest hash of every
plate set, the `PaperStyle` group digest, the smoke `paper` hash, and every image: the interior
brightens by the vignette's narrowing (the Lynmouth card centre goes from 0.940, 0.905, 0.828
to 0.954, 0.919, 0.840), the classic smudges are gone and the specks are added. The
sepia theme's pinned mean moves most (red 176.5 to 206.0), because its paper sets
`paper_vignette = 0.22`.

### Steps

| Step | Commit | Expected | Gate options |
|---|---|---|---|
| 0 | `bbd1c6f` | baseline: the merged code, before any regeneration | none |
| 1 | the merged code, compared with the committed goldens | paper, wash, pen, labels-centreline and map past the bound; the hash differs; `labels.txt` differs | none (recorded, not a gate) |
| 2 | `Fourth golden regeneration (P7.V2 to P7.V7b)` | every output byte-identical to the step 1 paint; the hash equal | `--require-identical all --require-hash equal` |

Step 2 compared with the step 1 paint was byte-identical for every output (differing
fraction 0.000000), hash `340a7f6e260ee1e2-d9c56c0811177b0f` on both sides.

### Label changes

Each place's expected label set (`tests/golden/test_places.py`) was re-measured on the merged
code, and each change was attributed by running the same fixtures on the code after each fix
in turn (before P7.V3; after P7.V3; after P7.V4 and P7.V5; after P7.V6, P7.V7 and P7.V7b;
after P7.V2). Every change in a set of names came from P7.V5; P7.V3, P7.V4, P7.V6, P7.V7 and
P7.V7b change positions and shapes, not which names are placed; P7.V2 changes how many times
the Cherwell is lettered, not the set.

| Place | Left | Entered | Fix |
|---|---|---|---|
| skye | `Cnoc an t-Sìthean`, `Giant Angus MacAskill Museum`, `Staffin Dinosaur Museum` | `Free Church of Scotland Kilmuir`, `Broadford Church of Scotland`, `Kensaleyre Church` | P7.V5 |
| ambleside | `Rydal Bridge`, `Rydal Road`, `Hope Church` | `Pelter Bridge`, `Loughrigg Fell`, `St Mary's` | P7.V5 |
| keswick | `Lake Road Chapel`, `The Retro Zone`, `Derwent Bridge` | `Theatre by the Lake`, `Friar's Crag`, `Derwent Pencil Museum` | P7.V5 |
| oxford | `High Street` | `Tom Tower` | P7.V5 |
| trotternish, yr-wyddfa, y-fenni | none | none | none |

### Hashes

- Manifest hash of the old goldens: `340a7f6e260ee1e2-e5a5f1b4b3ca2177`.
- Manifest hash of the regenerated goldens: `340a7f6e260ee1e2-d9c56c0811177b0f`. Only the
  style half moved (the paper fix); the geometry half did not.
  `GOLDEN_HASH` in `tests/unit/maps/test_pipeline_fetch_paint.py` is re-pinned to it.
- `PINNED_LABELS` in `tests/unit/maps/test_pipeline_letter_compose.py` (golden-marked, the
  Lynmouth card's names in placement order) follows `labels.txt`: `Hollerday Hill` and
  `Lyn Valley Art and Craft Centre` become `Lynton and Exmoor Museum` and `Living Waters
  Lynton United Reformed Church` (P7.V5).
- The smoke lock: `SMOKE_SHA` already held the P7.V6 and P7.V7b values and matches the
  merged code; `tests/golden/smoke/wash.webp` is unchanged.

### Docs images

All 55 registry entries and their masters were repainted with `make_docs_images.py`, the
fern (`painting-with-python/fern.webp`) included: its drawing is unchanged and it takes the
new paper (decision 3 of the round). Every entry stays within its kind's budget and its
slice's share, so the fallback rule of P7.V7b (a lossless entry that would exceed either goes
to lossy WebP at quality 95, recorded; a lossy entry over either stops the slice) did not
fire, and no entry sets `quality`. The closest to a budget: `gallery/lettering.webp` 56,640
bytes of the 60,000 thumbnail budget (lossless), `gallery/nib-line.webp` 54,578 (lossless),
`gallery/route-map.webp` 50,290 (lossy); P7.10's images 436,740 of its 500,000 share; all of
`docs/images/` 1,929,628 of 7,000,000 bytes.

## Consequences

- The goldens, the place pins, the map-styles means, the docs images and their masters record
  the seven fixes. The tolerance gate and the byte-exact golden run hold from this regeneration
  on.
- A further regeneration needs its own ADR. `docs/issues/letters-terminal-tails-pruned.md`
  is the one known engine fault this round leaves for it.

The machine the goldens were regenerated on: the agent's Linux container, Python 3.13, with the
parity stack at its pins. The exact run is green there; every other platform uses the tolerance
gate.
