# Shared random generators amplify sub-pixel changes

The painter and the lettering draw from random generators shared down a sequence of
independent items: one generator deforms every cover ring in `deform_ring`, one
`bloom_rng` places the blooms of every cover class, the lake and the sea in `bloom`, and
one label generator stamps every stroke of the map-ink group. A discrete decision early
in the sequence (a median test, an argmax, an `int()` or `round()`, a seed taken from a
rounded position) that flips under a sub-pixel change alters how much the generator
consumes, so everything drawn after it changes. Bloom placement is non-local as well: its
candidate centres are addressed by rank in raster order, so a coast that moves by under a
pixel relocates blooms in open sea.

Evidence: dropping the seam's 0.1 m rounding (ADR 0006) moved each point by
at most 0.05 m, yet moved 0.207 of the wash plate, 0.042 of the labels-centreline plate and
0.193 of the composed map. With the deform round counts, the bloom placements and the
lettering seeds held at their previous values, every output moved by under 0.005; the
remainder was edge antialiasing.

Possible fix: per-item generators seeded from stable ids (a ring's, a wash's or a label's
identity rather than its place in a sequence), and bloom seeding by local position rather
than raster rank, so a change to one item moves only that item's pixels.

Any fix here moves
the goldens and needs its own regeneration.
