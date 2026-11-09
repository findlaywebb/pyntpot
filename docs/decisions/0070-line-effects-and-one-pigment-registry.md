# 0070 — Line effects and one pigment registry (amends 0015, 0027, 0046 and 0069)

Status: accepted

Amends ADR 0015 (what `maps` reads at the boundary: palettes and `.gpl` files), 0027 (the
lettering's route-coloured ink is no longer independent of a fed colour, rule 18), 0046
(the dropped route casing, glow and shadow come back as a typed effect stack, rules 8 to
12, and `with_route_ink` changes behaviour, rule 18) and 0069 (a theme colour may be a
name or an alias, the hand-kept colour list goes, and a theme gains five top-level keys).
Spec: `specs/009-line-effects-and-registry/` for PR 1, and a stacked `specs/009a-*` for
PR 2. Evidence: `specs/009-line-effects-and-registry/research.md`. Issues: #72, #71,
#170, #159, #67, #69, #70, #104, #105, #106.

## Context

**The map paints from silent copies of the pigment tables.** `ink` exports `PIGMENTS` and
`TRANSPARENCY` (15 map roles) and `PAINTERS_PIGMENTS` and `PAINTERS_TRANSPARENCY` (10 tube
names), and no painter in `src/` reads any of them. The map reads `CoverStyle.pigments`, a
verbatim copy of `PIGMENTS`, and `PaperStyle.pigment_transparency`, a copy of
`TRANSPARENCY`. No test ties a copy to its table, so the two can drift, and the theme's
vocabulary of pigment keys is built from the copy. Painter's pigments are a second,
disjoint namespace that no theme can name. An unknown name in engine code is a bare
`KeyError`, and an unknown brush id gets no suggestion.

**A colour is a hex string with no type.** About twelve places can hold a colour; the
theme reaches eight key paths, every one a plain `str` of `#rrggbb`. The set of colour
fields is written twice, once by the fields and once by hand in `COLOUR_FIELDS`. Nothing
lower-cases a theme's hex, so `#C22050` and `#c22050` hash differently. Two functions
turn hex into RGB (`ink.sheet.rgb` and `compose_steps._rgb`). A theme cannot say
`ultramarine`: it must copy the hex.

**The casing values nothing read.** The route ink once carried a free `effect` table with
`casing_px`, `glow_px`, `shadow_px` and more. The compose step read none of them, so a theme
that set them changed no card. ADR 0046 dropped them and filed a feature for each (#104,
#105, #106). Nothing in the basemap draws a casing, a glow or a shadow either.

**#71 as written breaks ADR 0015.** It asks for `ink/data/*.yaml` loaded by `ink` at
import. ADR 0015 keeps validation libraries in `maps`, and its contract (widened by 0069)
keeps `ink` and `letters` free of `httpx`, `pydantic` and `ruamel`; PyYAML is banned for
the whole package. A YAML file read in `ink` cannot be built without loosening a contract,
so it is ruled out. A stdlib TOML or JSON file in `ink` fits the contract but needs a second
loader and checker beside `theme_check`, with no line numbers for a semantic error, which
is what ADR 0069 rejected TOML for.

**The route has two colours (#159).** `RouteInkStyle.colour` draws the line and
`NibStyle.label_route_ink` letters the route markers. `Style.with_route_ink` feeds only the
first, so a fed violet route keeps pink "start" and "finish" labels, and the nib plate is
byte-identical to the default's because `lettering_digest` does not move.

**Every new field moves a pinned hash.** `GOLDEN_HASH` embeds `BASE_DIGEST`, and a group's
digest hashes every field name. A new field at its default moves the digest, fails the
golden hash and invalidates every cached plate with no pixel changed, unless the field is
named in `DIGEST_OMITS_AT_DEFAULT`.

### Where the codebase lags current practice

The existing patterns are weaker than the prior art in five places, and this ADR changes
each on purpose:

- **Copies, not one keyed source.** openstreetmap-carto keeps its road colours as data in
  one file and hands them to the style; a painter names a paint by its tube and its Colour
  Index code. pyntpot copies values between groups by hand. Chosen: one registry, keyed by
  canonical name, read by everything (rules 1 to 3).
- **A hand-kept list where a type belongs.** `COLOUR_FIELDS` must be edited whenever a colour
  field is added. Chosen: the `Colour` type marks the field (rule 4).
- **Free-form effect keys.** The old `effect` table accepted any key. QGIS, Photoshop and
  Affinity attach a typed, ordered stack of effects to a symbol. Chosen: a typed stack per
  line class, checked like every other theme key (rule 8).
- **Every layer is a pigment glaze.** Every layer is composited by
  `composite`, by Kubelka-Munk or by multiplying. A glaze cannot lighten what lies under it,
  and the paint tools all build a halo or a casing as an image operation. Chosen: effects
  are RGB operations between layers, a deliberate departure from the compositing pattern,
  limited to effects (rule 11).
- **Errors without a way out.** A misspelt pigment or brush id fails with no suggestion.
  Chosen: every lookup suggests the nearest name by `difflib` (rule 2).

Where the prior art goes further than pyntpot needs, this ADR stays smaller on purpose: no
integer draw level per effect (QGIS symbol levels), no blend-mode enumeration (Mapnik's 37
comp-ops), no per-feature z-order, and no generated palettes.

## Decision

### The pigment registry

1. **Frozen Python tables in `ink`.** The shipped pigment catalogue is a typed, frozen
   Python table in `ink`, and so is the brush catalogue (`BRUSH_TREATMENTS`, `PEN_ROWS`,
   `BRUSH_COLOURS`) as it already is. Each pigment is a frozen
   `Pigment(name, colour, transparency, colour_index)`: `colour` is a `Colour` (rule 4),
   `transparency` is a float or `None`, and `None` means "take `paper.km_transparency`",
   which is what a 2-tuple layer and brush ink take today. `colour_index` is the Colour
   Index generic code (`PB29` for ultramarine), metadata only: it is never a lookup key and
   never a name. Today's 15 role pigments and 10 painter's pigments are entries, under
   their current names, so nothing is renamed. The registry holds no aliases: every alias
   comes from a theme or a palette (rules 5 and 7). Pigments a theme adds are parsed in
   `maps` by the theme reader and checker, with the file, key path, line and nearest name
   of ADR 0069. The import contracts do not change.
2. **One lookup.** `pigment(ref)` takes a `Pigment` (returned as itself), a canonical name,
   or a `#rrggbb` (an anonymous pigment with `transparency=None`), and otherwise raises
   `ValueError` naming the nearest names by `difflib.get_close_matches`. It is the one
   documented lookup; a name goes on to `PigmentRegistry.get`, the one place the miss
   message is written. `brush_from_id`
   suggests the nearest id the same way. The registry is immutable: adding pigments returns
   a new registry and never changes the shared one, so no module state moves under
   `pytest-randomly` or xdist.
3. **One source of values.** The four exported tables and the defaults of
   `CoverStyle.pigments` and `PaperStyle.pigment_transparency` are built from the registry,
   holding today's values, and a test ties each to it. No public name is removed in PR 1.

### Colours

4. **One `Colour` value type in `ink`.** `Colour` is a frozen `str` subclass holding a
   lower-case `#rrggbb`, with `.rgb` and `Colour.parse(text)`. It is a `str` subclass, not a
   dataclass, for two reasons: `theme_check` treats a dataclass hint as a sub-table, and
   `dataclasses.asdict` would hash a dict where the digest hashes the string today. As a
   `str` it keeps `==`, `json.dumps`, `asdict` and every existing default working, and a
   hex colour hashes as itself. `.rgb` computes exactly as `ink.sheet.rgb` does now
   (a float64 division, then float32) and `.rgb8` gives the three bytes, so they replace
   the two hex-to-RGB converters: `compose_steps._rgb` goes, and `ink.rgb` stays public,
   its behaviour unchanged (the `#` optional, characters after the sixth digit unread),
   sharing `Colour`'s channel arithmetic, so hex is parsed in `ink/colour.py` only.
   Every colour field of every style group is typed `Colour`; the type marks the field, so
   `COLOUR_FIELDS` is retired and the schema and checker test the hint instead. A plain
   `str` still reaches a field at runtime (a caller's keyword, `dataclasses.replace`,
   `Style.model_validate` from a dict), so each group with a `Colour` field normalises it
   in `__post_init__` through `Colour.parse`, a dict field rebuilt, and `Colour` gives
   pydantic its validator through `__get_pydantic_core_schema__`, which returns a
   plain-dict core schema calling `Colour.parse` and imports nothing from pydantic, so
   ADR 0015's contract holds and `Style` needs no `arbitrary_types_allowed`. A typed
   caller wraps a literal in `Colour(...)`; an untyped caller keeps working unchanged.
5. **How a theme names a colour.** Every theme colour field takes a `#rrggbb`, a canonical
   pigment name, or an alias the theme or its palette defines up front. Aliases are a
   top-level theme table, `colours:`, mapping an alias to a pigment name or a hex. An alias
   stands for a pigment, not a hex: an alias to a name holds that pigment, transparency
   and Colour Index included, and an alias to a hex holds the anonymous pigment
   `pigment("#...")` returns (rule 2). An alias
   may not name another alias (no chains) and may not reuse a built-in pigment name. A
   `maps`-side pydantic `BeforeValidator` resolves the value: a leading `#` goes to
   `Colour.parse`, anything else to an alias and then a registry name, and a miss is a
   located error with the nearest name. Strict, as ADR 0069 is: no `#abc` shorthand and no
   CSS names. Names and aliases resolve to hex at load, so an existing hex theme hashes as
   before, and retuning a pigment repaints every theme that names it, which is correct. A
   colour field takes its name's colour only; the pigment's transparency, which the alias
   keeps, is used from rule 17, in PR 2. The
   schema gives every `Colour` field `anyOf` three branches: an enum of the registry's
   names, the hex pattern, and the alias pattern `^[a-z][a-z0-9]*(_[a-z0-9]+)*$` (no
   leading, trailing or doubled `_`, so every alias is its own `.gpl` normal form). The
   schema is static and cannot know a theme's aliases or pigments, so the third branch
   keeps them valid in an editor; the enum still completes names, and the checker stays
   the path for good errors.
6. **Collisions are rejected.** A pigment a theme adds (a top-level `pigments:` table) whose
   name equals a built-in is an error at load, pointing at the derived form, `base:
   <pigment>` plus the fields it overrides. Rebinding a map role (`cover.pigments.built:
   "#f0b86a"`) stays allowed: that is a binding the theme owns, not a registry entry.
   Shadowing with a warning and namespacing are both rejected (Alternatives).
7. **Palettes.** A palette is a named, shareable set of aliases, each mapped to the pigment
   it stands for (`Palette.pigments`), so an alias to a built-in name keeps that
   pigment's transparency. A palette sees no theme, so its aliases name built-in pigments
   or hexes. A theme chooses one with a
   top-level `palette:` key, by name or `.yaml` path under ADR 0069's rule for themes, and
   may add aliases of its own. A theme alias that replaces a palette alias is an error
   unless the theme marks it `override`. Bundled palettes are YAML files in the `maps`
   package, read by the theme reader at the boundary, so ADR 0015 holds. A GIMP `.gpl`
   file imports as a palette's aliases, each an anonymous pigment of its row's hex, and
   the registry or a palette exports as `.gpl`, writing each name and its hex. `.gpl`
   carries RGB and a name only, so a pigment's transparency and Colour Index code do
   not travel in it; the YAML and the Python tables stay the source of truth. A `.gpl`
   name is normalised to an alias (lower case, each run of other characters one `_`,
   stripped). A row with no name, a name that does not normalise to an alias (it starts
   with a digit, say), two rows that normalise to one alias, and a name equal to a
   built-in pigment are each a located error, never dropped. The registry exports under
   its canonical names, for other tools; those are built-in names, so that file is not a
   palette a theme can read back.
   - **Down `extends`.** Aliases, theme pigments and theme presets accumulate from the
     base-most theme of the chain up, and replacing an inherited one needs `override:
     true`. A theme has one palette in effect, the nearest `palette:` in its chain, so a
     child's `palette:` replaces its parent's. A palette alias equal to an inherited theme
     alias is an error at the `palette:` line unless the theme rebinds that alias with
     `override`. Each file's names resolve in the scope it sees when it is checked, so a
     name binds where it is written: a child that rebinds `sky`, or picks another
     palette, does not recolour a field its parent set to `sky`. To recolour that field,
     the child sets the field. A parent theme therefore means the same whoever extends it,
     and every error names the line where the name was written.

### Line effects

8. **An effect stack per line class.** Each line class holds one optional, ordered effect
   stack of at most one casing, one glow and one shadow, applied in the stack's order. The
   keys are the code's line classes, `major`, `medium`, `minor`, `coast`, `road_major`,
   `lane` and `track`, plus `route`. The package ships three effect presets, `cased`,
   `halo` and `lifted`; a theme may define its own in a top-level `effect_presets:` table,
   and a theme preset may not reuse a built-in preset name. A line class takes a preset
   name or a full stack, never a mix of the two.
9. **One table, split at load.** A theme writes every stack in one top-level table,
   `line_effects:`, keyed by line class. At load it is split in two: the seven basemap
   entries become a field of a base group, read by the painter, so they move
   `base_digest` and a change repaints the plates (22 s for Lynmouth, 59 s for Skye); the
   `route` entry becomes a field of `route_ink`, read at compose, so it moves `digest()`
   only and a change costs one compose (about 0.3 s). The two fields have different names,
   because `DIGEST_OMITS_AT_DEFAULT` matches by name across groups. Route effects take the
   route's mask at compose, the pen plate's alpha or the solid line's, and are never painted
   into `pen.webp`. A retraced route is already one merged mask, and its casing and shadow
   use that mask, never one per strand.
   - **The two fields** are `basemap.line_effects`, a table of line class to stack
     (`basemap` is a `maps` group; `brush` is `ink`'s and cannot hold `maps` types), and
     `route_ink.effects`, one stack. Both are loader-only: a theme sets them only through
     `line_effects`, and naming either inside its group is a located error, so one key
     path names each thing.
   - **The schema shape.** `line_effects` keys are an enum of the line classes. A value is
     `anyOf` a built-in preset name, an alias-pattern string (a theme preset), or a stack
     object with `additionalProperties: false` and the optional keys `casing`, `glow` and
     `shadow`, each an object of that effect's fields by the same walk as a style group's
     sub-table, its colour the three-branch node of rule 5. `effect_presets` keys follow
     the alias pattern and are not a built-in preset name; each value is a stack object.
   - **Ranges are checked at load.** A width, spread, blur or offset is at least 0 and a
     strength is from 0 to 1. A value outside is a located error with the file, key path
     and line; nothing is clipped. The effect types refuse the same values in
     `__post_init__`, from one table of ranges.
   - **Off is nothing.** A casing of width 0 or strength 0, and a glow or a shadow of
     strength 0, is off. Each file's entry is kept as an explicit stack, an empty one
     included, so in the merge it replaces the parent's stack whole. Off effects and empty
     stacks are dropped once, after the final merge, when the groups are built (in the
     stack's and the basemap group's `__post_init__`). So a child turns off an inherited
     stack by writing `major: {}`, and a value equal to off moves no digest.
10. **Draw order.** The basemap draws the water group (`major`, `medium`, `minor`,
    `coast`), then the road group (`road_major`, `lane`, `track`). Within a group, every
    class's effects are laid on what lies beneath the group, in today's class order, and
    then the group's lines are laid over them in today's order: all casings lie under all
    lines, so a junction reads as one road, and a road crossing a river reads as a
    crossing. Basemap effects are steps inserted into the painter's `over` list between the
    water pad and the road pads; they never re-sort it, and with no effect set the list is
    today's. Water is one pad, so a per-class water effect builds a mask-only pad for its
    class, and those pads are built only when a water effect is set. The route is drawn at
    compose, above the whole base plate. No effect draws from `dither_rng`.
11. **Effects composite on RGB, not by Kubelka-Munk.** An effect is a plain function of the
    RGB beneath it, a float mask `m` and the effect's own small value type (`Casing`,
    `Glow`, `Shadow`, `PenCasing`, holding its widths, strength and colour), in `ink`,
    knowing nothing of maps. This is a
    deliberate departure from the compositing pattern, in which every layer is a pigment
    glazed or multiplied by `composite`: a glaze at `km_transparency = 0.06` cannot lay
    cream over a dark wood, and multiplying cannot lighten at all, so neither can make a
    casing or a glow. The departure is limited to effects; lines and washes still glaze.
    - **Casing:** a ring of width `w` round the line, covering its footprint, from the
      chamfer distance of `m >= τ`; the RGB is blended toward the casing colour laid over
      the paper, `rgb + a(c · paper - rgb)` (in wash space the paper is 1), so a white
      casing is the paper. The line is glazed over the casing as before, so the casing
      shows through the line's dry breaks.
    - **Glow:** a lift toward the paper, `rgb + a · max(paper - rgb, 0)`, with two
      numbers, a spread (a hard dilation) and a blur (a soft falloff). It has no colour of
      its own. The floor at 0 makes "never darkens" hold for any input; on real plates the
      card is at or below the paper, so the floor changes nothing there. At compose the
      target is the paper plate's pixels, not white, because the card is paper times wash.
      A pen-route glow thresholds the pen alpha first, so lossy WebP and resize noise do
      not glow.
    - **Shadow:** the mask offset, blurred and laid as a multiplying darken,
      `rgb(1 - a(1 - p))`, masked out wherever the line's density is at or above `τ`.
      Every shadow takes one light direction, the hillshade's azimuth (`Sun.azimuth`,
      315°, from the north-west), and falls away from it. The offset is rounded to whole
      pixels on each axis, half to even, and the shifted mask is zero-filled; the blur
      softens what a sub-pixel offset would have moved.
12. **Three invariants.** Each is a Hypothesis property on arrays, before the dither and the
    lossy encode:
    - a casing of width 0 is the identity, bit for bit, by an explicit early return;
    - a glow never darkens a pixel;
    - a shadow never paints over the line that casts it: where the line's density is at or
      above `τ`, the output equals the output with no shadow.
    The registry's properties sit beside them: an empty extension is the identity, and a
    caller's pigment never shadows a built-in.
13. **Pen casing.** In pen-and-ink a casing is a reserve: the paper left between two ink
    lines, with the wash beneath knocked out to the paper. It is an `ink` primitive with its
    own property tests in PR 1, off by default; its figures come in PR 2.
14. **Lettering is excluded.** No effect applies to lettering, leaders included: the nib
    refuses halos by design, and an effect there would move `lettering_digest`.
15. **Off by default, and no digest moves.** Every new field defaults to off, and every new
    field is named in `DIGEST_OMITS_AT_DEFAULT`, under a name unique across groups. A guard
    test shows every new field at its default leaves `digest()`, `base_digest()` and
    `lettering_digest()` of every packaged and example theme unchanged.

### Two PRs

16. **The split rule.** PR 1 (`specs/009-line-effects-and-registry`) moves no pinned image,
    no docs image and no hash, and a hash that moves with identical pixels counts as a
    moved image. It holds the registry (#72), the catalogues as Python tables (#71), the
    `Colour` type across every colour field, aliases, palettes and `.gpl`, the effect
    primitives with pen casing, the line-effect model, presets and theme fields (all off),
    and the labelled-grid helper (#170) with its five grids proved pixel-identical. Anything
    that moves a pixel or a hash goes to PR 2, stacked on PR 1, which is breaking (`!` in its
    title) and regenerates the goldens once at its end.
17. **A pigment carries its own transparency (PR 2).** `paper.pigment_transparency` is
    retired, and `cover.pigments` maps a cover class to a pigment reference: a `#rrggbb`, a
    pigment name or an alias, or a table `{pigment: <ref>, transparency: <0 to 1>}`. One
    rule gives every entry its transparency, whatever form it takes:
    - the entry's own `transparency`, if it sets one;
    - else the resolved pigment's own: a named pigment's, a theme pigment's, or, for a
      derived `{base: x}` pigment that sets none, its base's;
    - else the transparency of the cover class's built-in pigment, the registry's role
      pigment of the same name, which every cover class has.

    So an alias to a hex (a `.gpl` palette's aliases included), `{pigment: "#rrggbb"}`
    with no transparency, and a theme pigment whose transparency is unset all take the
    class's built-in transparency, and a theme that rebinds a class by hex keeps its look.
    An entry replaces its base theme's whole, so an `extends` child that rebinds a class
    by bare hex takes the built-in transparency, not its parent's. `paper.km_transparency`
    applies only to a transparency of `None`, which only Python can build. The resolver
    gets the cover class from the checker's validation context. The base digest is
    re-pinned and the pinned plates that move are listed.
18. **One public way to colour the route (PR 2, #159).** `with_route_ink(colour=c)` also
    sets `nib.label_route_ink = c`, so a fed colour changes every route-coloured thing. A
    theme may still letter the markers in a different shade; a fed colour overrides it.
    Feeding a colour now moves `lettering_digest` and re-strokes the nib plate once (about
    4.5 s); only a fed width stays compose-only. At the default nothing moves.

### Public names

`ink` gains `Colour`, `Pigment`, `PigmentRegistry`, `PIGMENT_REGISTRY`, `pigment`, and
the effect primitives `casing`, `glow`, `shadow` and `pen_casing` with their value types
`Casing`, `Glow`, `Shadow` and `PenCasing`, which each primitive takes whole. `maps` gains
`EffectStack`, the stack of `ink`'s effect types the theme fields hold, and `Palette`, which
reads a palette by name or path, maps each alias to its pigment, lists the packaged names,
and reads and writes `.gpl`
(rule 7's import and export need a public entry). ADR 0068's rule covers the new names;
this ADR is the record of the change it requires. No public name is removed or renamed. A
typed caller that passes a `str` literal to a colour field now wraps it in `Colour(...)`;
at runtime a `str` still works (rule 4). A theme gains the top-level keys `colours`,
`palette`, `pigments`, `line_effects` and `effect_presets`, and the schema is regenerated.

`ink/pigment.py` is renamed `ink/compositing.py`, because the public function `pigment`
cannot share the package with a submodule of that name (`tests/architecture/test_site.py`).
ADR 0068 says a module path is not part of the API, so the rename is no breaking change.
The four exported tables move to `ink/pigment_table.py` beside the registry's entries and
stay exported from `pyntpot.ink`.

## Consequences

- One registry feeds every pigment a map paints; the copies can no longer drift, and a theme
  can say `ultramarine`.
- A colour field takes a name or an alias as well as a hex; existing themes load unchanged
  and hash the same.
- A theme can case, light or shadow any line class and the route, by a preset or a stack; a
  route effect costs a compose, a basemap effect a repaint.
- Route effects appear only in `compose`'s output. The consumer's SVG page draws the route
  itself and does not get them; the docs say so. The `compose_steps.route` docstring that
  says no casing, glow or shadow is drawn changes when route effects land.
- PR 2 is breaking: `paper.pigment_transparency` goes, `cover.pigments` takes pigment
  references, a fed route colour reletters the markers, and the base digest and moved plates
  are re-pinned. PR 2 lists every moved pin and image with its reason, as ADRs 0006, 0036
  and 0052 require. `docs/images/how-to/route-ink.webp` moves there: its pink labels turning
  violet are the fix.
- A road over a river reads as a bridge only through the draw order; a river over a road
  cannot be expressed, because the basemap carries no per-feature z-order. Bridges from OSM
  `bridge` and `layer` tags, and water-lining from the glow's distance field, are filed as
  follow-ups.
- Shadows agree with the relief, since both take the hillshade azimuth.

## Alternatives considered

- **TOML or JSON in `ink` for the catalogues.** Fits the contract, but needs a loader and
  checker that duplicate `theme_check`, with no line numbers for a semantic error. Rejected
  for typed Python tables, checked by `ty` and pinned tests.
- **YAML in `ink` (#71 as written).** Breaks the import contract. Rejected.
- **Packaged YAML read by `maps` and injected into `ink`.** Leaves an engine-only caller with
  no built-in pigments and adds an init order. Rejected.
- **Hex only in themes.** No completion and no intent; the six example themes repeat
  `#7b2335`. Rejected for hex, names and aliases resolved to hex at load.
- **A `Colour` dataclass.** The checker would read it as a sub-table and the digest would hash
  a dict. Rejected for a `str` subclass.
- **Built-in aliases** (`blue` for `ultramarine`). Two names for one pigment in the registry
  break "one name per concept". Rejected: aliases belong to a theme or a palette.
- **Shadow a built-in with a warning, or namespace caller pigments** (`user:ultramarine`).
  Warnings are errors in the tests and the goal is never silently; a namespace adds syntax
  for a collision that rejection already prevents. Rejected for rejection with a pointer to
  the derived form.
- **Route effects in the brush table.** One dict in a base group would make a route casing
  move `base_digest`, repaint every plate and re-stroke the nib. Rejected for one theme
  table split at load.
- **Kubelka-Munk glazes for effects.** A glaze cannot lighten, so cream cannot cover a dark
  wood and a glow cannot lift; a glazed shadow lightens where the pigment is brighter than
  what lies under it. Rejected for RGB operations (rule 11).
- **Integer draw levels per effect** (QGIS symbol levels). The two fixed groups give the
  junction and crossing rules with nothing to set. Rejected.
- **A casing per feature** (MapLibre `line-gap-width`). Each feature cases itself and
  junctions show seams. Rejected.
- **Effects on leaders.** A letters-side change that moves `lettering_digest` and contradicts
  the nib's refusal of halos. Rejected.
- **#159 by tinting the route-token marks at compose, or by `label_route_ink = None` meaning
  the route colour.** The first moves default pixels and adds a plate; the second moves the
  pinned digests or special-cases the nib digest, and needs rule 18's behaviour anyway.
  Rejected for rule 18.
