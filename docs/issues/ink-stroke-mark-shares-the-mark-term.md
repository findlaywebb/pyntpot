# ink.stroke.Mark shares the glossary's "mark"

Area: `ink`.

`pyntpot.ink.stroke.Mark` holds the pressure and width along one stroke, and
how far a nib has run down; `ink.stroke` and `ink.stamp` use it. It is
private: it is in no `__all__`.

The glossary's "mark" is `pyntpot.letters.setting.Mark`, one stroke the hand
produces for the nib to run along. ADR 0026 made that class public, as
`pyntpot.letters.Mark`. Two classes now carry one name for two concepts, and
the project keeps one canonical name per concept, so the private one is the
one to rename.

P11 records the clash and changes no code: renaming an `ink` class is not part
of widening the public API.

Possible fix: rename `ink.stroke.Mark` to a name that says what it holds,
`StrokeProfile` for one, repointing its importers in the same commit with no
shim; check `GLOSSARY.md` first, and add a row if the new name is a term.
