### Image changes

Before: `origin/main`. After: `working tree`. 4 changed, 0 added, 0 removed.
Changed counts the pixels past channel delta 2; the parity gate bounds it at 0.005 (ADR 0030). Local: the box covers at most a quarter of the image.

| File | Size | Changed | Max delta | Box | Extent |
|---|---|---|---|---|---|
| `docs/images/places/oxford.webp` | 720x643 | 0.238284 (over 0.005) | 208 | 0,0 to 720,643 | widespread |
| `docs/images/places/y-fenni.webp` | 720x643 | 0.181720 (over 0.005) | 208 | 0,32 to 720,643 | widespread |
| `tests/golden/docs/places/oxford.png` | 240x214 | 0.056231 (over 0.005) | 171 | 37,33 to 210,110 | widespread |
| `tests/golden/docs/places/y-fenni.png` | 240x214 | 0.058664 (over 0.005) | 185 | 26,59 to 206,197 | widespread |

<details open>
<summary><code>docs/images/places/oxford.webp</code>: widespread, 0.238284</summary>

![docs/images/places/oxford.webp: before, after and difference](docs/images/places/oxford.webp.diff.png)

![docs/images/places/oxford.webp: the most-changed region at 1:1](docs/images/places/oxford.webp.crop.png)

</details>

<details open>
<summary><code>docs/images/places/y-fenni.webp</code>: widespread, 0.181720</summary>

![docs/images/places/y-fenni.webp: before, after and difference](docs/images/places/y-fenni.webp.diff.png)

![docs/images/places/y-fenni.webp: the most-changed region at 1:1](docs/images/places/y-fenni.webp.crop.png)

</details>

<details open>
<summary><code>tests/golden/docs/places/oxford.png</code>: widespread, 0.056231</summary>

![tests/golden/docs/places/oxford.png: before, after and difference](tests/golden/docs/places/oxford.png.diff.png)

![tests/golden/docs/places/oxford.png: the most-changed region at 1:1](tests/golden/docs/places/oxford.png.crop.png)

</details>

<details open>
<summary><code>tests/golden/docs/places/y-fenni.png</code>: widespread, 0.058664</summary>

![tests/golden/docs/places/y-fenni.png: before, after and difference](tests/golden/docs/places/y-fenni.png.diff.png)

![tests/golden/docs/places/y-fenni.png: the most-changed region at 1:1](tests/golden/docs/places/y-fenni.png.crop.png)

</details>
