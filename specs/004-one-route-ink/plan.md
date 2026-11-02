# 004 — plan

## Approach

Maps layer only (`src/pyntpot/maps/`); no boundary change, so the import-linter contracts
are untouched. The theme format and a public attribute of `Style` change, so ADR 0046
records it.

`RouteInk` becomes a flat frozen dataclass:

```python
@dataclass(frozen=True)
class RouteInk:
    style: str
    px: float
    colour: str
    blend: str = "normal"
    opacity: float = 1.0
```

`RouteInks` is deleted. `Style.route_inks: RouteInks` becomes `Style.route_ink: RouteInk`.
Because a pydantic field and a method cannot share a name, the `route_ink()` method is
removed and every caller reads the attribute `style.route_ink`. The strict-key validator
already recurses into any dataclass-typed `Style` field, so `[route_ink]` rejects unknown
keys (an old `effect` table, `casing_px`, …) with no new code.

`compose.route` / `_lay` take `ink.blend` and `ink.opacity` instead of an effect dict. The
`ValueError` checks stay in `_lay` (same messages), so a hand-built `RouteInk` with a bad
blend still fails where it did.

Every theme's four `[route_inks.*]` tables (plus four `.effect` sub-tables) are replaced by
one table holding the old `ride` ink's `style`, `px`, `colour` and `blend = "normal"`;
`opacity` is not written (it was absent before). The pixels cannot move because the only ink
ever read was `ride`, and `blend`/`opacity` keep their values.

The full `digest()` moves (the route ink group's JSON changes); `base_digest` and
`lettering_digest` are unaffected because `route_ink` is in neither `BASE_GROUPS` nor
`LETTERING_GROUPS`. `DIGEST` in `tests/unit/maps/test_style.py` is re-pinned once.

## Files to touch

- `src/pyntpot/maps/style_groups.py` — flat `RouteInk`, delete `RouteInks`, rewrite the
  module docstring and `RouteInk` docstring (one route ink; no sports).
- `src/pyntpot/maps/style.py` — field `route_ink: RouteInk`, drop `route_ink()` method,
  `with_route_ink` replaces the field directly; docstrings.
- `src/pyntpot/maps/compose.py` — `_lay` takes `blend`, `opacity`; drop `Any` import if unused;
  docstrings.
- `src/pyntpot/maps/strands.py`, `src/pyntpot/maps/pipeline.py` — `style.route_ink` attribute;
  "ride ink" wording to "route ink".
- `src/pyntpot/maps/themes/default.toml` and `examples/themes/*.toml` (10) — one
  `[route_ink]` table.
- `examples/how_to_route_ink.py` — `route_ink` attribute and `model_copy(update={"route_ink": …})`.
- Tests: `tests/unit/maps/test_style.py` (pinned `ROUTE_INK`, drop the dotted-sports test,
  digest test edits a field of `route_ink`, re-pin `DIGEST`, add a test that an old `effect`
  table / `route_inks` table is rejected), `tests/unit/maps/test_style_groups.py` (`PINNED`
  row `RouteInk: ("style", "px", "colour", "blend", "opacity")`),
  `tests/unit/maps/test_route_ink.py` (`dataclasses.replace(ink, blend=…, opacity=…)`),
  `tests/unit/maps/test_example_themes.py` (showcase test asserts `blend == "normal"`,
  drops the glow/casing/shadow line), `tests/unit/maps/painter/test_pen_strands.py`
  (replace the field), `tests/architecture/test_reference_pages.py` (drop the
  `route_inks.<sport>` pseudo-group).
- Docs: `docs/reference/style-fields.md` (one `## route_ink` section with five keys; remove
  the per-sport paragraph and the effect "no reader" paragraph; `route_inks` → `route_ink`
  in the digest table), `docs/how-to/write-a-theme.md`, `docs/how-to/change-the-route-ink.md`,
  `GLOSSARY.md` (route ink entry: `Style.route_ink` is a field),
  `docs/features/maps-themes-as-overrides.md` (snippet key), `docs/decisions/0046-one-route-ink.md`
  (new), `docs/decisions/README.md` (add row 0046, amends 0005, 0026, 0027 and 0037).
- Issues: delete `docs/issues/maps-route-ink-effect-unread.md` and
  `docs/issues/maps-style-route-inks-one-read.md`; add
  `docs/features/maps-route-casing.md`, `maps-route-glow.md`, `maps-route-shadow.md`, each
  with its GitHub issue (labels `enhancement`, `area: maps`).

Call sites the plan-reviewer listed, all repointed to the field: `test_style.py`
`TestEngineAdapters` (folded into the pinned-ink test) and `TestFedRouteInk` (compare
`blend` and `opacity`, not `effect`); `test_route_ink.py:113,132,158`;
`test_pen_strands.py:72,76`; `examples/how_to_route_ink.py:146-150,199`; the unused `Any`
import in `style_groups.py` and `RouteInk` import in `test_reference_pages.py`; "ride ink"
wording in `painter/pen.py` and `strands.py`.

The reference row for `style` says what the compose step does: `"pen"` tints the pen plate
when one was painted, any other value (`"solid"` in every theme) draws the line. It does not
promise `dotted`.

The overrides note's snippet becomes `route_ink:` / `  colour: "#7b2335"`.

Rejection tests pin `match=`: an old theme fails on `route_inks` (pydantic extra input); a
`[route_ink]` naming `casing_px` fails on `casing_px` (`_check_keys`'s `ValueError`, wrapped).

Before filing the three feature issues, search the open issues for casing, glow and shadow.

## Files to leave alone

- `docs/decisions/0005`, `0026`, `0027`, `0037` — accepted ADRs are history; 0046 amends them.
- `specs/001-port/**` — historical research and reviews mention `route_inks`; not living docs.
- `CHANGELOG.md` — drafted from the squash subject and the PR's Changelog lines at release.
- `src/pyntpot/letters/**` — `label_route_ink` is a different concept (lettering ink).
- `RouteStyle` — the pen plate group; tempting to merge with the ink, but it feeds the base
  digest and the ink must not.

## Test plan

- Red first: change the pinned `ROUTE_INK` literal and the `PINNED` row, add the rejection
  test (a theme with `[route_inks.ride.effect]`-style content, and a `[route_ink]` naming
  `casing_px`, are rejected); watch them fail; then implement.
- `test_route_ink.py` golden-marked blend/opacity tests prove the compose step still reads
  both keys with identical outcomes.
- No-pixel proof: run the full suite including golden-marked tests
  (`uv run pytest -n auto --dist loadgroup`); goldens are pinned literals, so any moved pixel
  fails. Docs-image checks run in the same suite.
- Gates: `prek run --all-files` (ruff, ty, lint-imports, file budget, docstrings).

## Delegation

Small, tightly coupled change (one dataclass shape ripples to ~25 files); kept in the main
context, serial. Delegated: the plan-reviewer gate (fresh context), and a full-suite run to a
`gate-runner` so the log stays out of context. Integrator job: run every gate after the code
and docs land.

## File-ownership partition

Single track (A): code + themes + tests, then docs + notes. No concurrency, no worktrees.

## Decisions

- **Drop, not paint** (maintainer, 2026-11-02); feature issues for casing, glow, shadow.
  `adaptive_pct` gets no feature issue: nothing in the repo says what it meant, and every
  theme set it to 0. The ADR names it as dropped.
- **Flat fields, not an `effect` sub-table**: two typed fields with defaults are checked by
  the existing strict-key validator and pydantic's types; a free `dict[str, Any]` is what let
  unread keys accumulate. A future casing/glow/shadow joins as typed fields too.
- **`route_ink` field replaces the `route_ink()` method**: the glossary's one name for the
  concept; a field and a method cannot share it. Breaking for callers of `route_ink()` and
  `route_inks`, recorded in ADR 0046 and the PR title's `!`.
- PR title: `fix(maps)!: one route ink, holding only the keys the compose step reads`.
