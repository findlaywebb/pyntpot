# 0016 — Providers as protocols, with attribution on by default

Status: accepted

## Context

Map data comes from volunteer-run public services whose limits and credit lines must be
respected, and a caller must be able to swap the source.

## Decision

This is a pointer. ADR 0004 records the decision: the protocols `Features` and
`Elevation`; the shipped `OverpassFeatures` and `OpenTopoData`; a required contact
string; published limits enforced by default; and the credit each provider carries.

One part sits outside 0004. `compose` draws the attribution unless called with
`attribution=False`, and the command line has `--no-attribution` for the same switch
(`pyntpot.maps.pipeline`, `pyntpot.maps.cli`).

## Consequences

- A change to a protocol or a default limit is an ADR amending 0004.
- Leaving the attribution off is the caller's explicit choice.
