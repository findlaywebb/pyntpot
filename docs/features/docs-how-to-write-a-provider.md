# A how-to could show how to write a data provider

GitHub issue: [#188](https://github.com/findlaywebb/pyntpot/issues/188)

**What exists today.** `Features` and `Elevation`, the provider protocols, are public from
`pyntpot.maps` (ADR 0068). The shipped `OverpassFeatures` and `OpenTopoData` meet them,
and so do the test suite's `FixtureFeatures` and `FixtureElevation`
(`tests/support/providers.py`), which read the committed fixture files.
`docs/how-to/self-host-providers.md` points the two shipped providers at another server; no
guide or example writes a provider of one's own.
`docs-missing-how-tos.md` (#173) does not list this task.

**What the feature would add.** A how-to, and an offline example beside it, that feeds
`fetch` from a local file through a small `Features` and `Elevation` of the reader's own:
the `id` the cache keys on, the `credit` the card prints, and the payload each method
returns.

**Possible shape.** The example reads a saved Overpass response and a saved elevation grid
for one of the fixture boxes, so it runs with no network and paints the same map as the
fixture tests. The guide says what `id` must keep stable and what each method returns,
and links the protocols' reference entries.

**Related.** `docs-missing-how-tos.md` (#173); `maps-typed-features-payload.md`, which would
change what a `Features` returns; `maps-fetch-hands-back-the-plates-dir.md` (#74).
