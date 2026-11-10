# Lettering could be laid over an image in one call

GitHub issue: [#165](https://github.com/findlaywebb/pyntpot/issues/165)

**What exists today.** `pyntpot.letters.nib_plate(marks, surface, groups, path)` strokes the
marks onto one RGBA plate and only writes it to disk, returning the path or `None`. A caller
who wants a word over a painted array does the rest by hand:

1. builds a second `Canvas` at twice the size (`NIB_SCALE = 2`, redefined in 12 example
   scripts), a zero `dark` array and a `NibSurface`, whose canvas is read only for `w` and `h`;
2. builds a `NibGroups` from five style objects, since it holds no defaults;
3. calls `nib_plate`, reopens the file with Pillow, resizes it with Lanczos, divides by 255
   and blends `image * (1 - alpha) + rgb * alpha`.

That round trip appears 14 times in 13 scripts under `examples/` (`nib_stages.py` has two),
and the copies have drifted: 6 scripts convert through `"RGBa"` before resizing and the rest
do not; 8 scripts write the plate into a `tempfile.TemporaryDirectory`, the other 5 leave
`<stem>-plate.webp` beside their output, which `tests/examples/test_letters_examples.py`
pins as behaviour; each works out the plate's `gran_px` its own way. The library does it
too: `src/pyntpot/maps/attribution.py` writes the attribution plate to a temporary
directory and reopens it the same way. The tutorial (`paint-a-watercolour.md`) and the
how-to `paint-your-own-shapes.md` teach the same steps, and Pillow is not part of the API
they otherwise teach.

**What the feature would add.** An in-memory nib plate, and one `letters` call that letters
settings or marks over an `(h, w, 3)` painting and returns the painting with the lettering
laid on by its alpha. Each example's 15 to 25 lines drop to two or three, and the disk
round trip leaves the library's own attribution step.

**Possible shape.** A suggestion, not a requirement:

- `nib_rgba(marks, surface, groups) -> tuple[np.ndarray, np.ndarray] | None`, the plate's
  colour and alpha as arrays; `nib_plate` becomes a thin writer over it.
- `letter_over(image, marks, groups, *, scale=2, gran_px=...)`, which builds the surface at
  `scale` times the image, strokes, downsizes and blends.
- `NibSurface.dark` defaulting to bare paper, and a `NibGroups` default (for example
  `NibGroups.default()` or defaults on its fields).

A widening of the public API, so an ADR (after `0026-widen-the-public-api.md`). The plate is
lossless WebP by default, so dropping the file costs only the 8-bit step, but the resize
moves from Pillow on 8-bit RGBA to arrays, so the docs images the 13 scripts draw, and any
golden that includes the attribution, are expected to move and need re-pinning.

**Related.** `docs-examples-review` (#63), the largest gap behind it. Not
`letters-nib-follows-writing-line` (#76), which is about the stroke's direction.
