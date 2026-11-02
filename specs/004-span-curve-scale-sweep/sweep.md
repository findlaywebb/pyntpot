# 004 — sweep

Written by `tests/fixtures/sweep_span_scale.py`. Cap height 14 px; offset `SPAN_OFFSET_CAPS` = 1.2 caps; stretches every 2 caps.

## Stretches by case, 16-cap length, before the vote

| fixture | stretches | no-outside | empty-mark | ambiguous-feet | even | decisive |
|---|---|---|---|---|---|---|
| ambleside | 40 | 0 | 0 | 0 | 36 | 4 |
| skye | 93 | 6 | 19 | 4 | 40 | 24 |
| y-fenni | 43 | 10 | 18 | 0 | 12 | 3 |

The decisive pool before the vote is 31 stretches: ambleside 4, skye 24, y-fenni 3. 77% of it is Skye's.

## Sweep, 16-cap length (decides)

| scale | voted | empty-mark | ambiguous-feet | even | decisive | right | % right |
|---|---|---|---|---|---|---|---|
| 0.6 | 9 | 1 | 0 | 7 | 0 | 0 |  |
| 0.7 | 7 | 0 | 0 | 6 | 0 | 0 |  |
| 0.8 | 9 | 2 | 0 | 6 | 0 | 0 |  |
| 0.9 | 10 | 1 | 0 | 7 | 0 | 0 |  |
| 1.0 | 16 | 4 | 0 | 7 | 0 | 0 |  |
| 1.1 | 18 | 1 | 1 | 10 | 1 | 0 | 0.0 |
| 1.2 | 18 | 2 | 0 | 12 | 3 | 1 | 33.3 |
| 1.3 | 26 | 4 | 0 | 15 | 3 | 0 | 0.0 |
| 1.4 | 27 | 3 | 2 | 13 | 5 | 1 | 20.0 |
| 1.5 | 35 | 5 | 3 | 17 | 4 | 1 | 25.0 |
| 1.6 | 34 | 6 | 2 | 14 | 5 | 1 | 20.0 |
| 1.7 | 37 | 6 | 2 | 21 | 3 | 0 | 0.0 |
| 1.8 | 39 | 5 | 3 | 20 | 5 | 0 | 0.0 |
| 1.9 | 38 | 9 | 4 | 21 | 1 | 0 | 0.0 |
| 2.0 | 41 | 5 | 2 | 26 | 4 | 0 | 0.0 |
| 2.1 | 49 | 7 | 2 | 25 | 6 | 0 | 0.0 |
| 2.2 | 55 | 7 | 2 | 30 | 6 | 0 | 0.0 |
| 2.3 | 52 | 9 | 1 | 31 | 4 | 0 | 0.0 |
| 2.4 | 50 | 8 | 2 | 29 | 4 | 0 | 0.0 |
| 2.5 | 61 | 12 | 2 | 32 | 7 | 0 | 0.0 |

## Decision

- `n` at 1.5: 4.
- 4 decisive stretches at 1.5 are too few to compare.
- Scale: 1.5 (kept).

## Sweep, 10-cap length (reported only; scales to 2.0)

185 stretches.

| scale | voted | empty-mark | ambiguous-feet | even | decisive | right | % right |
|---|---|---|---|---|---|---|---|
| 0.6 | 17 | 4 | 0 | 8 | 2 | 1 | 50.0 |
| 0.7 | 18 | 4 | 1 | 9 | 1 | 1 | 100.0 |
| 0.8 | 27 | 5 | 1 | 13 | 3 | 2 | 66.7 |
| 0.9 | 26 | 4 | 1 | 13 | 5 | 3 | 60.0 |
| 1.0 | 35 | 7 | 2 | 19 | 4 | 2 | 50.0 |
| 1.1 | 40 | 8 | 3 | 21 | 3 | 2 | 66.7 |
| 1.2 | 47 | 8 | 3 | 25 | 5 | 3 | 60.0 |
| 1.3 | 50 | 10 | 4 | 27 | 5 | 2 | 40.0 |
| 1.4 | 53 | 11 | 4 | 27 | 6 | 3 | 50.0 |
| 1.5 | 54 | 10 | 3 | 29 | 6 | 3 | 50.0 |
| 1.6 | 59 | 10 | 5 | 31 | 5 | 1 | 20.0 |
| 1.7 | 62 | 10 | 5 | 35 | 6 | 2 | 33.3 |
| 1.8 | 60 | 11 | 5 | 33 | 6 | 2 | 33.3 |
| 1.9 | 59 | 12 | 4 | 33 | 7 | 3 | 42.9 |
| 2.0 | 65 | 11 | 4 | 38 | 9 | 4 | 44.4 |

## Sweep, 24-cap length (reported only; scales to 2.5)

164 stretches.

| scale | voted | empty-mark | ambiguous-feet | even | decisive | right | % right |
|---|---|---|---|---|---|---|---|
| 0.6 | 4 | 0 | 0 | 3 | 0 | 0 |  |
| 0.7 | 4 | 0 | 0 | 3 | 0 | 0 |  |
| 0.8 | 4 | 0 | 0 | 3 | 0 | 0 |  |
| 0.9 | 4 | 0 | 0 | 3 | 0 | 0 |  |
| 1.0 | 11 | 1 | 1 | 5 | 0 | 0 |  |
| 1.1 | 8 | 1 | 0 | 4 | 0 | 0 |  |
| 1.2 | 13 | 3 | 1 | 5 | 2 | 0 | 0.0 |
| 1.3 | 18 | 1 | 1 | 7 | 5 | 1 | 20.0 |
| 1.4 | 13 | 2 | 0 | 5 | 4 | 1 | 25.0 |
| 1.5 | 24 | 5 | 2 | 6 | 6 | 1 | 16.7 |
| 1.6 | 28 | 6 | 1 | 8 | 5 | 1 | 20.0 |
| 1.7 | 26 | 7 | 1 | 8 | 4 | 0 | 0.0 |
| 1.8 | 27 | 4 | 1 | 11 | 7 | 1 | 14.3 |
| 1.9 | 26 | 2 | 1 | 8 | 10 | 1 | 10.0 |
| 2.0 | 27 | 4 | 1 | 10 | 8 | 1 | 12.5 |
| 2.1 | 36 | 5 | 1 | 14 | 9 | 1 | 11.1 |
| 2.2 | 39 | 8 | 1 | 16 | 8 | 1 | 12.5 |
| 2.3 | 40 | 12 | 2 | 13 | 8 | 1 | 12.5 |
| 2.4 | 37 | 10 | 1 | 15 | 7 | 0 | 0.0 |
| 2.5 | 38 | 8 | 1 | 15 | 9 | 0 | 0.0 |

---

## Reading (added after the run)

The sweep was run once, after the rule was committed (`0adadf0`; tool `e7b7a9e`). The
decision rule's first clause applies: 4 decisive stretches at 1.5 (1 right, 25%) are
under 30, so **1.5 is kept** and no scale is compared, as the spec expected. No scale
reaches 30 decisive stretches at any length (the most is 10). That is the honest
answer: on the three public fixture tracks, the scales from 0.6 to 2.5 cannot be told
apart.

Recorded, not acted on: wherever a scale has decisive stretches, the outside is the
better mark on fewer than half of them at the 16- and 24-cap lengths (0 to 33%), and on
20 to 100%, mostly near half, at 10 caps. With counts this small that is no evidence for
any scale. It does raise the question of whether the bend's vote helps at all, which is the
`SPAN_CURVE_SIDE` and `SPAN_CURVE_WEIGHT` follow-up, not this spec. The pool is 31
decisive stretches before the vote, 77% of them Skye's; plan review round 3's probe
counted 32.

In the sweep tables `voted` is more than the sum of the case columns, because the
`no-outside` case (both sides empty, so `_convex_side` returns 0) has no column: at 1.5,
35 voted against 5 + 3 + 17 + 4 = 29.
