# A name-only landmark is never counted against the landmark cap

`pyntpot.maps.lettering.picks.journal_picks` stops once `cap` landmarks are
kept, but it checks the cap only after a landmark given as an object. A
landmark given as a bare string is appended and the loop `continue`s past
the check, so a list of string landmarks is never capped, and a mix can end
over `cap`. `cap` is `style.lettering.label_max`.

P6 rewrote the docstring to state this and changed no code. Capping every
landmark is the more plausible intent, but the change could alter what a card
letters.

To show it: `Annotations(landmarks=("A", "B", "C"))` over a basemap whose
candidates include rows named A, B and C (each with `x` and `y`), with
`cap=1`; all three come back.

Possible fix: move the `if len(out) >= cap: break` check so it runs after
every append, string branch included, and add a test for a string-only list.
