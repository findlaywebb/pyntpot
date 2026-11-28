# 010 — plan

## Approach

Scoping group E-a (`specs/005-feature-scoping/sessions.md`, "E. Kill the boilerplate") is
three API changes: N1 lettering over an image (#165), N2 blank paper and keyword
arguments (#166), N3 the basemap's key (#167). Measured on `f6c8302`, the three together
with the caller migration N2 forces are too large for one reviewable PR (Decision D1), so
E-a is two stacked PRs and the sweep is a third:

| Spec | Issues | What | Pixels |
|---|---|---|---|
| **010** (this) | #166 | N2: the four `ink` signature changes, `Canvas.pixels`, and every caller moved | none |
| 010a | #165, #167 | N1 and N3: `nib_rgba`, `letter_over`, `NibGroups` defaults, `Basemap.key`; the attribution off disk | none |
| 010b | #63, #174 | E-b: examples, tutorials and how-tos onto the additive calls of 010 and 010a; N11 | none |

ADR 0073 is the design for all three API changes and is written in this PR (Start). This
PR lands its N2 rules (1 to 4); 010a lands the N1 and N3 rules (5 to 11), as ADR 0070
rule 17 landed in 009a.

This PR is one layer, `ink`, plus the callers of the four changed signatures in every
layer. No boundary changes: `ink` imports nothing new, `[tool.importlinter]` is untouched,
and no name enters or leaves any `__all__`. It is breaking: `Sheet`, `wash` and
`brush_from_id` refuse positional arguments they took before, and `wash`'s `base` is
renamed `body`. `Sheet` and `wash` are also in the top-level façade (`pyntpot.__all__`),
so ADR 0007's documented signatures are amended.

Why no pixel moves: every change is to how an argument is spelled, never to its value.
The forced migration rewrites call syntax only, and the one simplification it makes
(dropping a `brush_from_id` argument equal to the new default) passes the same value. S0
records the exact output hashes of every docs image's script on the base, and S4 checks
them; the golden suite runs with no regeneration.

Every fact below was measured on `f6c8302` unless it says otherwise. Read the spec, this
plan, ADR 0073 (written in Start), `CLAUDE.md` and `CONTRIBUTING.md` first.

### ADR 0073 contents

`docs/decisions/0073-boilerplate-free-calls.md`, "Status: accepted", amends 0007, 0026,
0027 and 0068 (each stays as written; 0073 says which sentences it supersedes). Rules:

1. **`Sheet` by keyword, width first.** `@dataclass(kw_only=True)`; the fields are
   reordered `w, h, gran_px, seed, fibre, fibre_stretch, fibre_angle, fibre_cell` (then the
   five `init=False` fields), so the repr and `Attributes:` read width first like
   `Canvas` and Pillow. Every field is keyword-only, so an old positional call, the only
   way to copy the order wrong, fails with `TypeError` instead of transposing. Supersedes
   0007's documented `Sheet(h, w, ...)`.
2. **`Canvas.pixels(*, w, h)`**, a classmethod returning
   `Canvas(0.0, 0.0, float(w), float(h), w, h)`: a canvas that is only its pixel grid, one
   world unit per pixel. Under 1 in either raises `ValueError`. The constructor keeps its
   positional, width-first form, which `maps` uses for a real metre box.
3. **`paper_plate(sheet, canvas, style, display_px=None)`**: `None` measures the grid
   against `canvas.w`. Additive.
4. **`wash(cover, sheet, *, body, pool, options=None)`** and
   **`brush_from_id(brush_id, width_display_px, *, scale=1.0, style=None,
   override=None)`**. `base` is renamed `body`, the glossary's word for the flat part of a
   wash, so one concept has one name. `style=None` means `BrushStyle()`, the default look
   (ADR 0069). Supersedes 0068's "`wash` keeps the signature `wash(cover, sheet, base,
   pool, options=None)`" (a new per-wash setting is still a new `WashOptions` field) and
   0026's positional `brush_from_id`. Tokens are unchanged: `override` still names one of
   the six `BrushStyle.brush_overrides` keys.
5. **`nib_rgba(marks, surface, groups) -> tuple[np.ndarray, np.ndarray] | None`** joins
   `pyntpot.letters.__all__` (010a): the nib plate's straight colour, `(h, w, 3)`, and its
   alpha, `(h, w)`, floats in 0 to 1 at the surface's size, uncast (float32 for a
   float32 darkness); `None` when nothing is drawn.
   `nib_plate` writes exactly these arrays.
6. **`letter_over(image, marks, groups=None, *, gran_px, scale=2, dark=None) ->
   np.ndarray`** joins `pyntpot.letters.__all__` (010a). The marks are in the image's
   pixels. It strokes them with `nib_rgba` on a surface `scale` times the image (built
   with `Canvas.pixels`), with the darkness `dark` (the image's size; `None` is bare
   paper, 0) brought up bilinearly and the paper's grain cell `gran_px` (image pixels)
   times `scale`. It stores the plate as the 8-bit RGBA `nib_plate` would write, shrinks
   it to the image with Lanczos on premultiplied alpha, and returns
   `image * (1 - alpha) + colour * alpha` as a new array. With nothing drawn it returns a
   copy of `image`. A wrong-shaped image or `dark`, or a `scale` under 1, raises
   `ValueError`. `groups=None` means `NibGroups()`.
7. **`NibGroups`' five fields default to the default look** (`NibStyle()`, `FaceStyle()`,
   `HandStyle()`, `BrushStyle()`, `PaperStyle()`), each by `default_factory` (010a).
   Positional construction is unchanged (0068's "keeps positional construction" holds).
   Supersedes the `NibGroups` docstring's "it holds no defaults" (0026's member list is
   unchanged).
8. **The 8-bit Lanczos step stays.** Measured on `f6c8302` with three plates (a
   wordmark on bare paper and two names over a darkness ramp): lossless WebP keeps the
   colour of every pixel with alpha above 0 and the alpha exactly, and Pillow premultiplies
   an RGBA image inside `resize` (so `.convert("RGBa")` before the resize and none give the
   same pixels). An in-memory 8-bit plate shrunk the same way is therefore bit-identical
   to the file round trip, and dropping the file moves no pixel. A float resize is
   rejected here: it would move every lettered docs image and the attribution for a
   difference an 8-bit output cannot show. Moving to one is its own decision with its own
   regeneration.
9. **The attribution writes no file** (010a): `maps.attribution` strokes with `nib_rgba`
   and shrinks with the same 8-bit Lanczos step, so it is bit-identical.
10. **`Basemap.key: str`**, a required keyword-only field, last in the class (010a): the
    cache key of the payloads it was built from, as `Cache.ensure` returned it. `fetch`
    and `build_basemap` set it. It is not in `canonical`, so the base hash and every plate
    are unchanged. The invariant "it carries no cache key, because the cache owns its
    keys" becomes "it carries the key the cache gave it and computes none". Supersedes
    0068's "a field added to [`Basemap`] goes at the end" for this field only: required,
    keyword-only, so a basemap built by hand names its key instead of getting a sentinel.
11. **Callers read the key from the basemap** (010a): `paint(basemap, style,
    cache.plates_dir(basemap.key))`, `candidate_export(track, cache, basemap.key)`,
    `vector_layers(track, cache, basemap.key, style)`. No signature changes; 0027's
    "both cache readers take the cache key" holds, and a caller no longer passes the
    providers a second time to build it.

Consequences: the PR titles (010 with `!`; 010a without, its `Basemap` line with `!` under
Changelog), no golden regeneration in either, and the sweep (010b) moves no pixel either.

### Running the gates

- **Slice gate** (every slice, before its checkpoint commit):

  ```bash
  uv run pytest -n auto --dist loadgroup -m "not golden" -q   # add --golden-tolerance off the pinning machine
  uv run ruff check . && uv run ruff format --check . && uv run ty check && uv run lint-imports
  prek run --all-files
  ```

  `tests/architecture/test_boundaries.py` (the 400-line budget) runs inside it. `ty`
  checks `src`, `examples` and `tests` (`[tool.ty.src]`, every rule an error), so a
  positional call to a keyword-only parameter left anywhere in Python is a type error:
  `uv run ty check` green is the completeness proof for the Python callers.
- **Docs grep** (S2 and S6), must print nothing:

  ```bash
  git grep -nE "Sheet\((H|h|ch|rh|size|height)\b|wash\([^)]*,[^)=]*[0-9.]+, *[0-9.]+\)|brush_from_id\([^)]*, *1\.0, " -- README.md docs ':!docs/decisions' ':!docs/features'
  ```

- **Output hashes** (S0 on the base; S4):
  `PYTHONPATH=tests uv run python tests/golden/output_hashes.py check specs/010-blank-paper-and-keyword-arguments/output-hashes.json`.
- **Coverage gate** (S2, S6): CI's own steps (`.github/workflows/ci.yml`):

  ```bash
  uv run pytest -m "not golden and not benchmark" --cov --golden-tolerance -n auto --dist loadgroup
  uv run coverage report --include="src/pyntpot/ink/*,src/pyntpot/letters/*" --fail-under=95 --precision=2
  uv run coverage report --include="src/pyntpot/maps/*" --fail-under=92 --precision=2
  ```

- **Golden suite** (S4 only, about 27 minutes on four cores):
  `uv run pytest -m golden -n auto --dist loadgroup` (add `--golden-tolerance` off the
  pinning machine).
- **Glossary regeneration** (S3): `PYTHONPATH=tests uv run python -m support.glossary`.
- **Strict docs build** (S3, S6):
  `NO_MKDOCS_2_WARNING=1 uv run --locked --group docs mkdocs build --strict -d "$SCRATCH/site"`.

Every test is written first and seen to fail for the stated reason. Each has a one-line
docstring; `parametrize` carries `ids=`; no mocking, no `autouse`, no `print`.

### Line budget (400; split, never thin)

| File | Now | After | Plan |
|---|---|---|---|
| `src/pyntpot/ink/brush.py` | 355 | about 362 | The two defaults and their `Args:` text. Near the budget: if it passes 380 while you write, move `_sheet_brush`, `_load_reservoir` and `_load_quality` whole to a new `ink/brush_load.py` (a pure move, its own commit) and update this table. |
| `src/pyntpot/letters/nib.py` | 357 | 357 | Two call lines change spelling only. 010a splits it before it grows. |
| `src/pyntpot/ink/washing.py` | 316 | about 318 | Signature, `body` in two lines, docstring. |
| `src/pyntpot/ink/sheet.py` | 199 | about 225 | `kw_only`, field order, `Canvas.pixels`. |
| `src/pyntpot/ink/paper.py` | 90 | about 93 | The default. |
| `tests/golden/output_hashes.py` | 113 (as `grid_hashes.py`) | about 125 | The `--stem` option. |

`tests/` is outside the budget test, but no test file grows past 400 here: the new cases
go into `test_sheet.py` (54), `test_paper.py` (168), `test_wash.py` (208) and
`test_brush.py` (137).

## Slices

Order: Start, S0, S1, S2, S3, S4, S5, S6, all serial on `work-010` (or the branch the
orchestrator names). S1 is additive and green on its own. S2 is the one breaking commit:
the signatures flip and every caller moves in the same commit, because the commit hook
runs `ty`, and no split of a keyword-only flip from its callers is green.

### Start

- Comment on #166 with the branch name; the spec names the issue.
- Write ADR 0073 from "ADR 0073 contents" above.
- The plan-reviewer passes this plan.

### S0: Baseline hashes (serial, first)

- **Owns:** `tests/golden/grid_hashes.py` renamed (`git mv`) to
  `tests/golden/output_hashes.py`, and
  `specs/010-blank-paper-and-keyword-arguments/output-hashes.json` (new).
- **Change:** the module hashes the entries of every `support.docs_images.IMAGES` stem
  by default; a repeatable `--stem STEM` narrows it (`--stem tutorial_grids --stem
  nib_stages ...` reproduces 009's set). `GRID_STEMS` goes. The docstring, the logger
  name and the usage line say `output_hashes`. `record` and `check` keep their meaning
  and their JSON shape (`{image: {"file": sha, "pixels": sha}}`). `git grep grid_hashes
  -- ':!specs'` is empty afterwards (009's spec files keep the old name as history).
- **Command, on the untouched base, committed alone:**
  `PYTHONPATH=tests uv run python tests/golden/output_hashes.py record specs/010-blank-paper-and-keyword-arguments/output-hashes.json`.
  Note the run time in the commit message; the same `check` runs in S4.
- **Gate:** `check` passes on the base; slice gate.

### S1: The additive half (serial)

- **Owns:** `src/pyntpot/ink/sheet.py` (`Canvas.pixels` only), `src/pyntpot/ink/paper.py`,
  `src/pyntpot/ink/brush.py` (the two defaults only; parameters stay positional here),
  `tests/unit/ink/test_sheet.py`, `tests/unit/ink/test_paper.py`,
  `tests/unit/ink/test_brush.py`.
- **Changes:**
  - `Canvas.pixels(cls, *, w: int, h: int) -> Self`, with a docstring (purpose, `Args:`,
    `Returns:`, `Raises:`) and a `ValueError` naming the value when `w < 1` or `h < 1`.
  - `paper_plate(..., display_px: int | None = None)`: `width = canvas.w if display_px is
    None else display_px`, read only inside the grid branch, as today. The `Args:` text
    says what `None` means.
  - `brush_from_id(brush_id, width_display_px, scale=1.0, style=None, override=None)`;
    `style = BrushStyle() if style is None else style` before the first read. Not
    `style=BrushStyle()`: `BrushStyle` holds dicts (`brush_overrides`), so a default
    instance would be shared by every call, and ruff's B008 refuses it.
- **Tests first:**
  - `test_sheet.py`: `Canvas.pixels(w=90, h=60)` equals `Canvas(0, 0, 90, 60, 90, 60)`, its
    `scale` is 1.0 and `px` returns its points unchanged; `w=0` and `h=0` raise
    (parametrized, `ids=`).
  - `test_paper.py`: on one sheet, `paper_plate(sheet, canvas, PaperStyle(grid=True))`
    equals the same call with `canvas.w`, bit for bit, and differs from one with
    `canvas.w // 2` (so the default is read). Same with the grid off. Each paper is drawn
    on a fresh sheet of the same seed, because the paper draws two fields from the
    sheet's generator.
  - `test_brush.py`: `brush_from_id("MAJ6-e", 3.0)` equals
    `brush_from_id("MAJ6-e", 3.0, 1.0, BrushStyle())` (brush fields and ink); a non-default
    `scale` still changes the width.
- **Gate:** slice gate.

### S2: The flip and the forced migration (serial; one commit)

- **Owns:** `src/pyntpot/ink/sheet.py` (`Sheet`), `src/pyntpot/ink/washing.py`,
  `src/pyntpot/ink/brush.py` (the `*`), `src/pyntpot/ink/__init__.py` and
  `src/pyntpot/__init__.py` (docstrings only, where they quote a signature), and every
  caller file below. New tests in `test_sheet.py`, `test_wash.py`, `test_brush.py`.
- **The signatures:**
  - `@dataclass(kw_only=True) class Sheet` with `w` before `h`, and the `Attributes:`
    entries reordered to match (`tests/architecture/test_field_docs.py` checks the
    order). The class docstring gains one sentence: every field is passed by keyword.
  - `wash(cover, sheet, *, body, pool, options=None)`; the two reads of `base` read
    `body`; `Args:` says `body: Density of the flat body of the wash.`.
  - `brush_from_id(brush_id, width_display_px, *, scale=1.0, style=None,
    override=None)`.
- **The callers, measured on `f6c8302` (AST count of calls):**

  | Callee | `src/` | `tests/` | `examples/` |
  |---|---|---|---|
  | `Sheet` | 2 calls, 2 files (`maps/painter/job.py`, `letters/nib.py`) | 44 calls, 17 files | 54 calls, 33 files |
  | `wash` | 5 calls, 3 files (`letters/nib.py`, `maps/painter/*`) | 23 calls, 6 files | 36 calls, 20 files |
  | `brush_from_id` | 4 calls, 3 files (`letters/nib.py`, `maps/painter/pen.py`, `maps/painter/brushes.py`) | 61 calls, 11 files | 27 calls, 19 files |

  About 256 calls in about 70 files. `uv run ty check` lists every one the rewrite
  misses.
- **How (mechanical, scripted):** write a throwaway script in your scratchpad, never
  committed, that parses each `.py` under `src`, `tests` and `examples` with `ast`, finds
  each `Call` whose callee is a name the module imports as `Sheet`, `wash` or
  `brush_from_id` from `pyntpot`, `pyntpot.ink` or their defining modules (or an
  attribute of an imported `pyntpot` module with that name), and rewrites only that call's
  argument list from its source positions, last call first:
  - `Sheet(a, b, c, d, ...)` becomes `Sheet(w=b, h=a, gran_px=c, seed=d, ...)`, keywords
    already present kept in place;
  - `wash(c, s, x, y[, o])` becomes `wash(c, s, body=x, pool=y[, options=o])`;
  - `brush_from_id(i, w, s, st[, o])` becomes `brush_from_id(i, w, scale=s, style=st[,
    override=o])`, leaving out `scale=` when `s` is the literal `1` or `1.0` and `style=`
    when `st` is a bare `BrushStyle()`.
  Comments on the call's lines (`# ty: ignore[...]` among them, as
  `tests/unit/ink/test_wash.py:40` carries) are kept. Then `uv run ruff format .`. Read
  the diff: every changed line is a call's argument list or its reflow, nothing else.
- **The Markdown, by hand:** the blocks the docs grep finds, and the prose:
  - `README.md` (the quick start quotes `examples/wash.py`);
  - `docs/tutorials/paint-a-watercolour.md` (10 `Sheet` lines among its quotes) and
    `docs/tutorials/painting-with-python/{curves,fractals,pictures}.md`, each block
    re-copied from its script after the rewrite, so `test_tutorial_quotes.py` holds;
  - `docs/how-to/paint-your-own-shapes.md` (its `wash` and `brush_from_id` lines);
  - `docs/explanation/how-the-wash-works.md:33`, prose, becomes
    "`wash(cover, sheet, body, pool, options)`" (`test_docs_signatures.py` checks that a
    quoted signature lists every parameter by name), and the sentence after it, which
    says "`pool`", is unchanged;
  - `docs/reference/brushes.md:43` becomes
    "`brush_from_id("MAJ2-c", 12, style=style, override="major")`".
- **Tests first (they fail before the flip):**
  - `test_sheet.py`: `Sheet(240, 360, 8.0, 11)` raises `TypeError` (with
    `# ty: ignore[...]`); each of the five fields of `Sheet(w=360, h=240, gran_px=8.0,
    seed=11)` has shape `(240, 360)`; and `Sheet(h=240, w=360, ...)` gives the same five
    arrays, bit for bit, so keyword order cannot matter. That the values equal today's is
    not pinned here (a hash of float noise is exact only on the pinning machine): the
    existing pins of every test that builds a sheet, which S2 rewrites in spelling only,
    and S4's output hashes prove it. The existing tests of this file are rewritten by the
    codemod like any other caller.
  - `test_wash.py`: `wash(cover, sheet, 0.6, 0.3)` raises `TypeError` (the call carries
    `# ty: ignore[...]`, as the file's existing misuse does); `wash(cover, sheet, body=0.6,
    pool=0.3)` equals the file's existing pinned density.
  - `test_brush.py`: `brush_from_id("MAJ6-e", 3.0, 2.0)` raises `TypeError`.
- **Gate:** slice gate, the coverage gate, and the docs grep empty.

### S3: Records (serial)

- **Owns:** `GLOSSARY.md` and the regenerated glossary files,
  `docs/features/ink-blank-paper-by-size.md` (deleted),
  `docs/features/docs-examples-review.md`, and every file `git grep -l
  ink-blank-paper-by-size` names outside `specs/` and `docs/decisions/`.
- **Glossary:** the "body" row reads "`wash`'s `body` is the body's density". Regenerate.
- **The note:** delete `ink-blank-paper-by-size.md`; repoint each link to ADR 0073. Add to
  `docs-examples-review.md` a section "The sweep onto the new calls (010b)": the 42
  `Canvas(0, 0, w, h, w, h)` in 25 example files and the watercolour tutorial's 12 onto
  `Canvas.pixels`; the 35 `display_px` arguments dropped where they equal the canvas
  width; 010a's `letter_over` and `basemap.key` sweeps (010a adds its own lines). Keep
  the note's second line, its issue link.
- **Gate:** slice gate (the docs tests run in it); the strict docs build; no em or en
  dash in the human prose changed (`git diff -U0 -- docs GLOSSARY.md README.md | grep
  -nP "[\x{2013}\x{2014}]"` prints nothing).

### S4: The pixel proof (serial)

- **Owns:** nothing; it runs checks.
- Output hashes `check` against S0's JSON: all 91 entries unchanged.
- The golden suite, with no regeneration. `git status --porcelain docs/images tests/golden`
  is empty.
- A failure is a defect in S1 or S2 (a value that changed, not a spelling): find it with
  the hash tool's `--stem` on the failing entry, fix it in that slice's files.

### S5: Mutation testing (serial, local)

```bash
patterns=$(mktemp)
uv run python tests/mutation/scope.py --base origin/main --out "$patterns"
xargs -r -a "$patterns" prlimit --as=3500000000 -- uv run mutmut run
uv run mutmut results | grep -v 'not checked'
```

- **Expected in scope:** `Canvas.pixels`, `paper_plate`, `wash` and `brush_from_id` in
  `ink`; `nib_brushes` (its inner `make`), `_sheet` and `_backing_wash` in `letters/nib.py`
  (their calls changed spelling). `Sheet` changes no function (its decorator and field
  order are not function bodies), so nothing of `sheet.py` but `pixels` should be listed;
  if `scope.py` lists more, mutate it anyway. A function `scope.py` lists only because a
  call's spelling changed is still mutated in full.
- **Survivors:** kill each with a test under `tests/unit/ink`, `tests/unit/letters` or
  `tests/property`, or record it as equivalent with the reason in
  `specs/010-blank-paper-and-keyword-arguments/mutation.md`, and copy the equivalents into
  the PR description. A survivor on a line this PR did not change is still killed or
  named; say which lines were untouched.

### S6: Final review and PR (serial, fresh context)

- **Gates:** slice gate, coverage gate, docs grep, strict docs build, `git diff
  origin/main -- pyproject.toml` empty, `git diff --stat origin/main -- docs/images
  tests/golden/docs tests/golden/lynmouth` empty.
- **Reviews:** a fresh-context diff review against this plan, spec compliance first and
  quality second; then the elegance pass. The orchestrator triages.
- **PR:** the spec's title and Changelog; `Closes #166`; the mutation equivalents; a
  "Golden and docs images" section stating none moved, with the S4 `check` log line
  count and the golden run's summary line.

## Files to touch

- `src/pyntpot/ink/sheet.py`, `paper.py`, `washing.py`, `brush.py`; docstrings of
  `src/pyntpot/ink/__init__.py` and `src/pyntpot/__init__.py` where they quote a
  signature.
- The callers in `src/` (`letters/nib.py`, `maps/painter/job.py`, `maps/painter/pen.py`,
  `maps/painter/brushes.py`, and the `maps/painter/*` modules that call `wash`), in
  `tests/` (unit, property, benchmarks, support, examples tests), and in `examples/`: only
  the call lines S2's table counts.
- `README.md`, `docs/tutorials/paint-a-watercolour.md`,
  `docs/tutorials/painting-with-python/{curves,fractals,pictures}.md`,
  `docs/how-to/paint-your-own-shapes.md`, `docs/explanation/how-the-wash-works.md`,
  `docs/reference/brushes.md`.
- `docs/decisions/0073-boilerplate-free-calls.md` (new), `GLOSSARY.md` and its generated
  files, `docs/features/ink-blank-paper-by-size.md` (deleted),
  `docs/features/docs-examples-review.md`.
- `tests/golden/grid_hashes.py` renamed `output_hashes.py`;
  `specs/010-blank-paper-and-keyword-arguments/{output-hashes.json,mutation.md,tasks.md}`.

## Files to leave alone

- **`Canvas`'s constructor and every `Canvas(...)` call**, the 42
  `Canvas(0, 0, w, h, w, h)` in `examples/` included: rewriting them onto
  `Canvas.pixels` is 010b's sweep. They are not broken, and touching them here doubles
  the diff and the tutorial re-quotes.
- **Every `paper_plate(..., W)` call**: dropping `display_px` is 010b's. The default
  exists so the sweep can.
- **Any example line that is not a call of the three changed signatures**: no renames,
  no tidying, even on a line beside one. Each extra line is one more thing the pixel
  proof has to cover and the reviewer has to read.
- **`NibSurface`, `nib_plate`, `NibGroups`, `maps/attribution.py`, `Basemap`, `fetch`,
  `cli.py`, `tests/support/golden.py`**: 010a's.
- **`docs/images/**`, `tests/golden/docs/**`, `tests/golden/lynmouth/**`** and every
  pinned literal: a pin that wants to move is a bug in this PR.
- **Earlier ADRs** (0007, 0026, 0027, 0068 and the rest) keep their text; 0073 says what
  it supersedes.
- **`docs/features/*` notes other than `ink-blank-paper-by-size.md` and
  `docs-examples-review.md`**: they quote today's code as "what exists today", which
  stays true of the time they were written. The N1 and N3 notes are 010a's.
- **`specs/009-*`**: they name `grid_hashes.py` as the history of that PR.
- `pyproject.toml`: no contract, budget or tool setting changes.

## Test plan

| Acceptance criterion | Test |
|---|---|
| `Sheet` keyword-only, `w` before `h`, fields unchanged | `tests/unit/ink/test_sheet.py` (S2): positional `TypeError`; shape; pinned field hashes; `test_field_docs.py` for the order of `Attributes:` |
| `Canvas.pixels` | `test_sheet.py` (S1): equals the six-number canvas, scale 1, identity `px`, refuses 0 |
| `paper_plate` default | `tests/unit/ink/test_paper.py` (S1): grid on and off, bit for bit with `canvas.w`, differs at `canvas.w // 2` |
| `wash` keywords and `body` | `tests/unit/ink/test_wash.py` (S2): positional `TypeError`; keyword call equals the existing pin |
| `brush_from_id` defaults and keywords | `tests/unit/ink/test_brush.py` (S1, S2) |
| Exported and rendered | `tests/unit/test_public_api.py` (unchanged lists, still green), `tests/architecture/test_public_signatures.py`, the strict docs build |
| Callers moved | `uv run ty check` (Python), the docs grep (Markdown), the whole suite |
| Quotes and prose signatures | `tests/docs/test_tutorial_quotes.py`, `test_readme.py`, `test_docs_signatures.py` |
| Pixels do not move | `output_hashes.py check` (S4), the golden suite, `git status` on the image trees |
| ADR, glossary, note | `tests/docs/test_glossary.py`, `test_docs_links.py`, the strict docs build |
| Mutation | S5, `mutation.md` |

No Hypothesis property is added: no algorithm changes. The existing properties under
`tests/property` that build sheets, washes or brushes are rewritten by S2 and stay green,
which is the property-level proof that values are unchanged.

## Delegation

- **Orchestrator (main context):** this plan, the plan-reviewer gate, ADR 0073, the
  integrator's checks after each slice (slice gate; after S2 also the coverage gate and the
  docs grep), commits and the PR.
- **Plan-reviewer:** a fresh-context sceptical staff engineer reads this plan and the
  spec before S0 and blocks until it passes.
- **Implementers:** S0, S1 and S3 are small and mechanical: a cheaper model, briefed
  with the slice section. S2 is mechanical but wide; brief one implementer with S2 alone
  and the instruction to read the diff line by line before committing. S4 is checks only.
  S5 runs locally (it forks).
- **After green:** a fresh-context diff review against the plan, then the elegance pass;
  findings triaged by the orchestrator.

## File-ownership partition

All slices are serial on one branch; a file owned by two slices is edited by the later
one on the earlier one's commit.

| Track | Owns | After |
|---|---|---|
| Start | `docs/decisions/0073-boilerplate-free-calls.md` | base |
| S0 | `tests/golden/output_hashes.py` (renamed), `output-hashes.json` | Start |
| S1 | `ink/sheet.py` (`pixels`), `ink/paper.py`, `ink/brush.py` (defaults), `tests/unit/ink/{test_sheet,test_paper,test_brush}.py` | S0 |
| S2 | `ink/{sheet,washing,brush,__init__}.py`, `pyntpot/__init__.py`, the caller files of S2's table, the Markdown listed in S2, `tests/unit/ink/{test_sheet,test_wash,test_brush}.py` | S1 |
| S3 | `GLOSSARY.md` and generated glossary files, the two notes, links | S2 |
| S4 | none | S3 |
| S5 | `mutation.md`, any test that kills a survivor | S4 |
| S6 | the PR | S5 |

## Decisions

Forks picked with no human in the loop, each with its reason:

- **D1. E-a is split into 010 (N2) and 010a (N1 and N3); the sweep is 010b.** N2's
  keyword-only change forces about 256 call rewrites in about 70 files before the suite
  is green, which is a whole review on its own, while N1 is the one design-heavy change
  (a new `letters` call, a bit-identity argument, a module split). Together, with the
  sweep, the diff would span many context windows and no reviewer could read it in one
  20-minute pass (the sizing rule). N2 goes first because 010a's `letter_over` builds its
  plate with `Canvas.pixels` and a keyword `Sheet`. The sweep is last and separate because
  every new call is bit-identical (D8 of 010a), so the scoping note's reason for one window
  ("re-pin the docs images once instead of three times") no longer applies: no sweep step
  re-pins anything.
- **D2. `Sheet` becomes keyword-only rather than positional `(w, h)`.** Swapping the
  positional order would make every old non-square call transpose silently, the exact
  defect the note names. Keyword-only makes every old call a `TypeError` and every new
  one order-proof. The fields are also reordered `w, h` so the repr agrees with `Canvas`.
- **D3. `Canvas`'s constructor stays positional; only the new `Canvas.pixels` is
  keyword-only.** The constructor is already width first, and its six numbers are a real
  metre box in `maps` (3 calls in `src`, 9 in `tests`). The pixels-only case gets its own
  name and the size goes by keyword, the same rule as `Sheet`.
- **D4. `wash`'s `base` is renamed `body`, and `options` is keyword-only too.** The
  glossary already calls it the body (one name per concept), and the rename costs nothing
  extra when every call is rewritten anyway. `options` follows the `*` so the whole tail
  reads by name; 24 of the 28 `src` and `tests` calls pass it positionally and are
  rewritten.
- **D5. `brush_from_id`'s `style` defaults to `None`, not `BrushStyle()`.** A shared
  default instance holding dicts is a hazard, and ruff B008 refuses the call. `None`
  documented as "`BrushStyle()`, the default look" is the same behaviour. The parameter
  keeps the name `width_display_px` (the note suggested `width_px`): `scale` converts
  display pixels to render pixels, and the name says which side it is on.
- **D6. `paper_plate` keeps its `canvas` and `style` parameters.** Dropping `canvas`
  (the sheet already knows its size) would be a fourth breaking change for no caller that
  `Canvas.pixels` does not already serve, and `maps` passes its job's canvas. `display_px`
  becomes optional, which is additive.
- **D7. The forced migration drops `brush_from_id` arguments equal to the new
  defaults.** Writing `scale=1.0, style=BrushStyle()` out would add the boilerplate this
  change exists to remove, and 010b would touch the same line again. It is the only
  simplification S2 makes; everything else is spelling.
- **D8. The pixel proof is exact hashes of every docs image's script output, plus the
  golden suite.** `grid_hashes.py` already does this for five stems; widening it to every
  stem (renamed `output_hashes.py`, since it no longer concerns grids) costs one option
  and proves the whole docs set, not a sample.
- **D9. One ADR, 0073, for all three changes, written here.** The constraint asks for
  one record; 010a implements its rules 5 to 11 and cites it. This follows ADR 0070, whose
  rule 17 landed a PR later.
- **D10. #166 closes here.** The API the note asks for exists and is documented in the
  reference; what remains (adopting `Canvas.pixels` in the examples and the tutorial) is
  the sweep, recorded under #63's note as 010b, so the issue and the note do not stay
  open for work another issue tracks.
