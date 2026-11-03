# 006 — tasks

- [ ] Start: comment the branch `feat/006-one-public-surface` on #168, #73, #78, #169, #164
      and #161.
- [x] ADR 0068 and its index row; spec, plan, tasks.
- [ ] Plan-reviewer passes the plan.
- [ ] S0: split `ink/brush.py` (`ink/brush_sheet.py`) and `maps/lettering/label.py`
      (`maps/lettering/label_sizing.py`); pure moves, suite green.
- [ ] S1: collision and directive tests red, four modules renamed, importers, reference
      directives and `references.md` paths repointed; green (#164).
- [ ] S2: `Pt` to `Point`, one `Box`, `Anchor` folded into `Align`, alias docstrings.
- [ ] S3: `griffelib` in `dev`; `test_public_signatures.py` and `test_field_docs.py` with
      self-tests and the per-lane pending ratchet; architecture tests green.
- [ ] S4 (parallel): ink lane: `Flow`/`Blooms` records, keyword-only ink groups and
      `WashOptions`, eight ink exports, ink field docs, `ink.md`; `_pending_ink.py`
      empty (#73).
- [ ] S5 (parallel): letters lane: keyword-only letters groups, `Align`, letters field
      docs, `__version__` docstring, `letters.md`; `_pending_letters.py` empty.
- [ ] S6 (parallel): maps lane: `LetteringStyle`/`RouteInkStyle`, keyword-only map
      groups, 31 maps exports with the protocols, maps field docs, `maps.md`, protocol
      conformance test; `_pending_maps.py` empty (#78).
- [ ] S7 (parallel): `Annotations.roads` letters the roads it names; goldens unchanged;
      `_pending_roads.py` empty (#161).
- [ ] Merge S5, S4, S7, S6; standard gate green after each.
- [ ] S8: ratchet deleted, gates absolute; `GLOSSARY.md` three rows, `BOUNDARIES.md`;
      six notes deleted, citing notes repointed (#168, #169).
- [ ] S9: docstring terminology sweep per `specs/007-docs-truth-and-glossary/spec.md`.
- [ ] S10: mutation run on changed `ink`/`letters` functions; survivors killed or named.
- [ ] S11: final review against plan and spec; all gates and the strict docs build green;
      PR body drafted with Changelog, `Closes #168 #73 #78 #169 #164 #161`, mutation
      equivalents and the session A handoff.
- [ ] Merge closes #168, #73, #78, #169, #164, #161 (ticked with the issues).
