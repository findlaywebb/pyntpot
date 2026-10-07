# Watercolour visual identity for a documentation website

Research date: 7 October 2026. Scope: CSS/SVG techniques, accessibility, dark mode, image weight, hand-lettered titles, pigment palettes and real examples, aimed at pyntpot generating its own docs artwork as rasters and applying it with CSS. Items marked "Inference" are my reasoning, not sourced fact.

## 1. CSS techniques: washes, painted edges, highlighters, blending, SVG filters, paper grain

### Takeaway
Everything needed is Baseline except `box-decoration-break`, which still needs a `-webkit-` prefix and is marked "limited availability". Masks (Baseline since December 2023), `mix-blend-mode` (since January 2020) and `image-set()` with `type()` (since September 2023) are all safe to use. Live SVG `feTurbulence`/`feDisplacementMap` filters are expensive, especially when animated or covering large areas. pyntpot should **pre-render** washes, edges and grain as raster or alpha-mask images rather than relying on runtime SVG filters.

### Cited Findings
- **Highlighter behind wrapped inline text**: by default, padding, border, box-shadow and similar decorations on an inline element are not applied where the text wraps onto a new line. `box-decoration-break: clone` fixes this by rendering each line fragment independently. — [DEV: highlighter effect](https://dev.to/nhuynh1/highlighter-effect-adding-box-decorations-like-padding-to-inline-elements-that-wrap-onto-multiple-lines-10ip)
- MDN marks `box-decoration-break` as "Limited availability… not Baseline because it does not work in some of the most widely-used browsers", and its examples write both `-webkit-box-decoration-break: clone;` and `box-decoration-break: clone;` (page last modified 21 July 2026). — [MDN box-decoration-break](https://developer.mozilla.org/en-US/docs/Web/CSS/box-decoration-break)
- With `clone`, "the background is also drawn independently for each fragment, which means that a background image with `background-repeat: no-repeat` may nevertheless repeat multiple times". `border-radius`, `border-image` and `box-shadow` also apply per fragment. With `slice` (the default), the background spans all fragments as one continuous box. — [MDN box-decoration-break](https://developer.mozilla.org/en-US/docs/Web/CSS/box-decoration-break)
- **Painted edges via masks**: `mask-image` is Baseline Widely available "since December 2023", though "some parts of this feature may have varying levels of support".
  - `mask-mode: alpha` uses only the alpha channel. `luminance` multiplies luminance by alpha. The default `match-source` treats most images as alpha masks, while SVG `<mask>` elements default to luminance.
  - Mask images load only over http(s); `file://` sources render as transparent black. — [MDN mask-image](https://developer.mozilla.org/en-US/docs/Web/CSS/mask-image)
- **Pigment-like overlap**: `mix-blend-mode` is Baseline Widely available "since January 2020". It creates a stacking context and blends with the backdrop. Use `isolation: isolate` on a parent to stop blending reaching past the group, and `background-blend-mode` to blend an element's own background layers with each other. — [MDN mix-blend-mode](https://developer.mozilla.org/en-US/docs/Web/CSS/mix-blend-mode)
- **Responsive and format-negotiated CSS backgrounds**: `image-set()` is Baseline Widely available "since September 2023". It supports resolution descriptors (`1x`, `2x`, `dppx`) and `type("image/avif")` so the browser skips formats it cannot decode, for example `image-set("x.avif" type("image/avif"), "x.jpg" type("image/jpeg"))`. Gradients are allowed as candidates. — [MDN image-set()](https://developer.mozilla.org/en-US/docs/Web/CSS/image/image-set)
- **Paper grain / noise overlay (CSS-Tricks "Grainy Gradients")**: an SVG with `<feTurbulence type='fractalNoise' baseFrequency='0.65' numOctaves='3'>` on a `<rect>` is used as a background layer under a gradient, then sharpened with `filter: contrast(170%) brightness(1000%)`.
  - `mix-blend-mode: multiply` with `isolation: isolate` is suggested for the overlay.
  - Blink and WebKit render `mix-blend-mode` differently, so test across browsers.
  - A commenter notes the trick is poor for performance, and another suggests masks as an alternative. — [CSS-Tricks: Grainy Gradients](https://css-tricks.com/grainy-gradients/)
- **SVG turbulence/displacement performance**: a GSAP forum thread reports that animating `feTurbulence` + `feDisplacementMap` was "really sluggish on iOS" and sometimes crashed Safari tabs. A respondent says SVG filters work only in short bursts or on small areas. — [GreenSock forum](https://greensock.com/forums/topic/33075-gsap-and-feturbulence-mobile-performance/)
- **Tyler Hobbs' watercolour algorithm** (context for pyntpot's own art):
  - Recursively deform polygons by displacing each segment's midpoint with a Gaussian draw.
  - Deform the base polygon about 7 times. For each layer, deform 4 to 5 more times, then draw it at about 4% opacity, with 30 to 100 layers.
  - A per-segment variance gives sharp edges (low variance) or soft edges (high variance), and children inherit slightly reduced variance.
  - Each layer has a texture mask of about 900 to 1000 random circles.
  - Colours are interleaved across layers (for example five red, five yellow, then red again). This is not physically accurate mixing, but it looks good. — [Tyler Hobbs: A Guide to Simulating Watercolor Paint with Generative Art](https://www.tylerxhobbs.com/words/a-guide-to-simulating-watercolor-paint-with-generative-art)

### Inferences
- **Recommended build**: pyntpot renders each decorative element as a static raster and CSS only places it.
  - Heading wash: transparent-edged AVIF or WebP as `background-image` on the heading or a `::before` pseudo-element.
  - Highlighter: a short horizontal brush-stroke strip, stretched with `background-size: 100% 0.6em` on the bottom half of the line box, with `box-decoration-break: clone` (prefixed) so each wrapped line gets its own stroke. Fallback: a flat translucent `linear-gradient`.
  - Section divider: a wide `<hr>` replaced by a painted stroke via `border-image` or `background`.
  - Painted edges: a ragged alpha mask PNG applied with `mask-image` to flat-coloured blocks, so the colour stays a CSS token and is easy to theme.
- Splitting the work into a **mask (shape)** and a **CSS colour (pigment)** is the most theme-friendly design. pyntpot would emit greyscale or alpha "edge" masks and paper-grain tiles, and CSS would supply the colours. This keeps dark mode and `prefers-contrast` handling in CSS without needing new artwork for each colour.
- Use `mix-blend-mode: multiply` for overlapping washes in light mode only. On a dark backdrop, multiply darkens towards black and the washes disappear. Dark mode needs `screen`, or a separate approach (see section 3).
- Avoid live `feTurbulence` filters on large or animated elements. If one is used at all, keep it static, small and at low `numOctaves`.

### Gaps
- I did not retrieve per-browser version tables (the MDN compatibility tables did not load). The exact browsers lacking unprefixed `box-decoration-break` (historically Chromium and Safari needed the prefix) are not confirmed for 2026.
- I found no quantitative benchmark of the paint cost of `mask-image` or `mix-blend-mode` versus plain backgrounds.
- No authoritative Smashing Magazine or web.dev article specific to watercolour CSS effects turned up.

## 2. Accessibility: contrast over painted backgrounds, motion and contrast preferences, colour-blind safety, text in images

### Takeaway
WCAG measures contrast against the background the text actually sits on, and failure technique F83 explicitly covers background images. The only robust guarantee is to keep text over flat paper colour, or over a scrim or wash whose darkest and lightest pixels have been checked against the text colour. Titles should stay real text with a painted backing: WCAG 1.4.5 says headings should be styled with CSS, not bitmaps.

### Cited Findings
- **WCAG 2.2 SC 1.4.3**:
  - Thresholds are 4.5:1 for normal text and 3:1 for large text. Large text is "18 point text or 14 point bold text", about 24px, or 18.5px bold.
  - Ratios must not be rounded: 4.499:1 fails.
  - Contrast "is measured with respect to the specified background over which the text is rendered in normal usage".
  - Failure F83 is "using background images that do not provide sufficient contrast with foreground text". — [W3C Understanding 1.4.3](https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html)
- Exempt text: pure decoration ("the words can be rearranged or substituted without changing their purpose"), text in a picture with significant other visual content, and logotypes. Text with poor contrast "due to corporate identity or brand guidelines is *not* exempted". — [W3C Understanding 1.4.3](https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html)
- **WCAG 1.4.5 Images of Text**:
  - Use text rather than images of text where the technology allows.
  - Exceptions: images that are customisable (font, size, colour and background can be set), essential presentation, and logotypes.
  - The worked example has an author who "uses CSS to achieve the same result" for headings.
  - Images of text alongside real text carrying the same information also satisfy the criterion. — [W3C Understanding 1.4.5](https://www.w3.org/WAI/WCAG22/Understanding/images-of-text.html)
- **`prefers-contrast`**:
  - Values are `no-preference`, `more`, `less` and `custom`. `custom` matches the condition that `forced-colors: active` detects.
  - Baseline Widely available since May 2022.
  - MDN's example swaps a dashed outline for a solid one under `(prefers-contrast: more)`. — [MDN prefers-contrast](https://developer.mozilla.org/en-US/docs/Web/CSS/@media/prefers-contrast)
- **Colour-blind-safe reference palette (Okabe-Ito)**: #E69F00 orange, #56B4E9 sky blue, #009E73 bluish green, #F0E442 yellow, #0072B2 blue, #D55E00 vermillion, #CC79A7 reddish purple, #000000 black. It is designed to stay distinguishable across common colour-vision deficiencies. — [Siegal lab, NYU: colour palette](https://siegal.bio.nyu.edu/color-palette/); [ConceptViz reference](https://conceptviz.app/blog/okabe-ito-palette-hex-codes-complete-reference)

### Inferences
- **Practical contrast guarantee pyntpot can automate**: because pyntpot generates the artwork, a build step can compute the WCAG contrast of the text colour against **every pixel** (or the 1st and 99th luminance percentile) of the region behind the text, composited onto the paper colour, and fail the build below 4.5:1. This is the "worst-case pixel" method. It suits pyntpot's gate-driven ethos.
- Prefer layouts where body text never sits on a wash. Washes go behind headings (large text, 3:1) and in margins, dividers and hero areas. Inline highlighter strokes must be light enough that body text still passes 4.5:1 against the darkest stroke pixel.
- Under `@media (prefers-contrast: more)` and `(forced-colors: active)`, drop the washes and grain (`background-image: none; mask-image: none`) and use solid tokens. Under `prefers-reduced-motion`, disable any animated "bleed-in" reveal. No source was fetched for reduced-motion specifically; that recommendation rests on general practice.
- Watercolour tints differ mainly in hue at similar lightness, which is exactly what fails for colour-blind readers. Admonition types (note, warning, danger) must carry an icon or label as well as a tint, in line with WCAG 1.4.1 Use of Colour. That criterion is not quoted from a fetched source here.
- Mark decorative art as `alt=""` or `aria-hidden`, or put it in CSS backgrounds so screen readers skip it. Content-bearing artwork, such as example route maps, needs descriptive alt text.

### Gaps
- I did not fetch the W3C pages for 1.4.1 (Use of Colour), 1.4.11 (Non-text Contrast) or `prefers-reduced-motion`. They are cited from general knowledge in the inferences only.
- WCAG gives no official method for textured backgrounds beyond "the specified background". The worst-case-pixel approach is my inference, not W3C text.
- `prefers-reduced-transparency` was not researched.

## 3. Dark mode for watercolour

### Takeaway
No source I found addressed watercolour dark mode specifically. The general guidance from web.dev:
- Swap artwork per scheme with `<picture><source media="(prefers-color-scheme: dark)">` when recolouring is not good enough.
- Desaturate photos slightly, because most surveyed users prefer "slightly less vibrant and brilliant images" in dark mode.
- Use `currentColor` for inline SVG.
- Declare `color-scheme: light dark`.

### Cited Findings
- Art-directed swap: `<picture><source srcset="dark.webp" media="(prefers-color-scheme: dark)"><source srcset="light.webp" media="(prefers-color-scheme: light)"><img src="light.webp"></picture>`, for cases where "re-colorization of images" is not good enough. — [web.dev: prefers-color-scheme](https://web.dev/articles/prefers-color-scheme)
- Dark-mode image filter: `img:not([src*='.svg']) { filter: grayscale(50%); }`. The survey found a "majority of the surveyed people prefer slightly less vibrant and brilliant images" in dark mode. `invert(100%)` works for icons but not for photos. — [web.dev: prefers-color-scheme](https://web.dev/articles/prefers-color-scheme)
- Inline SVG with `fill`/`stroke="currentColor"` adapts automatically, but not when the SVG is loaded via `<img src>` or CSS. `:root { color-scheme: light dark; }` themes form controls and scrollbars. — [web.dev: prefers-color-scheme](https://web.dev/articles/prefers-color-scheme)
- `image-set()` can carry the format choice for CSS backgrounds, and a `prefers-color-scheme` media block can switch the `background-image` itself. — [MDN image-set()](https://developer.mozilla.org/en-US/docs/Web/CSS/image/image-set)

### Inferences
- **Do not invert watercolour rasters.** Inverting turns ultramarine into a muddy orange and paper into black ink. Use one of these instead:
  - (a) **Separate dark-paper artwork**: pyntpot re-renders with a dark paper colour (for example a warm charcoal around #1e1b18 rather than pure black) and with pigments simulated as gouache or body colour. Translucent glazes cannot lighten a dark ground in real paint, so "pigment on dark paper" needs opaque, lighter, desaturated washes.
  - (b) **Mask + CSS colour approach** (section 1): only the colour tokens change. Washes become lighter, lower-chroma tints at reduced opacity, blended with `screen` or `normal` instead of `multiply`.
- Paper-grain tiles can be shared across themes if rendered as neutral grey with alpha and blended with `overlay` or `soft-light` at low opacity. Verify this visually.
- For `<img>` artwork, use `<picture>` with a `prefers-color-scheme` source. For CSS backgrounds, use custom properties (`--wash-h1: url(...)`) redefined inside `@media (prefers-color-scheme: dark)` and a `[data-theme=dark]` override, if the docs theme (for example Material for MkDocs or Furo) has a manual toggle.

### Gaps
- I found no published case study of a painterly or watercolour site's dark mode. This remains a design inference.

## 4. Image weight, formats, delivery and Core Web Vitals

### Takeaway
AVIF is supported in all major engines: Chrome and Opera since 2020, Firefox since 2021, Safari since 2022. It offers smaller files than WebP and JPEG, plus alpha transparency. Serve AVIF with a WebP fallback via `<picture>` or `image-set(type())`.

Two LCP rules matter most:
- Never lazy-load the LCP image.
- Preload any above-the-fold CSS background, because the browser's HTML scanner cannot discover it.

### Cited Findings
- AVIF aims for "improved perceptual quality at file sizes smaller than JPEG or WebP" and "PNG-like transparency". Netflix, Cloudinary and the Chrome codecs team rated it favourably. Browsers that cannot parse a format discard the image, hence the need for fallbacks. — [web.dev Learn Images: AVIF](https://web.dev/learn/images/avif)
- Good LCP is 2.5 s or less for at least 75% of visits, and over 4.0 s is poor. A CSS background image can be the LCP element but "can't be found by scanning the HTML". The fix is `<link rel="preload" fetchpriority="high" as="image" href="..." type="image/avif">`. — [web.dev: Optimize LCP](https://web.dev/articles/optimize-lcp)
- "Never lazy-load your LCP image". Use `fetchpriority="high"` on at most one or two images, and `fetchpriority="low"` for early but non-visible images. — [web.dev: Optimize LCP](https://web.dev/articles/optimize-lcp)
- `image-set()` supports `1x`/`2x` density variants for CSS backgrounds. — [MDN image-set()](https://developer.mozilla.org/en-US/docs/Web/CSS/image/image-set)

### Inferences
- **Paper texture**: a seamlessly tileable 256 to 512px greyscale tile (pyntpot would need wrap-around noise so edges match), encoded as AVIF or WebP at low quality, is typically a few KB to a few tens of KB. Apply it once on `body` or the main column.
- **Heading washes and highlighter strokes**: generate a small set (say 3 to 6 variants) and reuse them across pages via CSS classes, so they cache once for the whole site.
- Washes are soft, low-frequency images. They compress very well and can be rendered at reduced resolution (for example 0.5x) and upscaled by the browser, because blur hides the scaling.
- Watch for **banding** in AVIF and WebP on smooth washes. Paper grain or dither noise baked into the raster masks banding.
- **Suggested budget** (my proposal, not sourced): total decorative imagery of 100 KB or less per docs page on first load, with any single asset at 30 KB or less. Avoid decorative artwork as the LCP element; let the H1 text be the LCP. Give every `<img>` `width`/`height` to prevent CLS. Lazy-load (`loading="lazy"`) all below-the-fold art.

### Gaps
- No sourced numeric file-size comparisons (AVIF vs WebP percentages) or official docs-page weight budgets were retrieved.
- Encoding speed was not covered.

## 5. Hand-lettered titles: web font vs image vs SVG

### Takeaway
WCAG 1.4.5 favours real text styled with CSS for headings. Images of text are allowed only for logotypes, essential presentation, fonts the author cannot redistribute, or when real text is presented alongside.

The best pattern for pyntpot:
- the site wordmark or logo can be a painted raster or SVG with `alt="pyntpot"`;
- section and page titles should be real HTML text, in a legible display font, over a pyntpot-painted wash.

### Cited Findings
- Headings should be styled with CSS rather than bitmaps. Images of text are acceptable when a font is "not widely deployed", cannot be redistributed, or is needed to ensure anti-aliasing, and logotypes count as essential. Presenting an image of text together with the equivalent real text also meets the criterion. — [W3C Understanding 1.4.5](https://www.w3.org/WAI/WCAG22/Understanding/images-of-text.html)
- `font-display: swap` shows a fallback immediately and swaps in the web font with no time limit. It is suited to brand fonts and headings, can cause layout shift, and the shift can be reduced with font metric overrides. — [CoreWebVitals.io: Ensure text remains visible during webfont load](https://www.corewebvitals.io/pagespeed/ensure-text-remains-visible-during-webfont-load)
- Logotypes are exempt from contrast requirements. — [W3C Understanding 1.4.3](https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html)

### Inferences
- **Options ranked**:
  1. Real text in a self-hosted handwriting or display web font. Subset it to the glyphs used in titles, use `font-display: swap`, and set `size-adjust`/`ascent-override` on the fallback `@font-face` to limit CLS. Keep it for H1/H2 only, never body text.
  2. Real text in the body font, given a hand-made feel by a painted backing wash behind it.
  3. An image or SVG title produced by pyntpot's own lettering engine, paired with real text. Either visually hidden real text plus an `aria-hidden` image, or the image as `alt`-labelled content. Reserve this for the logo and hero.
- An image title fails to wrap, scale with user font settings, translate or be searched. That is acceptable for a one-off wordmark but not for the dozens of per-page headings.
- pyntpot could export its lettering as **SVG paths** for the wordmark: crisp at any size, small, and recolourable with `currentColor` when inlined.
- Hand-lettered titles still need 3:1 contrast against the darkest or lightest pixel of the wash behind them, at large-text size.

### Gaps
- No sourced research on the legibility of script or handwriting faces for headings.
- No sourced guidance on subsetting script fonts with contextual alternates.

## 6. Watercolour colour theory for UI: pigment palette and accessible text colours

### Takeaway
A limited palette of a few real pigments, harmonised by mixing, gives watercolour coherence. For UI, keep the pigments for washes and decoration and derive text colours as much darker "masstone" shades (or near-neutral mixes, such as ultramarine and burnt sienna greys) verified to 4.5:1 against the paper colour. Okabe-Ito is a CVD-safe reference for any colour that must distinguish categories.

### Cited Findings
- Handprint (Bruce MacEvoy) is a major watercolour pigment reference. A forum user's palette built from Handprint's recommendations included ultramarine blue (PB29), phthalocyanine blue GS (PB15:3), phthalocyanine green YS (PG36) and burnt sienna. — [WetCanvas: creating secondary palette](https://www.wetcanvas.com/forums/topic/creating-secondary-palette-daniel-smith-or-m-graham); [Lines and Colors on Handprint](https://linesandcolors.com/2006/05/16/handprint-watercolors-and-watercolor-painting/)
- Ultramarine and burnt sienna together produce a range of muted colours, from cool greys to greenish-browns depending on the ratio. One painter reports that ultramarine with brown umber gives lilacs through dark purples. — [WetCanvas: limited palette threads](https://www.wetcanvas.com/forums/topic/paintingglazing-with-a-limited-palette)
- Pigment code conflict: burnt sienna is given as PBr7 by one source, while a WetCanvas list files PR101 as "burnt sienna transparent red oxide". — [WetCanvas](https://www.wetcanvas.com/forums/topic/my-18-color-limited-palette). Inference from general knowledge: both are in use; PR101 is a synthetic iron oxide many brands now sell as burnt sienna. Note the conflict.
- Hobbs interleaves colours across translucent layers rather than mixing them physically, and finds this looks good even though it is not realistic. — [Tyler Hobbs guide](https://www.tylerxhobbs.com/words/a-guide-to-simulating-watercolor-paint-with-generative-art)
- Okabe-Ito hexes are listed in section 2. — [Siegal lab, NYU](https://siegal.bio.nyu.edu/color-palette/)

### Inferences
- **Suggested docs palette**: a split-primary or triad from real pigments, for example French ultramarine (PB29), quinacridone rose or magenta (PV19), a transparent yellow such as hansa or nickel azo, burnt sienna (PBr7 or PR101) and a phthalo (PB15:3) accent.
  - Washes use pale dilutions on warm paper (for example around #f7f2e8).
  - Body text uses an ultramarine and burnt sienna "neutral tint", roughly #2b2a33, well above 7:1 on paper.
  - Link and accent colours are darkened pigment hues (for example deep phthalo blue) checked to at least 4.5:1, with underlines retained.
  - The hex values here are illustrative and not sourced. pyntpot's own pigment model should generate them, and a contrast gate should check them.
- Derive tokens in a perceptual space (OKLCH). Keep hue and lower lightness until the WCAG ratio passes. pyntpot can compute this in Python at build time and emit CSS custom properties, so the art and the CSS share one pigment source of truth.
- Treat pigment hue as decoration, and pair any meaningful colour (admonitions, diff colours, map legend) with icon, text or pattern. Where categories must be distinguished, check the palette against Okabe-Ito or a CVD simulator.

### Gaps
- I could not reach Handprint's own palette pages. No sourced sRGB values for real pigments were found, so pigment-to-hex mapping must come from pyntpot's own model or a further source.
- No source on "watercolour UI colour theory" specifically was found.

## 7. Real sites doing watercolour or painterly UI

### Takeaway
The showcases I found are mostly from around 2010. Recurring patterns:
- watercolour as accent, not wallpaper;
- generous white or paper space where text lives;
- a restrained typeface and palette beside expressive painted areas.

I found no current (2025 to 2026) curated list of painterly documentation sites.

### Cited Findings
- Electric Pulp uses a watercolour touch at the top of the page and in a few details lower down. Agami Creative makes watercolour central but keeps readability with a sans-serif and a restrained palette. Fabien Barral sets brush strokes on white, with text in the white space. Viget uses a painted landscape header surrounded by white space. — [WebUrbanist: 14 Artistic Examples of Watercolor in Web Design (2010)](https://weburbanist.com/2010/07/26/14-artistic-examples-of-watercolor-in-web-design/); [Webdesigner Depot: A Showcase of Watercolor in Web Design (2010)](https://www.webdesignerdepot.com/2010/03/a-showcase-of-watercolor-in-web-design/)
- A broader roundup ranges from full-page painted looks to subtle brush-stroke accents. — [WebFX: 30 examples of watercolor effects and brush strokes](https://www.webfx.com/blog/web-design/30-examples-of-watercolor-effects-and-brush-strokes-in-web-design)
- Another roundup covers watercolour backgrounds. — [Weblium: Watercolor Background, 15 Examples](https://weblium.com/blog/watercolor-background-15-examples/)

### Inferences
- The consistent lesson, "paint around the text, not under it", matches the accessibility analysis. Painted hero and header, washes behind large headings, painted dividers and margins, and flat paper under body copy and code blocks.
- Code blocks should sit on flat, high-contrast panels. A faint paper texture is acceptable if contrast is checked, but no washes.

### Gaps
- No verified current examples, so check Awwwards, Behance or Dribbble for "watercolor" with recent dates. The sites listed may have been redesigned since 2010.
- No example of a software documentation site with a watercolour identity was found.
