# Label.as_dict has no caller

`pyntpot.maps.lettering.label.Label.as_dict` returns the placed label as a
plain dict. Its docstring said it is "the shape the drawing code has always
read", but nothing under `src/` or `tests/` calls it: the drawing code reads
`Label` fields directly.

P6 rewrote the docstring to say what the method returns and changed no code;
deleting a method is out of its scope.

Possible fix: delete `as_dict` (and the `Any` import if it goes unused), or,
if an export of placed labels is wanted, give it a caller and a test.
