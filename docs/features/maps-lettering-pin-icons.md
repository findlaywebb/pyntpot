# A theme could choose the pin icon at the end of a leader, and whether it turns to the leader

GitHub issue: [#149](https://github.com/findlaywebb/pyntpot/issues/149)

**What exists today.** A leader (the line from a name to the thing it names) ends in a pin,
drawn by `pin()` in `pyntpot.maps.lettering_furniture` and placed by `_furniture` in
`pyntpot.maps.lettering_marks`. The pin is a closed ring of a fixed size, and a theme cannot
change it. PR #138 (branch `fix/pin-ring-closes`, issue #130) is reworking the default into an
open ring (a C shape) rotated so its gap faces the leader, with the leader passing through the
gap into the centre. That fixes the ring closing into a dot, but the icon and its rotation stay
fixed in code.

**What the feature would add.** Theme fields for the pin:

- the icon: closed ring, open ring, dot, cross, small flag, or none, with room to add more;
- whether the icon rotates to face its leader, and the fixed angle it takes when it does not;
- the size, and for the open ring the gap width.

**Possible shape.** A pin table in the theme, most likely under `[lettering]` in the theme
TOML (alongside `home_glyph`), with typed fields on the lettering options: `pin_icon`,
`pin_turns`, `pin_angle`, `pin_px` and `pin_gap`. `pin()` would take the icon and dispatch to
one drawing function per icon, each returning the same list of points. The default theme keeps
the open ring that turns to the leader, so existing cards do not move once #138 has landed.

**Open questions.**

- Where the fields live: the `[lettering]` table, or a nested `[lettering.pin]` table.
- Per-kind overrides: whether places, landmarks and the caller's notes can each have their own
  icon, or one pin serves all three.
- How an icon with no natural gap (dot, cross, flag) meets the leader: the leader could stop at
  its edge or run to its centre.
- How the goldens cover each icon: one golden per icon on a small fixture card, or a single
  card that draws every icon, with the default's goldens left alone.
- Whether `none` also drops the leader's end cap, or only the icon.

**Related.** #130 (the ring closing into a dot) and PR #138 (the open ring); #113 (label
placement tuning, which covers leaders and pins); #80 (a theme declaring only what it changes)
and #77 (themes shipped by name), since new theme fields must fit how themes are declared and
overridden.
