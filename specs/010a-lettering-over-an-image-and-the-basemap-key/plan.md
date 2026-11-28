# 010a — plan

**Revision 2**, after the plan review (`review-plan.md`, verdict BLOCK), rebased on
`38179789` (main with the toolchain bump: ty 0.0.100). What changed:

- Finding 1 (blocking): `shrunk_rgba` premultiplies explicitly
  (`.convert("RGBa").resize(...).convert("RGBA")`), because Pillow skips its own
  premultiply when the size does not change, and the attribution strokes at the card's
  own size at supersample 2. S1 adds a pinned same-size test and S3 a `scale=1` case. The
  Approach, the spec's Problem section, and ADR 0073 rules 8 and 9 (in 010's "ADR 0073
  contents") say the premultiply happens only in a resize that changes the size.
- Findings 2 to 6 (should-fix), all applied: the parity recipe is written out, with the
  grain at `5.0 * 2`, the setting, the ramp and the corner. `references.md` is S3's. The
  lossless-only wording is in the spec, the `nib_rgba` docstring and the decode test. The
  attribution `fix` line has a test in `test_attribution.py`. S0 records the mutation
  base and S7 uses it.
- Findings 7 to 9 (consider), all applied: the real note-mention files are named. S1's
  libwebp decode test is replaced by a calls-through test. The round-trip AST check bans
  `nib_plate` and `Image.open` in `attribution.py`. The three builders use `key=KEY`. The
  canonical case goes in `OUTSIDE_THE_HASH`. `NibGroups() if groups is None else groups`.
- ADR 0073, not 0072: spec 008a holds 0072 and lands before 010.
- ty codes re-checked under ty 0.0.100: a `Basemap` built without `key` raises
  `missing-argument` (measured on a scratch file).

## Approach

ADR 0073 rules 5 to 11 are the design (written in 010, `specs/010-blank-paper-and-keyword-arguments/plan.md`,
"ADR 0073 contents"). This plan is how they land. It is PR 2 of scoping group E-a and
stacks on 010: cut the branch from `main` after 010 merges (or from 010's tip, rebasing
when it merges). Every fact below was measured on `f6c8302` unless it says otherwise;
re-measure the counts this plan quotes on the branch base before S0 and correct this file
if they differ. Read the spec, this plan, ADR 0073, `CLAUDE.md` and `CONTRIBUTING.md`
first.

Two independent changes, three layers:

1. **N1, lettering over an image (`ink`, `letters`, `maps`).** The nib plate's
   compositing is split from its writing: `nib_rgba` returns the arrays and `nib_plate`
   writes them. `letter_over` strokes marks onto a plate at `scale` times an image,
   shrinks it and lays it on. The shrink, and the 8-bit conversion `save_rgba` already
   does, move into one private `ink` module that `letters` and `maps.attribution` share,
   so `letters` stays free of Pillow and the attribution stops writing a file.
   `NibGroups` gains defaults.
2. **N3, the basemap's key (`maps`).** `Basemap` carries the cache key it was built
   under; the command line and the golden support read it instead of rebuilding it.

**Why no pixel moves (ADR 0073 rule 8), measured on `f6c8302`.** Three real nib plates
(the `word.py` wordmark on bare paper, and "Keswick" and "Y Fenni" over a darkness ramp)
were each written by `nib_plate`, reopened and shrunk with Lanczos as the examples do,
and compared with the same arrays converted in memory to 8-bit RGBA (`save_rgba`'s own
rounding) and shrunk the same way:

- At a 2x shrink, `.convert("RGBa").resize(...)` and `.convert("RGBA").resize(...)` give
  identical pixels, because Pillow converts RGBA to RGBa inside a `resize` that changes
  the size. A `resize` to the same size is a plain copy, with no premultiply: Pillow
  returns `self.copy()` before its premultiply branch. So the shared shrink converts to
  `RGBa` explicitly, as `maps/attribution.py` does today. The 010a review measured the
  attribution at supersample 2 and 3, where its plate is the card's own size: the explicit
  form gives 0 differing pixels, and a bare `.resize` gives 17,743 and 30,110.
- The file and the in-memory plate have identical alpha everywhere and identical colour
  wherever the alpha is above 0. They differ only in the colour of fully transparent
  pixels (8584, 51179 and 33731 of them), which libwebp's lossless encoder is free to
  rewrite and which premultiplication zeroes.
- The shrunk images are identical, bit for bit, for all three.

So keeping the 8-bit Lanczos step in memory is bit-identical to the file round trip, for
every style whose `PaperStyle.plate_lossless` is on (the default, and every shipped and
example theme: `git grep plate_lossless` finds no theme or caller that turns it off). No
golden, docs image or master moves, and the stacked sweep (010b) can be proved by exact
hashes too.

No boundary changes. `letters` imports no Pillow (it has none today); `ink` gains one
private module; `[tool.importlinter]` is untouched. Two names join
`pyntpot.letters.__all__`: `nib_rgba` and `letter_over`.

### Running the gates

- **Slice gate** (every slice, before its checkpoint commit):

  ```bash
  uv run pytest -n auto --dist loadgroup -m "not golden" -q   # add --golden-tolerance off the pinning machine
  uv run ruff check . && uv run ruff format --check . && uv run ty check && uv run lint-imports
  prek run --all-files
  ```

- **Output hashes** (S0 on the base; S6):
  `PYTHONPATH=tests uv run python tests/golden/output_hashes.py check specs/010a-lettering-over-an-image-and-the-basemap-key/output-hashes.json`.
  Narrow a failing run with `--stem` (the map stems are `route_map`, `place_card`,
  `map_styles`, `relief_grid`, `how_to_route_ink`, `how_to_line_effects`,
  `social_preview`).
- **Golden subset with the attribution** (end of S4a): `uv run pytest -m golden
  tests/golden/test_map_styles.py tests/golden/test_places.py` (add `--golden-tolerance`
  off the pinning machine).
- **Coverage gate** (S3, S4b, S8): CI's own steps, as in 010's plan
  (`--fail-under=95` for `ink` and `letters`, 92 for `maps`).
- **Golden suite** (S6, about 27 minutes): `uv run pytest -m golden -n auto --dist loadgroup`.
- **Glossary regeneration** (S5): `PYTHONPATH=tests uv run python -m support.glossary`.
- **Strict docs build** (S3, S5, S8):
  `NO_MKDOCS_2_WARNING=1 uv run --locked --group docs mkdocs build --strict -d "$SCRATCH/site"`.

Every test is written first and seen to fail for the stated reason. Each has a one-line
docstring; `parametrize` carries `ids=`; no mocking, no `autouse`, no `print`.

### Line budget (400; split, never thin)

| File | Now | After | Plan |
|---|---|---|---|
| `src/pyntpot/letters/nib.py` | 357 | about 300 | **Near the budget.** S2 moves `_backing_wash` and the four constants only it reads (`_COVERED`, `_GRAIN_REACH`, `_FEATHER_FLOOR`, `_LIFT_GAIN`) whole to `letters/backing_wash.py`, a pure move in its own commit, before S3 adds `nib_rgba`. |
| `src/pyntpot/letters/backing_wash.py` | new | about 90 | The moved function, renamed `backing_wash` (another module imports it), and its constants, with a module docstring. |
| `src/pyntpot/letters/image_lettering.py` | new | about 110 | `letter_over`. The stem is not `letter_over`: `tests/architecture/test_site.py` refuses a package binding a name equal to a submodule. |
| `src/pyntpot/ink/plate_resize.py` | new | about 90 | `rgba_image`, `shrunk_rgba`, `grown_bilinear`. |
| `src/pyntpot/ink/io.py` | 150 | about 145 | `save_rgba` calls `rgba_image`. |
| `src/pyntpot/letters/style.py` | 159 | about 165 | `NibGroups` defaults and docstring. |
| `src/pyntpot/maps/attribution.py` | 165 | about 158 | The temporary directory goes. |
| `src/pyntpot/maps/basemap.py` | 211 | about 222 | `key`, its `Attributes:` entry, the invariant. |
| `src/pyntpot/maps/layers.py` | 331 | 332 | `key=inputs.key`. |
| `tests/unit/letters/test_nib.py` | 403 | about 330 | S2 moves `TestBackingWash` (lines 240 to 309) to `tests/unit/letters/test_backing_wash.py`, mirroring the split. |

## Slices

Order: Start, S0, S1, S2, S3, S4a, S5, S6, S7, S8. S4b (the basemap key) owns files no
other slice owns and may run in a worktree cut after S0, merged before S5 (merge gate).
Everything else is serial.

### Start

- Comment the branch name and spec `010a` on #165 and #167; the spec names both.
- Re-measure the counts the spec quotes on the branch base (they are 010's base counts;
  010 changed no nib or key line, so they should hold).
- The plan-reviewer passes this plan.

### S0: Baseline hashes (serial, first)

- **Owns:** `specs/010a-lettering-over-an-image-and-the-basemap-key/output-hashes.json`.
- On the untouched base (010 merged):
  `PYTHONPATH=tests uv run python tests/golden/output_hashes.py record specs/010a-lettering-over-an-image-and-the-basemap-key/output-hashes.json`,
  committed alone. (010's JSON is not reused: it was recorded before 010's own diff, and
  the base of this PR is after it.)
- **The mutation base.** The commit message names the base commit, `git rev-parse HEAD`
  before this commit. It is `origin/main` once 010 has merged, or 010's tip if this
  branch was cut from it. S7 runs `scope.py --base <that commit>`, so 010's `ink`
  changes are never mutated under 010a.
- **Gate:** `check` passes on the base.

### S1: The plate resize in `ink` (serial)

- **Owns:** `src/pyntpot/ink/plate_resize.py` (new), `src/pyntpot/ink/io.py`,
  `tests/unit/ink/test_plate_resize.py` (new), `tests/unit/ink/test_io.py` (154 lines;
  only if an existing case names the moved conversion).
- **Shapes** (all private: in no `__all__`; module docstring states purpose, what it does
  not do, and the invariants):
  - `rgba_image(rgb: np.ndarray, alpha: np.ndarray) -> Image.Image`: the 8-bit RGBA
    image a plate is stored as, each channel `clip(x * 255 + 0.5, 0, 255)` truncated to
    `uint8`, today's `save_rgba` lines moved here unchanged.
  - `shrunk_rgba(rgb, alpha, size: tuple[int, int]) -> Image.Image`:
    `rgba_image(rgb, alpha).convert("RGBa").resize(size, Image.Resampling.LANCZOS).convert("RGBA")`.
    The docstring says the premultiply is explicit, and why: Pillow skips its own
    premultiply when the size does not change, and the attribution strokes at the card's
    own size whenever the card is supersampled 2x or more. It also says a transparent
    pixel's colour never reaches the result, and that the 8-bit step is kept on purpose
    (ADR 0073 rule 8). At any changed size this is exactly the operation Pillow runs inside
    `RGBA.resize`, so the examples' recipe and the parity tests are unaffected.
  - `grown_bilinear(values: np.ndarray, size: tuple[int, int]) -> np.ndarray`: a float
    field brought to `size` (width, height) as `Image.fromarray(values.astype(F32),
    "F").resize(size, BILINEAR)`, as float32; the form `examples/labelled_grid.py` and
    `maps.plates.dark_array` use (the latter is left alone).
  - `save_rgba` builds its image with `rgba_image`, so the conversion lives once.
- **Tests first** (`test_plate_resize.py`):
  - `rgba_image` rounds to nearest at pinned literals: 0.0, `0.5 / 255`, `0.499 / 255`,
    1.0 and an out-of-range 1.2 and -0.1 give 0, 1, 0, 255, 255, 0 (parametrized with
    `ids=`), for colour and alpha.
  - `save_rgba` calls through `rgba_image`: on a small random plate with some zero alpha,
    the `uint8` array decoded from the lossless file equals `np.asarray(rgba_image(...))`
    wherever alpha is above 0. This is the only decode test in S1. The libwebp property
    itself is the spec's criterion, tested once in S3 (review finding 8).
  - `shrunk_rgba` returns `size`, and premultiplies: a 4 by 4 plate whose left half is red
    at alpha 0 and right half blue at alpha 1, shrunk to 2 by 2, has no red in any pixel.
  - **The same-size pin** (review finding 1): a plate of colour `(200, 100, 50)` at alpha
    `3 / 255`, shrunk to its own size, reads `(170, 85, 85, 3)`, the lossy RGBa round trip
    today's attribution relies on. A bare `.resize` would return `(200, 100, 50, 3)`, so
    this test fails on revision 1's shape. A 2x shrink of the same plate equals
    `Image.fromarray(<its uint8 RGBA>, "RGBA").resize(size, LANCZOS)`.
  - `grown_bilinear` returns `(h, w)` float32, keeps a constant field constant, and
    zeros stay exactly zero.
- **Gate:** slice gate.

### S2: Split the backing wash out of the nib (serial; a pure move)

- **Owns:** `src/pyntpot/letters/nib.py`, `src/pyntpot/letters/backing_wash.py` (new),
  `tests/unit/letters/test_nib.py`, `tests/unit/letters/test_backing_wash.py` (new).
- Move `_backing_wash` (renamed `backing_wash`) and `_COVERED`, `_GRAIN_REACH`,
  `_FEATHER_FLOOR`, `_LIFT_GAIN` to `backing_wash.py`, byte for byte but the name, with a
  module docstring (purpose: the faint lift of paper under a word block; it does not
  stroke marks or write a file; invariant: nothing where the ground is paler than
  `label_wash_dark_floor`). `backing_wash` takes the `NibSurface` it reads, so
  `backing_wash.py` starts with `from __future__ import annotations` and imports
  `NibSurface` under `TYPE_CHECKING` only, as `maps/basemap.py` does for its types (no
  import cycle: `nib.py` imports `backing_wash` at run time, never the reverse). Move `TestBackingWash` whole to
  `test_backing_wash.py`, its imports repointed; `test_nib.py` loses the import of
  `_backing_wash`. Earlier ADRs that name `letters.nib._backing_wash` (0005, 0047, 0066)
  keep their text.
- **Check it is a pure move:** `git diff -M --stat` and a read of the diff show only the
  moved lines, the rename, the imports and the new docstring; no function body changes.
- **Gate:** slice gate; `uv run pytest tests/unit/letters` passes with the same count of
  tests as before.

### S3: `nib_rgba`, `letter_over` and the `NibGroups` defaults (serial)

- **Owns:** `src/pyntpot/letters/nib.py`, `src/pyntpot/letters/image_lettering.py` (new),
  `src/pyntpot/letters/style.py` (`NibGroups`), `src/pyntpot/letters/__init__.py`,
  `docs/reference/letters.md`, `docs/explanation/references.md` (the `nib` entry),
  `tests/unit/test_public_api.py`,
  `tests/unit/letters/test_nib_rgba.py` (new), `tests/unit/letters/test_letter_over.py`
  (new), `tests/unit/letters/test_style.py` (51 lines).
- **`nib_rgba(marks: Sequence[Mark], surface: NibSurface, groups: NibGroups) ->
  tuple[np.ndarray, np.ndarray] | None`**: today's `nib_plate` body down to the final
  compositing loop, returning `(out_rgb, out_a)` uncast. `nib_plate` becomes: call it;
  return `None` on `None`; `save_rgba(rgb, alpha, path, paper.paper_quality,
  lossless=paper.plate_lossless)`; return `path`. Both docstrings say what the other
  does. `nib_rgba`'s docstring says the file `nib_plate` writes holds exactly these arrays
  with `plate_lossless` on (the default). With it off, the colour is written lossy.
  `nib_rgba` carries the citation `` Source: `nib` in docs/explanation/references.md ``,
  and `nib_plate` keeps its own. The `nib` entry's "Implemented in" line in
  `references.md` (`:155`) adds `` `pyntpot.letters.nib.nib_rgba` ``, so
  `tests/architecture/test_reference_keys.py` holds. The module docstring's "writes the file" becomes "returns it as arrays
  (`nib_rgba`) or writes it (`nib_plate`)", and its invariant "with nothing to draw no
  file is written" also says `nib_rgba` returns `None`.
- **`NibGroups`**: each field `= field(default_factory=NibStyle)` and so on, in today's
  order. The docstring loses "it holds no defaults" and says `NibGroups()` is the default
  look and one group is changed with `NibGroups(nib=...)` or `dataclasses.replace`.
- **`letter_over(image: np.ndarray, marks: Sequence[Mark], groups: NibGroups | None =
  None, *, gran_px: float, scale: int = 2, dark: np.ndarray | None = None) ->
  np.ndarray`**, in `image_lettering.py`, six parameters (ruff `max-args`):
  1. Refuse `image` unless `image.ndim == 3` and `image.shape[2] == 3`, `scale < 1`, and
     a `dark` whose shape is not `image.shape[:2]`, each with a `ValueError` naming what
     was given.
  2. `h, w = image.shape[:2]`; `big = (w * scale, h * scale)`.
  3. The plate's darkness: `np.zeros((h * scale, w * scale), np.float32)` for `None`;
     else `grown_bilinear(dark, big)`. (Zeros grown are zeros, so the `None` branch
     equals `labelled_grid.py`'s, which grows a zero array.)
  4. `surface = NibSurface(Canvas.pixels(w=big[0], h=big[1]), float(scale), darkness,
     gran_px * scale)`; `drawn = nib_rgba(marks, surface, NibGroups() if groups is None
     else groups)`;
     `None` returns `image.copy()`.
  5. `rgba = np.asarray(shrunk_rgba(*drawn, (w, h)), np.float32) / 255`;
     `alpha = rgba[..., 3:]`; return `image * (1 - alpha) + rgba[..., :3] * alpha`, the
     examples' expression, so the result is bit-identical to theirs.
  The docstring: purpose; that the marks are in the image's pixels; what `gran_px`,
  `scale` and `dark` mean and their units; that it returns a new array and never writes a
  file; the 8-bit Lanczos step and why (rule 8); `Raises:`; and what it does not do (it
  does not choose, place or write names: the caller's `Hand` writes the marks).
- **Exports:** `letters/__init__.py` imports and lists `letter_over` and `nib_rgba`, and
  its docstring names them; `docs/reference/letters.md` gains one directive each, in the
  page's alphabetical order; `test_public_api.py`'s `LETTERS_PUBLIC` gains both.
- **Tests first:**
  - `test_nib_rgba.py`: `None` for no marks and for marks all under two points; shapes
    and range; the same marks give the same arrays. With the default `PaperStyle()`
    (`plate_lossless` on, which the test's docstring says), `nib_plate`'s file decodes to
    `rgba_image(*nib_rgba(...))` in alpha everywhere and in colour where alpha is above 0.
    With `plate_lossless` off the colour is lossy, and the test says it does not claim
    that case.
  - `test_letter_over.py`, on a 160 by 80 painted image (`paper_plate` on a keyword
    `Sheet`), with marks a `Hand` writes for `Setting("Keswick", 22.0, anchor=(8.0,
    52.0))` at seed 11, and `gran_px=5.0`:
    - **the parity tests**, the heart of the PR. `letter_over(image, marks, gran_px=5.0)`
      equals, bit for bit, the examples' recipe written out in the test:
      - `NibSurface(Canvas.pixels(w=320, h=160), 2, dark2, 5.0 * 2)`, with the plate's
        grain at `5.0 * 2`, because the examples pass the plate's grain
        (`GRAN_PX * NIB_SCALE`, `examples/word.py:121`) and `letter_over` takes the
        image's (D8). Never "fix" a failing parity test by dropping `letter_over`'s
        multiply;
      - `nib_plate` into `tmp_path`;
      - `Image.open(p).convert("RGBA").resize((160, 80), LANCZOS)`;
      - `np.asarray(..., np.float32) / 255`, then the blend.
      There are two cases:
      - `dark2` is `np.zeros((160, 320), np.float32)` and `dark=None`;
      - the ramp `np.tile(np.linspace(0, 1, 160, dtype=np.float32), (80, 1))`, passed as
        `dark`, with the recipe growing it as `labelled_grid.py:176-177` does:
        `np.asarray(Image.fromarray(ramp).resize((320, 160), BILINEAR))`.
      The review ran exactly these through the file and the in-memory path: bit-identical,
      zero and ramp. They pin that 010b's sweep moves no pixel;
    - `groups=None` equals `groups=NibGroups()`;
    - no marks: the result equals `image` and `result is not image`;
    - the input array is unchanged after the call;
    - the corner pixel `[0, 159]`, far from the name, equals the image's exactly;
    - `scale=1` runs without error, and the same corner pixel is exactly the image's
      (the same-size shrink, review finding 1);
    - `ValueError` for a 2-D image, a 4-channel image, a `dark` of the wrong shape, and
      `scale=0` (parametrized, `ids=`).
  - `test_style.py`: `NibGroups()` equals the five explicit defaults; `NibGroups(nib=n)`
    keeps the others; `NibGroups(n, f, h, b, p)` positional still builds.
- **Gate:** slice gate, coverage gate, strict docs build.

### S4a: The attribution in memory (serial, after S3)

- **Owns:** `src/pyntpot/maps/attribution.py`, `tests/unit/maps/test_attribution.py`,
  `tests/architecture/test_no_plate_round_trip.py` (new).
- **Change:** the `tempfile.TemporaryDirectory` block becomes `nib.nib_rgba` on the same
  surface (its canvas `Canvas.pixels(w=big[0], h=big[1])`, the same `float(factor)`, the
  same `dark_array(None, ...)` darkness of 0.35, the same grain), `None` logging "the
  attribution drew nothing" as today, then `plate = shrunk_rgba(rgb, alpha, block)` and
  today's paste. The imports of `tempfile`, `Path` (if now unused) and `Image.open` go.
  The module docstring's "shrunk with Lanczos" sentence says it is done in memory.
- **Tests first:**
  - `test_no_plate_round_trip.py`, an AST walk in the style of `test_one_hex_parser.py`,
    with two checks. `src/pyntpot/maps/attribution.py` calls neither `nib_plate` nor
    `Image.open` and imports no `tempfile`. No module under `src/pyntpot/letters/`
    imports `tempfile`. This checks what the spec cares about, that the attribution
    writes no file, rather than one proxy for it. It fails on the base for
    `attribution.py`.
  - `tests/unit/maps/test_attribution.py`, a new case backing the Changelog's `fix` line.
    A style built as `style.model_copy(update={"paper": dataclasses.replace(style.paper, plate_lossless=False)})` (Style is a frozen pydantic model; see `tests/support/basemaps.py:52`) draws the same
    bytes as `Style.default()`, on a 1440 by 600 card at scale 2.0. It fails on the base,
    where the plate goes through a lossy file, and passes after. The existing cases stay
    unchanged.
- **Gate:** slice gate; the golden subset with the attribution; `output_hashes.py check
  --stem route_map --stem place_card --stem map_styles` (the cards with the attribution)
  unchanged. This gate is what caught revision 1's same-size defect, and it stays.

### S4b: The basemap's key (parallel-capable; worktree cut after S0)

- **Owns:** `src/pyntpot/maps/basemap.py`, `src/pyntpot/maps/layers.py`,
  `src/pyntpot/maps/pipeline.py` (docstrings only), `src/pyntpot/maps/cli.py`,
  `tests/support/golden.py`, `tests/support/basemaps.py`,
  `tests/unit/maps/painter/jobs.py`, `tests/unit/maps/test_basemap.py`,
  `tests/unit/maps/test_pipeline_fetch_paint.py`.
- **Change:**
  - `Basemap` gains `key: str = field(kw_only=True)` as its last field, and an
    `Attributes:` entry, last: "The cache key of the payloads it was built from, as
    `Cache.ensure` returned it; `cache.plates_dir(key)` is where its plates are cached."
    The module docstring's "It carries no cache key, because the cache owns its keys"
    becomes "It carries the cache key it was built under and computes none: the cache
    owns how keys are made." `canonical`'s docstring adds the key to what it leaves out.
  - `build_basemap` passes `key=inputs.key`. `fetch`'s `Returns:` says the basemap
    carries its key.
  - `cli.py`: `plates = pipeline.paint(basemap, style, cache.plates_dir(basemap.key))`;
    the `key = cache.key(...)` line goes. `tests/support/golden.py` the same.
  - All three test builders pass `key=KEY` from `support.paths`: `tests/support/basemaps.py:92`,
    `tests/unit/maps/painter/jobs.py:59` and `tests/unit/maps/test_basemap.py:115`. No test
    paints a synthetic basemap into `plates_dir(basemap.key)`.
- **Tests first:**
  - `test_pipeline_fetch_paint.py`: the fetched basemap's `key` equals `KEY` and equals
    `cache.key(track, features, elevation)` for the fixture providers.
  - `test_basemap.py`: add `("key", "0" * 16)` to the existing `OUTSIDE_THE_HASH` table
    (`:147-156`), whose parametrized test already says a field outside the hash leaves
    it. Building one without `key` raises `TypeError`, with
    `# ty: ignore[missing-argument]` (the code ty 0.0.100 reports, measured).
  - `tests/unit/maps/test_cli.py` and `tests/golden/test_places.py` stay green unchanged.
- **Gate:** slice gate, coverage gate. **Merge gate (before S5):** merge S4b into the
  branch, run the slice gate and the coverage gate on the merged tree, and commit the merge
  only when green.

### S5: Records (serial)

- **Owns:** `GLOSSARY.md` and the regenerated glossary files,
  `docs/features/letters-lettering-over-an-image.md` and
  `docs/features/maps-fetch-hands-back-the-plates-dir.md` (both deleted),
  `docs/features/docs-examples-review.md`, and every file that names the two deleted
  notes. Measured, `git grep -l` outside `specs/` and `docs/decisions/` finds two, both
  plain-text mentions, not links:
  - `docs/features/docs-how-to-write-a-provider.md`;
  - `docs/features/docs-tutorial-opening-programs.md`.
  Each mention becomes the issue number and ADR 0073. The gate is
  `git grep 'letters-lettering-over-an-image\|maps-fetch-hands-back-the-plates-dir' --
  ':!specs' ':!docs/decisions'`, which must be empty.
- **Glossary:** "nib plate" adds `pyntpot.letters.nib_rgba`, `pyntpot.letters.letter_over`
  to its code column and one clause: `nib_rgba` hands it back as arrays without writing
  it. "basemap" adds: it carries the cache key it was built under. Regenerate.
- **Notes:** delete both; repoint links to ADR 0073. In `docs-examples-review.md`'s
  "The sweep onto the new calls (010b)" section (010 added it) list: the nine nib round
  trips and `labelled_grid.letter_over` onto `letter_over`, with `NIB_SCALE` gone from
  the 12 scripts; the 8 key lines in 6 scripts and the four docs pages onto
  `basemap.key`; the tutorial and `paint-your-own-shapes.md` teaching `letter_over`;
  `test_letters_examples.py`'s plate-file pin retired with the plate files. Add one
  sentence: the grid scripts' `gran_px` (`labelled_grid.LABELS.gran_px`, 12.0) is in
  plate pixels and halves on the sweep, because `letter_over` takes the image's grain.
  `(g / 2) * 2 == g` exactly, so no pixel moves.
- **Gate:** slice gate, strict docs build, no em or en dash in the changed prose.

### S6: The pixel proof (serial)

- `output_hashes.py check` against S0's JSON: all 91 entries unchanged.
- The golden suite with no regeneration; `git status --porcelain docs/images tests/golden`
  empty.
- A failure is a defect in S1, S3 or S4a: narrow it with `--stem`, fix it in that slice's
  files, never re-record.

### S7: Mutation testing (serial, local)

```bash
patterns=$(mktemp)
uv run python tests/mutation/scope.py --base "$BASE" --out "$patterns"   # BASE: the commit S0's message names
xargs -r -a "$patterns" prlimit --as=3500000000 -- uv run mutmut run
uv run mutmut results | grep -v 'not checked'
```

- **In scope:** `ink/plate_resize.py` (`rgba_image`, `shrunk_rgba`, `grown_bilinear`),
  `ink/io.save_rgba`, `letters/nib.nib_rgba` and `nib_plate`, and
  `letters/image_lettering.letter_over`. `NibGroups` changes no function body.
- **Moved, not changed:** `letters/backing_wash.backing_wash` (S2's pure move, shown
  unchanged by `git diff -M`). `scope.py` lists it as new; drop it from the patterns and
  say so in `mutation.md`.
- **`maps`** (`attribution`, `basemap`, `cli`) is outside mutmut's scope.
- **Survivors:** kill each with a test under `tests/unit/ink`, `tests/unit/letters` or
  `tests/property`, or record it as equivalent, with the reason, in
  `specs/010a-lettering-over-an-image-and-the-basemap-key/mutation.md` and the PR
  description. Expect `+ 0.5` to `+ 0.49` style mutants of the rounding to die on S1's
  pinned literals; `scale < 1` to `scale <= 1` dies on S3's `scale=1` case (add that
  case if it survives).

### S8: Final review and PR (serial, fresh context)

- **Gates:** slice gate, coverage gate, strict docs build, `git diff origin/main --
  pyproject.toml` empty, `git diff --stat origin/main -- docs/images tests/golden/docs
  tests/golden/lynmouth` empty.
- **Reviews:** a fresh-context diff review against this plan (spec compliance first,
  quality second), then the elegance pass; the orchestrator triages.
- **PR:** the spec's title and Changelog; `Closes #165`, `Closes #167`; the mutation
  equivalents; "Golden and docs images: none moved", with the S6 evidence.

## Files to touch

- New: `src/pyntpot/ink/plate_resize.py`, `src/pyntpot/letters/backing_wash.py`,
  `src/pyntpot/letters/image_lettering.py`, `tests/unit/ink/test_plate_resize.py`,
  `tests/unit/letters/{test_backing_wash,test_nib_rgba,test_letter_over}.py`,
  `tests/architecture/test_no_plate_round_trip.py`.
- Changed: `src/pyntpot/ink/io.py`, `src/pyntpot/letters/{nib,style,__init__}.py`,
  `src/pyntpot/maps/{attribution,basemap,layers,pipeline,cli}.py`,
  `tests/support/{golden,basemaps}.py`, `tests/unit/maps/painter/jobs.py`,
  `tests/unit/letters/{test_nib,test_style}.py`,
  `tests/unit/maps/{test_basemap,test_pipeline_fetch_paint,test_attribution}.py`,
  `tests/unit/test_public_api.py`, `docs/reference/letters.md`,
  `docs/explanation/references.md` (the `nib` entry), `GLOSSARY.md` and its generated
  files, `docs/features/docs-examples-review.md`,
  `docs/features/{docs-how-to-write-a-provider,docs-tutorial-opening-programs}.md` (the
  mentions of the two deleted notes only).
- Deleted: `docs/features/letters-lettering-over-an-image.md`,
  `docs/features/maps-fetch-hands-back-the-plates-dir.md`.
- `specs/010a-lettering-over-an-image-and-the-basemap-key/{output-hashes.json,mutation.md,tasks.md}`.

## Files to leave alone

- **Every script in `examples/`**, `labelled_grid.py`'s private `letter_over` included,
  and every tutorial, how-to and README block: the sweep is 010b. The public
  `letter_over` and the private one coexist for one PR; 010b deletes the private one. The
  parity test (S3) is what makes that later swap safe.
- **`tests/examples/test_letters_examples.py`**: it pins `<stem>-plate.webp` beside an
  example's output, which stays true until 010b changes the scripts.
- **`NibSurface`**: no `dark` default (Decision D4).
- **`maps/lettering/pipeline.py`**: it writes the lettering's nib plate into the cache on
  purpose (it is cached and reused); it keeps calling `nib_plate`.
- **`maps/plates.dark_array`** and `maps/compose_steps.py`: they resize with Pillow in
  `maps`, which is allowed; folding them onto `grown_bilinear` is a refactor nobody needs
  for this feature and would widen the pixel proof.
- **`fetch`, `paint`, `candidate_export`, `vector_layers` signatures**, and `Cache`:
  unchanged (rule 11).
- **`docs/images/**`, `tests/golden/docs/**`, `tests/golden/lynmouth/**`** and every pinned
  literal.
- **Earlier ADRs** keep their text, including the ones naming `letters.nib._backing_wash`.
- `pyproject.toml`: no contract, budget or tool setting changes (no new
  `extend-immutable-calls` entry is needed: the defaults are `default_factory`, and
  `letter_over`'s `groups` defaults to `None`).

## Test plan

| Acceptance criterion | Test |
|---|---|
| `nib_rgba` arrays, `None`, written by `nib_plate` | `tests/unit/letters/test_nib_rgba.py` (S3) |
| `letter_over` equals the examples' recipe (zero and ramp darkness) | `test_letter_over.py`, the parity tests (S3) |
| `letter_over` defaults, copy, unchanged input, far pixel, errors | `test_letter_over.py` (S3) |
| `NibGroups` defaults and positional construction | `tests/unit/letters/test_style.py` (S3) |
| The 8-bit conversion and premultiplied shrink, once in `ink` | `tests/unit/ink/test_plate_resize.py` (S1): rounding pins, calls-through, no red bleed, the same-size `(170, 85, 85, 3)` pin; `test_letter_over.py`'s `scale=1` case (S3) |
| The attribution writes no file | `tests/architecture/test_no_plate_round_trip.py` (S4a: no `nib_plate`, `Image.open` or `tempfile`); its pixels by the S4a hash gate and S6 |
| The attribution `fix` line (lossy styles letter it losslessly) | `tests/unit/maps/test_attribution.py`'s new case (S4a) |
| `nib_rgba` cites `nib` and is listed | `tests/architecture/test_reference_keys.py` (S3) |
| `Basemap.key` set by `fetch`, required, outside `canonical` | `tests/unit/maps/test_pipeline_fetch_paint.py`, `test_basemap.py` (S4b); `test_field_docs.py` for its entry |
| CLI and golden support read `basemap.key` | `tests/unit/maps/test_cli.py`, the golden suite (S6) |
| Exports and reference | `tests/unit/test_public_api.py`, `test_public_signatures.py`, `tests/docs/test_reference_pages.py`, the strict docs build |
| Glossary and notes | `tests/docs/test_glossary.py`, `test_docs_links.py`, the S5 `git grep` gate |
| Pixels do not move | `output_hashes.py check` (S6), the golden suite |
| Mutation | S7, `mutation.md` |

No Hypothesis property is added: `letter_over` composes existing, already-tested steps,
and its one algorithmic claim (equality with the recipe) is an exact parity test on real
marks, which a property over random marks would only make slower.

## Delegation

- **Orchestrator (main context):** this plan, the plan-reviewer gate, the merge gate, the
  integrator's checks after each slice (slice gate; seams: the two exports, the reference
  directives, `Basemap`'s field docs), commits and the PR.
- **Plan-reviewer:** a fresh-context sceptical staff engineer reads this plan, the spec
  and ADR 0073 before S0 and blocks until it passes.
- **Implementers:** S3 is the design-heavy slice (strongest model); S1 and S4a are small
  and exact (strong model, because bit-identity is the whole point); S0, S2 and S5 are
  mechanical (cheaper model). S4b is small and independent and may run in parallel in its
  own worktree. S7 runs locally.
- **After green:** a fresh-context diff review against the plan, then the elegance pass.

## File-ownership partition

| Track | Owns | After | Parallel |
|---|---|---|---|
| S0 | `output-hashes.json` | base (010 merged) | no |
| S1 | `ink/{plate_resize,io}.py`, `tests/unit/ink/{test_plate_resize,test_io}.py` | S0 | no |
| S2 | `letters/{nib,backing_wash}.py`, `tests/unit/letters/{test_nib,test_backing_wash}.py` | S1 | no |
| S3 | `letters/{nib,image_lettering,style,__init__}.py`, `docs/reference/letters.md`, `docs/explanation/references.md`, `test_public_api.py`, `tests/unit/letters/{test_nib_rgba,test_letter_over,test_style}.py` | S2 | no |
| S4a | `maps/attribution.py`, `tests/unit/maps/test_attribution.py`, `tests/architecture/test_no_plate_round_trip.py` | S3 | no |
| S4b | `maps/{basemap,layers,pipeline,cli}.py`, `tests/support/{golden,basemaps}.py`, `tests/unit/maps/painter/jobs.py`, `tests/unit/maps/{test_basemap,test_pipeline_fetch_paint}.py` | S0 | yes, worktree; merged before S5 |
| S5 | `GLOSSARY.md` and generated files, the notes and their links | S4a, merge gate | no |
| S6 | none (checks) | S5 | no |
| S7 | `mutation.md`, tests that kill survivors | S6 | no |
| S8 | the PR | S7 | no |

## Decisions

Forks picked with no human in the loop, each with its reason:

- **D1. Keep the 8-bit Lanczos step, in memory (ADR 0073 rule 8).** Measured
  bit-identical to the file round trip (Approach). The alternative the note expected, a
  float resize, would move every lettered docs image, their masters and the attribution
  on every card, for a difference an 8-bit output cannot show, and would put a
  regeneration window into a PR that otherwise moves nothing. It also makes the sweep
  provable by hashes.
- **D2. `letter_over` takes marks, not settings.** A setting becomes marks only through a
  `Hand` and a seeded generator, which are the caller's: the examples pick their own hand
  seed per script. Taking marks keeps `letter_over` free of the hand's randomness and
  keeps one call per concern (the hand writes, the nib letters). It costs the caller one
  line, `hand.write(setting, hand.generator(seed))`.
- **D3. `NibGroups` gets field defaults, not a `NibGroups.default()` classmethod.**
  `NibGroups()` and `NibGroups(nib=...)` read the way every style group's defaults do (ADR
  0069: the dataclass default is the default look), one group changes by keyword, and
  positional construction (ADR 0068) is untouched. A classmethod would be a second way to
  say the same thing.
- **D4. `NibSurface` is unchanged.** Giving `dark` a default needs `gran_px` to default
  too, or a reorder that breaks positional callers; `letter_over` already builds the
  surface for the common case, so the advanced path keeps its explicit four fields.
- **D5. The resize helpers live in `ink`, privately.** `ink` owns raster I/O and already
  resamples with Pillow (`pad.py`, `sheet.py`, `washing.py`); `letters` imports no Pillow
  today and need not start. One module holds the 8-bit conversion that `save_rgba`,
  `letter_over` and the attribution share, so the rounding is written once. They are not
  public: no caller outside the library needs them once `letter_over` exists.
- **D6. With nothing to draw, `letter_over` returns a copy of the image, not an error.**
  Lettering nothing over a painting is the painting; the examples' `RuntimeError` was
  their own choice about a file that was missing. A copy, not the same array, so the
  caller may write into the result.
- **D7. `dark` is at the image's size, grown bilinearly.** A caller knows the darkness of
  the picture it painted, not of a plate it never sees. Bilinear is what
  `labelled_grid.py` (the shared grid helper) and `maps.plates.dark_array` already do;
  `nib_stages.py`'s nearest-neighbour `np.repeat` is the one exception, and its marks are
  in design units (its surface scale is `NIB_SCALE * unit`), so 010b keeps it on
  `nib_rgba` with its own surface.
- **D8. `gran_px` is in the image's pixels and has no default.** Every copy computes the
  plate's grain as the image's grain times the plate scale; taking the image's grain and
  multiplying inside removes that step. No default, because the right value is the grain
  of the paper the image was painted on, which only the caller knows.
- **D9. The attribution uses `nib_rgba`, not `letter_over`.** It writes on a composed
  PIL card, on a block-sized plate over a 0.35 darkness, and pastes the block; `letter_over`
  works on a float array the size of the plate. Sharing `shrunk_rgba` is the right seam;
  bending `letter_over` to fit would add parameters only the attribution uses.
- **D10. A style with `plate_lossless` off now letters its attribution losslessly**
  (tested in S4a, review finding 5). The
  attribution was never a plate kept on disk; the lossy file was an artefact of the round
  trip. No shipped or example style turns the flag off, so no image moves; the Changelog
  says so as a `fix`.
- **D11. `Basemap.key` is required and keyword-only.** Rejected: a `Fetched` wrapper
  returned by `fetch` (changes `fetch`'s return type and every stage after it, which
  would all read `.basemap`); `key: str = ""` (a hand-built basemap would paint into
  `cache.plates_dir("")`, the plates root, in silence); `paint(basemap, style, cache)`
  (breaking, and it couples painting to the cache's layout). A required keyword-only
  field is the one shape with no sentinel; it breaks only a basemap built by hand, which no
  example or docs page does (three test builders, updated here), and the Changelog
  marks that line `!`. Not in `canonical`, so no plate hash moves.
- **D12. The CLI and `tests/support/golden.py` move in this PR; the examples and docs do
  not.** Both are the library's own callers of the pattern N3 removes, two lines each,
  and moving them proves the field end to end on the real pipeline. The examples and
  pages are the sweep (010b).
- **D13. #165 and #167 close here.** Their APIs exist and the reference documents them;
  the remaining work is the sweep, recorded under #63 as 010b.
- **D14. `shrunk_rgba` converts to `RGBa` explicitly** (review finding 1). This is the
  attribution's own form today. At a changed size it is the same operation Pillow runs
  inside `RGBA.resize`, so the examples are unaffected. It is the one form that is
  bit-identical at the card's own size too. Relying on Pillow's implicit premultiply would
  move every map card's attribution at the default supersample.
- **D15. The parity recipe passes the plate's grain, `5.0 * 2`** (finding 2). The
  examples pass the plate's grain and `letter_over` takes the image's, so the recipe
  multiplies and `letter_over` multiplies. A failing parity test is never fixed by
  dropping `letter_over`'s multiply.
- **D16. The mutation base is the commit S0 records** (finding 6), so a branch cut from
  010's tip never mutates 010's `ink` functions under 010a.

### Review findings, accepted and rejected

Every finding of `review-plan.md` is applied as the review prescribes. That includes the
three "consider" findings, which cost a line each. None is rejected.
