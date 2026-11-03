### Image changes

Before: `origin/main`. After: `working tree`. 4 changed, 0 added, 0 removed.
Changed counts the pixels past channel delta 2; the parity gate bounds it at 0.005 (ADR 0030). Local: the box covers at most a quarter of the image.

| File | Size | Changed | Max delta | Box | Extent |
|---|---|---|---|---|---|
| `docs/images/how-to/command-line.webp` | 720x583 | 0.121172 (over 0.005) | 225 | 0,95 to 720,583 | widespread |
| `tests/golden/docs/how-to/command-line.png` | 240x194 | 0.037414 (over 0.005) | 245 | 17,41 to 213,73 | local |
| `tests/golden/lynmouth/labels-centreline.webp` | 1800x1457 | 0.054307 (over 0.005) | 255 | 114,304 to 1800,608 | local |
| `tests/golden/lynmouth/map.png` | 1800x1457 | 0.029841 (over 0.005) | 215 | 122,308 to 1589,540 | local |

<details open>
<summary><code>docs/images/how-to/command-line.webp</code>: widespread, 0.121172</summary>

<img src="docs/images/how-to/command-line.webp.diff.png" alt="docs/images/how-to/command-line.webp: before, after and difference" width="720">

<img src="docs/images/how-to/command-line.webp.crop.png" alt="docs/images/how-to/command-line.webp: the most-changed region at 1:1">

</details>

<details open>
<summary><code>tests/golden/docs/how-to/command-line.png</code>: local, 0.037414</summary>

<img src="tests/golden/docs/how-to/command-line.png.diff.png" alt="tests/golden/docs/how-to/command-line.png: before, after and difference" width="720">

<img src="tests/golden/docs/how-to/command-line.png.crop.png" alt="tests/golden/docs/how-to/command-line.png: the most-changed region at 1:1">

</details>

<details open>
<summary><code>tests/golden/lynmouth/labels-centreline.webp</code>: local, 0.054307</summary>

<img src="tests/golden/lynmouth/labels-centreline.webp.diff.png" alt="tests/golden/lynmouth/labels-centreline.webp: before, after and difference" width="720">

<img src="tests/golden/lynmouth/labels-centreline.webp.crop.png" alt="tests/golden/lynmouth/labels-centreline.webp: the most-changed region at 1:1">

</details>

<details open>
<summary><code>tests/golden/lynmouth/map.png</code>: local, 0.029841</summary>

<img src="tests/golden/lynmouth/map.png.diff.png" alt="tests/golden/lynmouth/map.png: before, after and difference" width="720">

<img src="tests/golden/lynmouth/map.png.crop.png" alt="tests/golden/lynmouth/map.png: the most-changed region at 1:1">

</details>
