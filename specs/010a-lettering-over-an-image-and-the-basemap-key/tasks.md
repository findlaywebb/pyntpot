# 010a — tasks

Slices and files are in `plan.md`. Order: Start, S0, S1, S2, S3, S4a, then the merge gate
(S4b in, which may run in a worktree cut after S0), S5, S6, S7, S8. Stacks on 010.

## Start

- [ ] 010 merged (or this branch rebased on its tip); ADR 0073 present.
- [ ] Comment the branch name and spec `010a` on #165 and #167.
- [ ] Counts in the spec re-measured on the base; the spec corrected if any moved.
- [ ] The plan-reviewer passes the plan.

## S0: Baseline hashes

- [ ] On the untouched base: `output_hashes.py record specs/010a-lettering-over-an-image-and-the-basemap-key/output-hashes.json`, committed alone; `check` passes.

## S1: The plate resize in `ink`

- [ ] Red: `rgba_image` rounding at pinned literals; `save_rgba` writes it; `shrunk_rgba`
      size and premultiplied (no red from a transparent half); `grown_bilinear`.
- [ ] `ink/plate_resize.py`; `save_rgba` uses `rgba_image`; slice gate green.

## S2: Split the backing wash (pure move)

- [ ] `_backing_wash` and its four constants to `letters/backing_wash.py` as
      `backing_wash`; `TestBackingWash` to `tests/unit/letters/test_backing_wash.py`.
- [ ] `git diff -M` shows only the move, the rename, imports and the module docstring;
      same test count; slice gate green.

## S3: `nib_rgba`, `letter_over`, `NibGroups` defaults

- [ ] Red: `test_nib_rgba.py`; `test_letter_over.py` (the two parity tests against the
      examples' recipe, defaults, copy, unchanged input, far pixel, errors);
      `NibGroups` defaults in `test_style.py`.
- [ ] `nib_rgba`, `nib_plate` over it; `letter_over` in `letters/image_lettering.py`;
      `NibGroups` `default_factory` fields.
- [ ] Exports, `letters` docstring, `docs/reference/letters.md`, `test_public_api.py`.
- [ ] Slice gate, coverage gate, strict docs build green.

## S4a: The attribution in memory

- [ ] Red: `tests/architecture/test_no_plate_round_trip.py` (fails on `attribution.py`).
- [ ] `draw_attribution` on `nib_rgba` and `shrunk_rgba`; no temporary directory.
- [ ] Slice gate; golden `test_map_styles.py` and `test_places.py`; output hashes of
      `route_map`, `place_card` and `map_styles` unchanged.

## S4b: The basemap's key

- [ ] Red: `fetch(...).key == KEY == cache.key(...)`; `canonical` ignores `key`; a
      `Basemap` without `key` raises `TypeError`.
- [ ] `Basemap.key` (required, keyword-only, last, documented); `build_basemap` sets it;
      module invariant rewritten; CLI and `tests/support/golden.py` read `basemap.key`;
      the three test builders pass `key=`.
- [ ] Slice gate and coverage gate green.

## Merge gate

- [ ] S4b merged; slice gate and coverage gate green on the merged tree.

## S5: Records

- [ ] Glossary "nib plate" and "basemap" rows; regenerated.
- [ ] The #165 and #167 notes deleted, links repointed to ADR 0073; their sweep added to
      `docs-examples-review.md` under 010b.
- [ ] Slice gate, strict docs build, dash check.

## S6: The pixel proof

- [ ] `output_hashes.py check`: 91 entries unchanged.
- [ ] Golden suite green, no regeneration; `git status --porcelain docs/images tests/golden` empty.

## S7: Mutation testing

- [ ] Patterns from `scope.py`, `backing_wash` dropped as moved; survivors killed or
      named in `mutation.md`.

## S8: Final review and PR

- [ ] Fresh-context diff review against the plan; elegance pass; findings triaged.
- [ ] PR: title `feat(letters): letter over an image in one call, with an in-memory nib plate`,
      the four Changelog lines (the `Basemap` one with `!`), `Closes #165`, `Closes #167`,
      mutation equivalents, "Golden and docs images: none moved" with the S6 evidence.
