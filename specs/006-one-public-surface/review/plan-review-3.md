# 006 plan review 3

**Verdict: BLOCK**

One blocker remains. The fix is three lines.

S7's Lynmouth "too short" test uses `B3223`, and the plan's own `numbered` key makes
B3223 long enough to letter. As written, the test fails. The spec's acceptance criterion
states the same false fact. Change the road to `Lee Road` (details below). Every
round-2 blocker is fixed, and I checked each one against the code.

Reviewed at `a7d664d`. I ran the probes from the repo venv, with griffe 2.4.1 and the
Lynmouth fixture. Scratch scripts only; nothing in the tree was changed.

## Round-2 blockers: verified

| # | Fixed? | Evidence |
| --- | --- | --- |
| B1 S9 self-contained | yes | Appendix A.2's body is byte-for-byte 007's lines 216 to 380 at `529753f`: `diff` of `git show 529753f:specs/007-docs-truth-and-glossary/spec.md` against plan.md lines 1256 to 1420 is empty. `529753f` is the tip of `origin/docs/007-docs-truth-and-glossary`. N24 is carved out by name. Done criterion 1, run on today's tree, finds 31 `src` lines (every one an appendix row) and the 20 `tests` lines S9 lists, no more and no fewer. Criterion 2's `rg -U` finds exactly `lettering/pipeline.py:88-89` and `lettering/__init__.py:7-8`, as stated. |
| B2 S3 pinned | yes | The 38 names (6/1/31/0) and the 30 externals are typed in, with stop-and-report and no edit-to-match. The defining module of every one of the 38 checks out against `src` (`grep` per name; Flow in `wash.py` and Blooms in `bloom.py`, renamed by S1). The `Raises:` types in `src` (`KeyError`, `ValueError`, `json.JSONDecodeError`, `pydantic.ValidationError`, `tomllib.TOMLDecodeError`, plus the package's own errors) agree with the external list. My griffe count of missing field entries, over the public classes and the reached ones, is **ink 186, letters 38, maps 115**: exactly the pinned figures. |
| B3 S10 mutable and tested | yes | `PaintJob.bloom` is a plain method (`job.py:159`), so `xǁPaintJobǁbloom*` has mutants. `_ground`, `track_projection`, `named_lines` and `pick_roads` carry no decorator. `PaintJob.flow` is dropped, and S4's non-golden `test_job.py` test covers it. `test_ground.py` is non-golden and sits in the throwaway selection. The five files are listed by name, and the loop recreates the worktree from the new `HEAD`. None of the selected maps tests reads `REPO_ROOT`, `examples/` or a fixture directory, so they run inside `mutants/`. |

Also re-checked, all exact: S1's collision scan (AST over every `__init__.py`) finds only
`ink: stamp, wash` and `maps: compose, vector_layers`. The old-module search's hits are all
assigned. The S2 `Pt`/`Anchor`/`Box` claims hold. The four `Projection` field assignments
and the `track_projection` rewrite are correct. The S6 and S8 allowed hits for
`LetteringPolicy`/`RouteInk` match `git grep`. Every maps class the field gate will check
is defined in a file S6 owns (or `Lettering` in S7's `pipeline.py`).

## Blocking

### B1. `roads=("B3223",)` is not too short under the plan's own algorithm

- **The claim.** plan.md:790 says "`B3223` 83 px against a 89.6 px minimum", and S7's
  `test_a_named_road_too_short_on_the_card_falls_back_to_the_picked_roads` (plan.md:847)
  expects B3223 to be logged and the picked `["A39", "B3234"]` to come back. spec.md:102
  says the same.
- **Why it is wrong.** The 83 px figure counts only `lines["roads"]` (the named pieces).
  `named_roads` also reads the new `lines["numbered"]`, and B3223 has an unnamed numbered
  piece on the fixture: the basemap's roads with a `ref` and no name are `A39`, `B3223`
  and `B3234`. The joined run then grows:

  | Road | Named pieces only | Plus `numbered` (what S7 builds) |
  | --- | --- | --- |
  | `B3223` | 83.3 px | **274.2 px** |
  | `B3234` | 173.4 px | 358.9 px |
  | `A39` | 791.6 px | 1951.1 px |

- **End to end.** I painted the fixture, replaced `_ground` in-process with the plan's
  `_ground` and `named_roads` (logic copied from S7), and called `letter`:
  - `("B3223",)` places road labels `['B3223']`. That is a lettered road, not a
    fallback, so the test fails.
  - `()`, `("B3234",)`, `("Lynbridge Road",)` and `("Lydiate Lane",)` give
    `PINNED_LABELS`, `['B3234']`, `['B3234']` and `['Lydiate Lane']`, as the plan
    expects.
- **Why it blocks.** An implementer whose test goes red has to guess. The plausible
  wrong guesses are worse than the bug: dropping `numbered` from the length, filtering
  numbered pieces, or re-pinning the test to whatever comes out.
- **Fix.**
  - Use `roads=("Lee Road",)`. It is drawn, a real Lynton street in the fixture, and its
    longest run is 70.0 px against the 89.6 px minimum. My simulation logs it as too
    short and places `['A39', 'B3234']`. `Tors Park` (58.5 px) also works.
  - Update plan.md:790 and plan.md:847-849 and spec.md:102 to match.
  - Optionally keep B3223 as a positive test: `roads=("B3223",)` letters `B3223`. This is
    the only real-data proof that the `numbered` key matters, because the picker never
    letters B3223.

## Should fix

1. **The Approach's retired-word self-check always fires.**
   - `git diff origin/main -U0 -- '*.py' '*.md'` includes this branch's `specs/006-*`
     and ADR 0068.
   - plan.md's Appendix A and spec.md:116 contain every retired word. So every slice gets
     dozens of hits it did not write, against "It finds nothing a slice wrote itself".
   - A literal agent will stop or burn time on it.
   - Add `':!specs' ':!docs/decisions'`, and diff against the slice's base commit, not
     `origin/main`.
2. **`test_ground.py` on `tiny_basemap` is a trap.**
   - Its card is **80×50 display px**, and `road_min_px` is **89.6 px**. So no road that
     stays on the card can be lettered: the "picked `A591` beside the route" and the
     named `A66` must both run past the card's edges. That works only because
     `pick_roads` does not clip to the card.
   - "A66 far from the route" (more than 40 px, `ROAD_ON_ROUTE_PX`) also means off the
     card. The route runs at y ≈ 24-25 on a 50 px card.
   - `tiny_style(display_px=...)` raises a duplicate-keyword `TypeError`, so the card
     cannot be widened through it.
   - Say this in the plan: lines span roughly −40 to 120 px in x, or use
     `tiny_basemap(class_style(display_px=320, supersample=1))`.
3. **`pyntpot.ink.bloom.x_bloom*` also matches `bloom_radius`.**
   - Its survivors, in an unchanged function, then hit the done criterion ("no survivor
     not named equivalent"). That contradicts "survivors … in a function whose behaviour
     did not change are out of scope".
   - Use `pyntpot.ink.bloom.x_bloom__mutmut_*`, or say that results are filtered to that
     prefix. No other row over-matches; I checked each module's function names.
4. **S9 done criterion 3 for rows a lane moved.**
   - N19, C3, C8 and R6 are `#:` field comments that S4, S5 and S6 move into
     `Attributes:` entries and will likely rewrap. Their appendix "new" strings, `#:`
     included, will not `git grep -F`.
   - Extend "read in place and listed in the report" to every row a lane moved or
     rewrapped, not only those S9 rewrapped.
5. **`test_a_named_minor_road_is_lettered` does not pin the class filter as described.**
   - "`pick_roads` on the same lines letters nothing" proves the minor-class skip only if
     the road also passes `pick_roads`' other two tests: within 40 px of the route and at
     least 89.6 px long.
   - Prescribe that Old Lake Road lies beside the route and runs past the minimum length,
     with route pixels passed to `pick_roads`.

## Consider

- **Naming a road moves its label.** B3234's named-path baseline is the 358.9 px run, not
  the picked 173.4 px run, because the numbered pieces join it. Naming a road the card
  would pick anyway can therefore move where its number sits. That is fine, and it is
  arguably better tarmac to set on. One sentence in `named_roads`' docstring avoids a
  future "why did my label move" note.
- **Merge order.** `tests/unit/test_public_api.py`: S4's last insertion (`separated`,
  near `stamp`/`wash`) and S5's `"Align"` (first in `LETTERS_PUBLIC`) are a few lines
  apart. If the rebase conflicts, it is trivial. Tell the orchestrator that it is
  expected.
