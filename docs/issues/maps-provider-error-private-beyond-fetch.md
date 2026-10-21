# Public names other than fetch let the private ProviderError through

Area: `maps`.

The maintainer chose (2026-10-20) that `pyntpot.maps.fetch` raise `FetchError` when a
provider cannot answer (ADR 0028). That covers `fetch` only: three other public names
let the providers' errors through. `Cache.ensure` calls the providers with no handler,
and `OverpassFeatures.features`, `.landcover` and
`OpenTopoData.grid` raise `ProviderError` and its subclass
`ProviderBudgetExceededError`. Both are defined in `maps/providers/base.py`, and no
`__all__` exports either, so a caller of these names can catch them only as
`RuntimeError`.

The upstream consumer reaches this path: its forced refetch calls
`Cache.ensure(..., force=True)` before `fetch`, because `fetch` takes no `force`
argument (read from the upstream at `9139760`, `analysis/report/routemap.py:361`). A
network failure there reaches the consumer as the private type, whether or not
`fetch` wraps it.

To show it: `python -c "import pyntpot.maps as m; print('ProviderError' in m.__all__)"`
prints `False`, and `maps/cache.py`'s `ensure` calls `features.features`,
`features.landcover` and `elevation.grid` outside any `try`.

Awaiting a maintainer decision. Readings: (1) export `ProviderError` and
`ProviderBudgetExceededError` from `pyntpot.maps` as the providers' documented errors
(ADR 0004), in a new ADR; (2) keep both private and have `Cache.ensure` wrap them in a
public error as `fetch` does, which still leaves `OverpassFeatures` and `OpenTopoData`
raising a private type when called directly.
