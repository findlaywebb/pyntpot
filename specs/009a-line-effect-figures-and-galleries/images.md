# 009a: golden and docs images (for the PR body)

Recorded by `diff_images.py --ref <merge base with origin/claude/quirky-hypatia-z2pii3>`. Not
pushed: `publish_diffs.py --push` writes outside the branch, so the orchestrator publishes it.
4 changed, 40 added (20 images and 20 masters), 2 removed. The fraction is the share of pixels
past channel delta 2; the parity bound is 0.005.

## Moved

| File | Differing fraction | Extent | Reason |
| --- | --- | --- | --- |
| `docs/images/how-to/route-ink.webp` | 0.015441 | widespread | #159: markers from pink to the route colour |
| `tests/golden/docs/how-to/route-ink.png` | 0.000634 | local | same |
| `docs/images/map-styles/bold.webp` | 0.300743 | widespread | bold's route cased with `cased` |
| `tests/golden/docs/map-styles/bold.png` | 0.054654 | local | same |

Lynmouth: every image byte-identical; `plates.json` hash `90193bbb26f681bf-ebe16b5246aeb21f`.

## Retired

| File | Reason |
| --- | --- |
| `docs/images/reference/pigment-swatches.webp` | replaced by the pigment galleries |
| `tests/golden/docs/reference/pigment-swatches.png` | its master |

## Added (each with a master of the same name under `tests/golden/docs/`)

- `explanation/line-effects-draw-order.webp`
- `explanation/line-effects-glaze-or-rgb.webp`
- `explanation/wash-granulation-sweep.webp`
- `explanation/wash-pool-sweep.webp`
- `how-to/casing-sweep.webp`
- `how-to/glow-sweep.webp`
- `how-to/line-effects-presets.webp`
- `how-to/line-effects.webp`
- `how-to/relief-strength.webp`
- `how-to/shadow-sweep.webp`
- `painting-with-python/cased-stroke.webp`
- `painting-with-python/pen-casing-sweep.webp`
- `reference/brush-dryness-sweep.webp`
- `reference/brush-gallery-maj.webp`
- `reference/brush-gallery-riv-str-lan.webp`
- `reference/brush-gallery-trk.webp`
- `reference/palettes.webp`
- `reference/pigment-gallery-glazes.webp`
- `reference/pigment-gallery-painters.webp`
- `reference/pigment-gallery-roles.webp`
