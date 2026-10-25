# 0039 — Painter's pigments

Status: accepted

Amends the public API of `pyntpot.ink`: two names are added.

## Context

`PIGMENTS` is keyed by map role (`farmland`, `water`, `relief`), which `CoverStyle.pigments`
names, and the swatch sheet, the pigments page and the palette CSS are written from it. A
painter working with the engine directly names a pigment by its tube, which is not a map role.

## Decision

- **A separate table.** `ink/pigment.py` gains `PAINTERS_PIGMENTS` (name to `#rrggbb`) and
  `PAINTERS_TRANSPARENCY` (name to a transparency in 0 to 1, the meaning `TRANSPARENCY` has),
  both exported from `pyntpot.ink`. Keys: `ultramarine`, `cerulean`, `burnt_sienna`,
  `raw_sienna`, `yellow_ochre`, `sap_green`, `indigo`, `perylene_maroon`,
  `quinacridone_rose`, `paynes_grey`.
- **Nothing else moves.** `PIGMENTS`, `TRANSPARENCY`, the swatch sheet and its master, the
  pigments page's existing sections and the palette CSS are byte-identical. No map style reads
  the new tables, so no golden or digest moves.
- **Glossary.** The term is "painter's pigment".

## Consequences

- A script can glaze `ultramarine` over `burnt_sienna` by name.
- The pigments page gains a "Painter's pigments" section, and an architecture test requires
  every key to be named there.
