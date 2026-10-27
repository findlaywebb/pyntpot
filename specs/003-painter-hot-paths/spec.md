# 003 — Painter hot paths

GitHub issue: [#81](https://github.com/findlaywebb/pyntpot/issues/81) (the painter half;
the gates half is `specs/002-parallel-gates/`).

## Problem

Painting is most of every slow test. CodSpeed on `main` (simulation mode, so relative
only): `paint` 41.4 s, `compose` 2.8 s, `fetch` 2.7 s, `letter` 1.1 s. A `cProfile` of the
Lynmouth paint (`support.golden.paint_fixture`, 56 s wall on four contended cores,
2026-10-27) puts the time here:

| Cost | Self time | Where |
|---|---|---|
| `ink_density` | 10.7 s over 8 calls | `ink/pad.py`, element-wise on supersampled pads |
| `cumsum` in the box blur | 8.8 s over 4872 calls | `ink/noise.py::_box1`, the axis-0 pass is strided |
| lossless WebP encode | 4.3 s over 4 plates | `ink/io.py::save_webp` |
| `km_rt` | 3.7 s over 23 calls | `ink/pigment.py`, Kubelka–Munk compositing |
| `value_noise` | 3.3 s over 94 calls | `ink/noise.py` |
| `np.clip` calls | 1.9 s over 121519 calls | many small clips, mostly in `ink/raster.py::_edge` |

`fetch` from a warm cache, which makes no request, costing as much as `compose` is a
further lead. The same Lynmouth map is also painted about nine times per golden run, by
separate golden-marked unit tests.

## Acceptance criteria

- [x] A profile of the Lynmouth paint and of one place card, before and after, is
      recorded in `docs/features/tests-fast-gates.md`.
- [x] Every speed-up keeps every decoded pixel exact: the goldens, plates, docs images and
      masters are unchanged as pixels, checked by the exact local golden run.
- [x] A change that alters file bytes but not pixels (the WebP effort setting) is allowed,
      under an ADR, with the plate bytes re-pinned once in the same PR (maintainer,
      2026-10-27).
- [x] The CodSpeed `paint` benchmark falls, and no benchmark regresses by more than
      CodSpeed's own threshold.
- [x] Each rewrite is proven bit-identical to the old code on the inputs a real Lynmouth paint
      passes it, with the evidence in the PR; the exact local golden run is the standing
      check that it stays so.
- [x] Each rewrite that relies on an invariant (a pixel with no ink or paint is left
      exactly as it was; a cached field is the one a fresh build makes) has a unit or
      property test of that invariant. No new pinned hash: pinned hashes already differ
      across platforms (#86).
- [x] When the work lands, the measurements move into `docs/explanation/performance.md`,
      `docs/features/tests-fast-gates.md` is deleted and #81 is closed.

## Out of scope

- Changes that move a pixel, even by one level: those need their own ADR and goldens.
- New dependencies (scipy, numba): the runtime stays numpy and Pillow.
- Shared random generators (#61): a separate defect, and it moves goldens.
- The gate wiring: `specs/002-parallel-gates/`.
