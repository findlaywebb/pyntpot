# 0067 — A leader's pin is an open ring facing its leader: a golden regeneration

Status: accepted

## Context

A leader points at a pin: a small ring drawn round the thing a name is about, never a
filled dot. `maps.lettering_furniture.pin` drew a closed ring of fourteen sides with its
centreline at `max(size * 0.14, 2.2)` display pixels, and `leader` started its curve 2 px
past the pin's centre, on the far side, so a stub of it crossed the ring's hole. GitHub
issue #130 measured the hole filling: a ring stroked with its leader read as a dot on most
seeds.

The first draft of this decision sized the ring round its hole (its centreline half a pen
outside `max(0.14 * size, 2.8)`, with a new `letters.nib.mark_width_px` for the pen) and
started the leader at the ring's outer edge. That kept the hole bare paper, at the cost of a
ring about a quarter wider and a leader that only touches its pin.

The maintainer reviewed it and changed the design. A ring that closes now and then is not
much of an issue, so the enlargement is dropped and the ring keeps the size it has always
had. What a hand-drawn callout does instead is open the ring where the line comes in: the
pen draws a C, and the leader runs through its gap into the middle, so the ring and its
leader read as one mark rather than a dot with a line attached. Choosing a different pin
icon per theme, and turning the rotation off, is filed as its own feature (issue #149).

## Decision

- **A leader's pin is an arc with a gap.** `pin(hand, lb, rng, *, gap_at, gap_px)` draws
  the ring at its old radius, `pin_radius(lb)` = `max(size * 0.14, 2.2)`, open by a chord
  of `gap_px` at the centreline, centred on the direction `gap_at`. The arc takes its share
  of the closed ring's fourteen sides (eleven at the shipped size), and is wandered by the
  hand as before (0.2), from the same keyed generator, stroked with the same `pin` pen, brush
  and jitter. The wander keeps a stroke's ends, so the two ends of the arc bound the gap
  exactly. A gap wider than the ring opens it to a half circle and no further.
- **The gap faces the leader.** `_furniture` now draws the leader first, then reads
  `leader_angle`: the direction from the pin's centre to where the wandered leader first
  reaches the ring's radius. That, not the straight line to the name, is `gap_at`, so a
  leader bent near its pin still comes in through the middle of its gap. Over 360
  directions the gap's bisector is within 16 degrees of the straight line to the name at
  11 px, and within 12 at 20 px; the difference is the leader's bend.
- **The gap is the leader's pen, two ring pens and the bristles' jitter.**
  `pin_gap_px(leader_px, ring_px)` = `leader_px + PIN_GAP_RING_PENS * ring_px +
  PIN_GAP_CLEAR_PX`, with `PIN_GAP_RING_PENS = 2` and `PIN_GAP_CLEAR_PX = 1.1`. Half a ring
  pen at each end is the arc's own ink running past its centreline; another half a pen each
  side is paper for the hand's wander; and 1.1 px is twice the default brush's sideways
  jitter (`brush_jitter_px`, 0.55), once each side, which does not shrink with the pen. At
  20 px that is 0.612 + 2.55 + 1.1 = 4.262 px, a gap of about 99 degrees; at 11 px 2.84 px,
  about 80 degrees. Two ring pens alone (3.16 px at 20 px) left the gap visible on the
  larger names but filled at 11 and 14 px, which read as a closed ring with a line through
  it. The pens are the nib's: `letters.nib.mark_width_px(nib, role, size)` gives the
  `leader` and `pin` widths, the same number `nib_brushes` strokes them at, so
  `lettering_marks.marks` and `label_marks` take the `NibStyle`.
- **The leader runs into the ring's centre.** `leader(hand, ends, rng)` starts on the pin's
  centre and ends on the name, as before, but no longer over-runs 2 px past the centre. Its
  bend and wander are unchanged. Over 72 directions at 11, 20 and 40 px the leader's
  centreline stays more than both half pens and 0.55 px from the arc's: 1.25 px at 11 px
  against 1.07 needed, 1.82 against 1.49 at 20 px.
- **A pin given no gap is the closed ring.** `gap_at=None` or a `gap_px` that is not
  positive draws the fourteen-sided ring, point for point the ring `main` drew. Every pin on
  a map has a leader (a label without one takes no pin), so none is drawn closed today; the
  closed ring is the default a theme can choose once issue #149 adds the field.
- **Room for the theme field.** The pin's shape and turn are parameters of `pin`, and the
  decision of what to pass is one place, `lettering_marks._furniture`. A later theme field
  selects the icon there and passes a fixed `gap_at` to turn the rotation off. No theme
  field is added here.
- Not changed: the ring's radius, pen, brush, jitter and wander, the leader's pen, bend and
  wander, and every other mark.

Pinned by `tests/unit/maps/test_lettering_furniture.py`: over 72 directions at 11, 20 and
40 px the gap is centred on the leader's crossing and within 20 degrees of its name, and
the leader's centreline clears the arc's by both half pens and the jitter; the leader runs
from the pin's centre to its name; the gap is 4.262 px at the shipped size; the chord across
the arc's ends is the gap asked for; an east-facing arc's ends are pinned literals; a gap
wider than the ring leaves a half circle; a pin with no gap, or a gap of no width, is the
closed ring, and a name without a leader takes no pin; the same label draws the same pin
and leader, and a north-east leader's marks are pinned. `TestMarkWidth` in
`tests/unit/letters/test_nib.py` pins `mark_width_px` and the brush widths `nib_brushes`
makes from it.

Issue #130 is closed as not planned: the maintainer judged a closing ring not worth the
larger pin, and the open ring is a change of design, not a fix of that fault. The leader now
runs into the ring by intent.

## Golden regeneration

Process as ADRs 0036 and 0052, run on `main` with #124, #128 and #145 merged. The
tolerance bound is not changed, no gate is loosened and the hash input does not change.

GOLDENS

## Consequences

- A leader and its pin read as one callout: the ring opens towards its name and the line
  runs into its middle.
- The ring is the size it was; only its gap and the leader's last 2 px change.
- The leader is drawn before its pin, so the label's generator gives the leader's bend and
  wander first and the ring's wander after: both are redrawn, the name's glyphs are not.
- `lettering_marks.marks` and `label_marks` take the nib style; a caller that letters names
  passes the one it will stroke them with.
- A further regeneration needs its own ADR.
