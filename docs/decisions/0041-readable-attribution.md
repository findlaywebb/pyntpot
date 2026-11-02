# 0041 — Readable attribution: the fifth golden regeneration

Status: accepted

## Context

The maintainer reviewed the published maps and found the credit at the bottom right of
every card unreadable. It is the OpenStreetMap and elevation attribution, a licence
obligation, so it must be legible. The cause was in units: `ATTRIBUTION_SIZE_PX = 11.0`
was applied to the composed image at render size, which is the display width times
`card.supersample` (2), and the docs images are then downsized with Lanczos to the entry's
width (1440 to 720). The type landed near 5 display pixels. Its nib plate was also stroked
at `NibSurface` scale 1, so the strokes were coarse at that size.

## Decision

- **Sizes are in display pixels.** `draw_attribution(image, text, style, scale)` takes the
  card's render scale (render pixels per display pixel; `compose` passes the one it already
  computes) and multiplies the type size, the plate padding and the margin by it, so they
  survive the downsizing. `attribution_size(display_width)` is
  `max(12, 13 * display_width / 720)`: 13 display pixels on the 720 px published card
  (x-height about 6 px, which reads at 100 percent; 12 was tried by eye as the least that
  does), growing with the card so a larger card published smaller keeps 13 at the published
  width, and never under 12. The margin is 10 display pixels (was 8 render pixels).
- **A crisp plate.** The plate is stroked at no less than two render pixels per display
  pixel and shrunk to the block with Lanczos on premultiplied pixels, as the examples do for
  lettering. A card already composed at render scale 2 (the default supersample) adds no
  extra plate scale: an extra 2x there doubled `compose`'s time on the benchmark (3.3 s to
  5.3 s on CodSpeed) for no visible gain. The larger type still costs some time, about
  0.8 s on a 720 px card at scale 2, the price of a credit that can be read.
- **Wrapping.** A line wider than 70 percent of the card is broken into two right-aligned
  lines at the " · " separator nearest its middle, the dot being the break; the type is not
  shrunk under the floor. A line without a separator is not broken. The text is otherwise
  unchanged.
- The pinned text, `attribution_text` and the credits are untouched.

Verified by eye: the bottom right of the 720 px Ambleside showcase card, before and after,
at 100 percent (`credit-before-after.png` in the scratchpad of the run). Before, the line is
a smear; after, "OpenStreetMap contributors (openstreetmap.org/copyright) · elevation: NASA
SRTM" reads on one line at 58 percent of the card width.

## Golden regeneration (the fifth)

Process as ADR 0036. The tolerance bound is not changed, no gate is loosened and the hash
input does not change.

- **Lynmouth goldens did not move.** `make_golden.py --compare tests/golden/lynmouth` on the
  new code: every output byte-identical (differing fraction 0.000000) and the manifest hash
  equal, `340a7f6e260ee1e2-d9c56c0811177b0f`. The fixture card is composed with
  `attribution=False`, so nothing there reads the credit. `GOLDEN_HASH` is not re-pinned.
- **Docs images and masters.** Every map docs image that carries the credit, and its master,
  is repainted with `make_docs_images.py`; only the bottom-right block moves. The place pins
  and map-styles means are re-pinned only if the run moves them.

## Consequences

- The credit is readable at the published scale and stays so at any card width.
- `draw_attribution` has a fourth argument, `scale`, default 1.0 (display pixels equal image
  pixels).
- A further regeneration needs its own ADR.
