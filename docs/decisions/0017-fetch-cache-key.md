# 0017 — The fetch cache key

Status: accepted

## Context

A cache keyed by the activity would tie the fetched data to something it does not
depend on, and a cache directory found by module global would make runs depend on the
working directory.

## Decision

This is a pointer. ADR 0004 records the decision: the cache is keyed by a hash of the
bounding box, the margin and the provider ids, never by an activity id, and the cache
directory is always an explicit argument with no cwd-relative module global.

## Consequences

- Changing the key's inputs, or a provider id, changes every key; ADR 0004 says such a
  change is an ADR.
