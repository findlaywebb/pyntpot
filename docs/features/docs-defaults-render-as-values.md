# Parameter defaults could render as values in the reference

GitHub issue: [#TBD](https://github.com/findlaywebb/pyntpot/issues)

**What exists today.** The reference site renders a parameter default as written in the
source. Where the default names a private constant, the reader sees a bare name with no
value and no entry to follow: `OverpassFeatures(endpoints=DEFAULT_ENDPOINTS)`,
`FetchMargins.features_m = MARGIN_M` and `Label.tier = TIER_LANDMARK`.

**What the feature would add.** A reader sees what a default is: either the value, or a
documented constant the reference links to.

**Possible shape.** Document each such constant where it is defined and export it, or
render the value through the docs handler's options, or write the literal in the
signature. Check every public default, not only these three.

**Related.** `docs-reference-sections.md`.
