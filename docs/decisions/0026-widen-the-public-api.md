# 0026 — Widen the public API

Status: accepted

## Context

The tutorials start from the painting primitives (paper, wash, brush stroke, nib line,
pigment compositing, lettering, composition) and only then paint a route map. Under ADR
0007 nothing outside `pyntpot.__all__` is public, so no minimal primitive sequence can be
written with public names alone: building a brush, turning a stamped accumulator into
density, colouring a layer, setting a line of lettering and writing the finished image
all need names that 0007 leaves private.

## Decision

This ADR amends ADR 0007, which stays as the record of the first surface.

The public surface is `pyntpot.__all__` (unchanged, 0007's list) and the `__all__` of
`pyntpot.ink`, `pyntpot.letters` and `pyntpot.maps`. A name in no `__all__` is private,
whatever module defines it. By this rule `FetchError` and the map names already in
`pyntpot.maps.__all__` are public.

The existing functions and types are widened; no parallel convenience layer is added.
These names join a layer package's `__all__`:

| Public name | Defining module | Package |
| --- | --- | --- |
| `BrushStyle` | `ink.brush_style` | `pyntpot.ink` |
| `brush_from_id` | `ink.brush` | `pyntpot.ink` |
| `ink_density` | `ink.pad` | `pyntpot.ink` |
| `PaperStyle` | `ink.style` | `pyntpot.ink` |
| `PIGMENTS` | `ink.pigment` | `pyntpot.ink` |
| `TRANSPARENCY` | `ink.pigment` | `pyntpot.ink` |
| `PigmentLayer` | `ink.pigment` (was `Layer`) | `pyntpot.ink` |
| `rgb` | `ink.sheet` | `pyntpot.ink` |
| `paper_plate` | `ink.paper` (moved from `maps.painter.paper`) | `pyntpot.ink` |
| `save_image` | `ink.io` (new) | `pyntpot.ink` |
| `Setting`, `Mark` | `letters.setting` | `pyntpot.letters` |
| `FaceStyle`, `HandStyle`, `NibStyle`, `NibGroups` | `letters.style` | `pyntpot.letters` |
| `NibSurface` | `letters.nib` | `pyntpot.letters` |
| `nib_plate` | `letters.nib` (was `plate`) | `pyntpot.letters` |
| `Cache` | `maps.cache` | `pyntpot.maps` |
| `OverpassFeatures` | `maps.providers.overpass` | `pyntpot.maps` |
| `OpenTopoData` | `maps.providers.opentopodata` | `pyntpot.maps` |

A name that becomes public says what it is, so two are renamed as they are promoted, every
importer repointed at once and no shim left behind:

- `Layer` becomes `PigmentLayer`: the glossary's "layers" is the basemap's typed geometry,
  `maps.basemap.Layers`, and a public `ink.Layer` would give that term a second meaning.
- `plate` becomes `nib_plate`: "plate" is the glossary's word for every painted raster
  layer, so a bare `pyntpot.letters.plate` would name all of them.

One is moved: `paper_plate` goes from `maps.painter.paper` to a new `ink.paper` under its
own name, its parameter `plate` renamed `canvas` because it names a `Canvas`. The paper is
an engine primitive that reads only `ink` names; promoting it through `pyntpot.maps` would
put a primitive in the application layer. One helper is added, `save_image`, because the
raw sequence for writing a painted array (dither, convert, choose an encoder) is
unreasonable for a tutorial. No name in ADR 0007's list is renamed or removed: the
widening is additive.

No promoted name is top-level. `pyntpot.__all__` stays the short façade the README's
quick start uses; names such as `TRANSPARENCY`, `Mark` or `Cache` read clearly only beside
their package; and ADR 0007's Boundary already reaches the providers and the cache through
`pyntpot.maps`. A caller imports them from their layer package
(`from pyntpot.ink import brush_from_id`).

The boundary is unchanged: `maps -> letters -> ink`, `ink` and `letters` import neither
`httpx` nor `pydantic`, and the import-linter contracts stay as they are.

### Members

The public API is the names in a public module's `__all__` and their documented
signatures. The attributes and methods, not starting with `_`, of a class named in some
`__all__` are public with it: the fields of the five style groups promoted here
(`PaperStyle`, `BrushStyle`, `FaceStyle`, `HandStyle`, `NibStyle`) and of `NibGroups`, the
fields of `Setting`, `Mark` and `NibSurface`, `Cache`'s methods (`key` and `plates_dir`
among them), and the attributes of 0007's map types. For those map types this widens ADR
0007's "Anything not listed is free to move or be renamed": their members reached only
through attributes (`Style`'s inherited pydantic methods among them) are public from this
ADR on, while what 0007 binds stays bound, the names in `__all__` and their documented
signatures.

A class reachable only through an attribute of a public object and named in no `__all__`
is not itself a public name: the style groups reached only through `Style` (`WashStyle`
from `ink.style`; `CardStyle`, `RibbonStyle`, `CoverStyle`, `RouteStyle`, `RouteInks`,
`RouteInk`, `LetteringPolicy`, `BasemapStyle` from `maps.style_groups`), and `Label`
reached through `Lettering.labels`. Its members may change without an ADR (the public
attribute that holds it, such as `Style.route_inks` or `Lettering.labels`, stays fixed),
and the upstream consumer's reads govern them as before.

A field's default value is behaviour, not a name, and is not fixed by this ADR: the rule
below fixes a token's spelling and meaning, so a default that is a token (`"map"`,
`"centreline"`, `"srtm30m"`) keeps its spelling, while retuning a default to another value
(`PaperStyle.paper_hex`, the `NibStyle.label_*` inks, another brush id for
`NibStyle.label_brush`) needs no ADR.

### Tokens

The rule, which is the contract: a token is a string a caller passes to choose one of the
behaviours a public name offers (a free value such as a colour, a text or a contact
string is not one), as an argument of a public name or as a key or a value inside a dict
that is such an argument or a field of a class named in some `__all__`, or an enumerated
string that a public name or a public field returns; every token is part of the public
surface. A dict whose keys mirror a class's fields (a theme TOML table, the input of
`Style.model_validate`) is read as that class's fields, so a string inside it is a token
only where this rule reaches it through a field of a class named in some `__all__`.

A field's name, and so a theme TOML key that mirrors a field, is a member and follows the
member rule above, not this one; a string a provider fetches (an OSM tag key or value, an
elevation payload field) is data, not a token.

The tokens measured when this ADR was written are examples, not a closed list; among
them:

- the four ink keys `"map"`, `"route"`, `"water"` and `"in_water"` on `Setting.ink` and
  `Mark.ink` (which also take a free `#rrggbb` colour, not a token);
- `Mark.role`'s six roles (`"glyph"`, `"leader"`, `"span"`, `"tick"`, `"underline"`,
  `"pin"`);
- the two routes `"centreline"` and `"outline"` of `FaceStyle.label_route` (and of
  `Hand`'s `route`);
- `Setting.align`'s three edges (`"start"`, `"middle"`, `"end"`);
- the 112 brush sheet ids (`RIV1-a`, `MAJ6-e`, ...) that `brush_from_id`,
  `NibStyle.label_brush` and `NibStyle.label_leader_brush` take, and the six
  `BrushStyle.brush_overrides` keys `brush_from_id`'s `override` names;
- the 15 parameter keys of those overrides' entries that `brush_from_id` reads
  (`jitter_px`, `press_cell_px`, `wobble_px`, `darkness`, `bristles`, `gap`, `dry`, `thr`,
  `texture`, `press`, `load`, `pool`, `bleed`, `lift`, `solid`);
- the two `aux` keys `"res"` and `"tooth"` of `ink_density` and `stamp`;
- the seven class keys (`major`, `medium`, `minor`, `coast`, `road_major`, `lane`, `track`)
  of `BrushStyle.brushes`, `brush_width_px` and `river_curve`, and the 15 land-class keys
  of `PaperStyle.pigment_transparency`;
- the 15 pigment keys a caller subscripts `PIGMENTS` and `TRANSPARENCY` with;
- `OpenTopoData`'s `dataset` (`"srtm30m"` by default, which enters the provider's `id` and
  so the cache key).

Each is public behaviour from this ADR on. The default ink `"map"`, which `nib_plate`
resolves to `NibStyle.label_ink`, is the one a deferred triage row would rename:
`letters-map-ink-key` will carry its own ADR and stop for the maintainer.

## Consequences

- Tutorials and `examples/` import only public names, and
  `tests/architecture/test_examples.py` enforces it; `tests/unit/test_public_api.py` pins
  the top-level `__all__` and each layer package's.
- A new public name, or a change to one, to a public member or to a token this rule makes
  public, still needs a new ADR.
- A module-level name in no `__all__` (the triage's renamed underscore names among them),
  and a member of a class in no `__all__` (so `RouteInk.effect`, `RouteInk.casing` and
  `Label.as_dict`), may move, be renamed or be deleted freely.
- None of these is a token change: the `[route_inks.*.effect]` theme tables are read as
  `RouteInk`'s fields, and `RouteInk` is in no `__all__`, so neither the table header nor
  the entries inside `RouteInk.effect` are tokens; `Label.as_dict` is no public name, so
  its keys are no token; and the `maps-osm-elements-tunnel-no` fix changes how `fetch`
  reads OSM tags, which are provider data. None of the three needs an ADR, while a rename
  of the ink key `"map"`, which a caller passes as `Setting.ink` and `Mark.ink` returns,
  does.
