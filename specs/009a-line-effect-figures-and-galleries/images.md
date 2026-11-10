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

## Follow-up: casings anti-aliased and painted at 2x

Recorded by `diff_images.py --before` the tree at the pre-follow-up tip 9ef36cc6 `--after` a scratch repaint. 10 images and their 10 masters moved, 1 image and its master added, every other image unchanged. Lynmouth: every image byte-identical; `plates.json` hash `90193bbb26f681bf-ebe16b5246aeb21f` unchanged. `MEAN_RGB["bold"]` re-pinned from (214.1, 209.6, 184.8) to (214.2, 209.7, 185.0). Budgets: the 009a line-effects share is 361,066 bytes of 600,000 and the largest page image 230,762 bytes of 250,000; none edited.

### Moved

| File | Differing fraction | Extent | Reason | Judged at 2x |
| --- | --- | --- | --- | --- |
| `docs/images/explanation/line-effects-draw-order.webp` | 0.905005 | widespread | casings anti-aliased; third cell "casings as a union"; 2x | pass |
| `docs/images/explanation/line-effects-glaze-or-rgb.webp` | 0.803141 | widespread | casing column anti-aliased; 2x | pass |
| `docs/images/how-to/casing-sweep.webp` | 0.797262 | widespread | anti-aliased ring; 2x | pass |
| `docs/images/how-to/glow-sweep.webp` | 0.760201 | widespread | painted at 2x | pass |
| `docs/images/how-to/line-effects-presets.webp` | 0.133583 | widespread | the cased cell | pass |
| `docs/images/how-to/line-effects.webp` | 0.210213 | widespread | the cased road_major | pass |
| `docs/images/how-to/shadow-sweep.webp` | 0.786494 | widespread | painted at 2x | pass |
| `docs/images/map-styles/bold.webp` | 0.222238 | widespread | the cased route | pass |
| `docs/images/painting-with-python/cased-stroke.webp` | 0.876009 | widespread | anti-aliased casing; two reserve cells; 3 x 2; 2x | pass |
| `docs/images/painting-with-python/pen-casing-sweep.webp` | 0.693121 | widespread | continuous edge lines; 2x | pass |
| `tests/golden/docs/explanation/line-effects-draw-order.png` | 0.888506 | widespread | casings anti-aliased; third cell "casings as a union"; 2x | pass |
| `tests/golden/docs/explanation/line-effects-glaze-or-rgb.png` | 0.735417 | widespread | casing column anti-aliased; 2x | pass |
| `tests/golden/docs/how-to/casing-sweep.png` | 0.706397 | widespread | anti-aliased ring; 2x | pass |
| `tests/golden/docs/how-to/glow-sweep.png` | 0.652824 | widespread | painted at 2x | pass |
| `tests/golden/docs/how-to/line-effects-presets.png` | 0.013822 | local | the cased cell | pass |
| `tests/golden/docs/how-to/line-effects.png` | 0.034332 | widespread | the cased road_major | pass |
| `tests/golden/docs/how-to/shadow-sweep.png` | 0.695962 | widespread | painted at 2x | pass |
| `tests/golden/docs/map-styles/bold.png` | 0.029825 | local | the cased route | pass |
| `tests/golden/docs/painting-with-python/cased-stroke.png` | 0.865996 | widespread | anti-aliased casing; two reserve cells; 3 x 2; 2x | pass |
| `tests/golden/docs/painting-with-python/pen-casing-sweep.png` | 0.690011 | widespread | continuous edge lines; 2x | pass |

### Added

- `how-to/reserve-sweep.webp` and its master `tests/golden/docs/how-to/reserve-sweep.png`: the reserve sweep, new (added by the sweeps track, repainted unchanged).

### Verdicts (each image opened at 2x zoom)

- `how-to/casing-sweep`: pass. The ring is smooth and continuous at every width, with no pixelation, dotting or ringing; the paynes_grey row reads as a dark outline.
- `how-to/glow-sweep`: pass. Glow fades softly with no banding or halo ringing; in the blur 0 px row the 2, 4 and 6 px spreads have clean, continuous edges.
- `how-to/shadow-sweep`: pass. The south-east shadow is soft and smooth at 2x, with no stair-stepping.
- `how-to/reserve-sweep`: pass. The reserve cells show a clean paper ring at each width, and the pool 0.3 row gathers a faint darker edge just outside the ring, barely visible at 1x, with no drawn outline.
- `painting-with-python/pen-casing-sweep`: pass. The edge lines run continuous round the bends with no dotted breaks, at 1 to 4 px gaps.
- `painting-with-python/cased-stroke`: pass. The cased, glow and shadow cells are anti-aliased; the reserved and reserved pooled cells show the paper laid back without ringing.
- `explanation/line-effects-draw-order`: pass. The union cell is one unbroken ring round the junction with no seam, unlike the per-stroke cell's inner cut, and shows no ring through the first road, where the casings-first cell shows a faint pale band.
- `explanation/line-effects-glaze-or-rgb`: pass. The RGB casing ring is smooth; the glaze cell shows none, as intended.
- `how-to/line-effects`: pass. The cased `road_major` ring is smooth and continuous along the roads, with no dotting.
- `how-to/line-effects-presets`: pass. The cased cell shows a thin continuous ring; halo and lifted are soft with no ringing.
- `map-styles/bold`: pass. The cream-cased route is continuous and anti-aliased round every bend.
