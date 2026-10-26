# The command line could reach more of the library

GitHub issue: [#68](https://github.com/findlaywebb/pyntpot/issues/68)

**What exists today.** `pyntpot` has one command, `pyntpot map`, which paints a GPX
track as a map PNG with the default theme or a theme file. Everything else (painting
pictures, lettering, swatch and brush sheets, working with themes) is reached from
Python only.

**What the feature would add.** Further commands over the same public API, for
example:

- copying a shipped or example theme to a new file to edit (`pyntpot theme clone`),
  and checking that a theme file loads (`pyntpot theme check`);
- painting the reference sheets (pigments, brushes, nibs) to choose from;
- lettering a word or a place card;
- painting a drawing from an SVG file, once the SVG reader exists.

**Why it is not a defect.** At 0.1 the command line covers the main use, a route map,
and the rest is shown as Python in the docs (maintainer, 2026-10-24, P7 feedback
round 1: out of scope for P7).

**Possible shape.** Subcommands in `maps/cli.py`, or a small `cli` package if it
outgrows one file, using `argparse` only as now; each command a thin call into the
public API with a test that runs it on a fixture. Pairs with named themes
(`maps-named-themes.md`). An ADR for the command names.
