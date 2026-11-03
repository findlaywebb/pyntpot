# Feature scoping: what to build together

Scoping round of 2026-11-03. Inputs: the 34 open GitHub issues (27 feature notes in
`docs/features/`, 7 defect notes in `docs/issues/`) and five reviews of every tutorial,
how-to, reference and explanation page and every script in `examples/`, written as a
newcomer who copies the code (`review/01` to `review/05`, 97 findings). The reviews are the
review half of #63; its fix half is session E below.

This is scoping, not a spec: each session below becomes one `specs/NNN-name/` dir, one
branch and one PR when it is picked up.

## What the reviews agree on

Findings raised independently by three or more reviewers carry the most weight.

| Finding | Reviewers | Evidence |
|---|---|---|
| Lettering a picture takes 15 to 20 lines: `nib_plate` only writes a WebP, so callers reopen, resize and alpha-blend by hand | 5 of 5 | 14 copies in 13 scripts, already drifted (`RGBa` vs `RGBA`, 5 leave a `-plate.webp` behind) |
| Map vocabulary in plain pictures: `Canvas(0, 0, w, h, w, h)` "the card's metre box", `paper_plate` takes the width three times, `Sheet(h, w)` against `Canvas(..., w, h)` | 4 of 5 | 47 `Canvas` calls, 33 `paper_plate` calls in 25 files |
| Colour by two parallel tables, and non-map pictures picking colours by map role (`wetland`, `relief`) | 4 of 5 | 18 files; new evidence for #72 |
| `cache.plates_dir(cache.key(route, features, elevation))` rebuilt by every map caller, because `fetch` drops the key | 3 of 5 | 7 places including the first-map tutorial and the CLI |
| Bare positional numbers in `wash` and `brush_from_id(..., 1.0, BrushStyle())` | 4 of 5 | 26 of 30 `wash` calls; 15 `brush_from_id` calls |
| Glossary gaps and drift: painter's terms missing (tooth, pool, glaze, granulation, treatment, tip...), "nib plate" vs "label plate", "callout" vs `landmarks`, `Track` called a route | 4 of 5 | 20 of 53 glossary entries point only at private names |
| Pages are dead ends: no links from tutorials to how-to, reference or explanation | 3 of 5 | |

## New candidates the reviews found

Not yet a note or an issue. P numbers are defects, N numbers features; session letters are separate (A to K below).

**Defects**

- **P1. A trimmed theme silently paints a different map.** `Style.from_toml` fills a missing
  key from the dataclass default, not the default theme; 25 fields differ (wet bleed, blooms,
  fluid pass, KM glazing, landmarks). The same split means `PaperStyle()` and friends do not
  give the default look. One source of defaults is the fix. (maps; review/03 #1, review/05 #4)
- **P2. `with_route_ink` leaves the "start" and "finish" labels in the theme's pink.** They read
  `NibStyle.label_route_ink`. Deliberate today (the colour must not move `lettering_digest`),
  but the how-to's own image shows a violet route with a pink "start". (maps/letters; review/03 #2)
- **P3. The elevation credit always says "NASA SRTM"** whatever dataset the provider served.
  (maps; review/03)
- **P4. `Annotations.roads` is accepted and then ignored.** (maps; review/05 #13)
- **P5. The gallery caption under `nib-angles.webp` describes another figure** (Ambleside,
  three angles; the image is Keswick at four). (docs; review/04 N2, checked)
- **P6. `style-fields.md` gives wrong import locations for 8 of 13 style groups**, and the
  reference tests check that names appear, not that values are right. (docs; review/05 #3, #5)
- **P7. Public functions hide their modules:** `pyntpot.maps.compose.painted_map`, quoted in
  `references.md`, fails at runtime; likewise `wash`, `stamp`, `vector_layers`. (review/05 #6)

**Features**

- **N1. Lettering over an image in one call:** an in-memory nib plate and a `letters` call
  that lays it over a painting. Public API, so an ADR. (letters, L)
- **N2. Blank paper without map plumbing:** a paper helper that takes a size, one axis order
  for `Sheet` and `Canvas`, keyword arguments with names for `wash` densities and
  `brush_from_id`'s scale. Breaking, so an ADR. (ink, M)
- **N3. `fetch` hands back what `paint` needs** (the plates dir or a `Fetched` value), so the
  map pipeline is three calls with no key rebuilt. (maps, S/M)
- **N4. Export every type that appears in a public signature:** 34 private types, of which
  users must build `Landmark`, `SpanRequest`, `WashOptions`, `Features`, `Elevation`, `Card`,
  `Credit`, `Manifest`; plus a test that no public signature names a private type. Extends #73
  and #78. (all, M)
- **N5. Field docs that render:** the `#:` comments on `PaperStyle` (22 fields), `BrushStyle`
  (45), `Brush` (43), `NibStyle`, `Sheet` are invisible to mkdocstrings, `help()` and editors.
  Move to `Attributes:` and test that every rendered field has text. (all, M)
- **N6. Options on `pyntpot map`:** route colour and width, a landmarks file, `--size`,
  `--offline`, defaults in `--help`, errors without tracebacks. Extends #68, which covers new
  commands only. (cli, M)
- **N7. A labelled-grid helper for the docs scripts:** written five times today
  (tutorial_grids, nib_stages, brush_sheet, wash_stages, how_to_route_ink). The grids of #67
  and the galleries of #69 and #70 are all this helper. (docs, S)
- **N8. A colour or density profile along one stroke**, instead of cutting it into 16
  overlapping strokes. (ink, M; review/02)
- **N9. Docs restructure:** runnable programs in Painting with Python (today only fragments),
  nav order and "next" links, tutorials linking out, first-map reaching the hero look, a
  test that the gallery is complete, `performance.md` moved out of explanation. (docs, M)
- **N10. Sixteen missing how-tos**, the top ones: change the card's size, mark a stretch of the
  route, pin journal notes, map a planned route, add relief, use another font, handle fetch
  errors. Several wait on N4 (`SpanRequest`, `Landmark` must be public first). (docs, M)
- **N11. Example housekeeping:** themes resolved against the repo root (a copied script
  breaks), `map.png` overwritten per theme, `out/` `ambleside/` `cache/` not gitignored,
  `fern_family` copies `fern`, `kaleidoscope._dense` is a no-op the page quotes, six scripts
  with no fast test, no `examples/README`. (docs, S/M)

## Sessions

Each session shares files, an ADR, or a golden regeneration window, so doing its items
apart would mean touching the same code or re-pinning the same images twice. **Goldens**
marks a session that moves pinned images.

### A. Docs truth and glossary (docs only, no goldens) (start here)

#65 glossary in place · P5 caption · P6 style-fields imports and value-checking reference
tests · glossary gaps and drift · N9 docs restructure · `how-the-wash-works` misstatement.

Why together: all docs, all `GLOSSARY.md` and `tests/architecture/test_reference_pages.py`.
#65 generates definitions from the glossary, so fill the glossary in the same pass. No
code dependency, so it can run first or in parallel with anything. Size M.

### B. One public surface (one ADR widening the API)

N4 export signature types (#73 public wash options, #78 public provider protocols) · N5 field
docs that render · P7 name shadowing · P4 `Annotations.roads`.

Why together: one ADR in the line of 0026, one pass over every `__init__.py` and the
reference pages, one new architecture test pair (no private type in a public signature;
every rendered field documented). Unblocks the how-tos that need `Landmark` and
`SpanRequest`. No goldens. Size M/L.

### C. Themes as data

#80 overrides in YAML · #77 named themes · P1 one source of defaults · #79 preview card.

Why together: #80 and P1 are the same loader change (a theme merged over a base, never over
dataclass defaults), and #77 is shipping files in that format. The preview card is how the
new named themes get checked. Goldens: only if P1 changes what an existing example theme
resolves to, which is the point. Size L; split #79 off if the session runs long.

Follow-on **C2. New theme fields:** #147 cover order · #149 pin icons. Both need the C
format to declare a field without copying the whole theme. #149 also waits on PR #138's open
ring. Size M.

### D. Route ink

#104 casing · #105 glow · #106 shadow · P2 route labels follow the route ink.

Why together: all in `maps.compose.route` and the `route_ink` group, all reversed out by
ADR 0046 so one ADR brings them back, and P2 is the other half of "change the route ink".
Goldens: only themes that set the new fields, plus P2's lettering if the label colour joins
the route. Size M.

### E. Kill the boilerplate (the fix half of #63)

N1 lettering in one call · N2 blank paper and keyword arguments · N3 `fetch` hands back the
plates dir · then sweep every example and the tutorial, how-to and README snippets onto the
new calls · N11 example housekeeping.

Why together: each new call is only worth having once the 14 / 47 / 7 copies move to it, and
the sweep re-pins the docs images once instead of three times. Run after B (the new calls
are public API and want the same documentation rules). Goldens: docs images. Size L; the
natural split is E-a = N1 + N2 + N3 with their ADR, E-b = the sweep.

### F. Pigment and brush registry

#72 one pigment registry · #71 brushes and pigments as data · then the docs half:
#70 pigment gallery · #69 brush id gallery · #67 variable-effect grids · N7 grid helper.

Why together: #70 paints from #72's list, #69 from #71's brush data, and all three docs
items plus the five existing grids are N7. #71 uses the theme format of #80, so run after C.
Goldens: none for the registry if it is a pure move; docs images for the galleries. Size L;
split F-a = #72 + #71, F-b = galleries and grids.

### G. Command line

#68 wider commands · N6 options on `map`.

Why together: one ADR for command and option names. Wants #77 (named themes) for
`--theme NAME`, and N3 for a short `map` body. Run after C. Size M.

### H. Lettering placement

#113 placement tuning · #52 names under strokes and lakes · #115 water pricing cost ·
#132 letter the start place.

Why together: all reprice or reseat flat names in `maps/lettering/placement*`, and #132 and
#113 each move every lettered golden, so one regeneration window. #52 and #115 are named in
#113 as its consequences. Goldens: yes. Size L.

Companion **H2. Bend sweep follow-ups:** #141 unreachable refusal · #142 constants citing a
lost sweep · #143 short stretches · #144 outside of the bend. All spec 004's sweep, all in
the span-curve code; small and independent of H, so it can run in parallel. Size S/M.

### I. The hand

#152 glyphs share one random stream · #76 nib follows the writing line.

Why together: both change every lettered glyph, and #152 asks for a regeneration window and
an ADR of its own; #76 rides in the same window. Do not run alongside H (both move lettered
goldens). Size M.

### J. Brush tip

#75 stroke keeps its ends · #92 cheaper running sums · N8 profile along a stroke.

Why together: all in `ink/tip.py`. Do #92 first (bit-for-bit, no goldens), then #75 (moves
every smoothed stroke). N8 is optional here. Size M.

### K. Test infrastructure

#82 move off Lynmouth · #90 paint Lynmouth once · #91 macOS golden shards.

Why together: #90's shared paint and #91's sharding both depend on which fixture the goldens
read, which #82 decides; decide #82 first, and #90 may become moot. Best after the
golden-moving sessions (D, H, I, J) have landed. Size M/L.

### Standalone

- **#74 read an SVG drawing** (ink, optional dependency, ADR). Pairs naturally with the
  vector-drawing page of Painting with Python, which shows no code today. Size M.
- **P3 elevation credit** (maps, S): a quick fix any session can take.

## Suggested order

1. **A** and **B** in parallel: no goldens, no shared files beyond the reference pages
   (A owns the prose, B the docstrings and `__init__` files).
2. **C**, then **G** and **C2**; **E** once B has landed.
3. **F** after C. **D**, **H2**, **J** any time; they touch disjoint code.
4. **H** and **I** one after the other, never together.
5. **K** last.

## Before any of this

Each new defect and feature above needs its note in `docs/issues/` or `docs/features/` and a
GitHub issue, per CLAUDE.md. Proposed: P1 to P7 as defect notes, N1 to N11 as feature notes,
with N4 and N6 written as extensions to #73/#78 and #68 rather than new issues.
