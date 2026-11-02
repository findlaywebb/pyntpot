# 004 — One route ink

GitHub issues: [#57](https://github.com/findlaywebb/pyntpot/issues/57) (most of the route
ink's `effect` table is read by nothing) and
[#60](https://github.com/findlaywebb/pyntpot/issues/60) (the style holds four named route
inks and reads one).

## Problem

A theme carries four route inks (`[route_inks.run]`, `.ride`, `.swim`, `.other`), each
named for something a track records, but `Style.route_ink()` reads only `ride` and pyntpot
has no notion of what a track records. Each ink's free `effect` table holds casing, glow,
shadow and adaptive-percentage keys that nothing paints, so a theme setting `casing_px`
changes no card. Both are fields that promise behaviour the library does not have.

Maintainer decision (2026-11-02): drop the unread keys rather than paint them, and file a
feature note and GitHub issue for each dropped effect so it can be added back properly.

## Acceptance criteria

- [ ] A theme has one `[route_ink]` table with the keys `style`, `px`, `colour`, `blend`
      and `opacity`; `blend` defaults to `"normal"` and `opacity` to 1.0.
- [ ] `Style.route_ink` is a field holding one `RouteInk`; `Style.route_inks`,
      `RouteInks` and the `route_ink()` method are gone. `with_route_ink` keeps its
      signature and behaviour.
- [ ] A theme naming `route_inks`, an `effect` table, or any casing, glow, shadow or
      adaptive key is rejected at load, like any unknown key.
- [ ] The compose step reads `blend` and `opacity` from the ink's own fields, with the same
      checks and the same pixels as before.
- [ ] The packaged default theme and the ten example themes are rewritten to the new
      table, each keeping its old `ride` ink's `style`, `px`, `colour` and `blend`.
- [ ] No pixel moves: every golden, plate and docs image passes unchanged. Only the pinned
      `Style.digest()` literal moves, re-pinned once; `base_digest` and
      `lettering_digest` do not move.
- [ ] A new ADR records the theme-format and public-attribute change, amending ADRs 0005,
      0026, 0027 and 0037.
- [ ] Reference and how-to docs describe the one ink and its five keys; the "Fields with no
      reader" paragraph about `effect` is gone.
- [ ] One feature note in `docs/features/` and one GitHub issue each for a route casing, a
      route glow and a route shadow, recording the values the themes held when the keys
      were dropped.
- [ ] The notes `docs/issues/maps-route-ink-effect-unread.md` and
      `docs/issues/maps-style-route-inks-one-read.md` are deleted; the PR closes #57 and #60.

## Out of scope

- Painting a casing, glow or shadow (the new feature issues).
- `NibStyle.label_route_ink`, the lettering's route-coloured ink.
- `RouteStyle` (the route pen plate group).
- Themes as overrides (#80) beyond updating its illustrative snippet to the new table name.
