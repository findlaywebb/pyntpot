# 006 — One public surface

GitHub issues: [#168](https://github.com/findlaywebb/pyntpot/issues/168) (every type in a
public signature is public),
[#73](https://github.com/findlaywebb/pyntpot/issues/73) (public wash options),
[#78](https://github.com/findlaywebb/pyntpot/issues/78) (public provider protocols),
[#169](https://github.com/findlaywebb/pyntpot/issues/169) (field docs that render),
[#164](https://github.com/findlaywebb/pyntpot/issues/164) (public functions shadow their
modules) and [#161](https://github.com/findlaywebb/pyntpot/issues/161)
(`Annotations.roads` accepted and ignored).

Branch: `feat/006-one-public-surface`. Decision record: ADR 0068
(`docs/decisions/0068-one-public-surface.md`).

## Problem

The public surface is the four `__all__` lists (ADR 0026), but their signatures name 32
objects no list exports, and those name 8 more. A caller cannot import the
`Landmark` an `Annotations` holds, the `WashOptions` `wash` takes, or the `Features`
protocol `fetch` expects. The reference shows each as a dead name. Four public functions
shadow their own modules, so the package attribute is the function and the reference
needs deep-path directives. About 200 public fields are documented in `#:` comments that
the reference never renders. `Annotations.roads` is accepted and read by nothing.

## Acceptance criteria

The rule and its gates:

- [ ] ADR 0068 is written, indexed in `docs/decisions/README.md`, and amends 0004, 0005,
      0007, 0026 and 0027.
- [ ] `tests/architecture/test_public_signatures.py` fails when any name reached from a
      public signature (parameters, returns, public fields and properties, base
      classes, public alias values, protocol members, `Raises:` entries) is neither in a
      layer package's `__all__` nor on its exact-name allowlist. It reads the code with
      griffe and follows unions, `Optional`, generics, `Annotated` metadata, quoted
      forward references, `TYPE_CHECKING` imports and re-exports. Its self-tests prove
      each of those on a synthetic package written to `tmp_path`. It passes on the branch.
- [ ] `tests/architecture/test_field_docs.py` fails when a public class lacks an
      `Attributes:` entry with text for a public field, lists entries out of field
      order, lists an entry naming nothing on the class, or keeps a `#:` comment in its
      body. It also fails when a public module attribute has no attribute docstring. It
      passes on the branch.
- [ ] `tests/architecture/test_site.py` fails when any package under `src/pyntpot` binds
      a name in its `__init__.py` equal to one of its submodules or sub-packages, and when
      a reference name directive is not exactly `::: pyntpot.<layer>.<name>`. It passes on
      the branch.
- [ ] `griffelib` is in the `dev` dependency group; `uv.lock` resolves it to the same
      version the `docs` group uses.

The surface:

- [ ] `pyntpot.ink.__all__` adds `WashOptions`, `Flow`, `Blooms`, `WashStyle`,
      `separated`, `fluid_modulate`, `Point` and `Box`; `pyntpot.letters.__all__` adds
      `Align`; `pyntpot.maps.__all__` adds the 31 names in ADR 0068's table.
      `pyntpot.__all__` is unchanged. `tests/unit/test_public_api.py` pins all four lists.
- [ ] `Pt` is `Point` everywhere; `Box` has one definition (`ink.polyline`); `Anchor` is
      gone in favour of `Align`; `maps.painter.job` defines no `Pt` of its own.
- [ ] `Flow` and `Blooms` are frozen keyword-only dataclasses with the fields ADR 0068
      names; `wash` and `bloom` read them by name.
- [ ] `LetteringPolicy` is `LetteringStyle` and `RouteInk` is `RouteInkStyle`; every
      style group and `WashOptions` is `@dataclass(frozen=True, kw_only=True)`.
      `Style.digest()`, `base_digest()` and `lettering_digest()` pinned literals do not
      move.
- [ ] A test proves `OverpassFeatures` satisfies `Features` and `OpenTopoData` satisfies
      `Elevation`, by typed assignment that `ty check` verifies.
- [ ] `pyntpot.ink.stamp`, `pyntpot.ink.wash`, `pyntpot.maps.compose` and
      `pyntpot.maps.vector_layers` are no longer modules. Each attribute is the public
      function, and `import pyntpot.ink.washing as w; w.WashOptions` works. The modules
      are `ink.stamping`, `ink.washing`, `maps.compose_steps` and
      `maps.vector_layer_build`.
- [ ] Every reference directive is `::: pyntpot.<layer>.<name>`, every public name has
      one, and `uv run --group docs mkdocs build --strict` passes.

Field docs:

- [ ] Every public class's fields are documented in an `Attributes:` section and every
      public module attribute has an attribute docstring, as `test_field_docs.py`
      checks. No source file exceeds 400 lines. `ink/brush.py` is split
      (`ink/brush_sheet.py` takes the brush sheet catalogue) and
      `maps/lettering/label.py` is split (`maps/lettering/label_sizing.py` takes the
      sizing and wrapping rules) before any field text is added.

`Annotations.roads`:

- [ ] A road named in `Annotations.roads` (by number or OSM name, case-folded) that the
      basemap draws is lettered along its tarmac, whether or not the track was on it and
      whatever `label_ground` says. Named roads replace the picked roads. A name that
      matches no drawn road is logged at INFO. Tested on synthetic lines (`A591`, `A66`,
      `A9`) and through `letter` on the Lynmouth fixture: `roads=("B3234",)` letters
      `B3234` and not the `A39` the picker would choose, and `roads=("A591",)` letters
      no road and logs `A591`.
- [ ] With `roads` empty, output is byte-identical: every golden, plate hash and docs
      image passes unchanged on the pinning machine (`uv run pytest -n auto --dist
      loadgroup`).

Process:

- [ ] Mutation testing runs on the changed `ink` and `letters` functions; every survivor
      is killed by a focused test or named as equivalent, with the reason, in the PR
      description.
- [ ] The notes for #168, #73, #78, #169, #164 and #161 are deleted; notes that cite
      them or the old module paths are updated; the PR body says `Closes #168`,
      `Closes #73`, `Closes #78`, `Closes #169`, `Closes #164`, `Closes #161`.
- [ ] The prose under `docs/` that session A owns is untouched, except the path-only
      edits plan.md lists.

## Changelog

PR title:

```
feat(ink)!: one public surface: every type a public signature names is exported
```

Under "Changelog" in the PR description:

```
feat(maps): export every type a maps signature names: Landmark, SpanRequest, Card, Credit, Manifest, DarkGrid, BoundingBox, Layers, River, Road, ElevationPatch, Line, Projection, Label, Span, MAX_NOTES, MAX_NOTE_CHARS, VectorArea, VectorLine, HillshadeBand, HillshadeImage and ElevationGrid
feat(maps): export the seven map style groups, keyword-only, with LetteringPolicy renamed LetteringStyle and RouteInk renamed RouteInkStyle
feat(maps): export the Features and Elevation provider protocols for a caller's own data source
feat(ink): export WashOptions, Flow, Blooms, WashStyle, separated, fluid_modulate, Point and Box
feat(letters): export Align
feat(ink)!: PaperStyle and BrushStyle are keyword-only
feat(letters)!: FaceStyle, HandStyle and NibStyle are keyword-only
feat(maps): Annotations.roads letters the roads it names
fix(maps): public functions no longer shadow their modules, now ink.stamping, ink.washing, maps.compose_steps and maps.vector_layer_build
docs(ink): every public field and constant has text in the API reference
```

## Out of scope, filed separately

Each gets a note and a GitHub issue (CLAUDE.md, "Issues and features"), not part of this
plan:

- `docs-how-to-write-a-provider.md`: a how-to and an offline example that feeds `fetch`
  from a local file through `Features` and `Elevation`. Check #173
  (`docs-missing-how-tos.md`) first and add it there if it already lists one.
- `maps-clip-is-a-box.md`: four private `Clip` aliases (`maps.layers`,
  `maps.relief_layers`, `maps.cover`, `maps.osm_elements`) are the same concept as
  `Box`. One name per concept says they should be `Box`.
- `docs-reference-sections.md`: group each API reference page into sections that mirror
  the package docstring's task groups. `pyntpot.maps` grows from 21 to 52 names.
- `maps-lettering-frozen-records.md`: `Label` and `Span` are public and mutable, because
  the placer fills them in. Return frozen copies from `letter`.
- `maps-typed-features-payload.md`: a `Features` provider must return Overpass JSON text.
  A typed payload would let a non-OSM source plug in without faking Overpass.
- `docs-defaults-render-as-values.md`: a parameter default that names a private
  constant (`DEFAULT_ENDPOINTS`, `MARGIN_M`, `TIER_LANDMARK`) renders as a bare name. Show
  the value, or document the constant where it is used.
- `tests-public-surface-snapshot.md`: a pinned, generated snapshot of every public
  signature, so any surface change shows in review as a diff.

Also not in this PR: the prose under `docs/` that the changes make stale. Session A owns
it (plan.md, "Handed to session A"). Wording on the style-fields page also stays with
session A.
