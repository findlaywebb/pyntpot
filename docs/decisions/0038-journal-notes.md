# 0038 — Journal notes

Status: accepted

Amends the public API of `pyntpot.maps`: `JournalNote` is added and `Annotations` gains a field.

## Context

A map of a trip wants the walker's own sentences on it ("Rain came in here"), pinned to a
point, which no landmark, place or span says. The card is painted to its edges and no lettering
module defines a region for notes, so they are set among the labels.

## Decision

- **The type.** `maps.annotations.JournalNote(text, lat, lng)`, frozen, `extra="forbid"`,
  exported from `pyntpot.maps`. `Annotations.notes: tuple[JournalNote, ...] = ()`. At most 6
  notes, each of at most 60 characters (two lines of the existing wrap); otherwise validation
  fails naming the field.
- **Seated first.** `letter` seats the notes before any other name, one at a time, through
  `best_flat` (offered the one chosen form) as flat blocks with leaders: the leader rungs, the hand's row leading, and the
  wrap form `wrap_forms` gives, the single line first and the most balanced two-line form when
  one line is wider than a third of the card. Each is seated against the boxes already taken
  (the home glyph and its kin) and the notes already seated.
- **Never moved.** The notes' boxes join the `taken` boxes `place` avoids, so every later name
  pays the overlap cost against them; the notes are not in the list `place` orders, dedupes,
  swaps or drops. Notes are not counted against `label_max`.
- **Errors.** A note whose point is off the card, or whose cheapest seat is off the paper,
  raises `ValueError` naming it.
- **Where.** `maps/lettering/notes.py` (`note_labels`, `seat_notes`); `best_flat` gains an optional `forms`
  argument; `placement.py` is unchanged, as a note has no baseline and `off_own_feature` costs it nothing.
- **Glossary.** The term is "journal note".

## Consequences

`Annotations()` without notes letters exactly as before, so no golden or digest moves. A caller
with notes gets them first in `Lettering.labels` after the home glyphs.
