# The nib could turn with the writing line

**What exists today.** The nib's angle is fixed to the page.
`pyntpot.letters.nib._pen_profile` takes each segment's direction as
`arctan2(dy, dx)` in render pixels and compares it with
`radians(NibStyle.label_pen_angle_deg) + mark.pen`; both angles are measured from
the page's horizontal (y down). For a flat block the writing line is the page's
horizontal, so nothing turns. For a name set along a path
(`pyntpot.letters.hand.Hand._along`) each glyph is turned onto the path's tangent,
but the nib is not: a name written down a steep road has its thick and thin
strokes in the page's places, not the letter's. "Lyn" written along a horizontal
and a vertical path carries the same `Mark.pen` (-0.0389) on both. The lettering
goldens were made with the page-fixed nib (`East Lyn` is set along its water on
the golden card), and they pin it.

**What the feature would add.** A pen held by a hand turns with the line it
writes along. A style switch, off by default, would add the glyph's tangent
angle to the nib angle for names set along a path, so their thick and thin
strokes sit where they would on a flat block. With the switch off the current
look is kept, and the goldens do not move.

**Why it is not a defect.** The page-fixed nib is the ported behaviour and the
look the goldens record; the comment on `NibStyle.label_pen_angle_deg` and the
`angle` argument of `_pen_profile` say what the code does. An earlier comment
said "anticlockwise from the writing line", which is the turning nib; the
maintainer kept the current look and recorded the turning nib as a candidate.

**Possible shape.** Carry the glyph's tangent angle on each `Mark` written along
a path (or fold it into `Mark.pen`), and add it to the nib angle in `_items`
when the switch is on. A new `NibStyle` field holds the switch, in the lettering
group so that a change restrokes the label plate. A test writes one word along
a horizontal path and along the same path turned 90 degrees, strokes both with
`nib.plate` with the switch on, and compares the stroke widths of the same
glyph; a second test pins that the switch off leaves `Mark.pen` unchanged.
