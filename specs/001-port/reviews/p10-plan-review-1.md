# P10 plan review 1

Reviewed: `specs/001-port/plan.md`, section `### P10. Triage and address the
port's issues` (lines 5998 to 7138), and the P10 list in `specs/001-port/tasks.md`
(lines 163 to 187), branch `p10-triage` at `177a9f5`. I read them against
`CLAUDE.md`, "P3 and P4: how to run a slice" (line 350), `spec.md`, the issue files,
`p10-run-log.md`, the five dossiers, and the code at `177a9f5`. The P6 reviews set
the register.

Probes were run on 2026-10-07, read-only, with scratch scripts in the session
scratchpad. No golden test was run.

- **The attribution gate.** `attribution.py:64` and `lettering/pipeline.py:98` both
  gate on `style.lettering.labels`. No test passes `labels=False`.
- **prek.** `uv run prek --version` fails to spawn. `uvx prek` is 0.5.5. `ci.yml`
  has no prek step. `.pre-commit-config.yaml` is local hooks plus
  `pre-commit-hooks` v6.0.0.
- **The reference gate.** I read `test_reference_keys.py`. With the new entries in
  and no citation lines yet, `test_every_site_cites_its_key` fails with the stated
  message. `spend` is at `deposit.py:57` and `separated` at `wash.py:247`.
- **`edt`.** `grep -rlnw edt --include=*.py src tests` lists 8 `src` files and 6 test
  modules. `references.md:78-79` names `edt`. `performance.md` names `test_edt`,
  which `-w` does not match.
- **The deposit.** The off-grid branch matches the issue. I worked the plan's two
  test cases by hand: today they give 1.0 and 1.0, and after the masked form 0.0
  and 0.5. A float32 multiplied by a bool is exact, so the multiply-last form is
  byte-neutral on the grid.
- **The outline route.** `draw_plate` (`pipeline.py:175`) builds
  `NibGroups(style.nib, style.face, ...)`. `letter` calls it without `route`
  (`pipeline.py:118`). `nib.py:119` reads `face.label_route`.
- **The face's space.** Its advance is 0.23 and a missing glyph's is 0.28. The face
  covers every character of the attribution text.
- **The freer side.** I ran the plan's `_freer_side` set-up. It returns side 1 with
  margin 1.0, and `span_line` puts the middle of the line at (500.0, 283.2). That
  confirms the red value.
- **The landmark cap.** `journal_picks` skips the cap check on the string branch
  (`picks.py:45-58`).
- **`tunnel`.** It is read only at `osm_elements.py:228`, `bool(tags.get("tunnel"))`.
- **Private names.** The dossier's scan prints 58 cross-module underscore names,
  and the clash probe prints the 8 clashes as stated. All 56 functions among the 58
  already have docstrings, so ruff `D1xx` does not fire on a rename.
- **Non-canonical terms.** The 11 sites match: 10 grep lines plus the multiline hit
  at `placement.py:100-101`.
- **The other counts.** "card pixel" is on 60 `src` lines in 22 files and 7 test
  lines. "sheet" is on 50 lines in 13 files under `maps/lettering`, and on 117 lines
  in 45 files across `maps` once `Sheet` and `ink.sheet` lines are excluded. "page"
  is on 22 lines across `maps`.
- **vulture.** `uv run vulture --min-confidence 60 src` prints about 45 lines. That
  includes every target the plan names.
- **Trailers.** 32 of 80 commits at `91ff457` carry `Co-Authored-By:`.

## Verdict: BLOCK

The single most important change is to **make the phase's ordering true.** As
written:

- The `;` marks put slices that share files in parallel.
- The shared-file table gives a landing order that is wrong under the recommended
  Q13 answer.
- Nothing orders the after-P8 slices against P9. So a conditional slice is told to
  take P9's reserved ADR number.

A second blocker is that two conditional members depend on "P8's list", which no
phase is told to write anywhere a sub-agent can read it.

### What holds (verified, no action)

- **Golden-path facts.** The golden path letters with `None` annotations and
  composes with `attribution=False`. The default theme letters with
  `label_route = "centreline"`, and every route-ink colour equals `label_route_ink`
  (`default.toml:262-307`).
- **G-self claims.** P10.3a, P10.4b, P10.5a, P10.6 and P10.7 are byte-identical by
  the stated reasoning. P10.4c's multiply-last argument is sound.
- **Red-first tests.** P10.3a, P10.4c, P10.5a, P10.6 (cap and side) and P10.7 are
  concrete, red today for the stated reason, and use helpers that exist:
  `tiny_basemap`, `tiny_style`, `label_basemap`, `SpanSurroundings`, `flat_measure`,
  `Card.w`/`Card.h`, `_river_names`, `BESIDE` and `Landmark`.
- **P10.5b's member under Q5 (2).** It keeps the frozen `lettering_digest`
  (`d15ae2f30e9ca5ce`, `test_style.py:75`) unchanged for the default style. Its
  rejection of `route_inks` in `LETTERING_GROUPS` is correct against "What the
  window freezes".
- **P10.3b.** It loosens nothing: it adds a gate, and the named steps stay. P10.8
  keeps the coverage gates and says to stop rather than lower them.
- **P10.8.** `golden.yml` runs `-m golden` and the mutmut selection excludes
  `golden`, so marking the CLI test golden keeps it in CI and out of mutation runs.
- **P10.9's budget row.** ADR 0004 lines 33-34 say "Per instance, not per process",
  so the spec's open question is already settled.
- **Rule application.** I spot-checked every `fix` and `defer` row except the one
  under S8. The rule applies as claimed:
  - `ink-deposit-edge-clamp`: `pool` crops, and P6's line is a record, not intent.
  - `maps-lettering-picks-journal-picks-cap`: `label_max` is "The landmark cap",
    with no exception.
  - `shared-generators`: a redesign of the seeding contract that `job` states.
- **The P10.2 list.** It covers every `decide` row in the seed, and all but Q8 and
  Q12 carry readings, evidence, a recommendation and the outcome under each answer.

## Blocking

**B1. The parallel marks and the shared-file table contradict the phase's own
"never edited in parallel" rule.**
Plan lines 6216-6248 and 7001-7003.

- **What the plan says.** "`;` marks slices with disjoint owner files", and the
  middle line is `P10.4a ─ P10.4b ; P10.5a ; P10.8 ; P10.9`.
- **Pairs the line marks parallel that share an owner file.**
  - P10.4b and P10.5a share `src/pyntpot/letters/trace.py`: P10.4b repoints `edt`
    there, and P10.5a deletes `_radii` there.
  - P10.4b and P10.9 share `src/pyntpot/letters/nib.py`: P10.4b repoints `edt`,
    and P10.9 rewords the "dark field" line of the module docstring.
  - P10.5a and P10.9 are marked parallel, but P10.9's own body says "never in
    parallel with P10.5a". Under Q2 they share `maps/lettering/pipeline.py`.
- **Rows of the table that assume Q13 "no".** Under the recommended Q13 "yes",
  P10.9 runs before P8 and lands before P10.6 and P10.7. The table orders these
  rows the other way:
  - `osm_elements.py`: P10.7, then P10.9, then P10.10c.
  - `test_spans.py` line 64: P10.6, then P10.9.
  - `{label,spans,span_sides,placement*}.py`: P10.6, then P10.9, then P10.10d.
- **Why it blocks.** An orchestrator following the diagram dispatches colliding
  worktrees. A P10.6 implementer told "line 64 keeps 'the sheet' for P10.9" finds
  P10.9 already landed.
- **Fix.**
  - Make the middle line `P10.4a ─ P10.4b ─ P10.5a ─ P10.9`, with
    `P10.8 ; (that sequence)`.
  - Give each table row both orders, or one row per Q13 answer.
  - In P10.6, say "line 64: change only 'Rule seven'; leave the rest of the line as
    you find it".

**B2. The ordering of the after-P8 slices against P9 is unspecified, and the ADR
number rules collide with P9's fixed numbers.**
Plan lines 6822-6823 (P10.5b) and 7132-7134 (P10.11). Also P9 lines 5843-5846 and
the ADR table at line 513.

- **The collision.** P9 runs after P8, and so do P10.4c to P10.7, P10.10 and
  P10.11. Nothing orders them, and the plan's ADR table gives P9.1 0022 and P9.2
  0023 as fixed numbers.
  - P10.5b (Q5 (2)) says "the next free in `ls docs/decisions`". Before P9.1 that
    is 0022, P9.1's number, and P9.1 then stops ("if it is taken, stop and report").
  - P10.11 says "0024 if P9.2 has written 0023; if the number is taken, the next
    free one". That says nothing for the case where P9.2 has not run.
- **Shared files with P9.** P9.1 and P9.2 also edit `spec.md` and `GLOSSARY.md`,
  which P10.9 owns under Q13 "no". Of the P9 overlaps, only P9.4 is sequenced.
- **Fix.** Add a row "P9 vs P10" to the order section: either all after-P8 P10
  slices land before P9.1, or after P9.4. Give fixed numbers in the ADR table:
  0024 for P10.5b's route-ink ADR and 0025 for P10.11's regeneration ADR, both
  checked free before writing, stop otherwise.

**B3. "P8's list of what upstream reads" has no location, author or format, yet
two members depend on it.**

- **Where the plan relies on it.**
  - The seed (6310).
  - Q8 (6458-6464, 6527).
  - P10.6 (6860-6862): `as_dict` is deleted, or the row is closed with the
    consumer named.
  - P10.7 (6939, 6965-6967): which constants are deleted, and which are kept with
    comments.
- **Why it blocks.** P8 "touches only the upstream repo" (5822-5823), and D21's
  enumeration is not required to be committed here. A P10.6 or P10.7 implementer
  cannot evaluate its own precondition. Nothing says who flips Q8's row from
  `defer ("awaiting P8's list")` to `fix`.
- **Fix.** Name the artefact and its writer. For example: at P8's hand-off the
  orchestrating session appends to `p10-triage.md` a list, "upstream reads:", of
  every `pyntpot` attribute and method the upstream calls, from the call sites.
  Then it re-triages the `as_dict` and Q8 rows and states the outcome in each
  brief.
  - The brief carries a yes/no per name. The implementer never decides it.
  - Say what happens if P8 records no list: the `as_dict` row becomes `defer`, and
    the Q8 row applies S4's D21 reading.

## Should-fix

**S1. Q12 is "asked only if" a `fix-golden` reading is chosen, but Q4 and Q6 are
answered in the same round** (6495-6499, and 6196-6198).

- **The gap.** No row is `fix-golden` at P10.1. So either Q12 needs a second round,
  which breaks "P10's one sanctioned stop point", or it is never asked.
- **The knock-on.** A slice whose G-self later differs moves to `fix-golden` with no
  Q12 answer to apply.
- **Fix.** Always ask Q12 in the one list, as a conditional: "if any answer above,
  or a later G-self difference, makes a row `fix-golden`, may P10.11 open a second
  window?"

**S2. Q1's framing is not fair, and reading 1 leaves P10.3d waiting on an
unlisted action** (6389-6399, 6662-6664).

- **The framing.** The plan says "Reading 1 holds only if the maintainer adds an
  override line to `CLAUDE.md` themselves". But the maintainer's own answer in
  P10.2 is a user instruction, and it takes precedence over the session reminder.
  A `CLAUDE.md` line matters for durability across sessions, not for validity.
- **The wait.** Under (1), P10.3d "waits for" the line. But the line is not in
  P10.2's "Maintainer actions" list, so nobody is asked to add it.
- **Fix.** Restate the point as: "under (1), a line in `CLAUDE.md` carries the rule
  into later sessions. The maintainer adds it, or tells the session to." Add that
  to the Maintainer actions list under Q1 (1).

**S3. Q7 omits the most natural reading** (6444-6453; P10.3c leave-alone at 6617).

- **The case for it.** The P6 inclusion rule (b) (line 4813-4815) lists "edge
  darkening" as a `design-sources.md` technique. The Stamen post is already a design
  input of `edge-darkening`. The no-flow branch at `wash.py:218-219` is the other
  half of the same choice as `flow_edge`.
- **Reading (C).** Add `pyntpot.ink.wash.wash` to `edge-darkening`'s
  `Implemented in:` line, plus a `Source: edge-darkening` line in `wash`'s
  docstring. It needs no new key, and no blog post as a canonical source, which no
  other entry has.
- **Fix.** Add (C) with its consequence: `fix` in P10.3c and a release blocker.
  P10.3c's leave-alone then excepts `edge-darkening`'s `Implemented in:` line under
  (C).

**S4. Q8's evidence leaves out D6/D21, and P10.7's "consumer list" is ambiguous
against a pinned tuple** (6454-6464, 6965-6967).

- **The missing evidence.** `maps.style_groups` is private (D6: "Everything else is
  private"), and D21 says the upstream "never imports a private name". So
  `ROUTE_INK`, `ROUTE_EFFECT_OFF`, `ROUTE_SHADOW` and `CASING_COLOURS` cannot be read
  by a D21-compliant consumer. Only `RouteInk.casing`, reached through the public
  `Style`, could be. The question should say so. A defensible recommendation is to
  delete the four constants on the evidence now, and let only `casing` wait for P8.
- **The ambiguity.** "add them to the module docstring's consumer list" reads
  naturally as `CONSUMER_ONLY`. That is a tuple of field names, pinned by
  `test_style_groups.py:330`, and part of the frozen field-to-group table.
- **Fix.** Add `CONSUMER_ONLY` and its pin to P10.7's leave-alone. Say "one sentence
  in the module docstring" instead.

**S5. P10.9 under Q10 is under-sized and over-scoped, and its check cannot pass as
written** (6476-6483, 7043-7050).

- **The size.** Q10 says "50 lines in 14 lettering files, more in other `maps`
  modules". Across `src/pyntpot/maps` the body's scope is 117 non-`Sheet` lines in
  45 files.
- **"or page".** The slice adds "or page", but outside `maps/lettering`, "page"
  means the upstream SVG page. See `compose.py:3,63,95`, `painter/*` and
  `lettering_marks.py:72`, and `pipeline.py:187` ("the page and the card both draw
  the same pixels"). Renaming those to "map" would be wrong.
- **The check.** `placement_names.py:172` holds "sheet" in a `log.info` string. The
  AST-neutral check forbids changing it, but the check grep then prints it.
  Lowercase `sheet` arguments in `painter/*` (`sheet.coarse`) print too, and they
  name no `Sheet`.
- **Fix.**
  - Scope Q10 (1) to the issue's scope: `maps/lettering/**`, the
    `maps/lettering_*.py` modules, the three glossary rows and the one test line.
  - Allow "page" only inside that scope.
  - Give Q10 the real counts.
  - Make the check `grep -rnIiw sheet src/pyntpot/maps/lettering src/pyntpot/maps/lettering_*.py`,
    with an explicit allowed list (the log line, `ink.sheet` and `Sheet` lines)
    written into the brief.

**S6. P10.3d's check is not mechanical** (6665-6666).

- **The problem.** `grep -n -i "trailer" CONTRIBUTING.md specs/001-port/plan.md`
  will print many lines after the change: P0's line 139, line 6034, the seed row,
  Q1's own readings, and this section's rule. "Lists one after" cannot be judged.
- **Fix.** Pin a pattern and its expected output. For example,
  `grep -nE "no trailers|No co-authorship trailers|with no trailers" CONTRIBUTING.md specs/001-port/plan.md`
  prints exactly lines X, Y and Z before. After, it prints only P0's line 139 (a
  record) and Q1's reading text.

**S7. P10.3a and P10.3b wait on P10.2 although they depend on no question**
(6219-6220, 6544, 6582).

- **The contradiction.** The phase rule says "nothing else in P10 waits on the
  maintainer". A slice may start once its rows are `fix` in `p10-triage.md`, which
  is true after P10.1. As drawn, the two release blockers wait on the maintainer's
  answers, and then also on P10.3d (Q1).
- **Fix.** Let P10.3a and P10.3b start after P10.1, and P10.3c's two unconditional
  entries too. They commit under the interim trailer rule that "Commit messages"
  already states. P10.3d lands when Q1 is answered and fixes the rule from then on.

**S8. The README badge row misapplies rule 2** (6330).

- **The problem.** "`README.md` is P7.1's owner file" is neither out of the spec's
  scope nor missing data. The dossier had it right: badge or no badge is a
  presentation choice nothing settles, which is rule 3.
- **Fix.** Add a short Q14 with the dossier's two readings. Recommend (1), handed to
  P7.1 as a line in its brief. Under (2) the row becomes `close`.

**S9. P10.10c would edit accepted ADRs, including a frozen table** (7074-7077).

- **The problem.** ADR 0005's mentions (lines 322-331) are `geo._relief_layers` and
  `geo._osm_layers`, names in the deleted `_port.geo`, inside the field-to-group
  table that "What the window freezes" fixes. Renaming them to the new `maps` names
  would make the record false. ADR 0009:29 is historical prose.
- **Fix.** Put `docs/decisions/**` in P10.10's leave-alone, as P10.9 already does.
  Also drop P10.10a's `references.md` ownership: no entry cites an `ink.tip` name.

**S10. Who runs P10.1 and P10.2 is unstated.**
Lines 6094-6096 against 6265-6266 and 6383-6385.

- **The conflict.** The implementer "never edits ... `p10-triage.md`", yet P10.1's
  owner file is `p10-triage.md`, and P10.2 writes into it.
- **Fix.** State that P10.1 and P10.2 are run by the orchestrating session, not by a
  `plan-slice-implementer`. Alternatively, exempt P10.1's creation of the file from
  the rule.

## Nits

1. **P10.9 (7017).** The `spans.py:129` site is `SpanSurroundings`'s `dark`
   attribute, not `spans.place_spans`'s Args.
2. **P10.9 (7040).** "Rewrap any line ruff's length limit then breaks" does nothing:
   `E501` is ignored, and `ruff format` does not reflow docstrings. Say "keep
   reworded docstring lines within 100 columns".
3. **Place names.** P10.6 uses Countisbury, Foreland Point and Countisbury Hill.
   P10.7 uses Wharfe and Swale. None is on the `CONTRIBUTING.md` list that the slice
   rule cites, and only Watersmeet is a sanctioned fixture name. Either use list
   names (Watersmeet, Malham Cove, Dovedale; Exe, Tay) or state that existing test
   names may be reused.
4. **P10.3c `ink-reservoir`.** Baxter, Lin (2004) as the canonical source and again
   as a `Design input:` line duplicates it. Use the Chu, Tai line plus
   `Design input: the canonical source above.`
5. **P10.5b Q3 member.** "a fixed share of an em" should name the value: 0.28, the
   current literal.
6. **P10.4a.** It deletes non-golden tests but omits the coverage gates that the
   Coverage rule requires. That is harmless, because benchmarks are deselected from
   the coverage run, but say so.
7. **P10.10 pin.** Define the areas: `maps.lettering` is the package
   `pyntpot.maps.lettering`, and the `maps.lettering_*` modules are `maps`.
8. **"Measured at P10.0" (6067-6069).** vulture at 60 prints about 45 lines, so say
   "includes".
9. **Q1 (6392).** Say at which commit "33 of 81" was counted (at `91ff457` it is 32
   of 80).
10. **P10.6's `place_spans` test.** Say whether it is one call with both spans or two
    calls.
11. **P10.5b and P10.7.** Each makes two commits, while the preamble says "each slice
    as one commit". Say which commit ticks `tasks.md`.

## Counts

- 3 blocking:
  - B1: the parallel marks and the table order.
  - B2: P9 against P10, and the ADR numbers.
  - B3: "P8's list" has no location.
- 10 should-fix: S1 to S10.
- 11 nits.

Verdict: BLOCK
