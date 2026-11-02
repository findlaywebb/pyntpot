# A river's wet brush pools into a blob where the stroke starts at the card edge

GitHub issue: [#55](https://github.com/findlaywebb/pyntpot/issues/55)

On the Ambleside hero card (`docs/images/hero.webp`) the Brathay enters at the lower left as a
wide, dark blob with a comma-shaped tail, then continues as a thin line. The river is drawn
with a wet brush, and where the stroke begins inside the card the brush's pool gain stamps
one heavy dab. Lowering the theme's `pen_pool_gain`, `ink_dip_mult` and the `major` river
override's `pool` leaves it as it is, so it is not the theme's setting alone.

Found while calming the hero (round-2 map critique follow-up, 2026-10-25).

To show it: paint the hero from `tests/fixtures/ambleside/` in `examples/themes/ambleside-hero.toml`
and look at the lower left.

Possible fix: start a river stroke with no extra load when it enters from outside the card,
or taper the first dab.
