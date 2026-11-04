# 0068 — One public surface (amends 0004, 0005, 0007, 0026 and 0027)

Status: accepted

## Context

ADR 0026 made the public surface the four `__all__` lists and nothing else, but left the
names those lists' signatures reach undecided. Read with griffe, the way the reference
site reads it, the public functions, methods and fields name 32 objects that no `__all__`
exports, and those objects' own signatures name 8 more. Some are classes a caller must
build (`Landmark`, `SpanRequest`, `WashOptions`). Some are protocols a caller must satisfy
(`Features`, `Elevation`). Some are values a caller reads back (`Card`, `Credit`,
`Manifest`, `Label`). Some are type aliases (`Pt`, `Box`, `Line`, `Align`, `Anchor`,
`Flow`, `Blooms`) and two are constants (`MAX_NOTES`, `MAX_NOTE_CHARS`). Each one shows as a dead name in the rendered reference, and 0026's
"Members" paragraph called the style groups and `Label` private while the upstream SVG
page reads them through attributes 0007 fixes. That is a contract nobody can keep.

Four public functions also shadow the modules they share a name with (`pyntpot.ink.stamp`,
`pyntpot.ink.wash`, `pyntpot.maps.compose`, `pyntpot.maps.vector_layers`). The package
attribute is the function, so `import pyntpot.ink.wash as w; w.WashOptions` fails, and
griffe resolves the reference page's `::: pyntpot.ink.wash` to the module. The reference
pages carry deep-path directives to work round it.

The fields of the public style groups, `Brush`, `Sheet` and the rest are documented in
`#:` and trailing comments. griffe reads neither, so the reference shows the class prose
and no text for about 340 fields.

`Annotations.roads` is validated and then read by nothing.

## Decision

### The rule

Every name a public object's signature reaches is itself public. It is exported from
the `__all__` of the layer package that defines it, or it is on a short explicit allowlist
of standard-library and third-party names. "Reaches" means:

- the parameter and return annotations of a public function, and of a public method of
  a public class (any method not starting with `_`, plus `__init__` and `__call__`, the
  dataclass `__init__` griffe synthesises included);
- the annotation of a public field, attribute or property;
- the base classes of a public class;
- the value of a public type alias;
- the members of a public protocol;
- the exception types a public docstring's `Raises:` section names.

The rule reads annotations through every wrapper: unions, `Optional`, generics,
`Annotated` (its metadata included, so a constant in `pydantic.Field(max_length=...)`
counts), quoted forward references, and imports guarded by `TYPE_CHECKING`. It follows
a re-export to the defining object.

Parameter default values are outside the rule. 0026 already treats a default as
behaviour, not a name. A default such as `endpoints=DEFAULT_ENDPOINTS` renders as text
and binds nothing.

A module path is not part of the API. A public name is reached through its layer
package (`from pyntpot.maps import Landmark`). Its defining module may move without an
ADR, and the reference renders every name at `pyntpot.<layer>.<name>`.

### The names that become public

No promoted name is top-level: `pyntpot.__all__` stays 0007's façade (0026). Every
importer is repointed in the same change, with no shim and no second name left behind
(0026's precedent).

| Public name | Layer package | Defining module | Renamed or changed | Reached from |
| --- | --- | --- | --- | --- |
| `WashOptions` | `pyntpot.ink` | `ink.washing` | keyword-only | `wash(options)` (#73) |
| `Flow` | `pyntpot.ink` | `ink.washing` | was a tuple alias, now a frozen keyword-only dataclass `Flow(exp, ref_frac, frac)` | `WashOptions.flow` |
| `Blooms` | `pyntpot.ink` | `ink.bloom` | was a tuple alias, now a frozen keyword-only dataclass `Blooms(seed, count, radius_frac, lift, warp)` | `WashOptions.blooms` |
| `WashStyle` | `pyntpot.ink` | `ink.style` | keyword-only | `Style.wash`, `separated`, `fluid_modulate` |
| `separated` | `pyntpot.ink` | `ink.washing` | | #73 |
| `fluid_modulate` | `pyntpot.ink` | `ink.washing` | | #73 |
| `Point` | `pyntpot.ink` | `ink.polyline` | renamed from `Pt`; `maps.painter.job`'s copy deleted | `Hand.stroke`, `Mark.pts`, `Setting.anchor`, `Label`, `Span` |
| `Box` | `pyntpot.ink` | `ink.polyline` | one definition replacing three identical ones in `maps.lettering.label`, `maps.vector_layers` and `maps.card_geometry` | `Label.box`, `VectorLayers.bounds`, `VectorLayers.clip` |
| `Align` | `pyntpot.letters` | `letters.setting` | `maps.lettering.label.Anchor`, the same `Literal`, is deleted in its favour | `Setting.align`, `Label.anchor` |
| `Features`, `Elevation` | `pyntpot.maps` | `maps.providers.base` | | `fetch`, `Cache.key`, `Cache.ensure` (#78) |
| `ElevationGrid` | `pyntpot.maps` | `maps.providers.base` | | `Elevation.grid`, `OpenTopoData.grid` |
| `BoundingBox` | `pyntpot.maps` | `maps.track` | | `Track.bounding_box`, the provider methods |
| `Credit` | `pyntpot.maps` | `maps.credit` | | `Basemap.credits`, the providers' `credit` |
| `Card` | `pyntpot.maps` | `maps.card` | | `Basemap.card`, `Plates.card` |
| `Manifest`, `DarkGrid` | `pyntpot.maps` | `maps.plates` | | `Plates.manifest`, `Manifest.dark` |
| `Layers`, `River`, `Road`, `ElevationPatch`, `Line` | `pyntpot.maps` | `maps.basemap` | | `Basemap.layers`, `Basemap.track` |
| `Projection` | `pyntpot.maps` | `maps.projection` | | `Basemap.projection` |
| `Label`, `Span` | `pyntpot.maps` | `maps.lettering.label` | | `Lettering.labels`, `Lettering.spans` |
| `Landmark`, `SpanRequest` | `pyntpot.maps` | `maps.annotations` | | `Annotations.landmarks`, `Annotations.spans` |
| `MAX_NOTES`, `MAX_NOTE_CHARS` | `pyntpot.maps` | `maps.annotations` | | `Annotations.notes`, `JournalNote.text` |
| `VectorArea`, `VectorLine`, `HillshadeBand`, `HillshadeImage` | `pyntpot.maps` | `maps.vector_layer_build` | | `VectorLayers`' fields |
| `CardStyle`, `RibbonStyle`, `CoverStyle`, `RouteStyle`, `BasemapStyle` | `pyntpot.maps` | `maps.style_groups` | keyword-only | `Style`'s fields |
| `LetteringStyle` | `pyntpot.maps` | `maps.style_groups` | renamed from `LetteringPolicy`; keyword-only | `Style.lettering` |
| `RouteInkStyle` | `pyntpot.maps` | `maps.style_groups` | renamed from `RouteInk`; keyword-only | `Style.route_ink` |

That is 8 names in `pyntpot.ink`, 1 in `pyntpot.letters` and 31 in `pyntpot.maps`.

All the style groups are exported: `WashStyle` from `pyntpot.ink` and the seven map
groups from `pyntpot.maps`. So "`X`, from `pyntpot.Y`" on the style-fields page is true
for every group. Two groups are renamed because a public name says what it is and every
other group is `<Group>Style` (the naming convention below). Neither was public, so
neither rename breaks a caller. Theme TOML keys are `Style`'s field names, which do not
change, and the digests hash fields by those names, so no digest moves.

`Flow` and `Blooms` become dataclasses because a public five-number positional tuple is
not a usable contract. The fields carry the names `flow_edge` and `bloom` already give
those numbers, and the values the painter passes are the same, so no pixel moves.

`Pt` is renamed on promotion, as 0026 renamed `Layer` and `plate`: a public name says
what it is. `Box` and `Align` each had duplicate definitions under another name, and one
name per concept keeps one.

### No opaque types

No type stays opaque. Every candidate (`Layers`, `Projection`, `Label`, `Span`) is held
by an attribute 0007 fixes because the upstream SVG page reads it, so none can leave a
public signature. The rule puts them in `__all__`, and their members become public with
them under 0026's member rule.

`Label` and `Span` become keyword-only and stay mutable, because the placer fills them in:
it writes their fields in place at about thirty sites in `placement.py`,
`placement_flat.py`, `placement_leaders.py` and `spans.py`. Rewriting the placer to build
new records is behaviour work, outside a change to the surface. A `Label` or `Span` that
`letter` hands back is a finished value, and **writing to one is unsupported**. So
returning frozen records later is not a breaking change, and their fields are read-only
for a caller from now on. Which of their fields stay is settled with the frozen records
(see "Records the pipeline returns").

### Members (amends 0026)

0026's paragraph "A class reachable only through an attribute of a public object and
named in no `__all__` is not itself a public name ..." is superseded. Under the rule no
such class exists. The style groups, `Label`, `Span` and every name in the table are
public names, and their fields and methods are public members. Changing one needs an
ADR. The Consequences bullet that let `Label.as_dict` and the route ink's members change
freely is superseded the same way.

### Module renames (#164)

No name bound in a package's `__init__.py` may equal a module or sub-package of that
package. The four modules that broke this are renamed. The public names do not change.

| Old module | New module | Holds |
| --- | --- | --- |
| `pyntpot.ink.stamp` | `pyntpot.ink.stamping` | `stamp` and its helpers |
| `pyntpot.ink.wash` | `pyntpot.ink.washing` | `wash`, `WashOptions`, `Flow`, `flow_edge`, `separated`, `fluid_modulate` |
| `pyntpot.maps.compose` | `pyntpot.maps.compose_steps` | `painted_map`, `route`, `paste_labels` (`compose` stays in `maps.pipeline`) |
| `pyntpot.maps.vector_layers` | `pyntpot.maps.vector_layer_build` | `vector_layers`, `VectorLayers` and its parts |

0027's "Defining module" column for `vector_layers` and `VectorLayers` now reads
`maps.vector_layer_build`.

### Wash knobs (#73)

`WashOptions` is the one home for the settings of a single `wash` call. `wash` keeps the
signature `wash(cover, sheet, base, pool, options=None)` and takes no new parameter. A new
per-wash setting is a new `WashOptions` field whose default leaves the wash as it was.

`separated` and `fluid_modulate` are not `WashOptions` fields. They act on what washes
produce: `separated` turns one wash's density into one or two `PigmentLayer`s, and
`fluid_modulate` changes a whole stack of layers at once. Both read their settings from
`WashStyle`, the style group, because those settings belong to a plate, not to one wash.
They stay in `ink.washing` beside `wash` and are exported from `pyntpot.ink` under their
current names, which describe what they return and do.

### Extension seams

- **Providers.** `Features` and `Elevation` are the documented way to feed `fetch` and
  `Cache` from another source (amends 0004 and 0007's Boundary, which kept them
  unexported). A features provider offers `id`, `credit`, `features(box)` and
  `landcover(box)` and returns Overpass JSON text. pyntpot reads no other features
  format. An elevation provider offers `id`, `credit` and `grid(box, n)` returning an
  `ElevationGrid`. `id` enters the fetch cache key (0017), so it must change when the
  provider's output changes. A provider signals failure with `ProviderError` or
  `ProviderBudgetExceededError`, which `fetch` and `Cache.ensure` wrap (0028, 0029). The
  protocols are structural and not `@runtime_checkable`: ty checks a provider statically,
  and a runtime check would test only that the attributes exist.
- **Style groups.** Every style group is a frozen, keyword-only dataclass
  (`@dataclass(frozen=True, kw_only=True)`). A variant is made with
  `dataclasses.replace(group, field=value)`, and a style with one group changed with
  `style.model_copy(update={"wash": replace(style.wash, ...)})`. Because construction is
  by keyword, adding a field with a default, or reordering fields, breaks no caller.
  `NibGroups` is a bundle of five groups, not a style group, and keeps positional
  construction.
- **Option records.** `WashOptions`, `Flow` and `Blooms` are frozen and keyword-only for
  the same reason.
- **Naming convention.** A style group's class is `<Group>Style`. The settings record a
  public function takes as an argument is `<Call>Options` (`wash(..., options:
  WashOptions)`). A record nested inside one is named for what it sets: `Flow` (the flow
  rim) and `Blooms` (`bloom` is not public, so no `BloomOptions` is implied). The
  glossary's "style group" row records the convention.
- **Field names of the option records.** `Flow`'s fields `exp`, `ref_frac` and `frac`
  are the suffixes of `WashStyle.flow_rim_exp`, `flow_rim_ref_frac` and `flow_rim_frac`
  and the names of `flow_edge`'s parameters. `Blooms`' `radius_frac`, `lift` and `warp`
  are the suffixes of `WashStyle.bloom_radius_frac`, `bloom_lift` and `bloom_warp`, with
  `seed` and `count`. The `WashStyle` names are theme keys and digest inputs, so the
  records follow them, and a reader maps one onto the other by name.
- **Records the pipeline returns.** Every dataclass record this ADR makes public, except
  `Label` and `Span`, is `@dataclass(frozen=True, kw_only=True)`: `Card`, `Credit`, `Manifest`, `DarkGrid`,
  `Layers`, `River`, `Road`, `ElevationPatch`, `ElevationGrid`, `VectorArea`,
  `VectorLine`, `HillshadeBand`, `HillshadeImage` and `Projection` (which was mutable;
  `track_projection` now builds it without the origin shift, projects through it, and
  replaces it once with the shift, so no `Projection` is assigned to after it is
  built). Publishing a positional or mutable record would
  freeze its field order or its mutability into the contract. For these, adding a field
  with a default is additive wherever it goes. `Label` and `Span` are keyword-only and
  mutable (above). `BoundingBox` is a `NamedTuple`: it is a tuple, and its field order is
  its contract. `Basemap`, `Plates`, `Lettering` and `VectorLayers` were public before
  this ADR and keep their construction; a field added to one goes at the end. For every
  record, removing or renaming a field needs an ADR, with one exception. The fields of
  `Label` and `Span` that are the placer's working state (`Label.window`, `flat`,
  `anchors`, `mark`, `span_range`, `in_water`, `tx`, `ty` and `lift`; `Span.rank`,
  `offset_px` and `side`) may be removed or renamed without an ADR until the frozen
  records land (`maps-lettering-frozen-records`, filed with this ADR). That follow-up
  separates the record `letter` returns from the placer's working state and settles
  which fields stay; once it lands, the rule holds for every field.

### Field documentation (#169)

Every public field is documented in its class docstring's Google-style `Attributes:`
section. A public field is a field or annotated attribute, not starting with `_`, of a
class named in some `__all__`; pydantic's `model_config` and `ClassVar`s are not fields.
An attribute assigned in `__init__` is a field. There is one entry per field, in field
order (griffe's member order: the class body, then `__init__` assignments, each in source
order), each with non-empty text, and no entry names something the class does not have.
A property is documented by its own docstring and is not listed. A `#:` block shared by
several fields is split, one entry each. Neither a `#:` comment nor a trailing comment is
field documentation, and no comment stays in a public class body outside its methods,
except a tool pragma (`# type:`, `# noqa`, `# pragma`).

This is the convention `Basemap`, `Plates` and `Annotations` already use. griffe parses
the section and fills each entry's type from the field's annotation. mkdocstrings renders
it as the class's Attributes table. `help()` and an editor's class hover show the same
text. Attribute docstrings under each field were rejected: griffe renders them as
separate members, so a class would have two homes for field text, and the existing
convention would split.

A public module attribute (a constant, a type alias, `__version__`) is documented by an
attribute docstring, a string literal on the line after the assignment. Each one is
rendered by its own directive, and griffe attaches no module `Attributes:` entry to the
object. `mkdocs.yml` needs no new option.

### `Annotations.roads` (#161)

`roads` does what its name says. When a caller names roads, the roads lettered are
exactly the named ones the basemap draws, each set along its own tarmac. Every road the
basemap draws can be named, whatever its class: `major`, `minor` (the lanes and the path
band alike), and a numbered road whose pieces carry no name. A road matches when its
number (`road_ref`) or any of its pieces' OSM names equals a listed string, compared with
`str.casefold`. It is lettered by its number when it has one, as a picked road is, even
when the caller named it by its street name. A road listed twice, or matched by number
and by name, is lettered once, at its first place in the list; labels come in the
caller's order. A named road is lettered whether or not the track was on it, and the road
budget does not apply. The shortest run a number can be set along still applies: a named
road too short on this card is logged at INFO and not lettered. Named roads replace the
roads the lettering would pick itself, the way `Annotations.landmarks` replaces the
landmark heuristic, and as there, when none of them can be set the picked roads come back.
Caller annotations are not switched off by the theme, so named roads are lettered even
when `LetteringStyle.label_ground` is false.

A listed name that matches no road the basemap draws is an error: `letter` raises
`ValueError` naming every such name. A caller annotation that cannot be honoured is a
caller error, as a journal note off the card already is, and lettering nothing in silence
is the defect this section fixes. The check runs before any name is placed, so no nib
plate is written. When the style letters nothing, `letter` returns before the check.

A road the basemap does not draw cannot be lettered: `fetch` keeps minor roads by the
theme's `[basemap] pick_roads`, not by annotations, so a caller names such a road there
too. An empty `roads` (the default, and
the value every golden uses) takes the unchanged code path, so no pinned image moves.
The golden suite is the proof. Removing the field was rejected: wiring it costs one
function, and the how-to on picking roads (#173) needs it.

### The gates

- `tests/architecture/test_public_signatures.py`: the rule above, read with griffe.
  `griffelib` joins the `dev` dependency group so the test reads the code the same way the
  reference renders it, statically, through `TYPE_CHECKING` imports and quoted
  annotations. It walks transitively: every object a public signature reaches is itself
  walked by the same rule. A type alias, whose value is walked, is a module attribute
  annotated `TypeAlias`, a PEP 695 `type` statement, or an unannotated value that is a
  subscript, a `|` union or a name resolving to a class; any other constant contributes
  only its annotation. A reached `pyntpot` name the test cannot resolve fails it. A name
  counts as public only when the layer that defines it exports it; the façade's
  re-exports in `pyntpot.__all__` neither make a name public nor count against it. A
  string left in an annotation outside `Literal[...]`, or a `Raises:` entry that does not
  parse to a name, fails the test rather than being skipped. The allowlist is exact
  names, not module prefixes, so a new third-party type in a signature is a decision
  someone makes on purpose.
- `tests/architecture/test_field_docs.py`: the field documentation rule above.
- `tests/architecture/test_site.py` gains two checks: no package binds a name equal to one
  of its submodules, and every name directive is exactly `::: pyntpot.<layer>.<name>`.

## Consequences

- The reference renders every public name and field with text, and no public signature
  names a dead reference. The gates keep it so.
- **Breaking:** the public style groups that were already public (`PaperStyle`,
  `BrushStyle`, `FaceStyle`, `HandStyle`, `NibStyle`) are now keyword-only. A caller
  that built one positionally gets a `TypeError`. Nothing in `examples/` does.
- Importing from a private module path (`from pyntpot.ink.wash import WashOptions`)
  fails after the renames. Those paths were never public. The changelog names the new
  homes.
- Every name in the table, its fields and its methods are public. Changing one needs an
  ADR. Retuning a default still does not (0026).
- `Annotations.roads` changes the card only for a caller that sets it.
- A how-to that writes a provider over a local file is not part of this ADR (it is filed
  separately). The protocols and their reference entries are.
