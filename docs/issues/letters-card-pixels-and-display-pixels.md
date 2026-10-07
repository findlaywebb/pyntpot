# One pixel unit has two names in letters: card pixels and display pixels

The marks and settings in `pyntpot.letters` are in the card's display pixels,
the grid `maps.card.Card.xy` maps card metres to (`pyntpot.letters.nib.plate`
multiplies every mark by `NibSurface.scale`, display to render). The
docstrings call that one unit two things: "card pixels" in
`pyntpot.letters.setting.Setting`, `pyntpot.letters.setting.Mark`,
`pyntpot.letters.hand.Hand.measure`, `Hand.stroke` and `Hand.write`; "display
pixels" in `pyntpot.letters.setting.DEFAULT_LINE_PX`,
`pyntpot.letters.font.OutlineFont.measure` and `run`,
`pyntpot.letters.style.NibStyle` and `pyntpot.letters.nib.plate`. Across
`src/` at this commit "card pixel" appears on 57 lines and "display pixel" on
67.

`GLOSSARY.md` defines neither term: its `card` row names "the display and
render pixel grids", and its `mark` and `backdrop` rows say "card pixels". So
no rule picks the canonical name, and P6.5 leaves both in place rather than
choose one in one group.

Possible fix: add one glossary row (for example "display pixels: the card's
display grid, origin top left, y down; marks, settings and type sizes are in
it") and name the other a synonym to remove, then replace it across every
group in one docs pass.
