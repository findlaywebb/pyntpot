# 0008 — The hand writes settings

Status: accepted

## Context

`_port.labels.Hand` reads map types. `Hand.marks(placed, spans, route_px)` takes
`Label` and `Span` and decides, from their tier, kind, intent, `in_water`, `leader` and
`lift`, that a river leans and is set wide in the water ink, that a settlement over the
default size gets an underline, that a span gets a line and two ticks and that a pinned
name gets a ring and a leader. `Hand._baseline` still chooses a window along a label's
line for a name the placer skipped. That is placement one layer too low, and it is the
one dependency (`letters` reading `maps` types) that moving bytes cannot break
(architecture A2). The target is that `letters` takes a **setting** (what to write, at
what size, along which line or from which anchor, leaning how far, tracked how wide, in
which ink) and returns **marks**, and that `maps` translates labels and spans into
settings and draws its own furniture as marks through the same nib.

Reading the code as it stands (`186ac3f`) adds four facts the A2 sketch does not state,
and both shapes below have to answer them:

1. **One generator per instance, shared with the furniture.** `_label_marks` seeds one
   generator from `label_seed`, the name and the rounded anchor, then draws, in order:
   the pen tilt, the flat block's tilt (flat names only), every glyph's drift, lean,
   scale, rotation, nudge and wobble, and then the furniture: the pin ring's wobble,
   the leader's bend and wobble, the home glyph's wobble, the underline's rise and
   wobble. `_span_marks` likewise draws the span line's wobble, then its pen tilt, then
   each tick's wobble from one generator. Exact parity therefore needs the furniture
   drawn by `maps` to continue the same generator after the glyphs, in the same order.
   A `stroke(..., seed)` that opens a fresh generator per stroke (the plan's starting
   point) moves every pin, leader, underline, home glyph and tick.
2. **Furniture geometry draws from the generator before the wander.** The leader's bend
   and the underline's rise are random draws taken before the stroke is wobbled, and
   the span line's pen tilt is drawn after its wobble. So furniture cannot be a value
   handed to the hand to wobble; the caller interleaves its own draws with the hand's.
3. **The set width with tracking.** Window choice and the underline both need the
   face's width of a name at its size and tracking. `Hand.measure` returns
   `width + size * 0.5` without tracking, which is the placer's box, not the set width.
4. **The label plate key covers the furniture.** `plate_key` hashes the label rows
   (anchor, leader end, window, lift, wrap) and each span's line. A key over the
   settings alone would not see a moved pin, leader or span line, so a stale plate
   would be drawn.

## Two shapes

Both shapes share what the facts force: `Mark` and `DEFAULT_LINE_PX` move to
`letters.setting` unchanged; the instance's generator is explicit;
`Hand.measure(text, size, tracking=0.0) -> (width, height)` returns the face's own
metrics; `Hand.generator(seed: int) -> numpy.random.Generator` mixes `HandStyle`'s
`label_seed` into the seed `maps` derives from what names the instance (today's
`_seed`, exact when `maps` passes the CRC of the same parts); and
`Hand.stroke(points, rng, amount) -> list[Pt]` is the hand's own wander along a line the
caller drew, from which the caller builds the `Mark` with its own role, ink, size and,
where it draws one, pen tilt.

| | Shape 1, one value | Shape 2, two primitives |
|---|---|---|
| Write | `Hand.write(setting: Setting, rng) -> list[Mark]` | `Hand.along(text, line, size, rng, *, slant, tracking, ink, wash) -> list[Mark]` and `Hand.at(text, anchor, size, rng, *, lines, align, slant, tracking, ink, wash) -> list[Mark]` |
| New type | `Setting(text, size, anchor=None, path=None, align="start", slant=0.0, tracking=0.0, ink="map", lines=(), wash=True)`, frozen, hashable | none, or a parameter object once `at` is cut down to the argument limit |
| Mode | `path` or `anchor`, exactly one; validated on construction | which method is called |
| Invalid combinations | both or neither of `anchor` and `path`; a path with `lines`, an `align` or under two points: all refused by `Setting.__post_init__` | unrepresentable |
| Argument limit (`max-args = 6`) | `write` takes two besides `self` | `along` takes eight besides `self` and `at` ten: both need a parameter object, which is `Setting` by another name |
| One test with a string and a line | `write(Setting("Grasmere", 14.0, path=line), rng)` covers the entry point | covers `along`; `at` needs its own |
| Record for a batching caller | the `Setting` itself | the caller builds one per call |
| Public names in `letters` | `Setting`, `Mark`, `DEFAULT_LINE_PX`, `Align`, `Hand` with `measure`, `generator`, `write`, `stroke` | `Mark`, `DEFAULT_LINE_PX`, `Align`, `Hand` with `measure`, `generator`, `along`, `at`, `stroke`, plus the parameter object |

The plan's Shape 1 carried `seed: int` in the setting. It is left out: the furniture
needs the generator positioned after the glyphs (fact 1), so the generator crosses the
interface either way, and a setting that also held a seed could disagree with the
generator it is written with.

### How `maps` translates labels and spans (either shape)

All of this is `maps` code (`maps/lettering_marks.py`), reading `Label` and `Span` and
the map tables (`KIND_INK`, `KIND_SLANT`, `KIND_TRACKING`, `SPAN_INTENT_INK`,
`HOME_GLYPH`, `NO_LEADER`):

1. `rng = hand.generator(crc32("|".join(parts)))` with today's parts (name and rounded
   anchor for a label; name, start index and `"span"` for a span).
2. Ink, slant and tracking from the kind, tier and intent, as `_ink` and
   `_label_marks` do now (the span effort slant included). `wash` is `not in_water`.
3. Window choice (`_baseline`, moved whole with `_resample`, `_window`, `_turning` and
   `_bow`), using `hand.measure(name, size, tracking)[0]` as the set width; the window
   is never upside down. If a window is chosen, the path is that window offset by
   `lift_baseline(label, lift)`, the line the letters sit on.
4. Shape 1: `Setting(name, size, path=walk, ...)` or
   `Setting(name, size, anchor=(tx, ty), align=anchor, lines=wrapped, ...)`.
   Shape 2: the matching `along` or `at` call.
5. `hand.write(setting, rng)` (or the primitive): the hand draws the pen tilt first and
   then the glyphs, exactly as `_label_marks`, `_along` and `_flat` do.
6. The furniture, in today's order, from the same `rng`: pin, leader, home glyph,
   underline. Each is `maps` geometry (`_pin`, `_leader` with `_quad_at`,
   `_underline`, `HOME_GLYPH`) passed through `hand.stroke(points, rng, amount)` and
   wrapped in a `Mark` with role `pin`, `leader`, `span`, `underline`.
7. A span: its line through `hand.stroke`, then its pen tilt drawn from `rng`, then
   each tick through `hand.stroke`; marks with roles `span` and `tick`. Its name is a
   placed label and goes through steps 1 to 6 like any other.

### How furniture goes through the same nib

The nib plate takes `Sequence[Mark]` and does not know who made a mark. Furniture marks
carry the roles the nib already weights (`pin`, `leader`, `underline`, `span`, `tick`)
and get the hand's wander from `Hand.stroke`, so they are written with the same hand and
run through the same nib profile, ink pad and backing wash as the glyphs. `letters` has
no name for a leader, a pin or a tick.

## Decision

**Shape 1**: `Setting` in `letters.setting`, `Hand.write(setting, rng) -> list[Mark]`,
with `Hand.measure`, `Hand.generator` and `Hand.stroke` as above.

Against the plan's criteria:

- **No `Label`, `Span`, tier, kind or intent reaches `letters`.** Both shapes meet it.
- **The plate key derives from the input without a key list.** Both shapes meet it the
  same way, by keying on the marks (below); Shape 1's setting is a ready hashable
  record if a later key wants the settings too, where Shape 2 would need one built.
- **Window choice moves to maps placement.** Both: a setting takes the chosen, lifted,
  oriented line and the hand never chooses or reverses one.
- **One test with a string and a line covers the interface.** Shape 1: one call covers
  the one entry point. Shape 2 leaves `at` uncovered by that test.
- **Fewest public names.** Shape 1. Shape 2 trades `Setting` for a second method and
  still needs a parameter object, because both its methods are over the six-argument
  limit with no `noqa` allowed outside `_port`. That is the deciding reason: Shape 2's
  one advantage, no invalid modes, does not survive the argument limit, and the
  parameter object it needs is the setting.
- **Parity stays exact.** Both, given the shared generator and the draw order above.

The cost of Shape 1 is that its mode is a run-time check, not a type: a setting with
both or neither of `anchor` and `path` is refused on construction rather than
unrepresentable. The check is three conditions in `__post_init__`, tested.

### The label plate key

The lettering key is derived from the marks, the nib plate's own input, in a canonical
form (every coordinate rounded to three decimals, as ADR 0003 does for the base hash),
with the lettering style digest and the base hash. It covers the furniture (fact 4)
with no list of fields, and it no longer changes when a label's undrawn fields (`why`)
change. The price is writing the marks before the cache check: measured at `186ac3f`,
writing 40 labels (about 2,100 marks, 107,000 points) took 0.45 s, and a JSON hash of
the rounded points 0.25 s, against a nib raster that the key exists to skip. The settings
tuple alone is not a sufficient key, and neither shape changes that.

## Facts P3.17 could have moved, checked against `edc4381`

P3.17 (`b0ac21a`) rewrote `_port/labels.py` and `_port/mapcard.py`. Each fact above was
re-read on `main`:

- **Callers of `hand()` and `Hand.measure`: changed.** `mapcard` and `alphabet_sheet`
  are deleted. `hand()` is now called by `maps/lettering.py`'s `letter`, which passes
  `hand.measure` to `home_labels` and `place`, and by `maps/attribution.py`. `place`,
  `place_spans` and `home_labels` now require a measure (no default flat measure, no
  `measure_fn=None`), so the placer's box is always the hand's (`width + size * 0.5`,
  `Hand.measure` itself is unchanged and still has no tracking).
- **`Hand.marks` has one caller, `draw_plate`: unchanged**, and `letter` is the only
  caller of `draw_plate`. But `maps/attribution.py` now calls the private
  `Hand._label_marks` directly, on a `Label` it builds for the credit line, and sizes
  its block from `hand.measure` including the pad. The `maps` translation in P4.5 must
  therefore serve the attribution too, and keep the pad as a `maps` wrapper over the
  unpadded `Hand.measure` so the block size stays exact.
- **`plate_key` rows: unchanged** (label rows with `intent`, `lift`, `flat`, `lines`,
  `window`; span rows with the line), so fact 4 stands. The attribution plate is not
  keyed.
- **Draw order in `_label_marks` and `_span_marks`: unchanged** (fact 1 and step 6 hold).
- **`place`'s `measure_fn` default: gone**; the parameter is required.

None of this alters the decision: Shape 1, the explicit generator, the marks-keyed
plate and the draw order stand. The attribution caller adds one consumer of the
translation, not a new requirement on the interface.

## Consequences

- `letters.setting` holds `Setting`, `Mark`, `DEFAULT_LINE_PX` and `Align` now;
  `_port.labels` imports `Mark` and `DEFAULT_LINE_PX` from it.
- P4.5 builds `Hand.write`, `Hand.measure` (with tracking, without the placer's pad),
  `Hand.generator` and `Hand.stroke` (returning points; the caller makes the `Mark`),
  and `maps/lettering_marks.py` as described above. It keeps the draw order exactly.
- P4.7's lettering key takes `Sequence[Mark]`, not `Sequence[Setting]`; no record type
  is needed for Shape 2 because Shape 2 was not chosen.
- Changing `Setting`'s fields, the generator contract or the key's input is a new ADR.
