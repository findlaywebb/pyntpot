# 010a — tasks

Revision 2: matches `plan.md` revision 2.

Slices and files are in `plan.md`. Order: Start, S0, S1, S2, S3, S4a, then the merge gate
(S4b in, which may run in a worktree cut after S0), S5, S6, S7, S8. Stacks on 010.

## Start

- [ ] 010 merged (or this branch rebased on its tip); ADR 0073 present.
- [ ] Comment the branch name and spec `010a` on #165 and #167.
- [ ] Counts in the spec re-measured on the base; the spec corrected if any moved.
- [ ] The plan-reviewer passes the plan.

## S0: Baseline hashes

- [ ] On the untouched base: `output_hashes.py record specs/010a-lettering-over-an-image-and-the-basemap-key/output-hashes.json`, committed alone, the base commit named in the message (S7's mutation base); `check` passes.

## S1: The plate resize in `ink`

- [ ] Red: `rgba_image` rounding at pinned literals; `save_rgba` calls through it;
      `shrunk_rgba` size and premultiplied (no red from a transparent half); the same-size
      pin `(200, 100, 50)` at alpha `3 / 255` reads `(170, 85, 85, 3)`; `grown_bilinear`.
- [ ] `ink/plate_resize.py` with `shrunk_rgba` as `.convert("RGBa").resize(...).convert("RGBA")`;
      `save_rgba` uses `rgba_image`; slice gate green.

## S2: Split the backing wash (pure move)

- [ ] `_backing_wash` and its four constants to `letters/backing_wash.py` as
      `backing_wash`; `TestBackingWash` to `tests/unit/letters/test_backing_wash.py`.
- [ ] `git diff -M` shows only the move, the rename, imports and the module docstring;
      same test count; slice gate green.

## S3: `nib_rgba`, `letter_over`, `NibGroups` defaults

- [ ] Red: `test_nib_rgba.py` (decode claim with the default lossless `PaperStyle()`);
      `test_letter_over.py` (the two parity tests against the recipe written out, grain
      `5.0 * 2`, `Setting("Keswick", 22.0, anchor=(8.0, 52.0))`, zero and ramp darkness;
      defaults, copy, unchanged input, corner `[0, 159]`, `scale=1`, errors); `NibGroups`
      defaults in `test_style.py`.
- [ ] `nib_rgba` cites `nib`; `references.md`'s `nib` entry lists it.
- [ ] `nib_rgba`, `nib_plate` over it; `letter_over` in `letters/image_lettering.py`;
      `NibGroups` `default_factory` fields.
- [ ] Exports, `letters` docstring, `docs/reference/letters.md`, `test_public_api.py`.
- [ ] Slice gate, coverage gate, strict docs build green.

## S4a: The attribution in memory

- [ ] Red: `tests/architecture/test_no_plate_round_trip.py` (no `nib_plate`, `Image.open`
      or `tempfile` in `attribution.py`; no `tempfile` in `letters`; fails on the base);
      the lossy-style case in `test_attribution.py` (fails on the base).
- [ ] `draw_attribution` on `nib_rgba` and `shrunk_rgba`; no temporary directory.
- [ ] Slice gate; golden `test_map_styles.py` and `test_places.py`; output hashes of
      `route_map`, `place_card` and `map_styles` unchanged.

## S4b: The basemap's key

- [ ] Red: `fetch(...).key == KEY == cache.key(...)`; `("key", "0" * 16)` in
      `OUTSIDE_THE_HASH`; a `Basemap` without `key` raises `TypeError`
      (`ty: ignore[missing-argument]`).
- [ ] `Basemap.key` (required, keyword-only, last, documented); `build_basemap` sets it;
      module invariant rewritten; CLI and `tests/support/golden.py` read `basemap.key`;
      the three test builders pass `key=KEY`.
- [ ] Slice gate and coverage gate green.

## Merge gate

- [ ] S4b merged; slice gate and coverage gate green on the merged tree.

## S5: Records

- [ ] Glossary "nib plate" and "basemap" rows; regenerated.
- [ ] The #165 and #167 notes deleted; the mentions in `docs-how-to-write-a-provider.md`
      and `docs-tutorial-opening-programs.md` name the issues and ADR 0073; their sweep,
      with the grid `gran_px` halving sentence, added to `docs-examples-review.md` under
      010b; the `git grep` gate empty.
- [ ] Slice gate, strict docs build, dash check.

## S6: The pixel proof

- [ ] `output_hashes.py check`: 91 entries unchanged.
- [ ] Golden suite green, no regeneration; `git status --porcelain docs/images tests/golden` empty.

## S7: Mutation testing

- [ ] Patterns from `scope.py --base <S0's recorded base>`, `backing_wash` dropped as
      moved; survivors killed or named in `mutation.md`.

## S8: Final review and PR

- [ ] Fresh-context diff review against the plan; elegance pass; findings triaged.
- [ ] PR: title `feat(letters): letter over an image in one call, with an in-memory nib plate`,
      the four Changelog lines (the `Basemap` one with `!`), `Closes #165`, `Closes #167`,
      mutation equivalents, "Golden and docs images: none moved" with the S6 evidence.
