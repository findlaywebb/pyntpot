# 010 — plan

**Revision 2**, after the plan review (`review-plan.md`, verdict BLOCK), rebased on
`38179789` (main with the toolchain bump: ty 0.0.100). What changed:

- Findings 1 to 4 (blocking): the codemod's rules are now exact. It rewrites positional
  arguments only, never an existing keyword. It runs before the negative tests are
  written. It has one rule for a starred `Sheet` and refuses any other starred or `**`
  form loudly. S1's equality test writes its explicit side by keyword.
  `ruff check --fix --select F401` and the `BrushStyle` docstring and tutorial edits
  follow D7, and the spec's "nothing else changes" names them. S2 owns
  `tests/docs/test_docs_signatures.py`.
- Findings 5 to 12 (should-fix), all applied: the wash pin is `test_wash_density.PINNED`;
  `output_hashes.py --stem` semantics and a self-test; the ADR index row and the
  amended-by clauses; ADR rule 1 quotes only sentences that exist; the
  `docs-tutorial-opening-programs.md` mentions; an AST check over fenced blocks replaces
  the docs grep; a bounded mutation rule; three small ambiguities.
- Findings 13 to 15 (consider), all applied: 0073 says 010a may amend rules 5 to 11;
  `test_benchmark_inputs.py` gains a `brush_from_id` check; 0073's consequences keep the
  `maps` "base" theme vocabulary.
- From 010a's review, finding 1: ADR rules 8 and 9 say Pillow premultiplies only in a
  resize that changes the size, and `shrunk_rgba` premultiplies explicitly.
- The ADR number: 0072 is taken by spec 008a (the theme preview card), which lands before
  010, so this ADR is 0073.
- ty claims re-checked under ty 0.0.100: a positional call to these signatures is
  `too-many-positional-arguments` plus `missing-argument`, and a leftover `base=` is
  `unknown-argument` (measured on a scratch file). No plan line relies on the renamed
  `unresolved-import` rule.

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
rule 17 landed in 009a. The number skips 0072 because spec 008a (the theme preview card)
holds it and lands before 010.

This PR is one layer, `ink`, plus the callers of the four changed signatures in every
layer. No boundary changes: `ink` imports nothing new, `[tool.importlinter]` is untouched,
and no name enters or leaves any `__all__`. It is breaking: `Sheet`, `wash` and
`brush_from_id` refuse positional arguments they took before, and `wash`'s `base` is
renamed `body`. `Sheet` and `wash` are also in the top-level façade (`pyntpot.__all__`).
The documented signatures of public names are bound by ADR 0026's member rule, so 0073
records the break.

Why no pixel moves: every change is to how an argument is spelled, never to its value.
The forced migration rewrites call syntax only. Its one simplification, dropping a
`brush_from_id` argument equal to the new default, passes the same value. It also brings
two edits that simplification forces: a `BrushStyle` import left unused, and that name in
the module docstring's list of names used. S0
records the exact output hashes of every docs image's script on the base, and S4 checks
them; the golden suite runs with no regeneration.

Every fact below was measured on `f6c8302` unless it says otherwise. Read the spec, this
plan, ADR 0073 (written in Start), `CLAUDE.md` and `CONTRIBUTING.md` first.

### ADR 0073 contents

`docs/decisions/0073-boilerplate-free-calls.md`, "Status: accepted", amends 0007, 0026,
0027 and 0068. Each stays as written, and 0073 quotes only sentences that exist in them.
It says once, near the top, that rules 5 to 11 land in 010a, which may amend them in its
own PR if its implementation or review needs it. The index row says so until 010a lands.
Rules:

1. **`Sheet` by keyword, width first.** `@dataclass(kw_only=True)`; the fields are
   reordered `w, h, gran_px, seed, fibre, fibre_stretch, fibre_angle, fibre_cell` (then the
   five `init=False` fields), so the repr and `Attributes:` read width first like
   `Canvas` and Pillow. Every field is keyword-only, so an old positional call, the only
   way to copy the order wrong, fails with `TypeError` instead of transposing. This is a
   breaking change to the documented signatures of `Sheet` (one of 0007's façade
   names), `wash` (0068's "keeps the signature" sentence, rule 4) and `brush_from_id`
   (bound by 0026's member rule: "the names in `__all__` and their documented
   signatures").
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
   `brush_from_id`'s documented positional signature (0026). Tokens are unchanged:
   `override` still names one of the six `BrushStyle.brush_overrides` keys.
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
   times `scale`. It stores the plate as the 8-bit RGBA `nib_plate` would write, converts
   it explicitly to premultiplied `RGBa`, shrinks it to the image with Lanczos, converts
   back to `RGBA`, and returns
   `image * (1 - alpha) + colour * alpha` as a new array. With nothing drawn it returns a
   copy of `image`. A wrong-shaped image or `dark`, or a `scale` under 1, raises
   `ValueError`. `groups=None` means `NibGroups()`.
7. **`NibGroups`' five fields default to the default look** (`NibStyle()`, `FaceStyle()`,
   `HandStyle()`, `BrushStyle()`, `PaperStyle()`), each by `default_factory` (010a).
   Positional construction is unchanged (0068's "keeps positional construction" holds).
   Supersedes the `NibGroups` docstring's "it holds no defaults" (0026's member list is
   unchanged).
8. **The 8-bit Lanczos step stays, premultiplied explicitly.** Measured on `f6c8302`
   with three plates (a wordmark on bare paper and two names over a darkness ramp). With
   `plate_lossless` on (the default, and every shipped and example style), lossless WebP
   keeps the alpha exactly and the colour of every pixel whose alpha is above 0. Pillow
   premultiplies an RGBA image inside a `resize` that changes the size, so at a 2x shrink
   `.convert("RGBa")` before the resize and no conversion give the same pixels. A
   `resize` to the image's own size is a plain copy with no premultiply (Pillow returns
   `self.copy()` before its premultiply branch), and the attribution strokes at the card's
   own size whenever the card is supersampled 2x or more (its plate factor is 1). So the
   shared shrink always runs `.convert("RGBa").resize(...).convert("RGBA")`, which is the
   attribution's own form and, at any changed size, exactly what Pillow does inside. An
   in-memory 8-bit plate shrunk that way is bit-identical to the file round trip at every
   scale (measured by the 010a review at supersample 1, 2 and 3), and dropping the file
   moves no pixel. With `plate_lossless` off, the file was lossy, and the in-memory plate
   is the lossless one (010a's `fix` line). A float resize is rejected here: it would move
   every lettered docs image and the attribution for a difference an 8-bit output cannot
   show. Moving to one is its own decision with its own regeneration.
9. **The attribution writes no file** (010a): `maps.attribution` strokes with `nib_rgba`
   and shrinks with the same explicit-premultiply 8-bit Lanczos step, so it is
   bit-identical for every lossless style, at the card's own size included.
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
The word "base" stays in `maps`' cover vocabulary (`maps/painter/cover.py` unpacks
`base, pool` from the cover settings, and `CoverStyle.pale_base` feeds the wash body).
Those are theme keys, so renaming them would be a breaking theme change. It is out of
scope here, and the elegance pass must not "fix" it.

**The index** (`docs/decisions/README.md`, Start): a row
"| 0073 | Boilerplate-free calls (amends 0007, 0026, 0027 and 0068; rules 5 to 11 land
in 010a) |". Each of the four amended rows gains an "amended by 0073: ..." clause in the
form row 0069 uses:
- 0007: "its façade's `Sheet` and `wash` take keywords";
- 0026: "`brush_from_id` takes `scale`, `style` and `override` by keyword, and
  `NibGroups` has defaults";
- 0027: "a caller reads the key from `basemap.key`";
- 0068: "`wash` takes `body`, `pool` and `options` by keyword, and `Basemap` gains a
  required keyword-only `key`".
Once 010a lands, it removes "rules 5 to 11 land in 010a" from the 0073 row.

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
- **Docs call check** (S2 and S6), a throwaway script in your scratchpad, never
  committed, run with `PYTHONPATH=tests`. It takes every fenced block from `README.md`
  and from each page under `docs/` outside `docs/decisions/` and `docs/features/`
  (`support.site_pages.fenced_blocks`). It parses each block as Python, wrapping a block
  that does not parse in `def _():` with its lines indented, and skips a block that still
  does not parse, logging its page and line. It reports every `Sheet` call with a
  positional argument, and every `wash` or `brush_from_id` call with more than two
  positional arguments, with page and line. It must report nothing. Prose outside the
  blocks is covered by `git grep -n "brush_from_id(\|wash(" -- docs/reference/brushes.md
  docs/explanation/how-the-wash-works.md`, read by eye, and by `test_docs_signatures.py`.
  (It replaces revision 1's regex, which could not cross a `)` and missed
  `wash(_disc(...), sheet, body, 0.5)`, `curves.md:147` and `pictures.md:31`.)
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
docstring; `parametrize` carries `ids=`; no mocking, no `autouse`, no `print`. A
deliberate misuse carries the exact ty codes it raises under ty 0.0.100: a positional call
to these signatures is `# ty: ignore[too-many-positional-arguments, missing-argument]`
(measured). An ignore that is not needed is itself an error (`unused-ignore-comment`).

### Line budget (400; split, never thin)

| File | Now | After | Plan |
|---|---|---|---|
| `src/pyntpot/ink/brush.py` | 355 | about 362 | The two defaults and their `Args:` text. Near the budget: if it passes 380 while you write, move `_sheet_brush`, `_load_reservoir` and `_load_quality` whole to a new `ink/brush_load.py` (a pure move, its own commit) and update this table. |
| `src/pyntpot/letters/nib.py` | 357 | 357 | Two call lines change spelling only. 010a splits it before it grows. |
| `src/pyntpot/ink/washing.py` | 316 | about 318 | Signature, `body` in two lines, docstring. |
| `src/pyntpot/ink/sheet.py` | 199 | about 225 | `kw_only`, field order, `Canvas.pixels`. |
| `src/pyntpot/ink/paper.py` | 90 | about 93 | The default. |
| `tests/golden/output_hashes.py` | 104 (as `grid_hashes.py`) | about 130 | The `--stem` option and its narrowing. |

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
- Write ADR 0073 from "ADR 0073 contents" above, and its index row and the four
  amended-by clauses in `docs/decisions/README.md`.
- The plan-reviewer passes this plan.

### S0: Baseline hashes (serial, first; two commits)

- **Owns:** `tests/golden/grid_hashes.py` renamed (`git mv`) to
  `tests/golden/output_hashes.py`, `tests/golden/test_output_hashes.py` (new), and
  `specs/010-blank-paper-and-keyword-arguments/output-hashes.json` (new).
- **Change:** the module hashes the entries of every `support.docs_images.IMAGES` stem
  by default. A repeatable `--stem STEM` narrows it: `--stem tutorial_grids --stem
  nib_stages ...` reproduces 009's set. `GRID_STEMS` goes. The docstring, the logger
  name and the usage line say `output_hashes`. The JSON shape
  (`{image: {"file": sha, "pixels": sha}}`) is unchanged. With `--stem`:
  - `record` measures and writes only the selected stems' entries;
  - `check` measures only the selected stems' entries and compares them. It ignores
    recorded entries of other stems. It still errors, and exits 1, on a selected entry
    missing from the JSON, a selected entry whose hashes differ, and a recorded entry of
    a selected stem that no longer exists;
  - a `--stem` that names no registered stem is an argparse error (exit 2), checked
    before anything is painted.
  Without `--stem`, both behave as today across every entry. `git grep grid_hashes --
  ':!specs'` is empty afterwards (009's spec files keep the old name as history).
- **Self-test first** (`tests/golden/test_output_hashes.py`, the precedent being the
  other `tests/golden/test_*.py` helper tests). It drives the selection and comparison
  functions on a hand-written recorded mapping and a hand-written measured mapping,
  without painting:
  - a narrowed check ignores another stem's recorded entries;
  - it reports a selected entry that is missing or differs;
  - an unknown stem is refused.
  If the module's structure needs splitting so selection and comparison are callable
  without painting, do that in this slice.
- **Commits:** the tool change and its self-test are one commit. The JSON recorded on the
  untouched base (`src/`, `tests/` and `examples/` as on the base, the tool aside) is a
  second commit, alone. Its message names the base commit and the run time:
  `PYTHONPATH=tests uv run python tests/golden/output_hashes.py record specs/010-blank-paper-and-keyword-arguments/output-hashes.json`.
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
  - `test_paper.py`: with the grid on, `paper_plate(sheet, canvas, PaperStyle(grid=True))`
    equals the same call with `canvas.w`, bit for bit, and differs from one with
    `canvas.w // 2`, so the default is read. With the grid off it asserts equality with
    the `canvas.w` call only: `display_px` is not read when the grid is off
    (`paper.py:84-85`), so no "differs" case can hold. Each paper is drawn on a fresh
    sheet of the same seed, because the paper draws two fields from the sheet's generator.
  - `test_brush.py`: `brush_from_id("MAJ6-e", 3.0)` equals
    `brush_from_id("MAJ6-e", 3.0, scale=1.0, style=BrushStyle())`, brush fields and ink.
    The explicit side is written **by keyword**, which is legal in S1 and which S2's
    codemod never touches (rule 1 below), so the test keeps proving that `style=None`
    means `BrushStyle()`. A non-default `scale` still changes the width.
- **Gate:** slice gate.

### S2: The flip and the forced migration (serial; one commit)

- **Owns:** `src/pyntpot/ink/sheet.py` (`Sheet`), `src/pyntpot/ink/washing.py`,
  `src/pyntpot/ink/brush.py` (the `*`), every caller file below,
  `tests/docs/test_docs_signatures.py`, `tests/architecture/test_benchmark_inputs.py`,
  the module docstrings of the 14 example files
  named below, and the new tests in `test_sheet.py`, `test_wash.py` and `test_brush.py`.
  Neither `__init__.py` docstring quotes a signature (verified by the review), so neither
  is touched.
- **The signatures:**
  - `@dataclass(kw_only=True) class Sheet` with `w` before `h`, and the `Attributes:`
    entries reordered to match (`tests/architecture/test_field_docs.py` checks the
    order). The class docstring gains one sentence: every field is passed by keyword.
  - `wash(cover, sheet, *, body, pool, options=None)`; the two reads of `base` read
    `body`; `Args:` says `body: Density of the flat body of the wash.`.
  - `brush_from_id(brush_id, width_display_px, *, scale=1.0, style=None,
    override=None)`.
- **The callers, measured on `f6c8302` (AST count of calls, reproduced by the review):**

  | Callee | `src/` | `tests/` | `examples/` |
  |---|---|---|---|
  | `Sheet` | 2 calls, 2 files (`maps/painter/job.py`, `letters/nib.py`) | 44 calls, 17 files | 54 calls, 33 files |
  | `wash` | 5 calls, 3 files (`letters/nib.py`, `maps/painter/*`) | 23 calls, 6 files | 36 calls, 20 files |
  | `brush_from_id` | 4 calls, 3 files (`letters/nib.py`, `maps/painter/pen.py`, `maps/painter/brushes.py`) | 61 calls, 11 files | 27 calls, 19 files |

  About 256 calls in about 70 files. The one call through an attribute is
  `pyntpot.Sheet(64, 64, 8.0)` (`tests/unit/test_public_api.py:173`). No target call nests
  inside another, and none carries a `# ty: ignore`. `uv run ty check` lists every call
  the rewrite misses.
- **Order inside the slice:** the signature changes first, then the codemod, then
  `ruff format` and the F401 pass, then the Markdown, then the three negative tests.
  The negative tests are written **after** the codemod has run, in the same commit, so
  the codemod never sees them. To watch them fail for the right reason, run them once on
  a `git worktree add` of S1's commit in your scratchpad: there each call is still
  accepted, and each test fails with "DID NOT RAISE". This ordering replaces any rule
  about skipping calls inside `pytest.raises` blocks.
- **The codemod (mechanical, scripted).** A throwaway script in your scratchpad, never
  committed. It parses each `.py` under `src`, `tests` and `examples` with `ast`. It finds
  each `Call` whose callee is a name the module imports as `Sheet`, `wash` or
  `brush_from_id` from `pyntpot`, `pyntpot.ink` or their defining modules, or an
  attribute of an imported `pyntpot` module with that name. It rewrites only that call's
  argument list from its source positions, last call first. Its rules:
  1. **Positional arguments only.** It never adds, drops, renames or reorders a keyword
     argument that is already present. An existing `scale=1.0` or `style=BrushStyle()`
     keyword stays as written (S1's test depends on it).
  2. `Sheet(a, b, c, d, ...)` becomes `Sheet(w=b, h=a, gran_px=c, seed=d, ...)`.
  3. **A starred first argument to `Sheet`.** `Sheet(*s, ...)` becomes
     `Sheet(w=s[1], h=s[0], ...)`, with `s` written as its source text, and any further
     positional arguments mapped from `gran_px` on as in rule 2. No new local variable.
     The four cases (all `(height, width)` tuples):
     - `tests/unit/maps/painter/test_paper.py:23` and `:38`:
       `Sheet(w=job.shape[1], h=job.shape[0], gran_px=6.0, seed=3)`;
     - `tests/unit/maps/painter/test_water.py:32`:
       `Sheet(w=cov.shape[1], h=cov.shape[0], gran_px=8.0, seed=5)`;
     - `examples/line_effect_grids.py:201`:
       `Sheet(w=size[1], h=size[0], gran_px=GRAN_PX * SUPERSAMPLE, seed=SEED)`
       (`size` is `(height, width)`, `:200`).
  4. `wash(c, s, x, y[, o])` becomes `wash(c, s, body=x, pool=y[, options=o])`.
  5. `brush_from_id(i, w, s, st[, o])` becomes `brush_from_id(i, w, scale=s, style=st[,
     override=o])`. It leaves out a positional `s` that is the literal `1` or `1.0`, and
     a positional `st` that is a bare `BrushStyle()` (D7). This applies to positional
     arguments only, by rule 1.
  6. **Loud refusal.** Any other starred argument (`*x` anywhere but `Sheet`'s first
     position) or any `**kwargs` in a target call makes the script stop with the file and
     line, writing nothing. There is none today. A new one is handled by hand and added
     to this plan.
  The script keeps comments on the call's lines. Then run `uv run ruff format .`.
- **The fallout of D7, prescribed.** Dropping `style=BrushStyle()` leaves `BrushStyle`
  imported and unused in 14 example files. Two commands and two hand edits follow:
  1. `uv run ruff check --fix --select F401 src tests examples`. Read its diff: it
     removes only `BrushStyle` from the import lists of these 14 files and nothing else.
     - `examples/brush_gallery.py`, `brush_sheet.py`, `brush_stroke.py`,
       `cased_stroke.py`, `curves.py`, `fern.py`, `fern_family.py`, `kaleidoscope.py`
     - `examples/line_effect_reasons.py`, `line_effect_scenes.py`, `nib_line.py`,
       `site_theme.py`, `svg_drawing.py`, `tutorial_grids.py`
  2. In each of those 14 module docstrings, remove `BrushStyle` from the sentence that
     lists the public names the script uses or introduces. For example,
     `brush_stroke.py:10` reads "Public names it introduces: `BrushStyle`,
     `brush_from_id`, ...", and `nib_line.py:9` reads "Public names it uses:
     `BrushStyle`, ...". `brush_stroke.py:3-5`'s "with the `BrushStyle` defaults" becomes
     "with the default brush style", which stays true.
  3. Re-copy every tutorial block that quotes one of the changed lines (imports and
     docstrings included).
  4. `tests/architecture/test_benchmark_inputs.py` stops a benchmark from building
     `BrushStyle` directly, so that it never times whatever the default look is. With
     `style=None` meaning `BrushStyle()`, a benchmark's `brush_from_id(id, w)` would get
     round that check. Extend it: a `brush_from_id` call under `tests/benchmarks/` with
     no `style=` keyword is flagged. Today's three calls (`tests/benchmarks/test_ink.py:63,
     91, 104`) pass `flags_off(BrushStyle)`, which the codemod turns into `style=...`, so
     the extended check is green. Write that case first and watch it fail on a scratch
     benchmark call without `style=`.
  5. In `tests/unit/test_public_api.py:172`, the test docstring
     "`pyntpot.Sheet(64, 64, 8.0)` constructs a sheet" becomes
     "`pyntpot.Sheet(w=64, h=64, gran_px=8.0)` constructs a sheet". This is the one test
     docstring edit S2 makes.
- **Reading the diff.** Every changed line is one of these:
  - a target call's argument list or its reflow;
  - an import line losing `BrushStyle` (the 14 files);
  - a name-list sentence or the `brush_stroke.py` sentence in those 14 module
    docstrings;
  - the `test_public_api.py:172` docstring and the `test_benchmark_inputs.py` case;
  - a Markdown line listed below;
  - a new test.
  Anything else is a defect of the script.
- **`tests/docs/test_docs_signatures.py:76-77`.** The extractor's self-test literals
  ``"`wash(cover, sheet, base, pool)` here."`` and
  ``"`wash(cover, sheet, base, pool, options)` here."`` read `body` for `base`. They are
  strings, so neither the codemod nor ty reaches them.
- **The Markdown, by hand.** The blocks the docs call check finds, and the prose:
  - `README.md` (the quick start quotes `examples/wash.py`);
  - `docs/tutorials/paint-a-watercolour.md` (10 `Sheet` lines among its quotes) and
    `docs/tutorials/painting-with-python/{curves,fractals,pictures}.md`. Each block is
    re-copied from its script after the rewrite, so `test_tutorial_quotes.py` holds;
  - `docs/how-to/paint-your-own-shapes.md` (its `wash` and `brush_from_id` lines);
  - `docs/explanation/how-the-wash-works.md:33`, prose, becomes
    "`wash(cover, sheet, body, pool, options)`". `test_docs_signatures.py` checks that a
    quoted signature lists every parameter by name. The sentence after it, which says
    "`pool`", is unchanged;
  - `docs/reference/brushes.md:43` becomes
    "`brush_from_id("MAJ2-c", 12, style=style, override="major")`".
- **The negative tests (written last, see "Order"):**
  - `test_sheet.py`: `Sheet(240, 360, 8.0, 11)` raises `TypeError`, with
    `# ty: ignore[too-many-positional-arguments, missing-argument]`. Each of the five
    fields of `Sheet(w=360, h=240, gran_px=8.0, seed=11)` has shape `(240, 360)`.
    `Sheet(h=240, w=360, ...)` gives the same five arrays, bit for bit, so keyword order
    cannot matter. That the values equal today's is not pinned here, because a hash of
    float noise is exact only on the pinning machine. The proof is the existing pins of
    the tests that build a sheet, which S2 rewrites in spelling only: `test_paper.py`'s
    classic plate and `tests/unit/ink/test_wash_density.py`'s `PINNED`. S4's output
    hashes prove it too.
  - `test_wash.py`: `wash(cover, sheet, 0.6, 0.3)` raises `TypeError`, with the same
    ignore codes. There is no keyword-equals-pin assertion here. The pinned densities are
    `PINNED` in `tests/unit/ink/test_wash_density.py:15-24` (body 0.52, pool 0.20), and
    the codemod rewrites the test that reads them
    (`test_each_option_lays_the_pinned_density`, `:41`) into keyword form. That rewritten
    test, still green, is the proof.
  - `test_brush.py`: `brush_from_id("MAJ6-e", 3.0, 2.0)` raises `TypeError`, with the
    ignore codes ty reports for it.
- **Gate:** slice gate, the coverage gate, and the docs call check reporting nothing.

### S3: Records (serial)

- **Owns:**
  - `GLOSSARY.md` and the regenerated glossary files;
  - `docs/features/ink-blank-paper-by-size.md` (deleted);
  - `docs/features/docs-examples-review.md`;
  - `docs/features/docs-tutorial-opening-programs.md`, at lines 15 and 21 only;
  - every other file `git grep -l ink-blank-paper-by-size` names outside `specs/` and
    `docs/decisions/`.
- **Glossary:** the "body" row reads "`wash`'s `body` is the body's density". Regenerate.
- **The note:** delete `ink-blank-paper-by-size.md` and repoint each link to ADR 0073.
  - In `docs-tutorial-opening-programs.md:15` and `:21`, the backticked name becomes
    "#166, closed by ADR 0073; the sweep is under `docs-examples-review.md`".
  - Add to `docs-examples-review.md` a section "The sweep onto the new calls (010b)":
    - the 42 `Canvas(0, 0, w, h, w, h)` in 25 example files, and the watercolour
      tutorial's 12, move onto `Canvas.pixels`;
    - the 35 `display_px` arguments are dropped where they equal the canvas width;
    - 010a's `letter_over` and `basemap.key` sweeps (010a adds its own lines).
  - Keep the note's second line, its issue link.
- **Gate:**
  - the slice gate (the docs tests run in it);
  - the strict docs build;
  - `git grep ink-blank-paper-by-size -- ':!specs' ':!docs/decisions'` is empty;
  - no em or en dash in the changed human prose
    (`git diff -U0 -- docs GLOSSARY.md README.md | grep -nP "[\x{2013}\x{2014}]"`
    prints nothing).

### S4: The pixel proof (serial)

- **Owns:** nothing; it runs checks.
- Output hashes `check` against S0's JSON: all 91 entries unchanged.
- The golden suite, with no regeneration. `git status --porcelain docs/images tests/golden`
  is empty.
- A failure is a defect in S1 or S2: a value that changed, not a spelling. Narrow it with
  `check --stem <stem>` (S0's semantics: other stems are ignored) and fix it in that
  slice's files. Never re-record.

### S5: Mutation testing (serial, local, bounded)

```bash
patterns=$(mktemp)
uv run python tests/mutation/scope.py --base origin/main --out "$patterns"
xargs -r -a "$patterns" prlimit --as=3500000000 -- uv run mutmut run
uv run mutmut results | grep -v 'not checked'
```

- **The rule, and why.** S2 changes the bodies of `wash`, `brush_from_id`,
  `nib_brushes`, `letters.nib._sheet` and `_backing_wash` only in how a call is spelled
  or a name is read (`base` to `body`). Their behaviour is unchanged, and the pins and S4
  prove it. 006 faced the same case and kept spelling-only functions out of its run list,
  having compared normalised ASTs.
  - **In full:** `Canvas.pixels` (new) and `paper_plate` (a new branch) are mutated in
    full, and every survivor is killed or named.
  - **Spelling-only:** for each of the five functions above, first show it is
    spelling-only. Compare its `ast.dump` on the base and on the branch after
    normalising the rewritten calls' keywords and the `base`/`body` name. Record the
    comparison in `mutation.md`.
  - **Then** mutate `wash` and `brush_from_id` anyway, because they are the signatures
    that changed. Check each survivor against the equivalent lists already recorded for
    them in `specs/006-one-public-surface/mutation.md` (`wash`: 203 mutants, 8
    equivalents), `specs/008-themes-as-data/mutation.md` and
    `specs/009-line-effects-and-registry/mutation.md`. The mutant numbers will have
    moved, so each reason is re-checked against the code, not copied. A survivor those
    lists name, whose reason still holds, is recorded as equivalent with that reason.
  - **Kept out:** the other three, which are spelling-only and in `letters`, are left out
    of the run, and `mutation.md` says so and why.
- **Where survivor tests go:**
  - `ink`: `tests/unit/ink/test_wash.py`, `test_brush.py`, `test_paper.py` (168 lines)
    and `test_sheet.py`;
  - `letters`: `tests/unit/letters/test_nib.py`, or a new file under
    `tests/unit/letters/`, because `test_nib.py` is already 403 lines;
  - `tests/property`.
  No test file may pass 400 lines; start a new file instead.
- **The bound.** If killing one function's survivors would add more than about 150 lines
  of tests, kill the ones on lines this PR changed. File the rest as a `docs/issues/`
  note and a GitHub issue (CLAUDE.md, "Issues and features"), and name them in
  `mutation.md` and the PR description. They are not added to this diff.
- **Record:** `specs/010-blank-paper-and-keyword-arguments/mutation.md`, and the
  equivalents in the PR description.

### S6: Final review and PR (serial, fresh context)

- **Gates:**
  - the slice gate, the coverage gate, the docs call check and the strict docs build;
  - `git diff origin/main -- pyproject.toml` is empty;
  - `git diff --stat origin/main -- docs/images tests/golden/docs tests/golden/lynmouth`
    is empty.
- **Reviews:** a fresh-context diff review against this plan, spec compliance first and
  quality second; then the elegance pass. The orchestrator triages.
- **PR:** the spec's title and Changelog; `Closes #166`; the mutation equivalents; a
  "Golden and docs images" section stating none moved, with the S4 `check` log line
  count and the golden run's summary line.

## Files to touch

- `src/pyntpot/ink/sheet.py`, `paper.py`, `washing.py`, `brush.py`.
- The callers in `src/` (`letters/nib.py`, `maps/painter/job.py`, `maps/painter/pen.py`,
  `maps/painter/brushes.py`, and the `maps/painter/*` modules that call `wash`), in
  `tests/` (unit, property, benchmarks, support, examples tests), and in `examples/`: only
  the call lines S2's table counts, plus the D7 fallout S2 prescribes (the `BrushStyle`
  import and docstring name in 14 example files) and the `test_public_api.py:172`
  docstring.
- `tests/docs/test_docs_signatures.py` (two literals), `tests/architecture/test_benchmark_inputs.py`
  (the `brush_from_id` case), `tests/golden/test_output_hashes.py` (new).
- `README.md`, `docs/tutorials/paint-a-watercolour.md`,
  `docs/tutorials/painting-with-python/{curves,fractals,pictures}.md`,
  `docs/how-to/paint-your-own-shapes.md`, `docs/explanation/how-the-wash-works.md`,
  `docs/reference/brushes.md`.
- `docs/decisions/0073-boilerplate-free-calls.md` (new), `docs/decisions/README.md` (the
  row and four amended-by clauses), `GLOSSARY.md` and its generated files,
  `docs/features/ink-blank-paper-by-size.md` (deleted),
  `docs/features/docs-examples-review.md`, `docs/features/docs-tutorial-opening-programs.md`
  (lines 15 and 21).
- `tests/golden/grid_hashes.py` renamed `output_hashes.py`;
  `specs/010-blank-paper-and-keyword-arguments/{output-hashes.json,mutation.md,tasks.md}`.

## Files to leave alone

- **`Canvas`'s constructor and every `Canvas(...)` call**, the 42
  `Canvas(0, 0, w, h, w, h)` in `examples/` included: rewriting them onto
  `Canvas.pixels` is 010b's sweep. They are not broken, and touching them here doubles
  the diff and the tutorial re-quotes.
- **Every `paper_plate(..., W)` call**: dropping `display_px` is 010b's. The default
  exists so the sweep can.
- **Any example line that is not a call of the three changed signatures**, other than
  the D7 fallout S2 names: no renames, no tidying, even on a line beside one. Each extra line is one more thing the pixel
  proof has to cover and the reviewer has to read.
- **`NibSurface`, `nib_plate`, `NibGroups`, `maps/attribution.py`, `Basemap`, `fetch`,
  `cli.py`, `tests/support/golden.py`**: 010a's.
- **`docs/images/**`, `tests/golden/docs/**`, `tests/golden/lynmouth/**`** and every
  pinned literal: a pin that wants to move is a bug in this PR.
- **Earlier ADRs** (0007, 0026, 0027, 0068 and the rest) keep their text; 0073 says what
  it supersedes, and only their index rows gain the amended-by clause.
- **`docs/features/*` notes other than `ink-blank-paper-by-size.md`,
  `docs-examples-review.md` and lines 15 and 21 of `docs-tutorial-opening-programs.md`**: they quote today's code as "what exists today", which
  stays true of the time they were written. The N1 and N3 notes are 010a's.
- **`specs/009-*`**: they name `grid_hashes.py` as the history of that PR.
- `pyproject.toml`: no contract, budget or tool setting changes.
- **`maps`' "base" cover vocabulary** (`maps/painter/cover.py`'s `base, pool`,
  `CoverStyle.pale_base`): theme keys, out of scope (ADR 0073, consequences).

## Test plan

| Acceptance criterion | Test |
|---|---|
| `Sheet` keyword-only, `w` before `h`, fields unchanged | `tests/unit/ink/test_sheet.py` (S2): positional `TypeError`; shape `(h, w)`; keyword order irrelevant; values proven by the existing pins (`test_paper.py`'s classic plate, `test_wash_density.PINNED`) and S4; `test_field_docs.py` for the order of `Attributes:` |
| `Canvas.pixels` | `test_sheet.py` (S1): equals the six-number canvas, scale 1, identity `px`, refuses 0 |
| `paper_plate` default | `tests/unit/ink/test_paper.py` (S1): grid on, bit for bit with `canvas.w` and differs at `canvas.w // 2`; grid off, equal only |
| `wash` keywords and `body` | `tests/unit/ink/test_wash.py` (S2): positional `TypeError`; the values by `tests/unit/ink/test_wash_density.py`'s `PINNED`, rewritten to keywords by the codemod |
| `brush_from_id` defaults and keywords | `tests/unit/ink/test_brush.py` (S1, the explicit side by keyword; S2); `test_benchmark_inputs.py`'s new case |
| Exported and rendered | `tests/unit/test_public_api.py` (unchanged lists, still green), `tests/architecture/test_public_signatures.py`, the strict docs build |
| Callers moved | `uv run ty check` (Python), the docs call check over fenced blocks (Markdown), `ruff check` (no F401 left), the whole suite |
| The hash tool's `--stem` narrowing | `tests/golden/test_output_hashes.py` (S0) |
| Quotes and prose signatures | `tests/docs/test_tutorial_quotes.py`, `test_readme.py`, `test_docs_signatures.py` |
| Pixels do not move | `output_hashes.py check` (S4), the golden suite, `git status` on the image trees |
| ADR, glossary, note | `tests/docs/test_glossary.py`, `test_docs_links.py`, the strict docs build, the `git grep ink-blank-paper-by-size` gate; the index row by reading |
| Mutation | S5, `mutation.md` |

No Hypothesis property is added: no algorithm changes. The existing properties under
`tests/property` that build sheets, washes or brushes are rewritten by S2 and stay green,
which is the property-level proof that values are unchanged.

## Delegation

- **Orchestrator (main context):** this plan, the plan-reviewer gate, ADR 0073, the
  integrator's checks after each slice (slice gate; after S2 also the coverage gate and the
  docs call check), commits and the PR.
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
| Start | `docs/decisions/0073-boilerplate-free-calls.md`, `docs/decisions/README.md` | base |
| S0 | `tests/golden/output_hashes.py` (renamed), `tests/golden/test_output_hashes.py`, `output-hashes.json` | Start |
| S1 | `ink/sheet.py` (`pixels`), `ink/paper.py`, `ink/brush.py` (defaults), `tests/unit/ink/{test_sheet,test_paper,test_brush}.py` | S0 |
| S2 | `ink/{sheet,washing,brush}.py`, the caller files of S2's table, the 14 example docstrings and imports of D7's fallout, the Markdown listed in S2, `tests/docs/test_docs_signatures.py`, `tests/architecture/test_benchmark_inputs.py`, `tests/unit/test_public_api.py` (docstring), `tests/unit/ink/{test_sheet,test_wash,test_brush}.py` | S1 |
| S3 | `GLOSSARY.md` and generated glossary files, the two notes, `docs-tutorial-opening-programs.md` (lines 15 and 21), links | S2 |
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
  simplification S2 makes; everything else is spelling. Kept over the review's
  alternative (narrow D7 to `scale`) because the spec requires it and its fallout is
  bounded and prescribed: an unused `BrushStyle` import removed by `ruff --fix --select
  F401` and the name taken out of the same 14 module docstrings (S2).
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
- **D11. The codemod rewrites positional arguments only and runs before the negative
  tests are written** (review finding 1). Ordering, rather than a rule that skips calls
  inside `pytest.raises` blocks, keeps the script simple and leaves no case it must
  recognise. The negative tests are still seen failing, on a worktree of S1.
- **D12. A starred `Sheet` maps `*s` to `w=s[1], h=s[0]`; every other starred or `**`
  form stops the script** (finding 4). The four starred calls all unpack a numpy-style
  `(height, width)`, so the mapping is exact. Refusing unknown forms keeps a transposition
  from being invented in silence.
- **D13. Spelling-only functions are proven spelling-only, not mutated in full**
  (finding 11). This follows 006's rule. `wash` and `brush_from_id` are still mutated,
  because their signatures changed, with the earlier equivalent lists as the check. A
  150-line bound sends any larger survivor work to `docs/issues/`. CLAUDE.md requires
  mutation testing to run, not to grow the PR without bound.
- **D14. `test_benchmark_inputs.py` is extended rather than the gap filed** (finding 14).
  It is one AST case in a file S2 already touches, and it keeps a benchmark from timing
  the default look by accident.
- **D15. ADR 0073 says 010a may amend rules 5 to 11** (finding 13). This is the 0070
  rule 17 precedent, made explicit, so an accepted ADR never states a design that 010a's
  review changes without saying so.

### Review findings, accepted and rejected

Every finding of `review-plan.md` is applied. One is applied differently from its first
suggestion:
- **Finding 1, option 2:** the review offered "skip calls inside `pytest.raises`" or
  "write the negative tests after the codemod". This plan takes the second option (D11).
- **Finding 2:** the review offered narrowing D7 to `scale`. This plan keeps D7 whole and
  prescribes its fallout (D7).
None is rejected.

## Implementation notes from the re-review (binding)

1. The `brush_from_id` negative test carries `# ty: ignore[too-many-positional-arguments]`
   only: every keyword-only parameter there has a default, so ty 0.0.100 reports no
   `missing-argument` (a two-code ignore fails with `unused-ignore-comment`). The `Sheet` and
   `wash` negative tests keep both codes.
2. S5's spelling-only proof covers `wash`, `nib_brushes`, `_sheet` and `_backing_wash`.
   `brush_from_id` gains the `style = BrushStyle() if style is None else style` line, so it is
   mutated and checked against its recorded equivalents instead.
3. `output_hashes.py` imports `from golden.make_docs_images import fixture_options`, as
   `repaint.py:28` does.
