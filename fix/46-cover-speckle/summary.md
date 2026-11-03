### Image changes

Before: `/tmp/claude-0/-home-user-pyntpot/1d79c270-6236-5bf4-82b6-e519237905dd/scratchpad/g46/before`. After: `/tmp/claude-0/-home-user-pyntpot/1d79c270-6236-5bf4-82b6-e519237905dd/scratchpad/g46/after`. 4 changed, 0 added, 0 removed.
Changed counts the pixels past channel delta 2; the parity gate bounds it at 0.005 (ADR 0030). Local: the box covers at most a quarter of the image.

| File | Size | Changed | Max delta | Box | Extent |
|---|---|---|---|---|---|
| `docs/images/hero.webp` | 1200x854 | 0.389120 (over 0.005) | 95 | 0,0 to 1200,854 | widespread |
| `docs/images/social-preview.jpg` | 1280x640 | 0.272316 (over 0.005) | 93 | 0,0 to 1280,640 | widespread |
| `tests/golden/docs/hero.png` | 240x171 | 0.235453 (over 0.005) | 92 | 0,0 to 240,171 | widespread |
| `tests/golden/docs/social-preview.png` | 240x120 | 0.204687 (over 0.005) | 97 | 0,0 to 240,120 | widespread |

<details open>
<summary><code>docs/images/hero.webp</code>: widespread, 0.389120</summary>

![docs/images/hero.webp: before, after and difference](docs/images/hero.webp.diff.png)

![docs/images/hero.webp: the most-changed region at 1:1](docs/images/hero.webp.crop.png)

</details>

<details open>
<summary><code>docs/images/social-preview.jpg</code>: widespread, 0.272316</summary>

![docs/images/social-preview.jpg: before, after and difference](docs/images/social-preview.jpg.diff.png)

![docs/images/social-preview.jpg: the most-changed region at 1:1](docs/images/social-preview.jpg.crop.png)

</details>

<details open>
<summary><code>tests/golden/docs/hero.png</code>: widespread, 0.235453</summary>

![tests/golden/docs/hero.png: before, after and difference](tests/golden/docs/hero.png.diff.png)

![tests/golden/docs/hero.png: the most-changed region at 1:1](tests/golden/docs/hero.png.crop.png)

</details>

<details open>
<summary><code>tests/golden/docs/social-preview.png</code>: widespread, 0.204687</summary>

![tests/golden/docs/social-preview.png: before, after and difference](tests/golden/docs/social-preview.png.diff.png)

![tests/golden/docs/social-preview.png: the most-changed region at 1:1](tests/golden/docs/social-preview.png.crop.png)

</details>
