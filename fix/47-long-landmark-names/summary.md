### Image changes

Before: `origin/main`. After: `working tree`. 4 changed, 0 added, 0 removed.
Changed counts the pixels past channel delta 2; the parity gate bounds it at 0.005 (ADR 0030). Local: the box covers at most a quarter of the image.

| File | Size | Changed | Max delta | Box | Extent |
|---|---|---|---|---|---|
| `docs/images/how-to/command-line.webp` | 720x583 | 0.128507 (over 0.005) | 225 | 0,112 to 720,583 | widespread |
| `tests/golden/docs/how-to/command-line.png` | 240x194 | 0.037973 (over 0.005) | 244 | 17,41 to 213,83 | local |
| `tests/golden/lynmouth/labels-centreline.webp` | 1800x1457 | 0.054836 (over 0.005) | 255 | 114,304 to 1800,1022 | widespread |
| `tests/golden/lynmouth/map.png` | 1800x1457 | 0.029916 (over 0.005) | 215 | 122,308 to 1590,620 | local |

<details open>
<summary><code>docs/images/how-to/command-line.webp</code>: widespread, 0.128507</summary>

![docs/images/how-to/command-line.webp: before, after and difference](docs/images/how-to/command-line.webp.diff.png)

![docs/images/how-to/command-line.webp: the most-changed region at 1:1](docs/images/how-to/command-line.webp.crop.png)

</details>

<details open>
<summary><code>tests/golden/docs/how-to/command-line.png</code>: local, 0.037973</summary>

![tests/golden/docs/how-to/command-line.png: before, after and difference](tests/golden/docs/how-to/command-line.png.diff.png)

![tests/golden/docs/how-to/command-line.png: the most-changed region at 1:1](tests/golden/docs/how-to/command-line.png.crop.png)

</details>

<details open>
<summary><code>tests/golden/lynmouth/labels-centreline.webp</code>: widespread, 0.054836</summary>

![tests/golden/lynmouth/labels-centreline.webp: before, after and difference](tests/golden/lynmouth/labels-centreline.webp.diff.png)

![tests/golden/lynmouth/labels-centreline.webp: the most-changed region at 1:1](tests/golden/lynmouth/labels-centreline.webp.crop.png)

</details>

<details open>
<summary><code>tests/golden/lynmouth/map.png</code>: local, 0.029916</summary>

![tests/golden/lynmouth/map.png: before, after and difference](tests/golden/lynmouth/map.png.diff.png)

![tests/golden/lynmouth/map.png: the most-changed region at 1:1](tests/golden/lynmouth/map.png.crop.png)

</details>
