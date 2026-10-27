# 0043 — Lossless plate effort: faster opaque plates, same pixels

Status: accepted

## Context

`save_webp` (`src/pyntpot/ink/io.py`) writes the paper and wash plates as lossless WebP at
`method=5` and Pillow's default quality of 80. For lossless WebP, method and quality set
how hard the encoder works to make the file small, not how close it is to the image: the
decoded pixels are the written ones whatever the setting. Writing the two opaque plates was
about 3.6 s of a 56 s Lynmouth paint (`specs/003-painter-hot-paths/`).

A sweep over methods 0 to 6 and qualities 10 to 100 on the Lynmouth paper and wash plates
(2026-10-27) found:

| Setting | Paper | Wash |
|---|---|---|
| method 5, quality 80 (before) | 2.04 s, 1,432,228 B | 1.57 s, 1,073,764 B |
| method 1, quality 40 (after) | 0.76 s, 1,409,538 B | 0.75 s, 1,071,772 B |
| method 0, quality 10 | 0.13 s, +29 % | 0.10 s, +27 % |

Methods 1 to 3 give the same bytes, and quality 40 the same bytes as 50. Every setting
decoded to the source pixels exactly.

The pen and labels plates carry alpha (`save_alpha`, `save_rgba`, method 4). There libwebp
rewrites the colour under fully transparent pixels, and only method 4 keeps today's decode
of those hidden pixels for both plates. They never reach a card, since compose pastes
through the alpha, but a changed hidden pixel would change a plate's decoded bytes.

## Decision

`save_webp` writes lossless plates at `method=1, quality=40`. `save_alpha`, `save_rgba` and
every lossy write keep their settings.

The plate files' bytes change once, and their decoded pixels do not. Re-pinned in the same
change, and only these: `tests/golden/lynmouth/paper.webp`, `wash.webp` and the `sizes` and
`bytes` of `plates.json`; `tests/golden/smoke/wash.webp` and `SMOKE_SHA["paper"]` and
`SMOKE_SHA["wash"]` in `tests/unit/maps/painter/test_smoke.py`. Each re-pinned image was
checked to decode equal to the image it replaced.

## Consequences

- A paint writes its opaque plates in under half the time. At map size the files are 0.2 to
  1.6 % smaller (Lynmouth paper 1,432,228 to 1,409,538 bytes, wash 1,073,764 to 1,071,772);
  a very small plate can grow (the 120-pixel smoke box's wash, 8,662 to 9,502 bytes).
- A plate written by an earlier version and one written now hold the same pixels in
  different bytes, so a cache comparing plate bytes across versions sees a change; the
  manifest's hash, which hashes the layers and style, does not change.
- Choosing method 0 would save another 1.3 s at about 28 % larger plates; that is a size
  decision, not taken here.
