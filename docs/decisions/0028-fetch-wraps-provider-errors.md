# 0028 — `fetch` raises `FetchError` when a provider cannot answer

Status: accepted

## Context

`fetch` let a `ProviderError` through from `Cache.ensure` when a provider could not
answer. No `__all__` exports `ProviderError`, so a caller of `fetch` could catch it only as
`RuntimeError`, not by a public name. The maintainer chose to wrap it (2026-10-20).

## Decision

This ADR amends ADR 0004's "Errors", which stays as written.

`fetch` catches `ProviderError`, a `ProviderBudgetExceededError` included, and raises
`FetchError` from it, with the provider's error as `__cause__`.

`FetchError` means `fetch` could not build a basemap: a provider could not answer, or the
cached features were missing once the fetch had run.

No name joins or leaves an `__all__`. `ProviderError` and `ProviderBudgetExceededError`
stay private, and `Cache.ensure` and the providers' own methods still raise them.

## Consequences

- The default render, every golden and the pinned digests are unchanged, since only the
  failure path of `fetch` changes.
- The payloads fetched before the failure stay cached (`Cache.ensure`'s invariant).
- A caller that caught `RuntimeError` still catches it, as `FetchError` is one.
- A new public name, or a change to one, still needs a new ADR.
