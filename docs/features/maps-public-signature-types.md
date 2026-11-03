# Every type in a public signature could be public

GitHub issue: [#168](https://github.com/findlaywebb/pyntpot/issues/168)

**What exists today.** The four `__all__` lists (`pyntpot`, `pyntpot.ink`, `pyntpot.letters`,
`pyntpot.maps`) export 49 names. Their signatures and attributes name 34 types and values that
are in none of them:

- 26 classes and protocols: `BasemapStyle`, `BoundingBox`, `Card`, `CardStyle`,
  `CoverStyle`, `Credit`, `Elevation`, `ElevationGrid`, `Features`, `HillshadeBand`,
  `HillshadeImage`, `Label`, `Landmark`, `Layers`, `LetteringPolicy`, `Manifest`,
  `Projection`, `RibbonStyle`, `RouteInk`, `RouteStyle`, `Span`, `SpanRequest`, `VectorArea`,
  `VectorLine`, `WashOptions`, `WashStyle`;
- 4 type aliases: `Align`, `Box`, `Line`, `Pt`;
- 4 constants the rendered pages name: `DEFAULT_ENDPOINTS`, `PUBLIC`, `MAX_NOTES`,
  `MAX_NOTE_CHARS`.

Some a caller has to build or read: `Annotations.landmarks` holds `Landmark`s and
`Annotations.spans` holds `SpanRequest`s, whose keys are documented only on those private
classes; `Basemap.card`, `Basemap.credits` (walked by the how-to `credit-the-map-data.md`)
and `Plates.manifest`; the eight `Style` groups. The API pages link nowhere for any of them,
and a caller cannot import them to annotate their own code. No test catches a new one.

**What the feature would add.** For each type, a decision: export it, or change the public
signature so it stops naming it. Then an architecture test that every type a public
signature or public attribute names is public or third-party, so the gap cannot reopen.

**Possible shape.** A suggestion: export `Landmark`, `SpanRequest`, `Credit`, `Card`,
`BoundingBox`, `Manifest` and the style groups from their layer's `__all__`; keep the
painter's internals (`Layers`, `Projection`, `Label`, `Span`) behind a narrower attribute
type or document them as opaque. The test belongs in `tests/architecture/`, reading the
annotations of everything in the four `__all__` lists. Widening the public API is an ADR
(after `0026-widen-the-public-api.md`); no pixels move, and the reference pages gain entries.

**Related.** Two of these types already have their own issues, which stay separate:
`WashOptions` is `ink-public-wash-options` (#73) and `Features` and `Elevation` are
`maps-public-provider-protocols` (#78). This note covers the other 31 and the test.
