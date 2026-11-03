# Each Painting with Python page could open with a short complete program

GitHub issue: [#TBD](https://github.com/findlaywebb/pyntpot/issues/TBD)

**What exists today.** The five Painting with Python pages (`curves.md`, `symmetry.md`,
`fractals.md`, `pictures.md`, `vector-drawing.md` under
`docs/tutorials/painting-with-python/`) teach from a full example script, quoted in marked
blocks that the docs tests hold verbatim to the script. A reader meets the whole script's
setup (blank paper, the sheet, lettering the result) before the idea the page is about.

**What the feature would add.** A short program at the top of each page, complete enough
to copy and run, that paints the page's idea and nothing else, before the page walks the
full script. Setting up blank paper and lettering over an image each take several calls
today, so the opening programs are shorter once those take one call each:
`ink-blank-paper-by-size.md` (#166) and `letters-lettering-over-an-image.md` (#165).

**Possible shape.** Each opening program lives in `examples/` like every other quoted
program, so the verbatim-quote and command tests cover it with no new test. It should land
after #165 and #166, or be shortened when they land.

**Related.** `ink-blank-paper-by-size.md` (#166), `letters-lettering-over-an-image.md`
(#165), `docs-examples-housekeeping.md` (#174).
