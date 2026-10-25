# 0040 — Fetch margins

Status: accepted

Amends 0004 (the fetch cache key), 0007 (public API: `FetchMargins`) and 0029 (`fetch` and the cache).

## Context

`Cache.ensure` fetched the features and the elevation grid over the module constant
`MARGIN_M` (1500 m) and the land cover over `LANDCOVER_MARGIN_M` (2600 m), and never varied
them. A map of an island, or of a walk whose card is widened by the aspect floor, needs
ground beyond that. The card clips every layer to its own box, so ground fetched beyond the
card is never painted: the margin has to be sized so the card box lies inside the fetched
box.

## Decision

- **One public type, held by the cache.** `maps.cache.FetchMargins(features_m=MARGIN_M,
  landcover_m=LANDCOVER_MARGIN_M)`, a frozen dataclass exported from `pyntpot.maps`, and
  `Cache(directory, margins=FetchMargins())`. `Cache.key`, `Cache.ensure` and therefore
  `pipeline.fetch` read `cache.margins`, so none of their signatures change. The cache is
  configured for the ground it fetches; a margin per call would have given `fetch` eight
  parameters, over the lint's limit, and one `margins` argument still seven.
- **The key.** `features_m` is the key's `margin_m`; `landcover_margin_m` joins the canonical JSON only
  when it is not the default (the omit-at-default rule of the style digests), so the default
  key is byte-identical: no fixture is renamed and no golden moves, while two recordings that
  differ only in the land cover margin get different keys.
- **Validation.** `FetchMargins.__post_init__`: each margin is at least 0 and at most 20 000 m,
  and `landcover_m` is at least `features_m`; otherwise `ValueError` naming the bad value.
- **The card does not depend on the margins.** Its frame is the ribbon fields', and
  `build_basemap` clips every layer to the card box. The invariant a recording keeps is that
  the card box lies inside the fetched feature box. The margins are explicit, not derived from
  the frame, so two caches over one directory with different margins get different payload names, and the names do not depend on the theme's ribbon fields.
- **Consumers.** `pyntpot map` gains `--margin-m`, which builds the `Cache`'s `FetchMargins`, the
  land cover margin being the larger of its default and the given margin. `record_fixture.py`
  gains `--margin-m` and `--landcover-margin-m`. The examples and the golden support keep the
  defaults.

## Consequences

- A recording can fetch as wide a box as its card needs, within 20 km.
- Every existing key, payload name and golden is unchanged.
- A cache filled at one margin is not reused at another; the payloads are fetched afresh.
