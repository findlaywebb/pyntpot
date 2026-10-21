# A lettering test names a place that does not exist

Area: tests (`maps` lettering).

`tests/unit/maps/lettering/test_picks.py` builds a candidate village called
"Faraway" (line 87) and asserts it is not picked (line 92). "Faraway" is an
invented name. `CLAUDE.md` and `CONTRIBUTING.md` ("Place names in tests and
examples") say test place names are real UK countryside names, never invented,
and that where a string is compared, a real name of the same length is used.

Possible fix: rename "Faraway" to "Keswick" in both places. Keswick is on
`CONTRIBUTING.md`'s list, has the same seven letters, and is not otherwise
used in the file. The test only compares the name, so nothing else changes.

The same test's "Little Combes" (line 83) and "Tarns Bridge" (line 84) are not
on the list either and may also be invented; whoever fixes this should check
them and swap any that are not real for listed names of the same length.
