# The command line could reach more of the library

GitHub issue: [#68](https://github.com/findlaywebb/pyntpot/issues/68)

**What exists today.** `pyntpot` has one command, `pyntpot map`, which paints a GPX
track as a map PNG. Its `--style` takes a packaged theme's name (`sepia`) or a `.yaml`
theme file, and a theme that does not load prints each problem and exits 2 with no
traceback. Everything else (painting pictures, lettering, swatch and brush sheets, working
with themes) is reached from Python only.

**What the feature would add.** Further commands over the same public API, for
example:

- starting a new YAML theme that `extends` a packaged or example theme
  (`pyntpot theme clone`), and checking that a theme file loads, printing its problems,
  without painting (`pyntpot theme check`);
- painting the reference sheets (pigments, brushes, nibs) to choose from;
- lettering a word or a place card;
- painting a drawing from an SVG file, once the SVG reader exists.

**Options on `pyntpot map`.** The one command also lacks options the how-tos need. Its
flags today are `-o`, `--cache`, `--contact`, `--style`, `--margin-m` and
`--no-attribution` (`maps/cli.py`), and three guides say outright that the command line
cannot do their task (`change-the-route-ink.md`, `letter-your-own-landmarks.md`,
`work-offline-and-reuse-the-cache.md`). Each missing option is a thin call into the
existing API:

- `--route-colour` and `--route-width`, through `Style.with_route_ink`;
- `--landmarks FILE`, reading the table shape `examples/places.toml` already uses;
- `--size`, the card's display width, as `examples/place_card.py --size` does;
- `--offline`, building the providers with a budget of 0 so a cache miss fails rather than
  going online;
- defaults in `--help`: it shows neither `--margin-m`'s 1500 nor that land cover is
  fetched at no less than 2600;
- errors without tracebacks: `main` catches nothing, so a missing GPX file prints a
  Python traceback ending in `FileNotFoundError` and exits 1. A short
  `pyntpot map: error: <message>` for a missing file, a bad GPX and a `FetchError` would
  let the command-line guide list messages, not exception classes, as it already does for
  a theme that does not load.

**Why it is not a defect.** At 0.1 the command line covers the main use, a route map,
and the rest is shown as Python in the docs (maintainer, 2026-10-24, P7 feedback
round 1: out of scope for P7).

**Possible shape.** Subcommands in `maps/cli.py`, or a small `cli` package if it
outgrows one file, using `argparse` only as now; each command a thin call into the
public API with a test that runs it on a fixture. The theme commands use
`Style.from_theme` and `Style.themes()`, as `--style` does. An ADR for the command names.
