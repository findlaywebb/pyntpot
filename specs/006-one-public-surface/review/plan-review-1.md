# 006 plan review 1

**Verdict: BLOCK**

The approach is right. A griffe-read rule gives one public surface, the module renames fix
#164, and the per-lane ratchet is sound: it is two-way, owned per lane and deleted in S8,
so the contract is not loosened. The ADR's table of 40 names checks out: a transitive
griffe walk of today's code finds exactly those names. But eight defects will make an
agent build the wrong thing, collide with another lane, or fail to meet its own done
criterion. Most important: **S7 cannot letter a minor road**, which is the case #161
exists for, and **S7's Lynmouth tests will make the golden card test order-dependent**.

Reviewed against commit `385fce3`. I ran griffe 2.4.1 and ty on the real tree, simulated
the `Pt` rename with ruff format, and grepped importers across src, tests, examples, docs,
mkdocs.yml, benchmarks and the mutation config.

## Blocking

### 1. S7 skips every minor road, against the ADR, the spec and #161

- **Evidence.** The filter is at `picks_roads.py:83`:
  `entry.get("c") not in ("major", "medium")`. `osm_elements.py:250` gives roads only
  `"major"` or `"minor"`, so in practice only major roads are gathered. plan.md:374-377
  extracts the loop into `_road_pieces` "statement for statement", which keeps the filter
  for `named_roads` too.
- **Why that is wrong.** ADR 0068:207-218 says the roads lettered are "exactly the named
  ones the basemap draws", and that minor roads are drawn through `[basemap] pick_roads`.
  Spec line 85 says "that the basemap draws". The #161 note is about "a named minor
  road". As planned, `Annotations(roads=("Lynbridge Road",))` for a drawn minor road
  logs "no road on the card is named" and letters nothing.
- **Second defect, same slice.** plan.md:375-376 gives `_road_pieces` a 2-tuple return.
  plan.md:383-384 then says it "also returns" the OSM name sets, which makes it a
  3-tuple. The agent has to pick one.
- **Fix:**
  - Use `_road_pieces(basemap, lines, card, classes: tuple[str, ...]) -> tuple[pieces, widths, osm_names]`.
  - `pick_roads` passes `("major", "medium")`. `named_roads` passes every road class the
    basemap draws (`("major", "minor")`).
  - Add a synthetic test that a named minor road is lettered.
  - State the four open behaviours:
    - the label text is the road's key (its number when it has one), even when the match
      was by OSM name;
    - a road matched twice (by number and by name, or listed twice) gets one label, at
      its first position in `names`;
    - a minor road's `feature_px` falls back to the default (`ROAD_PX_DEFAULT` has no
      `"minor"` key);
    - the `picks_roads.py` module invariant at lines 9-10 ("a road the track was never
      on is not lettered") and `_ground`'s docstring are rewritten to match.

### 2. S7's Lynmouth tests overwrite the plate the golden card test reads

- **Evidence.** `draw_plate` (`lettering/pipeline.py`, `root / f"labels-{hand.route}.webp"`)
  writes to a fixed file name inside `plates.directory`.
- **What fails.** plan.md:417-422 runs `letter(...)` with `roads=` "on the module's
  `painted` fixture". That replaces the label plate that `lettered.plate_path` points
  at. `TestCompose.test_the_card_matches_the_golden_map` composes from that file, so it
  passes or fails depending on test order (pytest-randomly).
- **Precedent.** The existing span test copies the plates directory for exactly this
  reason (`test_pipeline_letter_compose.py:113-117`).
- **Fix.** Each new `letter` test copies the plates directory the same way. The three
  tests go in `TestLetter`, so they carry `@pytest.mark.golden` and the module's
  `xdist_group`.

### 3. Lanes S4 and S6 own overlapping files, and S4 cannot pass its own gate

- **What fails.** S4 makes `PaintJob.bloom` return `Blooms`. `tests/unit/maps/painter/test_job.py:51,62-63`
  index the tuple (`big[1]`, `wood[0]`) and will break.
- **Who owns what.** That file sits under S6's `tests/unit/maps/**` (plan.md:365).
  S4 cannot edit it, so S4's full-suite gate fails. Meanwhile S4 owns
  `tests/unit/maps/painter/test_water.py` (plan.md:288), which is also inside S6's glob.
- **Fix.** S4 owns `test_job.py`, and `test_water.py` only if it needs it. S6's glob
  excludes both explicitly.

### 4. S3's allowlist instructions contradict each other, and lanes must edit a file no lane owns

- **Contradiction one.** plan.md:187-194 hard-codes `ALLOWED`, and plan.md:217 adds
  `test_every_allowed_name_is_reached`, which fails on any stale entry. Several listed
  names are never reached:
  - `None` can never be reached. griffe keeps it as a string, not an `ExprName`.
    Verified: `Label.box` parses to `ExprBinOp(ExprName('Box'), '|', 'None')`.
  - `bytes`, `object`, `set`, `frozenset`, `type`, `Exception` and
    `collections.abc.Iterator` are not reached by any public signature today.
- **Contradiction two.** Some external names are reached only once a lane exports the
  class that names them:
  - `typing.NamedTuple`, through `BoundingBox`;
  - `typing.Protocol`, through `Features` and `Elevation`;
  - `json.JSONDecodeError` and `KeyError`, through `Manifest` and `ElevationGrid`.

  S3 cannot add these, because the stale-entry test would fail. S6 has to add them to
  `_public_surface.py`, which it does not own.
- **Fix.**
  - At S3, `reached` walks transitively through every reached private object. That is
    the ADR's "32 name 8 more", and the end state is unchanged.
  - The pending sets and `ALLOWED` are then complete from the first run, and no lane
    touches `_public_surface.py`.
  - Replace the hard-coded list with "exactly the external canonical paths the first
    transitive run reaches, each listed".

### 5. S3's gate leaves "alias" undefined and its self-tests miss items the spec names

- **"Public type alias" is undefined.** `pyntpot.__version__` has the value
  `importlib.metadata.version('pyntpot')`, and `PigmentLayer` and `Line` carry no
  `TypeAlias` annotation. If the gate walks every public attribute's value, it reaches
  `importlib.metadata.version` and similar non-type names.
- **Define it as:** a module attribute annotated `TypeAlias`, a PEP 695 `type`
  statement (a griffe `TypeAlias` object, which the planned walker would silently skip),
  or a value whose expression is a subscript, a `|` union, or a name that resolves to a
  class. Every other constant contributes its annotation only.
- **Spec gap.** spec.md:31-37 says "its self-tests prove each of those". The plan's
  list (plan.md:203-212) has no test for `Optional`, a return annotation, a property, a
  public method, an alias value, or a protocol member.
- **Fix, tests.** Add those six. Also add `list["_Private"]`, a quoted reference nested
  inside a generic.
- **Fix, fail closed.** A reached `pyntpot.*` path that does not resolve to a loaded
  object is a failure, never skipped.

### 6. S2 and S8 done criteria cannot pass, and S2's replace instruction can corrupt goldens

- **Evidence.** `grep -rnw Pt src tests` (plan.md:168) matches 24 binary goldens under
  `tests/golden/` (verified), and `grep -rnw Anchor src` matches a `.pyc` file.
- **Risk.** "Word-boundary replace of `\bPt\b` ... everywhere under `src/` and `tests/`"
  invites an agent to run `sed` over binary files. The S8 grep (plan.md:459) has the
  same problem.
- **Fix.** Replace only in tracked `*.py` files. Every done grep uses
  `git grep -nw Pt -- '*.py'` (and the same form elsewhere).

### 7. S10 has no bound and its fallback cannot run

- **Scope.** The `Pt` to `Point` rename changes the signature line of **52** `ink` and
  `letters` functions (counted by AST), and S9 changes more docstrings. `scope.py` marks
  every one as changed.
- **What "done" would demand.** "Zero unexplained survivors" (plan.md:496) then means
  killing pre-existing survivors in about 60 functions that have nothing to do with this
  feature. That is unbounded scope creep.
- **Fallback.** The fallback is to run the Actions workflow if the list passes 150. That
  needs a pushed branch, and S11 says "do not commit or push".
- **Fix.** Split the scope.py list in two:
  - Functions whose body changed (`wash`, `bloom`, the `Flow`/`Blooms` readers, anything
    S4 or S5 touched beyond annotations): kill every survivor, or name it as equivalent.
  - Functions changed only by an annotation or a docstring: run them, as CLAUDE.md
    requires, and record pre-existing survivors in one `docs/issues/` note and GitHub
    issue, listed in the PR.

  Also set a time cap, and either drop the Actions fallback or authorise the push.

### 8. S8's done grep cannot pass with the files S8 owns

- **First file.** `docs/issues/docs-style-fields-imports-and-reference-checks.md:11`
  names `LetteringPolicy` and `RouteInk`, but plan.md:524 puts it on the "Files to leave
  alone" list.
- **Second file.** `src/pyntpot/ink/bloom.py:8` says "`ink.wash`". It is not in S1's
  importer list (plan.md:123-140), S4 owns it but is not told about this line, and S8
  does not own it.
- **Third file.** `maps-route-{casing,glow,shadow}.md` also name `RouteInk` at lines
  16-20. S8 lists only line 6 of these files.
- **Fix.** Add `bloom.py:8` to S1. Exclude the #163 note from the grep, or allow the
  edit. List the `route-*` lines. Add `docs/features/ink-data-driven-brushes-and-pigments.md:5`
  (it says the brush tables are in `ink/brush.py`).

## Should fix

1. **The ADR decision that will age worst: `Label` and `Span`, and positional records.**
   - **`Label` and `Span`.** The ADR makes the placer's 23 + 12 mutable working fields
     (`span_range`, `anchors`, `mark`, `in_water`, ...) public members whose change
     needs an ADR. The spec then defers "return frozen copies"
     (`maps-lettering-frozen-records`), which would be a breaking change to a contract
     just published. Either return frozen records now, or have the ADR say these
     members are provisional.
   - **Positional records.** `Card`, `Credit`, `Manifest`, `DarkGrid`, `Layers`,
     `River`, `Road`, `ElevationPatch`, `ElevationGrid`, `Vector*` and `Projection`
     (which is also mutable) are positional dataclasses. So "adding a field with a
     default is additive" (ADR:178-180) is false except at the end, and field order
     becomes part of the contract. Either make the newly public records
     `kw_only=True`, the ADR's own reasoning for the style groups, or state that
     positional construction of returned records is unsupported.
2. **Names that become permanent.** `Flow(exp, ref_frac, frac)` gives three cryptic
   public field names that can then only change by ADR. `Blooms` breaks the ADR's own
   `<Call>Options` convention (`bloom(..., blooms)`). Decide both before they are
   published.
3. **Package docstrings.** BOUNDARIES.md:29-31 requires each `__init__` docstring to be
   kept current. S4 and S5 do not say to list the new names in the `ink` and `letters`
   package docstrings, and S6 says it only for the protocols. Prescribe the exact
   sentence or grouping for each package.
4. **Field-docs gate definitions:**
   - **Field order.** State it as griffe's member order: class body first, then
     `__init__` assignments.
   - **Instance attributes count.** Attributes assigned in `__init__` count as fields
     (`Hand.route`, `font`, `seed`, `OverpassFeatures.endpoints`, `user_agent`, ...).
   - **Size.** About 340 entries are missing, not about 200: ink 186, letters 38,
     maps 115.
   - **Trailing comments.** The ADR bans trailing comments in public class bodies too,
     but the checker detects only `#:`.
5. **The 380-line rule would force unplanned splits in S2.**
   - `placement_costs.py` is 397 lines and becomes 399 after the S2 rename. I simulated
     this with ruff format: line 379 overflows and is reflowed.
   - `span_line.py` (385) and `osm_elements.py` (387) are already past 380.
   - Read literally, "any file a slice finds heading past 380 is split" makes S2 split
     all three.
   - **Fix.** Make the hard limit 400, and apply the split rule only to files a slice
     grows with docstrings. Name `placement_costs.py` in the budget table.
6. **Seven follow-up notes have no owner.** spec.md:130-151 lists seven notes and issues
   to file, but no slice files them. Assign them to S8.
7. **Commits are not stated.** The plan never says each slice ends with a commit. The
   merges, the hook-green ratchet and `scope.py` (`origin/main...HEAD`) all depend on it.
8. **Factual slips an agent will trip on:**
   - `HandStyle(seed=...)` (plan.md:311): the field is `label_seed`.
   - `label_sizing` also needs `TIER_SPAN`, `Basemap`, `Point`, `Callable` and `math`
     (plan.md:92).
   - `Box` importers number 10 in src plus 2 in tests, not 8.
   - The providers need `contact` (use the tests' `CONTACT` pattern), not "default
     arguments".
   - Ruff's RUF022 puts `MAX_NOTES` and `MAX_NOTE_CHARS` first in `maps.__all__`.
   - The tuple sites also include `test_bloom.py:45,60,68,80` and
     `test_keyed.py:132-133,153-157`.
   - S3 owns seven files, not six.
   - `test_site.py`'s module docstring (line 6) still describes deep paths.
9. **Dangling links.** `how-the-wash-works.md:141` and `self-host-providers.md:9` link to
   notes S8 deletes. Coordinate merge order with session A so `main` never carries dead
   links.

## Consider

- **Future-proofing the gate:**
  - PEP 695 type parameters and `TypeVar` bounds;
  - `@overload` signatures;
  - check that a name is exported from the layer that *defines* it, as ADR:34-36 says
    (the planned gate accepts any layer's `__all__`).
- **#161 proof that does not need the pinning machine.** Add `letter(..., Annotations())`
  labels `== PINNED_LABELS`, and a unit test that `_ground` with empty `roads` equals
  today's list.
- **Spec wording.** The spec says `B3234` is lettered "and not the `A39` the picker would
  choose", but today the picker letters both (`PINNED_LABELS` lines 29-30). Reword it to
  "named roads replace both picked roads".
