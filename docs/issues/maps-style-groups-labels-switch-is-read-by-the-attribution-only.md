# The `labels` switch turns off the attribution, not the label plate

`pyntpot.maps.style_groups.LetteringPolicy.labels` is documented as the switch
"the label plate is turned off with once there is one, so a theme that wants
the painting bare has somewhere to say so", and as read by nothing. The label
plate exists now, and the field is read in one place only:
`pyntpot.maps.attribution.draw_attribution` opens no hand, and so writes no
attribution line, when it is off. `pyntpot.maps.lettering.pipeline.letter`
does not read it, so a theme with `labels = false` still gets a lettered card,
and it loses the data attribution it owes.

Show it with `grep -rnw labels src/pyntpot/maps --include=*.py`: the only
reader is `attribution.py`. The docs pass rewrote the comment to say what the
code does; changing which stage reads the field is a code change, which P6
does not make.

Possible fix: have `letter` skip the label plate when `labels` is off, and
have `draw_attribution` stop reading it, so the attribution is written
whenever `compose` is asked for it. The goldens use the default theme
(`labels = true`), so neither change moves a golden pixel; add a unit test for
each half.
