# 0046 — One route ink (amends 0005, 0026, 0027 and 0037)

Status: accepted

## Context

A theme carried four route inks, `[route_inks.run]`, `.ride`, `.swim` and `.other`, each
named for something a track records, held in `RouteInks` on `Style.route_inks`. Only
`ride` was ever read, through `Style.route_ink()`; pyntpot has no notion of what a track
records, and since ADR 0027 a caller that inks routes differently keeps its own table and
feeds `with_route_ink` (#60).

Each ink also carried a free `effect` table, `dict[str, Any]`, holding casing, glow, shadow,
blend, opacity and adaptive-percentage keys, copied from the upstream consumer, whose page
drew those effects itself. The compose step reads `blend` and `opacity` (ADR 0037) and
nothing else, so a theme's `casing_px` or `glow_px` changed no card, and because the table
was free any key loaded without complaint (#57).

## Decision

Maintainer decision, 2026-11-02: drop the unread keys rather than paint them, and file a
feature for each dropped effect so it can be added back properly.

- `RouteInk` is flat: `style`, `px`, `colour`, `blend` (default `"normal"`) and `opacity`
  (default 1.0). There is no `effect` table. `casing_colour`, `casing_px`, `glow_px`,
  `glow_opacity`, `shadow_px`, `shadow_blur_px` and `adaptive_pct` are gone.
- `RouteInks` is deleted. `Style.route_inks` becomes the field `Style.route_ink: RouteInk`,
  the glossary's one name for the concept. A pydantic field and a method cannot share a
  name, so the `route_ink()` method is removed: callers read the attribute.
- A theme has one `[route_ink]` table. The packaged default and the example themes keep
  their old `ride` ink's `style`, `px`, `colour` and `blend`, so no pixel moves.
- The existing strict-key check covers the new table, so an old `[route_inks.*]` table, an
  `effect` table or any dropped key is rejected when the theme loads.
- `with_route_ink` keeps its signature and behaviour.
- `Style.digest()` moves for every theme, because the group's fields changed; `base_digest`
  and `lettering_digest` do not, since the route ink feeds neither. The pinned `DIGEST` is
  re-pinned once.

ADR 0026 fixed `Style.route_inks` as a public attribute; this ADR replaces it with
`Style.route_ink`. ADR 0027's `route_ink()` becomes the `route_ink` field. ADR 0037's
`route_inks.<sport>.effect` `blend` and `opacity` become `route_ink.blend` and
`route_ink.opacity`, read and checked as before. ADR 0005's `RouteInks` group is now the
`RouteInk` group. The boundary and the import-linter contracts are unchanged.

## Consequences

- A theme written for an earlier release fails to load until its four `[route_inks.*]`
  tables become one `[route_ink]` table: copy the `ride` ink's `style`, `px` and `colour`,
  and its `blend` (and `opacity` if set) from its `effect` table, and drop the rest.
- `style.route_ink()` becomes `style.route_ink`.
- Every field of the route ink is read; a key nothing reads cannot be written.
- A route casing, glow and shadow are features to build, each as typed fields with its own
  golden regeneration: `docs/features/maps-route-casing.md`, `maps-route-glow.md` and
  `maps-route-shadow.md`. `adaptive_pct` has no feature note: every theme set it to 0 and
  nothing records what it meant.
