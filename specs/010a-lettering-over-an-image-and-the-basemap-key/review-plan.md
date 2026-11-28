# 010a plan review

Reviewer: fresh-context plan reviewer. Measured on `d764a881` (branch `work-010`, main plus
the 010/010a spec commit), Pillow 13.0.0 (`uv.lock:1219-1220`). The scripts I ran are
throwaway, outside the repository.

## Verdict: BLOCK

The design is sound. The approach is right: split compositing from writing, keep the 8-bit
Lanczos step, share one private `ink` shrink, and add a required keyword-only
`Basemap.key` outside `canonical`. The slices are well partitioned, and most of the
plan's claims about the code hold (see "What I verified").

One finding stops it. **The prescribed `shrunk_rgba` is not bit-identical for the
attribution at the default supersample.** As written, S4a moves the attribution pixels on
every map card. The S4a hash gate would then fail, and the plan forbids re-recording, so
the agent has no prescribed way out. The fix is one call (`.convert("RGBa")` before the
resize, `.convert("RGBA")` after), plus one pinned test and a corrected sentence in the
spec and ADR 0073.

## Findings

### 1. [BLOCKING] `shrunk_rgba` drops the premultiply round trip when the size is unchanged, which the attribution hits at supersample 2

- **Plan:**
  - S1 `shrunk_rgba` is `rgba_image(rgb, alpha).resize(size, LANCZOS)`, and its docstring
    says Pillow premultiplies RGBA inside the resize.
  - S4a: `plate = shrunk_rgba(rgb, alpha, block)`.
  - Approach, first bullet: "Pillow converts RGBA to RGBa inside `resize`."
  - The same claim is in the spec's Problem section and in ADR 0073 rule 8
    (`specs/010-.../plan.md:82-90`).
- **Evidence:**
  - Pillow 13's `Image.resize` returns `self.copy()` when `self.size == size`. It does this
    **before** its `if self.mode in ["LA", "RGBA"] ... convert("RGBa")` branch (read from
    `inspect.getsource(Image.Image.resize)`). So at the same size, an RGBA image is copied
    straight, with no premultiply.
  - Today's attribution premultiplies explicitly:
    `opened.convert("RGBa").resize(block, LANCZOS).convert("RGBA")`
    (`src/pyntpot/maps/attribution.py:314`). At the same size that is an RGBa copy followed
    by an un-premultiply, a lossy round trip at low alpha. For example, `(200, 100, 50, 3)`
    comes back as `(170, 85, 85, 3)`.
  - The same size is the default case:
    - `plate_scale(scale) = max(1, ceil(2.0 / scale))` (`attribution.py:234-236`).
    - `compose` passes `k = card.width / display width` (`pipeline.py:164,171`).
    - `CardStyle.supersample` defaults to 2 (`style_groups.py:63`).
    - So `factor == 1`, `big == block`, and the resize is a no-op.
  - Measured by replaying `draw_attribution` with the prescribed in-memory path on a flat
    card:

    | scale | factor | pixels that differ from today | max difference |
    |---|---|---|---|
    | 1.0 | 2 | 0 | 0 |
    | 2.0 | 1 | 17,743 | 1 level |
    | 3.0 | 1 | 30,110 | 1 level |

    Every `route_map`, `place_card` and `map_styles` output moves, and so does any golden
    composed with the attribution. The S4a gate (`output_hashes.py check --stem route_map
    ...`) fails, and S6 says "never re-record".
  - `letter_over` at `scale=1` has the same gap. No recipe uses `scale=1` today, so no
    parity test catches it. All S1 and S3 tests shrink 2x and pass with the wrong code.
- **Fix:**
  - **S1, the shape:** `shrunk_rgba(rgb, alpha, size)` is
    `rgba_image(rgb, alpha).convert("RGBa").resize(size, Image.Resampling.LANCZOS).convert("RGBA")`.
    I measured this at 0 differing pixels for scales 1, 2 and 3. At a 2x shrink it is
    exactly the operation Pillow runs internally for `RGBA.resize`, so the examples'
    recipe and the S3 parity tests are unaffected.
  - **The docstring** says why the premultiply is explicit: Pillow skips its own
    premultiply when the size does not change, and the attribution strokes at the card's
    own size whenever the card is supersampled 2x or more.
  - **S1, a pinned test:** a plate of `(200, 100, 50)` at alpha `3 / 255`, shrunk to its
    own size, reads `(170, 85, 85, 3)`. A 2x shrink of the same plate equals
    `Image.fromarray(...).resize(...)`.
  - **S3:** add a `letter_over(..., scale=1)` case that runs without error and leaves a
    far pixel exactly as it was.
  - **Spec, Problem section:** "Pillow premultiplies an RGBA image inside `resize`" becomes
    "inside a `resize` that changes the size". Make the same edit to the plan's Approach
    bullet.
  - **ADR 0073 rules 8 and 9** need the same caveat, in 010's "ADR 0073 contents", before
    010 lands, because an accepted ADR keeps its text.
  - **S4a's gate stays as written.** It is the check that would have caught this.

### 2. [SHOULD-FIX] The parity test does not say the recipe's grain is `gran_px * 2`

- **Plan:** S3 `test_letter_over.py` compares `letter_over(image, marks, gran_px=5.0)` with
  "the examples' recipe written out in the test (`NibSurface` at twice the size ...)".
- **Evidence:**
  - D8 and ADR 0073 rule 6 make `gran_px` image pixels, and `letter_over` multiplies it by
    `scale`.
  - The examples' recipes take the plate's grain: `NibSurface(canvas2, NIB_SCALE, dark2,
    GRAN_PX * NIB_SCALE)` (`examples/word.py:121`, `composition.py:125`,
    `lettering.py:84`).
  - `labelled_grid.letter_over` takes `gran_px` already in plate pixels
    (`examples/labelled_grid.py:163-164,179`; `LABELS.gran_px=12.0` at `:148`).
  - An agent that writes `5.0` into the recipe's surface gets a failing parity test. It may
    then "fix" `letter_over` by dropping the multiply, which contradicts the ADR.
- **Fix:**
  - Write the recipe out: `NibSurface(Canvas.pixels(w=320, h=160), 2, dark2, 5.0 * 2)`,
    `nib_plate` into `tmp_path`, `Image.open(p).convert("RGBA").resize((160, 80), LANCZOS)`,
    `np.asarray(..., np.float32) / 255`, and the blend.
  - The ramp case is `np.tile(np.linspace(0, 1, 160, dtype=np.float32), (80, 1))`, grown
    with `Image.fromarray(ramp).resize((320, 160), BILINEAR)` as
    `labelled_grid.py:176-177` does.
  - Prescribe the setting too, `Setting("Keswick", 22.0, anchor=(8.0, 52.0))`, so "a corner
    pixel far from the name" is `(0, 159)`. I ran exactly this through the file and the
    in-memory path: bit-identical, zero and ramp.
  - Add one sentence for 010b to `docs-examples-review.md`: the grid scripts' `gran_px` is
    in plate pixels and halves on the sweep. `(g / 2) * 2 == g` exactly, so no pixel moves.

### 3. [SHOULD-FIX] `nib_rgba` will trip the reference gate if it cites `nib`, and no slice owns `references.md`

- **Plan:** S3 moves `nib_plate`'s body into `nib_rgba`. The plan says nothing about
  `Source:` lines or `docs/explanation/references.md`.
- **Evidence:**
  - `nib_plate` cites `` Source: `nib` in docs/explanation/references.md `` (`nib.py:289`).
  - The entry lists `pyntpot.letters.nib.nib_plate` (`references.md:155`).
  - `test_reference_keys.py:140`, "every cited key has an entry listing the site", fails
    if `nib_rgba` cites `nib` without being listed. Citing it is the natural move, since
    the algorithm now lives there.
- **Fix:**
  - `nib_rgba` carries the citation, and `nib_plate` keeps its own.
  - Add `` `pyntpot.letters.nib.nib_rgba` `` to the `nib` entry's "Implemented in" line.
  - Add `docs/explanation/references.md` to S3's owned files.

### 4. [SHOULD-FIX] "`nib_plate` writes exactly these arrays" is true only when `plate_lossless` is on

- **Spec/plan:** spec AC 1; S3 `test_nib_rgba.py`; S1's `save_rgba` decode test.
- **Evidence:** I measured `PaperStyle(plate_lossless=False)`. The colour where alpha is
  above 0 differs from the 8-bit arrays, and the shrunk plate is off by up to 85 levels on
  zero darkness and 128 on a ramp. The alpha stays exact.
- **Fix:**
  - The AC and the `nib_rgba` docstring say "with `plate_lossless` on (the default)".
  - The decode tests use the default `PaperStyle()` and say so in their docstring.

### 5. [SHOULD-FIX] The attribution `fix` in the Changelog has no test

- **Plan:** D10, and the spec's Changelog line
  `fix(maps): the attribution is lettered in memory, so a style with lossy plates no longer ...`.
- **Evidence:** No test exercises `draw_attribution` with `plate_lossless=False`. `maps` is
  outside mutation scope (`pyproject.toml:271`), so nothing pins the claimed behaviour.
- **Fix:** In S4a, add a case to `tests/unit/maps/test_attribution.py`: a style whose
  `paper` is `replace(style.paper, plate_lossless=False)` draws the same bytes as
  `Style.default()` on a 1440 by 600 card at scale 2.0. It fails on the base (lossy file)
  and passes after. Add `test_attribution.py` to S4a's owned files, which today say it
  "stays green unchanged".

### 6. [SHOULD-FIX] The mutation base is `origin/main`, but the plan also allows cutting from 010's tip

- **Plan:** Approach (cut from main after 010 merges, "or from 010's tip, rebasing when it
  merges"), and S7 `scope.py --base origin/main`.
- **Evidence:** If 010 is not yet merged, `origin/main...HEAD` includes 010's changed
  `ink` functions (`Sheet`, `wash`, `brush_from_id`, `Canvas.pixels`, `paper_plate`), and
  S7 mutates them under 010a.
- **Fix:**
  - S0 records the base commit in its commit message.
  - S7 runs `scope.py --base <that commit>`. That is `origin/main` once 010 has merged.

### 7. [CONSIDER] S5's candidate list of files that link the deleted notes is wrong

- **Evidence:** `git grep -l 'letters-lettering-over-an-image\|maps-fetch-hands-back-the-plates-dir' -- ':!specs'`
  returns only `docs/features/docs-how-to-write-a-provider.md` and
  `docs/features/docs-tutorial-opening-programs.md`. Both are plain-text mentions, not
  links. It does not return `cli-wider-commands.md` or `letters-nib-follows-writing-line.md`.
- **Fix:** Name the two real files. The `git grep` instruction already makes the slice
  safe.

### 8. [CONSIDER] Two decode tests check libwebp, not our code

- **Evidence:** S1's "`save_rgba`'s file decodes to `rgba_image`'s alpha ..." and S3's
  "`nib_plate`'s file decodes to `rgba_image(*nib_rgba(...))` ..." assert the same
  lossless property. Both would fail only if libwebp changed (CLAUDE.md: "Never test
  third-party code").
- **Fix:** Keep the S3 one, which is the spec AC, and drop the S1 one. S1 already pins
  `rgba_image`'s rounding, and its `save_rgba` test can assert that `save_rgba` calls
  through it: the same `uint8` array as `np.asarray(rgba_image(...))` where alpha is
  above 0.

### 9. [CONSIDER] Small decisions that are cheap to pin now

- **The `tempfile` ban is a proxy.**
  - `test_no_plate_round_trip.py` bans only `tempfile`. A round trip through `io.BytesIO`
    or `nib_plate` into a cache path would pass it.
  - The thing the spec cares about is "the attribution writes no file". Make the AST check
    "`maps/attribution.py` calls neither `nib_plate` nor `Image.open`", plus "no `letters`
    module imports `tempfile`".
- **The `key=` value in the three test builders.** "`key=KEY` ... or the key their fixture
  already names" leaves a choice open. Prescribe `key=KEY` from `support.paths` in all
  three builders:
  - `tests/support/basemaps.py:92`
  - `tests/unit/maps/painter/jobs.py:59`
  - `tests/unit/maps/test_basemap.py:115`

  No test paints a synthetic basemap into `plates_dir(basemap.key)`.
- **Where the canonical case goes.** Add `("key", "0" * 16)` to the existing
  `OUTSIDE_THE_HASH` table (`test_basemap.py:147-156`) rather than writing a new test. The
  parametrized "field outside the hash leaves it" already says it.
- **`groups or NibGroups()`.** Write `NibGroups() if groups is None else groups`. It is
  explicit, and it does not lean on a dataclass being truthy.

## What I verified (no finding)

- **`nib_plate`'s shape.** `nib.py:284-357`: it returns `None` for no marks (`:302`) and
  for no two-point mark (`:306-308`), then composes `out_rgb`/`out_a` (`:345-354`) and
  writes (`:356`). `nib_rgba` is a clean cut at `:355`. Both arrays are float32 for a
  float32 darkness (measured).
- **`NibGroups` today.** It is `@dataclass(frozen=True)` with five required positional
  fields (`style.py:139-159`). `field(default_factory=...)` keeps positional construction,
  needs no `extend-immutable-calls` entry, and satisfies `test_one_source_of_defaults`.
- **The file round trip equals the in-memory plate at a 2x shrink.** I reproduced it with
  `plate_lossless` on: "Keswick" on zero and ramp darkness, "Y Fenni", "Abergavenny" with
  no backing wash, and "Lynmouth" at an odd size. In every case:
  - the alpha is identical;
  - the colour is identical wherever alpha is above 0;
  - transparent pixels differ in colour (1,111 to 16,217 of them);
  - the shrunk images are identical bit for bit, whether shrunk with
    `.convert("RGBa").resize` or `.convert("RGBA").resize`.
- **Integer and float scale give the same plate.** `NibSurface(..., 2, ...)` and
  `NibSurface(..., 2.0, ...)` write byte-identical plates, so the plan's `float(scale)` is
  safe.
- **`grown_bilinear` holds a constant exactly.** A constant float32 field grown 2x stays
  exactly constant, for 0.3, 0.35, 1/3 and 0.123 at three sizes.
  `Image.fromarray(a, "F")` raises no deprecation under `-W error` on Pillow 13. The grown
  array is read-only, and the nib never writes into `surface.dark`.
- **The rounding literals hold.** 0.0, `0.5/255`, `0.499/255`, 1.0, 1.2 and -0.1 give 0, 1,
  0, 255, 255 and 0, in float64 and float32.
- **Pillow.** `letters` imports no `PIL` today. `ink` already does in `pad.py`,
  `sheet.py`, `io.py` and `washing.py`. No import-linter contract changes.
- **The `Basemap` constructors.** There are four:
  - `src/pyntpot/maps/layers.py:318` (`build_basemap`; `inputs.key` from
    `cache.ensure`, `pipeline.py:93-95`)
  - `tests/support/basemaps.py:92`
  - `tests/unit/maps/painter/jobs.py:59`
  - `tests/unit/maps/test_basemap.py:115`

  `examples/`, `docs/`, `README.md` and the property tests construct none.
  `with_fields` and `_nudged` use `dataclasses.replace`, so they keep `key`. Nothing
  compares or caches basemaps by value. `canonical` reads only the card and the layers
  (`basemap.py:184-198`).
- **The callers that move.** CLI `cli.py:92-93`, and `tests/support/golden.py:68`.
  `examples/` has 8 key sites in 6 scripts, as the spec counts.
- **Public surface.**
  - `test_site.py:94` refuses only `__init__` names that shadow submodules, so
    `image_lettering.py` is the right stem.
  - `max-args = 6` (`pyproject.toml:169`), and `letter_over` has 6.
  - Alphabetical directives go `letter_over`, `nib_plate`, `nib_rgba`
    (`docs/reference/letters.md`).
  - `LETTERS_PUBLIC` is at `test_public_api.py:74-85`. The root `pyntpot.__all__` does not
    re-export `letters` beyond `Hand`.
- **S2 is a pure move.** `TestBackingWash` (`test_nib.py:240-309`) is self-contained: it
  builds its own surface and uses only `_backing_wash`, `_sheet` and `flags_off`.
  `nib.py` needs `NibSurface` only as an annotation in `backing_wash.py`, so the
  `TYPE_CHECKING` import is cycle-free. The split is not forced: about 385 lines without
  it. It is a cheap, reversible pre-emptive move.
- **The `tempfile` test fails for the right reason.** Only `maps/attribution.py` imports
  `tempfile` in `src/` today.
- **Budgets.** Every touched `src` file stays under 400. `test_nib.py` is 403 lines, but
  the line budget scans `src` only (`test_boundaries.py:41-54`).
