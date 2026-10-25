# A broad nib's width flickers where a stroke is nearly along the nib

`_pen_profile` in `letters/nib.py` sets the width along each stroke from the angle between
the stroke's local direction and the nib, scaled by `label_pen_thin`. The direction is read
from the stroke's own points, which come from a thinned skeleton and change direction a
pixel at a time. Where a stroke runs close to the nib's angle and `label_pen_thin` is high,
a small change of direction swings the width between wide and hairline, stamp by stamp. At
0.85 on `docs/images/explanation/nib-angles.webp` the edges of the thinned strokes are
jagged and stair-stepped, with spikes where the width flips, and read as damage and not as a
broad nib. At the 90 degree cell the K and the w break into dots.

To show it: letter "Keswick" at 52 px with `NibStyle(label_pen_angle_deg=90,
label_pen_thin=0.85, label_pen_width_px=3.4)` and look at the diagonals and the curves; the
width profile of one of them, plotted against distance, is a saw tooth.

Possible fix: smooth the stroke's direction before the width is computed, with a short
moving average of the tangent over a few stamps (about one nib width of path), and keep the
profile's samples evenly spaced along the smoothed path. The lettered goldens and docs
images move, so it needs a regeneration window of its own with an ADR.

Found by the P7.V13 round-2 reference critique (2026-10-25).
