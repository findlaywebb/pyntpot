# 0073 — Boilerplate-free calls

Status: accepted

Spec: `specs/010-blank-paper-and-keyword-arguments/`. Issues: #166 (this ADR's rules 1 to 4),
#165 and #167 (rules 5 to 11). It amends 0007, 0026, 0027 and 0068, each of which stays as
written. Rules 5 to 11 land in spec 010a, which may amend them in its own pull request if its
implementation or review needs it (the precedent is ADR 0070 rule 17, which landed in 009a).
The index row says so until 010a lands.

## Context

Scoping group E-a ("Kill the boilerplate") found three calls that make a caller write the same
lines again and again: a blank sheet needs a hand-built `Canvas` and a `Sheet(h, w, ...)` whose
positional order is the one way to transpose height and width without an error; a lettering
over an image needs a hand-built nib surface, a plate round trip through a file and a
composite; and the basemap's cache key is rebuilt by the caller from the providers it already
passed once. Three API changes remove that, and the caller migration the first forces is too
large to share a pull request with the others, so E-a is two stacked pull requests (010 for
rules 1 to 4, 010a for rules 5 to 11) and the example sweep is a third (010b). No pixel moves
in any of them.

## Decision

1. **`Sheet` by keyword, width first.** `@dataclass(kw_only=True)`; the fields are reordered
   `w, h, gran_px, seed, fibre, fibre_stretch, fibre_angle, fibre_cell` (then the five
   `init=False` fields), so the repr and `Attributes:` read width first like `Canvas` and
   Pillow. Every field is keyword-only, so an old positional call, the only way to copy the
   order wrong, fails with `TypeError` instead of transposing. This is a breaking change to the
   documented signatures of `Sheet` (one of 0007's façade names), `wash` (0068's "`wash` keeps
   the signature `wash(cover, sheet, base, pool, options=None)`" sentence, rule 4) and
   `brush_from_id` (bound by 0026's member rule: "the names in `__all__` and their documented
   signatures").
2. **`Canvas.pixels(*, w, h)`**, a classmethod returning
   `Canvas(0.0, 0.0, float(w), float(h), w, h)`: a canvas that is only its pixel grid, one
   world unit per pixel. Under 1 in either raises `ValueError`. The constructor keeps its
   positional, width-first form, which `maps` uses for a real metre box.
3. **`paper_plate(sheet, canvas, style, display_px=None)`**: `None` measures the grid against
   `canvas.w`. Additive.
4. **`wash(cover, sheet, *, body, pool, options=None)`** and
   **`brush_from_id(brush_id, width_display_px, *, scale=1.0, style=None, override=None)`**.
   `base` is renamed `body`, the glossary's word for the flat part of a wash, so one concept
   has one name. `style=None` means `BrushStyle()`, the default look (ADR 0069). Supersedes
   0068's "`wash` keeps the signature `wash(cover, sheet, base, pool, options=None)`" (a new
   per-wash setting is still a new `WashOptions` field) and `brush_from_id`'s documented
   positional signature (0026). Tokens are unchanged: `override` still names one of the six
   `BrushStyle.brush_overrides` keys.
5. **`nib_rgba(marks, surface, groups) -> tuple[np.ndarray, np.ndarray] | None`** joins
   `pyntpot.letters.__all__` (010a): the nib plate's straight colour, `(h, w, 3)`, and its
   alpha, `(h, w)`, floats in 0 to 1 at the surface's size, uncast (float32 for a float32
   darkness); `None` when nothing is drawn. `nib_plate` writes exactly these arrays.
6. **`letter_over(image, marks, groups=None, *, gran_px, scale=2, dark=None) -> np.ndarray`**
   joins `pyntpot.letters.__all__` (010a). The marks are in the image's pixels. It strokes them
   with `nib_rgba` on a surface `scale` times the image (built with `Canvas.pixels`), with the
   darkness `dark` (the image's size; `None` is bare paper, 0) brought up bilinearly and the
   paper's grain cell `gran_px` (image pixels) times `scale`. It stores the plate as the 8-bit
   RGBA `nib_plate` would write, converts it explicitly to premultiplied `RGBa`, shrinks it to
   the image with Lanczos, converts back to `RGBA`, and returns
   `image * (1 - alpha) + colour * alpha` as a new array. With nothing drawn it returns a copy
   of `image`. A wrong-shaped image or `dark`, or a `scale` under 1, raises `ValueError`.
   `groups=None` means `NibGroups()`.
7. **`NibGroups`' five fields default to the default look** (`NibStyle()`, `FaceStyle()`,
   `HandStyle()`, `BrushStyle()`, `PaperStyle()`), each by `default_factory` (010a).
   Positional construction is unchanged (0068's "keeps positional construction" holds).
   Supersedes the `NibGroups` docstring's "it holds no defaults" (0026's member list is
   unchanged).
8. **The 8-bit Lanczos step stays, premultiplied explicitly.** Measured with three plates (a
   wordmark on bare paper and two names over a darkness ramp). With `plate_lossless` on (the
   default, and every shipped and example style), lossless WebP keeps the alpha exactly and the
   colour of every pixel whose alpha is above 0. Pillow premultiplies an RGBA image inside a
   `resize` that changes the size, so at a 2x shrink `.convert("RGBa")` before the resize and no
   conversion give the same pixels. A `resize` to the image's own size is a plain copy with no
   premultiply (Pillow returns `self.copy()` before its premultiply branch), and the
   attribution strokes at the card's own size whenever the card is supersampled 2x or more (its
   plate factor is 1). So the shared shrink always runs
   `.convert("RGBa").resize(...).convert("RGBA")`, which is the attribution's own form and, at
   any changed size, exactly what Pillow does inside. An in-memory 8-bit plate shrunk that way
   is bit-identical to the file round trip at every scale (measured at supersample 1, 2 and 3),
   and dropping the file moves no pixel. With `plate_lossless` off, the file was lossy, and the
   in-memory plate is the lossless one. A float resize is rejected here: it would move every
   lettered docs image and the attribution for a difference an 8-bit output cannot show. Moving
   to one is its own decision with its own regeneration.
9. **The attribution writes no file** (010a): `maps.attribution` strokes with `nib_rgba` and
   shrinks with the same explicit-premultiply 8-bit Lanczos step, so it is bit-identical for
   every lossless style, at the card's own size included.
10. **`Basemap.key: str`**, a required keyword-only field, last in the class (010a): the cache
    key of the payloads it was built from, as `Cache.ensure` returned it. `fetch` and
    `build_basemap` set it. It is not in `canonical`, so the base hash and every plate are
    unchanged. The invariant "it carries no cache key, because the cache owns its keys" becomes
    "it carries the key the cache gave it and computes none". Supersedes 0068's "a field added
    to one goes at the end" for this field only: required, keyword-only, so a basemap built by
    hand names its key instead of getting a sentinel.
11. **Callers read the key from the basemap** (010a): `paint(basemap, style,
    cache.plates_dir(basemap.key))`, `candidate_export(track, cache, basemap.key)`,
    `vector_layers(track, cache, basemap.key, style)`. No signature changes; 0027's "Both cache
    readers take the cache key" holds, and a caller no longer passes the providers a second
    time to build it.

## Consequences

- The PR titles: 010 carries `!` (rules 1 and 4 break positional callers); 010a does not, its
  `Basemap` line carrying `!` under Changelog. No golden regeneration in either, and the
  sweep (010b) moves no pixel either: every change is to how an argument is spelled, never to
  its value.
- The word "base" stays in `maps`' cover vocabulary: `maps/painter/cover.py` unpacks `base,
  pool` from the cover settings, and `CoverStyle.pale_base` feeds the wash body. Those are
  theme keys, so renaming them would be a breaking theme change, out of scope here.
- 0007, 0026, 0027 and 0068 stay as written; the index rows carry an "amended by 0073" clause.
- The ADR number skips 0072, which spec 008a (the theme preview card) holds.
