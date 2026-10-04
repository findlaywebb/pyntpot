# 0004 — Provider protocols, usage limits and the fetch cache key

Status: accepted

## Context

The ported engine fetches OpenStreetMap features and land cover from Overpass and an
elevation grid from OpenTopoData through module functions that hard-code the endpoints,
send no contact details, pause only between elevation calls, and cache under a key the
caller names after the activity. A caller cannot swap in another source, a test cannot
fetch without the network, and nothing bounds how many queries one run sends to a
volunteer-run public service. The two services publish their limits: Overpass asks for
one request at a time, back-off on 429 and bounded responses (one map needs two queries,
so regular use stays under 100 a day); the OpenTopoData public API takes 100 points a
call, one call a second and 1000 calls a day.

## Decision

- **Two protocols.** `Features` (`id`, `credit`, `features(box)`, `landcover(box)`,
  returning Overpass JSON text) and `Elevation` (`id`, `credit`, `grid(box, n)`,
  returning an `ElevationGrid`) live in `pyntpot.maps.providers.base`. They are the
  sanctioned exception to the rule of three: the provider seam is settled design, and
  the fixture providers in the tests are already a second implementation of each.
- **Errors.** `ProviderError(RuntimeError)` when a provider cannot answer;
  `ProviderBudgetExceededError(ProviderError)`, raised by both shipped providers before the
  call that would pass their budget, so no request is sent.
- **A required contact.** Each shipped provider takes a `contact` string as a required
  constructor argument and sends it in its User-Agent; an empty contact is a
  `ValueError`.
- **Published limits enforced by default.** Overpass: one request at a time, back-off on
  429 before trying the next endpoint, at most 100 queries per provider instance, and a
  `[maxsize:N]` header bounding each response. OpenTopoData: 100 points a call, one call
  a second by a fixed pause (no clock read), at most 1000 calls per provider instance.
- **Per instance, not per process.** A budget is a counter on the provider instance.
  There is no global state, nothing is shared between tests, and a caller who builds two
  instances has chosen to.
- **Credit per provider.** Each provider carries the `Credit` its data is owed; the map
  draws the short lines.
- **The fetch cache key** is the first 16 hex characters of the `sha256` of the
  canonical JSON of the bounding box, the margin and both provider ids. It never uses an
  activity id, and the cache directory is always an explicit argument.
- **Fixture providers carry the shipped ids** (`overpass`, `opentopodata-srtm30m`) and
  the shipped credits, so the key computed for the real providers finds the fixture
  files. The fixture files are renamed to that key after the golden regeneration; the
  rename is safe there because the key is in neither the base hash input nor the
  manifest.
- **Tests never reach the network.** Provider tests run against a real HTTP server on
  the loopback interface that answers from a script.

## Consequences

- A caller can plug in another source, a mirror or a cached dataset by implementing a
  protocol; the painter never sees which source answered.
- A default-configured provider cannot exceed a public service's published limits from
  one instance, at the cost of slow first fetches over large boxes.
- Changing a provider id changes every cache key computed with it, so ids are stable
  names, not versions.
- A later change to either protocol, to the default limits or to the key's inputs is
  itself an ADR.
