# 0071 — Golden regeneration: one route colour, pigments that carry their transparency, and bold's cased route

Status: accepted

Spec: `specs/009a-line-effect-figures-and-galleries/`. Issues: #159, #69, #70, #67, #104, #105,
#106. This is the second half of the work ADR 0070 began: it applies rules 17 and 18 of that
ADR and regenerates the goldens once. It does not amend ADR 0070, whose rule 17 was edited in
place to the rule below because 0070 was unmerged.

## Context

ADR 0070 fixed two pixel-moving rules for a second pull request: a fed route colour also letters
the start and finish markers (rule 18, #159), and a pigment carries its own transparency, so
`paper.pigment_transparency` goes (rule 17). That pull request also shows the line effects and
the registry's catalogues with figures and galleries, and bold, whose theme had declared a
cased route since ADR 0046, adopts the `cased` preset.

## Decision

- **`CoverPigment` is public.** `pyntpot.maps.CoverPigment(colour, transparency)` is a
  `NamedTuple`, one entry of `CoverStyle.pigments`. It is a leaf: the theme checker reads a
  tuple as a leaf, a merge replaces it whole, and `dataclasses.asdict` keeps it, so a child
  theme's entry for a class replaces its parent's and never inherits half of it. A theme
  writes it as a ref string or as `{pigment, transparency}`, never as a list. A transparency
  of `None` means `paper.km_transparency` and only Python builds one.
- **Transparency precedence (rule 17).** The entry's own, else the resolved pigment's own (a
  derived pigment's base's), else the cover class's built-in pigment's, so a bare hex in a
  theme does not change look. The class key reaches the validator through validation context,
  beside `scope`. The painter stays registry-free.
- **`RENAMED_KEYS` departs from ADR 0069.** ADR 0069 makes a removed field fail as an unknown
  key. `paper.pigment_transparency` did not vanish: its value moved to
  `cover.pigments.<class>.transparency`. So `theme_check.RENAMED_KEYS` carries one row for it,
  and the error names where the value went. No second retired-key mechanism is added.
- **The tuned presets (D1)**, chosen by eye on the Ambleside fixture, pinned by
  `test_the_presets_hold_the_values_tuned_by_eye`:

  | Preset | Provisional | Tuned |
  | --- | --- | --- |
  | `cased` | `width_px` 1.2, `strength` 1.0 | `width_px` 1.8, `strength` 0.9 |
  | `halo` | `spread_px` 1.0, `blur_px` 2.5, `strength` 0.8 | `spread_px` 1.5, `blur_px` 3.0, `strength` 0.85 |
  | `lifted` | `offset_px` 1.2, `blur_px` 1.5, `strength` 0.35 | `offset_px` 2.5, `blur_px` 2.0, `strength` 0.45 |

- **bold cases its route.** `bold.yaml` sets `line_effects: {route: cased}`. This moves
  `digest()` at compose only; bold's base plates and nib plate are byte-identical.
- **Regenerated once, at the end.** Each figure slice committed its own new images; only two
  images moved, and no other.

## The Lynmouth compare

`repaint.py` against `tests/golden/lynmouth`, on the pinning machine:

```
paper.webp: identical yes, differing fraction 0.000000
wash.webp: identical yes, differing fraction 0.000000
pen.webp: identical yes, differing fraction 0.000000
labels-centreline.webp: identical yes, differing fraction 0.000000
map.png: identical yes, differing fraction 0.000000
manifest hash: 90193bbb26f681bf-ebe16b5246aeb21f here, 90193bbb26f681bf-d9c56c0811177b0f before
```

Only the base digest half moved (rule 17 changes the style's base group); `plates.json`
alone changed, and every Lynmouth image is byte-identical.

## Moved images

| Image | Differing fraction | Extent | Reason |
| --- | --- | --- | --- |
| `docs/images/how-to/route-ink.webp` | 0.015441 | widespread | #159: "start" and "finish" from pink to the route colour |
| `tests/golden/docs/how-to/route-ink.png` (master) | 0.000634 | local | same |
| `docs/images/map-styles/bold.webp` | 0.300743 | widespread | the route is cased with `cased` |
| `tests/golden/docs/map-styles/bold.png` (master) | 0.054654 | local | same |

`MEAN_RGB["bold"]` is re-pinned to (214.1, 209.6, 184.8). The widespread fractions are the
lossy encoder's noise round a changed region; the difference images show the change itself on
the route and its markers only.

Pins that moved with identical pixels (ADR 0070 rule 16): the style digest and base digest of
the default style, the six example themes and the four named themes, `SOURCED[PaperStyle]` and
`SOURCED[CoverStyle]`, `GOLDEN_HASH`'s base half, and the Lynmouth manifest hash above; bold's
`digest()` moves a second time for the cased route.

## Added images (20, with a master each)

Not moved: no pinned value changes. Each was added in its own slice.

| Image | Differing fraction |
| --- | --- |
| `explanation/line-effects-draw-order.webp` | none, added |
| `explanation/line-effects-glaze-or-rgb.webp` | none, added |
| `explanation/wash-granulation-sweep.webp` | none, added |
| `explanation/wash-pool-sweep.webp` | none, added |
| `how-to/casing-sweep.webp` | none, added |
| `how-to/glow-sweep.webp` | none, added |
| `how-to/line-effects-presets.webp` | none, added |
| `how-to/line-effects.webp` | none, added |
| `how-to/relief-strength.webp` | none, added |
| `how-to/shadow-sweep.webp` | none, added |
| `painting-with-python/cased-stroke.webp` | none, added |
| `painting-with-python/pen-casing-sweep.webp` | none, added |
| `reference/brush-dryness-sweep.webp` | none, added |
| `reference/brush-gallery-maj.webp` | none, added |
| `reference/brush-gallery-riv-str-lan.webp` | none, added |
| `reference/brush-gallery-trk.webp` | none, added |
| `reference/palettes.webp` | none, added |
| `reference/pigment-gallery-glazes.webp` | none, added |
| `reference/pigment-gallery-painters.webp` | none, added |
| `reference/pigment-gallery-roles.webp` | none, added |
## Retired image

| Image | Reason |
| --- | --- |
| `docs/images/reference/pigment-swatches.webp` and its master | its grey ink bar read as the same line on every swatch; the pigment galleries show transparency as washes at three strengths. `pigment-gallery-roles` shows in its place |

## Consequences

- A third-party theme that set `paper.pigment_transparency` fails with the new location named.
  An `extends` child's bare hex no longer keeps its parent's transparency for that class.
- A pigment's retune repaints every theme naming it.
- Any other moved image after this ADR is a defect in the slice that moved it.
