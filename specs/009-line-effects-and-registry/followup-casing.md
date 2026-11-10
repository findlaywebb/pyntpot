# 009 follow-up: anti-aliased casings, casing unions and a paper reserve (PR 1)

PR: findlaywebb/pyntpot#211, branch `claude/quirky-hypatia-z2pii3`. Its figures and docs are the
stacked #213 (`specs/009a-line-effect-figures-and-galleries/followup-casing.md`). Decisions 24 to
27 of the orchestrator's decisions log are binding and not reopened. Evidence: the casing
research and its prototype scripts (`aa.py`, `measure.py`, `union_reserve.py`); every number below
that a test pins comes from there. Decision record: ADR 0070, amended in place ("The ADR").
Base of this follow-up: `8be0b017` (PR 1's tip before it), used for the mutation scope and for
the "no pin moved" check.

## Problem

1. **Casings look pixelated.** `casing` thresholds the mask at τ = 0.3, then takes
   `chamfer_distance` of the binary core. The ring therefore follows the staircase of the
   thresholded pixels. Its distance is measured from core pixel centres, not from the line's
   edge, and the chamfer's iso-lines are octagons, up to 8% off Euclidean. On a straight 3 px
   line, the ring's edge wobbles 0.24 to 0.41 px.
2. **Pen casing edge lines are dotted.** `pen_casing`'s reserve and edge band are boolean. A
   0.75 px edge at a 1 px gap catches only the diagonal neighbours: ink per column falls to
   0.00, and the edge wobbles 0.33 to 0.48 px.
3. **A pen route's casing has no sub-pixel edge.** `route_effects.pen_mask` binarises the pen
   plate's alpha before any line effect is laid.
4. **One class's casing shows through another class's line.** Each class's stack is laid from
   that class's own mask, and every line is a translucent glaze. So a lane's ring that falls
   inside a major road's footprint shows through the major road: 141 pixels at the research
   junction, mean luminance 0.403 against 0.359 with one ring round both.
5. **A theme cannot lay the paper back exactly.** A white casing at strength 1 is the paper, but
   nothing names that intent. There is also no way to get masking fluid's faint pooled line just
   outside the reserved shape.

## What changes (all off by default)

- `ink` gains `contour_distance` (private). It is the signed sub-pixel Euclidean distance from
  each pixel centre to the line's τ contour: negative inside, positive outside.
- `casing` and `pen_casing` take their ring from it, by box-filtered coverage. Width is now
  measured from the line's edge. `chamfer_distance` is unchanged, because nine other callers
  use it.
- `ink` gains `Reserve(width_px, pool)` and `reserve` (exported), and a private union
  primitive, `casing_union`.
- `EffectStack` may hold a reserve in place of a casing.
- A theme gains the top-level `casing_unions:` table, loaded into the loader-only field
  `basemap.casing_unions`. The painter lays each union's ring once.
- `route_effects.pen_mask` hands the line effects the pen alpha's density, not a binary mask.

## Acceptance criteria

### `contour_distance` (ink, private)

- [ ] `ink/effect_distance.py` defines
      `contour_distance(mask, *, threshold, radius) -> np.ndarray`, float32, the shape of
      `mask`. It is pure numpy: no scipy, no random number.
- [ ] Sign:
      - the value is at most 0 wherever `mask >= threshold`, and at least 0 elsewhere, bit for
        bit;
      - a mask with no pixel at `threshold`, or none below it, returns the documented cap
        (`radius + 2` outside, `-(radius + 2)` inside, no seed reached).
- [ ] Accuracy, against an exact reference computed by the test from the shape's geometry
      (never by the code under test):
      - shapes: an anti-aliased half-plane at any angle and offset (`mask = clip(0.5 - s, 0, 1)`
        for `s` the signed distance to the line), and an anti-aliased disc of radius 3 to 12 px;
      - the τ contour is at `s = 0.5 - τ`;
      - for every pixel whose reference distance is at most `radius`, the absolute error is at
        most 0.3 px;
      - C1 records the worst observed error in "Measured" below; the tolerance is not widened
        to pass.
- [ ] `ring_coverage(distance, width_px) -> np.ndarray` (same module, private) is
      `clip(width_px + 0.5 - d, 0, 1) * clip(d + 0.5, 0, 1)`: box-filter coverage of the ring
      `[0, width_px]` beyond the edge.
- [ ] Cost (recorded in "Measured", not a gate): `contour_distance` on a 1800 × 1281 array at
      radius 3, 8, 16 and 33. If radius 33 (16 display px at scale 2) takes over 3 s, C1 adds a
      two-stage form before C2: the disc minimum within 3 px, a separable bound beyond. The
      accuracy property must hold for either form.

### Casing and pen casing, anti-aliased

- [ ] `casing`'s weight is
      `effect.strength * ring_coverage(contour_distance(mask, ...), width_px)`, forced to 0
      wherever `mask >= threshold`. Its signature and its early returns are unchanged.
- [ ] `pen_casing`:
      - reserve coverage `r` is 1 on the core and `clip(width_px + 0.5 - d, 0, 1)` outside;
      - band density is `clip(width_px + edge_px + 0.5 - d, 0, 1) - r` outside the core, and 0
        on it;
      - the output is `r * ground + (1 - r) * rgb`, so the paper is exact wherever `r == 1`.
      Its signature is unchanged.
- [ ] Quality pins (`tests/unit/ink/test_effect_quality.py`, new). Each uses a straight
      anti-aliased 3 px line at 7°, 20° and 33°:
      - **Casing edge.** For a casing of 1.8 px and of 3.6 px, take the row where the weight
        crosses 0.5 in each column, by linear interpolation. It deviates from a fitted straight
        line by at most 0.22 px (now 0.24 to 0.41; prototype at most 0.20).
      - **Pen edge ink.** For a pen casing at gap 1 with a 0.75 px edge, the band's ink per
        column on one side is from 0.70 to 0.95 (now as low as 0.00; prototype 0.75 to 0.93).
      - **Pen edge position.** The band's centre deviates from a straight line by at most
        0.10 px (prototype at most 0.08).
- [ ] The unit pins in `tests/unit/ink/test_effect_edges.py` (`TestTies`, `TestSoftStep`) are
      rewritten in place to the new geometry:
      - a mask exactly at τ still counts as the line;
      - the ring is whole from 0.5 px beyond the contour to 0.5 px inside its width;
      - a quarter pixel inside the width gives coverage 0.75 (box filter), not the cubic step.
      Nothing is deleted.

### `Reserve` and `reserve` (ink, exported)

- [ ] `Reserve`, in `ink/effect_types.py`:
      - a frozen, keyword-only dataclass `Reserve(width_px: float = 0.0, pool: float = 0.0)`,
        off at a width of 0;
      - `EFFECT_RANGES` gains `"pool": (0.0, 1.0)`;
      - `check_effect_numbers` enforces the upper bound of every field that does not end in
        `_px` (`strength` and `pool`), so `Reserve(pool=1.5)` raises `ValueError` naming
        `pool`;
      - `Reserve(width_px=100.0)` is accepted, as for `Casing`.
- [ ] `reserve(rgb, mask, effect, *, threshold=LINE_THRESHOLD, paper=None) -> np.ndarray`, in
      `ink/effect_reserve.py`:
      - coverage `c = ring_coverage(d, width_px)`, 0 on the core;
      - output `c * ground + (1 - c) * rgb`;
      - then, when `pool > 0`, a pool band `b = clip(width_px + 1.5 - d, 0, 1) - clip(width_px + 0.5 - d, 0, 1)`,
        0 on the core, deepens each pixel darker than the ground: `ground * (out / ground) ** (1 + pool * b)`.
        A pixel at or above the ground, or a ground of 0, is left as it is;
      - it refuses `threshold <= 0`;
      - width 0, or a mask nowhere at the threshold, returns `rgb` itself.
- [ ] `pyntpot.ink` exports `Reserve` and `reserve`. They are documented in
      `docs/reference/ink.md` and listed in `INK_PUBLIC`. Their docstrings meet
      `test_field_docs` and `test_public_signatures`.
- [ ] `GLOSSARY.md`:
      - gains **reserve**: the paper laid back in a ring round a line, every pigment beneath it
        lifted, with an optional pool;
      - gains **casing union**: one casing or reserve round several line classes as one
        footprint;
      - `pool` mentions the reserve's pool.
      The glossary page and tooltips are regenerated
      (`PYTHONPATH=tests uv run python -m support.glossary`).

### Casing unions

- [ ] **The ink primitive.** `ink/effect_union.py` defines
      `casing_union(rgb, members, *, threshold=LINE_THRESHOLD, paper=None) -> np.ndarray`.
      `members` is a sequence of `(mask, Casing)` or `(mask, Reserve)` pairs, all of one type.
      - The ring's coverage is the maximum of the members' `ring_coverage`, each at its own
        width.
      - The weight is 0 wherever any member's mask is at or above `threshold`.
      - A casing union blends with its members' one colour and strength.
      - A reserve union lays the paper as `reserve` does, with a pool band from the minimum of
        `d_i - width_i` over the members.
      - It raises `ValueError` for:
        - mixed kinds;
        - casings whose colour or strength differ;
        - reserves whose pool differs;
        - an empty sequence.
      - It is not exported; `maps` imports it by module, as `effect_pass` imports
        `ink.effect_types`.
- [ ] **The model.** `maps/casing_unions.py` (new, pure: no loader, no style group):
      - `union_problems(stacks, unions) -> tuple[tuple[int, str], ...]` returns one
        `(union index, message)` per problem against a basemap stack table;
      - `BasemapStyle.__post_init__` runs it after `checked_line_effects` and raises
        `ValueError` with the first message;
      - `EffectStack` accepts a `Reserve`, refuses a casing and a reserve in one stack ("a stack
        takes a casing or a reserve, not both"), and drops a reserve of width 0 as off.
- [ ] **The field.** `BasemapStyle.casing_unions: tuple[tuple[str, ...], ...] = ()`:
      - named in `DIGEST_OMITS_AT_DEFAULT`, under a name unique across the groups;
      - listed in `theme_vocab.LOADER_FIELDS` as set only by the top-level `casing_unions`;
      - naming it under `basemap` is a located error;
      - documented in `docs/reference/style-fields.md`.
- [ ] **The theme table.**
      - A top-level `casing_unions:` is a list of lists of basemap line classes, checked in
        `maps/theme_unions.py` (new; the `theme_` prefix keeps it under the loader import
        guard).
      - A child's `casing_unions` replaces its parent's whole.
      - `casing_unions: []` turns an inherited set off.
      - A union of one class is allowed.
- [ ] **The painter.** `painter/effects._lay_group` lays each union's ring once:
      - at the place of the union's member that comes first in the group's class order and has
        a mask;
      - at the ring's own position in that member's stack;
      - every member's ring step is skipped at its own place;
      - glows and shadows stay per class;
      - `effect_pass.lay_stack` gains `ring=None` (`None`: the stack's own ring; `()`: no ring;
        pairs: the union's ring, each member's `*_px` scaled);
      - with no union set, `_lay_group` makes today's calls.
- [ ] **The route joins no union.** Its line effects are laid at compose on the composed card.
      `route` in `casing_unions` is a located error.
- [ ] **A reserve on the route.** `lay_stack` lays a `Reserve` through `reserve`: in wash space
      in the painter, and against the paper plate at compose.

### The pen route mask

- [ ] `route_effects.pen_mask` returns the alpha's density, 0 to 1, with every value below
      `8/255` set to 0 (the floor keeps Lanczos ringing and lossy noise from casting a
      shadow).
- [ ] C5 measures the largest off-line alpha on the Lynmouth pen plate and records it in
      "Measured"; it is below the floor.
- [ ] Unit tests:
      - an alpha of only sub-floor values gives zeros;
      - values at or above the floor are kept exactly;
      - `test_a_route_casing_changes_only_pixels_within_its_ring` still passes, its ring now
        `width + 0.5` px from the contour.

### Schema

- [ ] A stack object gains the optional key `reserve`, an object of `width_px` (0 to 16) and
      `pool` (0 to 1), `additionalProperties: false`. This holds in both `line_effects` and
      `effect_presets`.
- [ ] The top level gains `casing_unions`: an array of arrays, each with `minItems: 1` and
      `uniqueItems: true`, of an enum of the seven basemap classes. It is placed after
      `line_effects`, and `test_theme_schema.py` pins the order.
- [ ] Cross-member rules (one group; colours agree) are load-only, and the schema's
      description says so.
- [ ] Both committed copies are regenerated (`PYTHONPATH=tests uv run python -m support.theme_schema`)
      and checked.

## Hypothesis properties

All are on arrays before any dither or encode, with fields drawn finite over `EFFECT_RANGES`
and `threshold` from `floats(0.01, 1)`. New files: `tests/property/test_contour_distance.py`,
`tests/property/test_line_effect_rings.py` and `tests/property/test_casing_union_digests.py`;
`tests/property/test_line_effects.py` is edited in place.

1. **`contour_distance` agrees with the exact reference.** Within 0.3 px on random anti-aliased
   half-planes and discs (radius 3 to 12), for every pixel the reference puts within `radius`.
   The sign holds bit for bit.
2. **Width 0 is the identity.** A casing, a reserve or a pen casing of width 0 returns `rgb`
   itself (`is`). `casing_union` of members all of width 0 does too.
3. **The core is untouched.** Wherever `mask >= threshold`, the output equals `rgb` bit for bit,
   for `casing`, `glow`, `reserve` and `casing_union` (for any member's mask).
4. **Pen casing, as documented (rule 11's exemption).**
   - It is exact paper wherever `r == 1`, the core included.
   - Band density is from 0 to 1.
   - `r + band <= 1` everywhere (replacing "the band lies outside the reserve").
5. **A reserve is exact paper where its ring is whole.** Where coverage is 1, `reserve`'s output
   equals the paper plate pixel bit for bit, with a random paper plate and with `paper=None`.
6. **A reserve's pool never lightens.** For any `pool`, the output is at most the zero-pool
   output, channel by channel.
7. **A reserve's pool never darkens bare paper.** Where `rgb == ground`, the output equals the
   ground for any `pool`.
8. **A union ring is never inside a footprint.** It never changes a pixel where any member's
   mask is at or above `threshold`.
9. **A union of one is that class's own ring.** `casing_union(rgb, [(m, c)])` equals
   `casing(rgb, m, c)`, and `[(m, r)]` equals `reserve(rgb, m, r)`, bit for bit. At the painter,
   a style with `casing_unions = (("road_major",),)` paints the same wash plate as one without
   (unit, on the small fixture used by `tests/unit/maps/painter/test_effects.py`).
10. **An empty `casing_unions` is the identity on every digest.** A child of every packaged and
    example theme writing `casing_unions: []` has its parent's `digest()`, `base_digest()` and
    `lettering_digest()`, and equals it.
11. **Off reserves move no digest.** The `_OFF` strategy of `test_line_effect_digests.py` gains
    `{"reserve": {"width_px": 0}}` and `{"reserve": {"width_px": 0, "pool": 0.5}}`.

## Located load errors

Each problem names the file, the dotted key path, the line, and the nearest valid name where
there is one. Each is a unit test in `tests/unit/maps/test_theme_unions.py` (new) or
`test_theme_effects.py`. A CLI case shows exit 2 with no request made.

| Problem | Key path | When checked | Message (shape) |
| --- | --- | --- | --- |
| Not a list of lists | `casing_unions` / `casing_unions.<i>` | per file | "is a list of lists of line classes" |
| An empty union | `casing_unions.<i>` | per file | "names no class" |
| Unknown class | `casing_unions.<i>.<j>` | per file | "'lnae' is not a basemap line class; did you mean lane?" |
| `route` | `casing_unions.<i>.<j>` | per file | "the route is cased at compose from its own mask and joins no union" |
| A class in two unions, or twice in one | the later `casing_unions.<i>.<j>` | per file | "lane is already in casing_unions.<k> (line n)" |
| Members span water and road | `casing_unions.<i>` | per file | "mixes water (major) and road (lane); a union lies within one group, so a road over a river still reads as a crossing" |
| A member with no casing or reserve | `casing_unions.<i>` | after the final merge | "lane has no casing or reserve; give it one in line_effects, or drop it from the union" |
| Members' casing colour or strength differ | `casing_unions.<i>` | after the final merge | "road_major's casing is #ffffff at 0.9 and lane's is #fbf6e8 at 1; a union takes one colour and strength" |
| A casing and a reserve in one union, or reserve pools that differ | `casing_unions.<i>` | after the final merge | "a union is all casings or all reserves, with one pool" |
| A casing and a reserve in one stack | `line_effects.<class>.reserve` | per file | "a stack takes a casing or a reserve, not both" |
| `reserve.width_px` or `reserve.pool` outside `EFFECT_RANGES`, or not finite | `line_effects.<class>.reserve.<field>` (and `effect_presets.<name>.reserve.<field>`) | per file | "pool is 1.5; it must be from 0 to 1" |
| `basemap.casing_unions` written in the group | `basemap.casing_unions` | per file | "set only by the top-level casing_unions" |

**How the post-merge checks are located.** `theme_resolve.resolve` checks the merged basemap
table after the merge (`theme_unions.merged_union_problems(merged, files)`). Each problem is
located at `casing_unions.<i>` in the nearest file of the chain that writes `casing_unions`.

- If the reader records no line for a list entry, the problem takes the line of
  `casing_unions` itself; C4's red step checks which.
- A union whose members' stacks a child turned off fails here, and the message says how to
  drop it.

## The ADR

**Amend ADR 0070 in place, keeping every rule number.** Why: 0070 is unmerged, PR 1 is its
record, and 0071 already set the precedent (its rule 17 was edited in place for the same
reason). A new rule 19 would split one draw-order statement across two places. Under its
status, the header gains: "Amended in place before merge by
`specs/009-line-effects-and-registry/followup-casing.md` (casings anti-aliased, casing unions, a
reserve)."

- **Rule 8.** A stack holds at most one casing or reserve (never both), one glow and one
  shadow. The top-level `casing_unions:` table lists unions of basemap classes.
- **Rule 9.** `casing_unions` is the loader-only `basemap.casing_unions`, so it moves
  `base_digest` and repaints the plates. Add its schema shape, its per-file checks, and its
  post-merge checks located in the nearest file writing it.
- **Rule 10.** A union's ring is laid once, from its members' masks, at the first member's place
  in the group's class order. Its weight is 0 on every member's footprint, so no ring shows
  through a translucent line of the union. Glows and shadows stay per class. A union lies
  within one group. The route joins none.
- **Rule 11.**
  - Casing: coverage of the ring `[0, w]` beyond the τ contour, from `contour_distance`; width
    is measured from the line's edge.
  - Reserve (new bullet): the paper, exact where the ring is whole; the pool deepens pigment
    just outside and never touches bare paper.
  - Pen casing: fractional reserve and band.
  - The pen route mask is the alpha's density above a noise floor. The old sentence "a pen-route
    glow thresholds the pen alpha first" becomes: every primitive thresholds the mask itself,
    and the floor keeps resampling noise from casting a shadow.
- **Rule 12.** Add the invariants of properties 5 to 9.
- **Rule 13.** Pen casing's band is fractional. The reserve is the watercolour counterpart of
  the pen casing.
- **Rule 15.** `casing_unions` is in `DIGEST_OMITS_AT_DEFAULT`.
- **Public names.** `ink` gains `Reserve` and `reserve`; the theme gains `casing_unions`;
  `contour_distance` and `casing_union` stay private.
- **Alternatives considered** (new rows):
  - `colour: paper`: breaks the `Colour` type and schema;
  - `reserve: true` on `Casing`: moves the digest of every cased theme and gives two spellings
    of one thing;
  - `union:` on a casing: cannot join a preset;
  - unions by group: all or nothing;
  - the route joining: pulls it into `base_digest`;
  - scipy's EDT: a new dependency;
  - changing `chamfer_distance`: nine other callers.

## Public names

- **Exported from `pyntpot.ink`:** `Reserve` and `reserve`. A Painting with Python reader
  reserves a stroke with them, as they case one with `casing`.
- **Private: `contour_distance`.** It is an implementation detail beside the unexported
  `chamfer_distance`. The Painting with Python page calls the primitives, never a distance
  field, so it needs no export.
- **Private: `casing_union`.** A union is a map idea (line classes in one group), and `maps`
  reaches it by module path.
- **No name is removed or renamed.** The PR title keeps no `!`.

## Files to touch

| Slice | Files |
| --- | --- |
| C0 | `docs/decisions/0070-line-effects-and-one-pigment-registry.md`, this file |
| C1 | `src/pyntpot/ink/effect_distance.py` (new), `tests/unit/ink/test_contour_distance.py` (new), `tests/property/test_contour_distance.py` (new), `tests/benchmarks/test_ink.py` |
| C2 | `src/pyntpot/ink/effect_casing.py`, `src/pyntpot/ink/effect_pen_casing.py`, `tests/unit/ink/test_effect_edges.py`, `tests/unit/ink/test_effects.py`, `tests/unit/ink/test_effect_quality.py` (new), `tests/property/test_line_effects.py` |
| C3 | `src/pyntpot/ink/effect_types.py`, `src/pyntpot/ink/effect_reserve.py` (new), `src/pyntpot/ink/effect_union.py` (new), `src/pyntpot/ink/__init__.py`, `tests/unit/ink/test_effect_types.py`, `tests/unit/ink/test_effect_reserve.py` (new), `tests/unit/ink/test_effect_union.py` (new), `tests/property/test_line_effect_rings.py` (new), `tests/unit/test_public_api.py`, `docs/reference/ink.md`, `GLOSSARY.md`, `docs/reference/glossary.md` and the generated tooltips |
| C4 | `src/pyntpot/maps/casing_unions.py` (new), `src/pyntpot/maps/line_effects.py`, `src/pyntpot/maps/theme_effects.py`, `src/pyntpot/maps/theme_unions.py` (new), `src/pyntpot/maps/theme_check.py`, `src/pyntpot/maps/theme_resolve.py`, `src/pyntpot/maps/theme_vocab.py`, `src/pyntpot/maps/style_groups.py`, `src/pyntpot/maps/style.py`, `src/pyntpot/maps/theme_schema_tables.py`, `src/pyntpot/maps/themes/theme.schema.json`, `docs/reference/theme.schema.json`, `docs/reference/style-fields.md`, `tests/unit/maps/test_line_effects.py`, `tests/unit/maps/test_theme_effects.py`, `tests/unit/maps/test_theme_unions.py` (new), `tests/unit/maps/test_casing_unions.py` (new), `tests/unit/maps/test_theme_schema.py`, `tests/unit/maps/test_digest_omits.py`, `tests/property/test_line_effect_digests.py`, `tests/property/test_casing_union_digests.py` (new), `tests/architecture/test_theme_imports.py` only if `casing_unions.py` must be named there |
| C5 | `src/pyntpot/maps/effect_pass.py`, `src/pyntpot/maps/painter/effects.py`, `src/pyntpot/maps/route_effects.py`, `tests/unit/maps/painter/test_effects.py`, `tests/unit/maps/painter/test_union_wash.py` (new), `tests/unit/maps/test_route_effects.py` |
| C6 | `specs/009-line-effects-and-registry/mutation.md` |
| C7 | this file (ticks, "Measured"), `specs/009-line-effects-and-registry/tasks.md` (one line pointing here) |

Each file has one owning slice. A later slice imports an earlier slice's module, and never
edits it.

## Files to leave alone

- `src/pyntpot/ink/noise.py` (`chamfer_distance`, `smoothstep`)
- `src/pyntpot/ink/effect_glow.py`, `src/pyntpot/ink/effect_shadow.py`,
  `src/pyntpot/ink/effect_mask.py`
- `src/pyntpot/maps/compose_steps.py`: its `pen_mask` call is unchanged
- `src/pyntpot/maps/painter/pen.py` and `src/pyntpot/maps/painter/plates.py`: `pen_groups`
  already masks every class with a stack
- every theme YAML; `BUILT_IN_PRESETS`
- `letters/**`
- every file under `examples/`, `docs/images/`, `tests/golden/`
- `specs/009-line-effects-and-registry/grid-hashes.json`
- `pyproject.toml`'s import contracts
- `CLAUDE.md`, `CONTRIBUTING.md`, ADR 0071

## Hard rule: PR 1 moves no image, hash or digest

- No PR 1 example, golden or theme sets a casing, a reserve, a union or a route line effect, so
  no pixel moves.
- `casing_unions` is omitted from the digest at its default, and the `reserve` kind adds no
  field to `Casing`, so no digest moves.
- Proven at C2, C5 and C7:
  - the golden docs subset, and at C7 the full golden suite, pass with no regeneration;
  - the grid hash check passes;
  - `git diff 8be0b017 -- tests | grep -E '^-.*\b[0-9a-f]{16}\b'` prints nothing (no pinned
    hash literal changed or removed).
- A slice that turns any golden red stops and reports. It never regenerates.

## Line budget and signatures

- **400 lines per `src` file; split, never thin.**
  - `style_groups.py` is about 351 lines on PR 1 and about 370 on PR 2. If either branch would
    pass 400 after C4, C4 first moves `BasemapStyle` whole to `maps/style_basemap.py` as a pure
    move commit.
  - `theme_resolve.py` goes from about 280 to about 300.
  - Every new module is under 200.
- **Every signature has at most 6 parameters, with no `# noqa: PLR0913`:**
  - `contour_distance(mask, *, threshold, radius)`
  - `ring_coverage(distance, width_px)`
  - `reserve(rgb, mask, effect, *, threshold, paper)`
  - `casing_union(rgb, members, *, threshold, paper)`
  - `lay_stack(rgb, mask, stack, *, scale, paper, ring)`
  - `union_problems(stacks, unions)`
  - `check_casing_unions(check, value)`
  - `merged_union_problems(merged, files)`

## Slices and gates

The order is serial: C0, C1, C2, C3, C4, C5, C6, C7. Each slice is red then green, with a
checkpoint commit.

**Slice gate (every slice).** Add `--golden-tolerance` off the pinning machine; never use
`-n auto`.

```bash
uv run pytest -n 2 --dist loadgroup -m "not golden" -q
uv run ruff check . && uv run ruff format --check .
uv run ty check
uv run lint-imports
PYTHONPATH=tests uv run python tests/golden/grid_hashes.py check specs/009-line-effects-and-registry/grid-hashes.json
uv run --locked --group docs mkdocs build --strict
uv run prek run --all-files
```

**Golden, no regeneration.**

- At C2 and C5: `uv run pytest -m golden -n 2 --dist loadgroup tests/golden/test_docs_images.py`.
- At C7: `uv run pytest -m golden -n 2 --dist loadgroup` (about 55 min at `-n 2`).

**C0: start.**

- Amend ADR 0070 as above.
- Commit this file.
- Record `8be0b017` as the base.
- Run the slice gate on the untouched tip as a baseline.

**C1: `contour_distance`.**

- Red: properties 1 and the cap cases; unit cases at a mask exactly at τ, a one-pixel line, an
  array edge.
- Green: implement it; record accuracy and cost in "Measured"; add the two-stage form if radius
  33 is over 3 s.
- Add a benchmark smoke entry.

**C2: casing and pen casing.**

- Red: the quality pins; the rewritten `TestTies` and `TestSoftStep`; property 4; properties 2
  and 3 for `casing`.
- Green: switch both primitives to `contour_distance`; update their module and function
  docstrings ("width from the line's edge").
- Run the golden docs subset.

**C3: `Reserve`, `reserve`, `casing_union`, exports, glossary.**

- Red: `Reserve` defaults, ranges and `pool` bound; properties 2, 3 and 5 to 9 at the ink
  level; `test_public_api` lists `Reserve` and `reserve`.
- Green: implement; export; `ink.md` entries; glossary terms regenerated.

**C4: the theme model.**

- Red: `EffectStack` with a reserve and the casing-or-reserve refusal; every row of "Located
  load errors"; a child's `casing_unions` replacing its parent's; `casing_unions: []`;
  `BasemapStyle` refusing a bad union in Python; property 10; the off-reserve strategy; the
  schema order and nodes; `DIGEST_OMITS_AT_DEFAULT` unique-name test.
- Green: implement; regenerate both schema copies; add the `style-fields.md` row.

**C5: painter and compose.**

- Red:
  - a union of `road_major` and `lane` on the small fixture leaves the major road's footprint
    unchanged where the lane's own ring would fall (pixel equality with the road-only plate
    there);
  - property 9 at the painter;
  - the ring step is skipped at later members;
  - a route `reserve` at compose equals the paper plate where whole;
  - the `pen_mask` cases.
- Green: implement `ring=` in `lay_stack`, the union pass in `_lay_group`, the reserve branch
  and the soft `pen_mask`.
- Run the golden docs subset.

**C6: mutation testing.** See below.

**C7: whole PR.**

- Run the full golden suite with no regeneration, and the pin-literal check.
- Update the PR body: the "Changelog" lines below, and the mutation survivors with their
  reasons.
- Push. Then merge this branch into `claude/quirky-hypatia-z2pii3-stacked`; that is PR 2's T0.

## Mutation testing

Follow `CONTRIBUTING.md` ("Mutation testing") on the changed `ink` functions:

- `effect_distance.contour_distance`, `effect_distance.ring_coverage`
- `effect_casing.casing`, `effect_pen_casing.pen_casing`
- `effect_reserve.reserve` and its helper
- `effect_union.casing_union`
- `effect_types.check_effect_numbers`, `Reserve.__post_init__`

Scope:

```bash
patterns=$(mktemp)
uv run python tests/mutation/scope.py --base 8be0b017 --out "$patterns"
xargs -r -a "$patterns" prlimit --as=3500000000 -- uv run mutmut run --max-children 2
uv run mutmut results | grep -v 'not checked'
```

Use the pytest-9 workaround from `specs/009-line-effects-and-registry/mutation.md`: mutmut 3.8
reads `item._nodeid`. Run with a `sitecustomize.py` outside the repository (in the session
scratch directory, on `PYTHONPATH`) that aliases `Node._nodeid`; nothing in the repository
changes.

Kill each survivor with a focused test in `tests/unit/ink/`, or name it as equivalent with its
reason. Record the result as a new section of `mutation.md` ("Follow-up: anti-aliased casings,
reserve and unions") and in the PR description. Known equivalent shapes carry over: the `copy`
flag on a final `astype`; a clip that the final clip absorbs.

## Changelog (added under "Changelog" in #211's description; the title is unchanged)

```
feat(ink): Reserve and reserve, a line effect that lays the paper back round a line, with an optional pool
feat(maps): casing_unions theme table: one casing or reserve round several line classes of one group
fix(ink): casing and pen_casing are anti-aliased, their widths measured from the line's edge
```

## Measured (filled by C1 and C5)

- `contour_distance` worst error on the reference shapes: …
- Its time at radius 3, 8, 16 and 33 on 1800 × 1281: …
- Largest off-line pen alpha on the Lynmouth pen plate: …

## Risks


**Risks:**
- `contour_distance` is a prototype: nobody has checked its accuracy against an exact reference. The 0.3 px tolerance may fail at 45 degrees, and its cost grows with the square of the radius, so 16 display px at scale 2 may need the two-stage form.
- PR 2's goldens go red on the merge until T6, so push both branches together.
- Merge conflicts in `style_groups.py`, the schema copies and `style-fields.md` could hide a dropped hunk, so regenerate rather than hand-merge.
- The 8/255 pen-mask floor is an estimate until C5 measures it.
- Painting at 2x moves the glow and shadow sweeps, beyond the research's list. Overrule decision 1 of block B if you only want the research's images to move.
- Cached plates have no code-version key, so they keep their old casings.
- Bold's cream-versus-reserve question stays with you.
