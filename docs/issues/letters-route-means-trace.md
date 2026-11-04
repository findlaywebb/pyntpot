# Some identifiers say route where they mean the trace

GitHub issue: [#181](https://github.com/findlaywebb/pyntpot/issues/181)

Area: letters, with maps (lettering).

`GLOSSARY.md` names how a glyph becomes strokes the trace (`centreline` or `outline`),
and keeps route for the painted line of the track. Three identifiers still say route for
the trace:

- `FaceStyle.label_route` in `letters/style.py` (and `label_route` in
  `maps/themes/default.toml` and every theme);
- the `route=` argument of `Hand` in `letters/hand.py` (`self.route = route or
  face.label_route`);
- the nib plate's sidecar key `route`, written by `maps/lettering/pipeline.py`.

`NibStyle.label_route_ink` is a different thing (the ink of the route markers) and
sharing the word makes the two easy to confuse.

Possible fix: rename to say trace, with an ADR since `FaceStyle` is public and themes
carry the key. The sidecar key is part of the fetch cache's layout, so renaming it changes
`docs/reference/cache-layout.md` and needs old caches to read or refetch.
