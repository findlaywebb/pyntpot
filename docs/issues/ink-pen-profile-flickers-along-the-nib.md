# A stroke laid exactly along the nib still flickers past the property's bound

GitHub issue: [#225](https://github.com/findlaywebb/pyntpot/issues/225)

Area: ink (pen).

`tests/property/test_pen_profile.py::TestPenProfile::test_a_stepped_straight_stroke_does_not_flicker`
asks that a pixel staircase at any angle to the nib keep one width: no two neighbouring
samples of `pen_profile` differ by more than 0.12, and no inner sample is more than 0.12 from
the true width `(1 - thin) + thin * |sin(heading - nib)|`, with `thin = 0.85`.

Hypothesis found a counterexample on unchanged `main` (`38179789`), while 010 was being
built: `heading == nib ≈ 2.3724`, `length = 42`, giving 0.1204 against the 0.12 bound. The
stroke there lies exactly along the nib, so its true width is the hairline,
`1 - thin = 0.15`, the edge of the range where #42 (the broad nib's width flickering where a
stroke is nearly along the nib) was fixed. Which of the two assertions it breaks is not yet
recorded.

Two consequences:

- CI can go red on it at random, whenever Hypothesis happens to draw that region; once a
  machine's example database holds it, every local run there fails.
- The bound may be right and the profile wrong along the nib, or the profile may be right and
  the bound too tight at the hairline; that is the first thing to decide. Loosening the bound
  to get green is not the fix (CLAUDE.md: a red gate is the architecture speaking).

Reproduce with the counterexample pinned as an `@example(heading=2.3724, nib=2.3724, length=42)`
on the property.
