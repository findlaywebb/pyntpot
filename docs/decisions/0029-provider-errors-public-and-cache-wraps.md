# 0029 — The provider errors are public, and `Cache.ensure` wraps them

Status: accepted

## Context

ADR 0028 made `fetch` raise `FetchError` when a provider cannot answer and kept
`ProviderError` and `ProviderBudgetExceededError` private. `Cache.ensure` and the shipped
providers' `features`, `landcover` and `grid`, public through `Cache`, `OverpassFeatures`
and `OpenTopoData` (ADR 0026), still raised a type a caller could catch only as
`RuntimeError`. A caller that forces a refetch calls `Cache.ensure` itself, since `fetch`
takes no `force`. The maintainer chose (2026-10-21) to export both errors and to have
`Cache.ensure` wrap them.

## Decision

This ADR amends ADR 0004's "Errors" and ADR 0028, which stay as written.

`ProviderError` and `ProviderBudgetExceededError` join `pyntpot.maps.__all__`. They are
still defined in `pyntpot.maps.providers.base` and raised by the providers' own methods.
This replaces ADR 0028's "No name joins or leaves an `__all__`" and "stay private".

`Cache.ensure` catches `ProviderError`, a `ProviderBudgetExceededError` included, from any
provider it calls and raises `FetchError` from it, with the provider's error as
`__cause__`.

`FetchError` is defined in `pyntpot.maps.cache`, because `maps.pipeline` imports
`maps.cache`; its public path `pyntpot.maps.FetchError` is unchanged.

`fetch` catches nothing itself, as it reaches the providers only through `Cache.ensure`,
and raises `FetchError` on a provider failure as ADR 0028 says.

## Consequences

- A provider called directly raises a public type, and `Cache.ensure` and `fetch` raise
  one `FetchError` with the provider's error as its cause.
- The default render, every golden and the pinned digests are unchanged, since only
  failure paths change.
- The payloads written before a failure stay on disk (`Cache.ensure`'s invariant).
- A caller that caught `RuntimeError` still catches both.
- A new public name, or a change to one, still needs a new ADR.
