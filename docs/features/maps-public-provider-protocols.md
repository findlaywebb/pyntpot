# A caller could write their own data provider

**What exists today.** The provider protocols `Features` and `Elevation` are
settled design, but they are not in `pyntpot.maps.__all__`. The public
providers are `OverpassFeatures` and `OpenTopoData`, each of which can point at
a self-hosted server.

**What the feature would add.** `Features` and `Elevation` become public, so a
caller can feed the map pipeline from another source (a local OSM extract, a
national elevation model) with their own class.

**Why it is not a defect.** Self-hosting the two shipped services is supported.
At 0.1 the self-host guide covers those services only (maintainer, 2026-10-23,
P7 research default J).

**Possible shape.** Add both protocols to `pyntpot.maps.__all__` with an ADR
amending 0007 and 0026, document the methods a provider must offer and the
errors it raises (ADR 0028, 0029), and add a how-to guide with a small worked
provider over a local file.
