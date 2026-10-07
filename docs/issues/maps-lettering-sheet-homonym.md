# The lettering modules use "sheet" for the paper the card is drawn on, which the glossary gives to the noise fields

`GLOSSARY.md` defines *sheet* as "the paper's noise fields, seeded",
`pyntpot.ink.sheet.Sheet`. The docstrings and comments of
`pyntpot.maps.lettering` use "the sheet" about 48 times for something else:
the drawn card with everything already on it ("what is already on the
sheet", "a river crossing the whole sheet", "runs down the sheet"), and
"the page" a few times for the same thing.

This is a homonym, not a synonym of one glossary term, so the P6.5
one-name-a-concept rule does not settle it: "card" names the coordinate
frame, not the paper with its names and marks, and replacing each use by
hand risks changing meaning in a docs pass. P6.5e left the word as it is.

Possible fix: decide the canonical word for "the card's paper as drawn so
far" (for example *card*, or a new glossary row), add it to `GLOSSARY.md`,
then reword the lettering docstrings and comments in one pass, checking each
use against the code it describes.
