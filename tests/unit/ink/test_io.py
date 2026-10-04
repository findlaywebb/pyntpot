"""Tests for the plate encoders: lossless keeps the ramp and a plate carries its own alpha."""

import numpy as np
from PIL import Image

from pyntpot.ink.io import save_rgba, save_webp, to_img


def _ramp_plate(h: int = 96, w: int = 96) -> np.ndarray:
    """A card carrying narrow coloured marks on a grainy ground.

    Three or four pixels wide, drawn at an angle, on paper with fine noise on
    it: the plate the lossy encoder is worst at and the one the painter writes.
    """
    rng = np.random.default_rng(3)
    arr = np.full((h, w, 3), 0.93, np.float32)
    arr -= rng.random((h, w, 1)).astype(np.float32) * 0.03
    yy = np.arange(h, dtype=np.float32)[:, None]
    xx = np.arange(w, dtype=np.float32)[None, :]
    for x0, pig in ((22.0, (0.42, 0.24, 0.13)), (58.0, (0.15, 0.36, 0.50))):
        d = np.abs(xx - (x0 + yy * 0.32))
        cov = np.clip(1.0 - d / 1.9, 0.0, 1.0) ** 0.8
        arr *= 1.0 - cov[..., None] * (1.0 - np.array(pig, np.float32))
    return np.clip(arr, 0.0, 1.0)


def _plateau_share(arr: np.ndarray) -> float:
    """Share of steps across the marks that do not move at all.

    The fault, as a number: a ramp that is two
    flats and a jump spends most of its width not changing, and a continuous
    one moves at nearly every pixel.
    """
    got = []
    grey = arr.mean(axis=2)
    for r in range(8, arr.shape[0] - 8):
        for c in (22, 58):
            x0 = int(c + r * 0.32)
            seg = grey[r, max(x0 - 5, 0) : x0 + 6]
            if seg.size > 6:
                got.append(float((np.abs(np.diff(np.round(seg * 255))) < 1).mean()))
    return float(np.mean(got))


def _grain(arr: np.ndarray) -> float:
    """High-frequency energy: what is left of the paper after a 3 by 3 mean."""
    a = arr.mean(axis=2)
    k = (a[:-2, 1:-1] + a[2:, 1:-1] + a[1:-1, :-2] + a[1:-1, 2:] + a[1:-1, 1:-1]) / 5.0
    return float(np.abs(a[1:-1, 1:-1] - k).mean())


def test_the_lossy_encoder_is_what_flattens_a_narrow_strokes_ramp(tmp_path):
    """The two plateaus and the step between them are the encoder, not the paint.

    A mark under four pixels wide is narrower than the 4 by 4 block the lossy
    encoder transforms in and than the half resolution chroma plane it carries,
    so its edge-to-centre ramp comes back as a light flat, a jump and a dark
    flat. Lossless returns the ramp the painter composed, exactly.
    """
    truth = _ramp_plate()
    img = to_img(truth, np.random.default_rng(23))
    ref = np.asarray(img, np.float32) / 255.0

    lossy = tmp_path / "lossy.webp"
    clean = tmp_path / "clean.webp"
    n_lossy = save_webp(img, lossy, quality=74)
    n_clean = save_webp(img, clean, quality=74, lossless=True)
    back_lossy = np.asarray(Image.open(lossy).convert("RGB"), np.float32) / 255.0
    back_clean = np.asarray(Image.open(clean).convert("RGB"), np.float32) / 255.0

    assert np.array_equal(back_clean, ref)  # exactly what was composed
    assert np.abs(back_lossy - ref).max() > 0.02  # and the lossy one is not
    # The fault itself: flats across the mark, and the paper's grain gone.
    assert _plateau_share(back_lossy) > _plateau_share(back_clean) * 1.4
    assert _grain(back_lossy) < _grain(back_clean) * 0.75
    assert n_clean > n_lossy  # which is what it costs


def test_a_plate_can_carry_its_own_colour_and_its_own_alpha(tmp_path):
    """Multiply can only darken; a backing wash in the paper's colour lightens."""
    rgb = np.zeros((4, 6, 3), np.float32)
    rgb[..., 0] = 1.0
    alpha = np.linspace(0.0, 1.0, 24, dtype=np.float32).reshape(4, 6)
    path = tmp_path / "labels.webp"
    assert save_rgba(rgb, alpha, path) > 0
    back = Image.open(path).convert("RGBA")
    assert back.size == (6, 4)
    assert back.getchannel("A").getextrema()[0] == 0
