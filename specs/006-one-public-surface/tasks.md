# 006 — tasks

- [x] Start: comment the branch `feat/006-one-public-surface` on #168, #73, #78, #169, #164
      and #161.
- [x] ADR 0068 and its index row; spec, plan, tasks.
- [x] Plan-reviewer passes the plan (round 4).
- [x] S0: split `ink/brush.py` (`ink/brush_sheet.py`) and `maps/lettering/label.py`
      (`maps/lettering/label_sizing.py`); pure moves, suite green.
- [x] S1: collision and directive tests red, four modules renamed, importers, reference
      directives and `references.md` paths repointed; green (#164).
- [x] S2: `Pt` to `Point`, one `Box`, `Anchor` folded into `Align`, alias docstrings.
- [x] S3: `griffelib` in `dev`; `test_public_signatures.py` (transitive walk, alias rule,
      `layer_of`, strings fail closed, `ALLOWED` the reviewed 30-name literal) and
      `test_field_docs.py` with self-tests and the per-lane pending ratchet; the run
      reproduces plan.md's expected 38 violations (6/1/31/0) and 30 external names, or S3
      stops and reports; architecture tests green.
- [x] S4 (parallel): ink lane: `Flow`/`Blooms` records, keyword-only ink groups and
      `WashOptions`, eight ink exports, ink field docs, `ink.md`; `_pending_ink.py`
      empty (#73).
- [x] S5 (parallel): letters lane: keyword-only letters groups, `Align`, letters field
      docs, `__version__` docstring, `letters.md`; `_pending_letters.py` empty.
- [x] S6 (parallel): maps lane: `LetteringStyle`/`RouteInkStyle`, keyword-only map
      groups, 31 maps exports with the protocols, newly public records frozen and
      keyword-only (`Projection` frozen, `Label`/`Span` keyword-only), maps field docs,
      `maps.md`, protocol conformance test; `_pending_maps.py` empty (#78).
- [x] S7 (parallel): `Annotations.roads` letters the roads it names, every class and
      numbered-only roads; unmatched names raise `ValueError`; non-golden
      `test_ground.py` covers `_ground`; goldens unchanged; `_pending_roads.py` empty
      (#161).
- [x] Merge S5, S4, S7, S6; standard gate green after each.
- [x] S8: ratchet deleted, gates absolute; `GLOSSARY.md` three rows, `BOUNDARIES.md`;
      six notes deleted, citing notes repointed; seven follow-up notes and issues filed
      (#168, #169).
- [ ] S9: docstring terminology sweep: every row of plan.md Appendix A (007 at
      `529753f`), the N24 log message, the test docstrings; no retired word left in
      `src/**/*.py` or `tests/**/*.py` but the two `"callouts"` key lines.
- [ ] S10: local mutation run on the behaviour-changed functions (plan.md S10 table and
      rule; the seven maps patterns in a throwaway worktree config, re-run from each new
      `HEAD` until every survivor is killed or named).
- [ ] S11: final review against plan and spec; all gates and the strict docs build green;
      PR body drafted with Changelog, `Closes #168 #73 #78 #169 #164 #161`, mutation
      equivalents and the session A handoff.
- [ ] Merge closes #168, #73, #78, #169, #164, #161 (ticked with the issues).
