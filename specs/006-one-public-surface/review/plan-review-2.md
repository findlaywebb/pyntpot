# 006 plan review 2

**Verdict: BLOCK**

All eight round-1 blockers are fixed, and I checked each fix against the code, not just
the plan's text. The #161 design now holds up: `named_lines` files a numbered piece with
no name under `numbered`, `named_roads` has no class filter, the `ValueError` is raised in
`_ground` before `place` and `draw_plate`, and the `Lettering` tests copy the plates
directory. The record list and the positional-construction sites are exact. I re-ran the
AST scan and it finds the same 17 sites and nothing else.

Three defects remain, and each will make an agent either fail its done criterion or
guess:

- S9 does not point precisely at 007's list, and it contradicts the log-message change
  the orchestrator approved.
- S3's done criterion can only be true, because it compares the gate's output with
  itself.
- S10's maps rows cannot finish with the files S10 owns.

Reviewed at `5eff1dd`. For the S3 checks I ran griffe 2.4.1 from the repo venv on a copy
of `src` with the four S1 renames applied.

## Round-1 blockers: verified

| # | Fixed? | Evidence |
| --- | --- | --- |
| 1 minor roads | yes | `named_roads` passes `classes=None`. `picks_lines.py:90-94` files a road with no name under `crossings`, so the `numbered` key is needed, and the plan adds it. `pick_roads` keeps `("major", "medium")`. Its `not key` test equals today's `not name` because `named_lines` puts only named entries in `roads` (`picks_lines.py:74`). |
| 2 plate overwrite | yes | Every new `letter` call copies the plates directory, as `test_pipeline_letter_compose.py:113-117` does. |
| 3 S4/S6 overlap | yes | S4 owns `test_job.py`, and S6's glob excludes it. `git grep` finds no other Flow or Blooms tuple use under `tests/unit/maps`. |
| 4 allowlist | yes, see B2 | The walk is transitive. Post-S1, `separated` and `fluid_modulate` reach no new external name, so the claim "no lane changes `ALLOWED`" holds. |
| 5 alias and self-tests | yes | The alias definition and the seven self-tests are added. |
| 6 binary grep | yes | `git grep` runs over `*.py`/`*.md`/`*.toml`/`*.yml` only. |
| 7 S10 unbounded | yes for ink, see B3 for maps | |
| 8 S8 grep | yes | `bloom.py:8`, the `route-*` lines 16/19/20 and the #163 allowed hit all match `git grep`. |

## Blocking

### B1. S9 points at the wrong section, in a file outside this tree, and its done criterion forbids the approved log change

- **Evidence: the file is not in this tree.** plan.md:775 says "per
  `specs/007-docs-truth-and-glossary/spec.md`, Canonical terms section". That file is
  not in this worktree (`ls specs/` has no 007). It exists only on
  `origin/docs/007-docs-truth-and-glossary` (at `7b61165`, and in
  `/home/user/pyntpot-docs`).
- **Evidence: the wrong section.** "Canonical terms" is the glossary table. The section
  an agent can execute is **"Docstring changes for 006's S9"** (007 spec.md:205-330): 58
  lines in 21 files, N1-N24, T1-T3, M1-M4, C1-C8, R1-R12, L1 and S1-S5, each with its
  exact old and new string.
- **Evidence: the plan's own sample does not match.** plan.md:776's "known candidates"
  say 22 uses of "label plate". 007 counts 25, and the four candidates leave out the C
  and R rows (`ink` saying "card", `letters` saying "route").
- **The log-message contradiction.** N24 rewords the log message at
  `maps/pipeline.py:167`, which the orchestrator approved. But plan.md:778-783 says
  "Docstrings and comments ... only. No code" and "Done: `git diff` touches no line
  outside a docstring or comment". If the agent does N24, it fails S9's done criterion.
  If it skips N24, 007 fails.
- **Retired words from earlier slices.** 007's plan step S8.9
  (`/home/user/pyntpot-docs/specs/007-docs-truth-and-glossary/plan.md:878-886`) extends
  `test_no_page_or_example_uses_a_retired_word` to `src/**/*.py` **and** `tests/**/*.py`
  once 006 has landed. A retired word in `src/` is a 006 defect that 007 will not fix.
  S4, S5 and S6 write about 340 new field entries, and S7 and S10 write new test
  docstrings. None of them is told the retired words, so "label plate", "callout" or
  "raster card" in new text will turn 007 red. One plausible path: S7 copies the plan's
  own phrase "leaves no label plate written" into a test docstring.
- **Fix:**
  - S9: "Execute every row of 'Docstring changes for 006's S9' in
    `git show 7b61165:specs/007-docs-truth-and-glossary/spec.md` (branch
    `origin/docs/007-docs-truth-and-glossary`). Find each row by its old string. Owned:
    those lines. The one string literal it changes is N24, the log message at
    `maps/pipeline.py:167`."
  - Done: the diff touches only docstrings, comments and that one literal, and 007's
    grep
    `grep -rniE 'label plate|label$|raster card|recorded route|centreline route|outline route|callout' src/pyntpot`
    finds only the three lines 007 names. Also run the same grep, without `label$`,
    over the lines this branch added under `tests/`
    (`git diff origin/main -- tests | grep '^+'`).
  - Put the retired-word table (007 plan.md:203-207) in the plan's Approach, as a rule
    for every slice that writes prose: S4, S5, S6, S7, S8 and S10.
  - Delete the "known candidates" sentence.

### B2. S3's done criterion compares the walker with itself

- **What the plan says.** plan.md:279-288 and 364-366 fill `ALLOWED` and the four pending
  sets "from the first run", then define done as "`ALLOWED` equals the external set
  reached, and the pending sets name nothing that does not violate".
- **Why that proves nothing.** Both halves are true by construction. The self-tests are
  synthetic, so nothing checks what the walker does on the real tree. A walker that
  over-reaches gets its noise blessed into a committed allowlist. Examples: walking a
  constant's value (my naive probe reached `importlib.metadata.version` that way), or
  walking a default. A walker that under-reaches silently shrinks every pending set.
  Once committed, the two-way tests (`..._unknown_external_name`,
  `test_every_allowed_name_is_reached`) do stop later loosening, so the problem is the
  first fill, not a ratchet that loosens itself. It is still a golden recomputed by the
  code under test, which CLAUDE.md's testing rules forbid.
- **Evidence for the expected sets.** An independent probe of the post-S1 tree, with S2's
  renames applied by hand, gives:
  - **Signature violations: 38**, which is ADR 0068's 40 minus `separated` and
    `fluid_modulate`, which nothing reaches.
    - `_pending_ink`, 6: `pyntpot.ink.polyline.{Point,Box}`,
      `pyntpot.ink.style.WashStyle`, `pyntpot.ink.washing.{WashOptions,Flow}` and
      `pyntpot.ink.bloom.Blooms`.
    - `_pending_letters`, 1: `pyntpot.letters.setting.Align`.
    - `_pending_maps`, 31: the ADR table.
    - `_pending_roads`: 0 entries.
  - **External names: 30.** `KeyError`, `RuntimeError`, `ValueError`, `bool`, `dict`,
    `float`, `int`, `list`, `str`, `tuple`;
    `collections.abc.{Callable,Mapping,Sequence}`; `httpx.Client`;
    `json.JSONDecodeError`; `numpy.ndarray`, `numpy.random.Generator`,
    `numpy.typing.ArrayLike`; `pathlib.Path`; `PIL.Image.Image`;
    `pydantic.{BaseModel,Field,ValidationError}`; `tomllib.TOMLDecodeError`;
    `typing.{Annotated,Any,Literal,NamedTuple,Protocol,Self}`.
  - Note that `PIL.Image.Image` (the return of `compose`, reached once S1 un-shadows
    it) and `typing.Self` are not in the plan's list of source groups. An agent may read
    them as a walker error.
- **Fix:**
  - Pin both lists in the plan as the expected values.
  - S3's done criterion becomes: the first run's `ALLOWED` equals the 30, and the union
    of `SIGNATURES` equals the 38, partitioned as above.
  - Any difference means stop and report to the orchestrator, never edit to match.
  - Pin the expected `FIELD_DOCS` counts per lane the same way (ink 186, letters 38,
    maps 115 is close enough to check against).

### B3. S10's maps rows cannot be finished as written

- **`PaintJob.flow` has no mutants.** It is a `@property` (`job.py:136-142`), and mutmut
  3.8 makes no mutants under any decorator except a lone `staticmethod` or `classmethod`
  (`tests/mutation/scope.py:95-104`). The table row (plan.md:808) cannot be run.
- **`_ground` has no test in the selection, and nowhere to put one.** No non-golden test
  calls it. Today only `letter` does, and every `letter` test is in
  `test_pipeline_letter_compose.py` under `@pytest.mark.golden`, which `-m "not golden"`
  drops. So every `_ground` mutant reports `no tests`, and plan.md:847 then requires a
  focused test. S10 owns no file where that test can go and also be in the selection: a
  test added to the golden file stays excluded, which is a loop.
- **Smaller gaps:**
  - "`only_mutate` set to the four files" lists five (plan.md:836-838).
  - The maps patterns are left as "(maps)". They should be written out, as the ink rows
    are.
  - Nothing says how a kill is re-verified. Tests written in the throwaway worktree are
    lost when it is removed, and tests written in the main tree are absent from a
    worktree made before them.
- **Fix:**
  - Drop the `PaintJob.flow` row, noting "property; no mutants (scope.py)".
  - Write the seven patterns out:
    - `pyntpot.maps.lettering.picks_roads.x_named_roads*`
    - `pyntpot.maps.lettering.picks_roads.x__road_pieces*`
    - `pyntpot.maps.lettering.picks_roads.x_pick_roads*`
    - `pyntpot.maps.lettering.picks_lines.x_named_lines*`
    - `pyntpot.maps.lettering.pipeline.x__ground*`
    - `pyntpot.maps.projection.x_track_projection*`
    - `pyntpot.maps.painter.job.xǁPaintJobǁbloom*`
  - S7 owns a new non-golden `tests/unit/maps/lettering/test_ground.py`. It calls
    `_ground` on `tiny_basemap` and `tiny_style` and covers the empty, named,
    `label_ground` false and too-short fallback cases. Add it to the throwaway selection
    and to S10's owned files.
  - Say "five files".
  - Loop: write the tests in the main worktree and commit, then recreate the throwaway
    worktree from the new `HEAD` (`git worktree add --detach`) and run again.

## Should fix

1. **S6 `track_projection` cannot build `Projection` "once".**
   - `raw = [proj(a, b) ...]` (`projection.py:83`) needs a projection before `x0` and `y0`
     exist, so "compute x0 and y0 first, then build once" (plan.md:488-490, ADR:198) is
     impossible as written.
   - Prescribe: `base = Projection(lat0=..., lat_ref=..., lng_ref=...)`, then
     `raw = [base(a, b) ...]`, then the two unchanged branches, then
     `proj = dataclasses.replace(base, x0=x0, y0=y0)`.
   - This is bit-identical: `- 0.0` changes nothing.
   - Fix the ADR's wording to match: "never assigned after it is built".
2. **S7's "writes no plate" test cannot catch a write.**
   - The copied directory already holds `labels-<route>.webp` whenever the module's
     `lettered` fixture ran first, which depends on test order.
   - So "holds no `labels-*.webp` it did not hold before" still passes for an
     implementation that writes the plate and then raises.
   - Snapshot `{p.name: p.stat().st_mtime_ns}` of the copy before the call and assert it
     is unchanged after.
3. **S7 must not name `LetteringPolicy` or `RouteInk`.**
   - `test_named_roads_are_lettered_when_the_style_letters_no_ground` needs a style with
     `label_ground=False`. S6 renames the class in parallel and merges last.
   - If S7 writes `LetteringPolicy(...)`, S6 has to edit a file S7 owns.
   - Prescribe `style.model_copy(update={"lettering": dataclasses.replace(style.lettering, label_ground=False)})`.
4. **The "defining layer" check is ambiguous because of the façade.**
   - Every canonical path lives "under" `pyntpot`, and `pyntpot.__all__` re-exports 17
     layer names (`Hand`, `Style`, `wash`, ...). `public_objects` returns a
     `dict[canonical → layer]`, so a name exported twice keeps whichever layer was
     written last.
   - Define `layer_of(path)` as the longest prefix among `pyntpot.ink`,
     `pyntpot.letters` and `pyntpot.maps`, else `pyntpot`. A name is public iff
     `layer_of(path)`'s `__all__` exports it. Façade exports are ignored by the check.
   - Also limit "an alias griffe cannot resolve is a violation" to targets under
     `pyntpot.`. External aliases (numpy, httpx) are never resolved, because only
     `pyntpot` is loaded.
5. **Label and Span: the ADR contradicts itself, and this is the decision that will age
   worst.**
   - ADR:194 says "**Every** dataclass record this ADR makes public is
     `frozen=True, kw_only=True`". `Label` and `Span` are made public by the same ADR
     and are not frozen. Say "every one except `Label` and `Span`".
   - The bigger cost: ADR:204 ("removing or renaming a field needs an ADR") now covers
     the placer's working state: `window`, `flat`, `anchors`, `mark`, `span_range`,
     `in_water`, `tx`, `ty`, `lift`, and `Span.rank`, `offset_px`, `side`.
   - Freezing them later does not break callers, but slimming them later does. Either
     have the ADR name those fields as placement state that may change without an ADR
     until `maps-lettering-frozen-records` lands, or scope that follow-up note to
     include separating the returned record from the placer's working state.
   - The gate and tests treat Label and Span correctly as planned: field docs are
     required, the keyword-only test includes them, and the frozen test excludes them.
6. **Approach, "bodies change in exactly these places" (plan.md:8-17) is not true.**
   S6's `Credit(...)` rewrites in `opentopodata.py:59` and `overpass.py:193`, and S2's
   `Point` renames, also edit function bodies. List them, or S11's diff-vs-plan check
   flags them.
7. **Fail closed for strings.** `names_in` skips strings that are not forward references,
   but it never says how it tells the two apart. Prescribe: string constants are skipped
   only inside `Literal[...]`. Any other string left in an annotation, or a `Raises:`
   entry griffe could not parse into an expression, is a violation. Today every
   `Raises:` entry parses to an `ExprName`/`ExprAttribute`; I checked all 27.

## Consider

- **Check one test name.** The synthetic minor-road test calls Lake Road "Ambleside's
  unnumbered minor road" (plan.md:662). I believe the A591 follows Lake Road from
  Waterhead into Ambleside. Check that before it is pinned, since CONTRIBUTING requires
  real facts. Wansfell Road or another plainly unnumbered street avoids the question.
- **A drawn road that `named_lines` drops.** A named road can be drawn but simplified
  below two points by `named_lines`. Today that raises "no road the card draws ...",
  although it is drawn. If that is acceptable, say so in `named_roads`' docstring.
  Otherwise treat it as too short.
- **Iterate one dict.** `_road_pieces` should fill `osm_names` only when it appends to
  `pieces`, and `named_roads` should iterate `pieces` keys. That way a matched key always
  has pieces and widths.
