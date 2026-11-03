Verdict: BLOCK

# 007 plan review 1

Reviewed `plan.md`, `spec.md` and `tasks.md` at `7b61165`, checked against the worktree, the
locked docs group (Markdown 3.11.2, pymdown-extensions 12.3, mkdocs 1.6.1, Material 9.8.0)
and 006's plan. Two versions of 006's plan were read: the committed one at `c936970`, and the
working copy in `/home/user/pyntpot`, which another agent is rewriting in 006's fix round
(+561/-148, not committed).

The approach is right, and it meets the standard the user asked for. The glossary is generated
from one source with a drift check. The suite is data-driven from `mkdocs.yml`, the registry and
the code. Statements that are only true after 006 wait for S8, so S0 to S7 write only text
that is true on both sides of 006. Most of the plan's claims checked out:

- **abbr.** It skips inline code, fenced code and indented code. It applies in headings and
  links without changing the slug or the TOC label. A raw `<span id="term-x">` counts as an
  anchor, and a missing `#term-…` fails the strict build.
- **Prototypes.** The from-claim prototype finds exactly #163's 8 claims. All 57 "In the code"
  paths resolve. The glossary rows cover every current row and every spec term.
- **The four missing gallery images.** Confirmed.
- **Retired words.** No retired word is split across a line wrap today.
- **The `callouts` key.** Read in only three places: `place_card.py:69`, `test_places.py:194`
  and `test_example_themes.py:70`. No golden keys on the script source.
- **ruff on Markdown.** Leaves indented (unparsable) python blocks alone, so verbatim quotes
  survive the format hook.
- **006 overlap.** No overlap with 006 before S8 in either version of its plan. 006 now adds
  griffe to the `dev` group (`pyproject.toml`, `uv.lock`), which 007 does not touch.

Five defects still make slices fail as written.

## Blockers

### 1. S0's index-order test turns red when S4 adds its `Next:` lines

- **Evidence.** S0's `test_every_section_index_lists_its_pages_in_nav_order` (plan.md:134-138)
  requires the index page's same-section links, in order, to *equal* the section's pages. S4
  (plan.md:574-577) appends `Next: [Paint a watercolour](paint-a-watercolour.md)` to
  `tutorials/index.md` and `Next: [Curves](curves.md)` to `painting-with-python/index.md`. Both
  pages already link those targets (`tutorials/index.md:8`, the series index's first bullet).
- **Result.** The link lists become `[paint, first-map, paint]` and
  `[curves, …, vector-drawing, curves]`, and the test fails. S4 does not own `test_nav.py` or
  `site_pages.py`, and its gate runs `tests/docs`.
- **Also undecided: what "pages of the same section" means.** With exact `sections`-tuple
  equality the test passes today. With prefix (flattened) matching it fails on Tutorials,
  because `tutorials/index.md` links the subsection's index but not curves and the rest.
- **Fix.** Specify that the test compares the first occurrence of each link, with duplicates
  dropped, or reads `prose` minus the trailing `Next:` line. Specify that "same section" means
  `NavEntry.sections` is exactly equal, so a subsection's pages belong to the subsection's own
  index.

### 2. `Block.marker` misses the marker convention of curves and fractals: 20 blocks fail as "unmarked"

- **Evidence.** The plan defines `marker` as "the `<!-- ... -->` comment on the line before the
  fence" (plan.md:126-128). `curves.md` (7 blocks, e.g. lines 19-21) and `fractals.md` (13
  blocks, e.g. line 45) put a blank line between the marker and the fence. The existing regex
  allows that (`test_tutorials.py:33`, `-->\s*\n`).
- **Result.** S4's `test_every_python_block_on_a_tutorial_page_is_marked` would fail on 22
  blocks, not the "two blocks on `pictures.md`" the plan expects (plan.md:555-556). All 39
  marked blocks are verbatim today; I checked them with the existing regex. S4 cannot change
  S0's helper, so it would either edit 20 blocks' spacing (not in its steps) or reach into
  S0's file.
- **Fix.** `marker` is the nearest preceding non-blank line, when that line is an HTML comment.

### 3. The CLI synopsis comparison breaks on argparse's line wrapping

- **Evidence.** The plan compares "line by line with whitespace runs collapsed" (plan.md:437-440).
  At the default 80 columns (xdist workers have no terminal), `build_parser()`'s `map` subparser
  usage comes out as three lines:
  `pyntpot map [-h] -o OUTPUT --cache CACHE --contact CONTACT\n                   [--style STYLE] [--margin-m MARGIN_M] [--no-attribution]\n                   track`.
  At `COLUMNS=200` it is one line.
- **Result.** The page shows one line per parser, so a line-by-line comparison depends on the
  environment and fails in CI.
- **Fix.** For each parser, take `format_usage()`, remove `usage: `, and collapse *all*
  whitespace, newlines included, to single spaces. Compare the result to the matching
  non-empty line of the synopsis block (root first, then the subparsers in `choices` order).
  Say this in the plan.

### 4. S1's own test contradicts S1's own data

- **Evidence.** `TestTheGlossary` asserts that "every 'Say instead' is a term" (plan.md:377).
  The retired words (spec.md:201-203) say instead "centreline trace" and "outline trace", and
  neither is a term. The term is "trace" (plan.md:264).
- **Result.** As prescribed, the test fails on the file S1 writes, and the agent has to choose
  between changing the test and changing the data.
- **Fix.** Either "every Say instead contains a term as a whole word", or make the two cells
  read `trace (centreline trace)`. Pick one in the plan.

### 5. The #162 caption check would pass on #162's own bug

- **Evidence.** `test_every_label_number_in_a_caption_is_a_literal_of_its_script`
  (plan.md:503-505; spec.md:96-98) only requires each number to be *some* numeric literal of
  the script. Every number in the wrong caption, `-38, 0 and 90 … 0.5 and 0.85`
  (`gallery.md:221`), is a literal of `examples/nib_stages.py`: line 90 has -38.0, 0.0, 90.0
  and 0.85, and line 117 has `0.5 * w`. Dropping 38 is not caught either.
- **Result.** The plan relies on the name test to catch #162 (plan.md:507). The number check
  adds almost nothing, because small numbers appear in every script. That falls short of
  "check content truly" and of #162's "stop it drifting again".
- **Fix.** For each "across" and "down" clause with two or more numbers, and no "to" range,
  the numbers in order must equal the numeric elements of one tuple or list literal in the
  script's AST. Unary minus counts. Compare as floats.
- **Prototype.** I ran this against every current caption. It passes all the correct ones:
  `tutorial_grids` paper, wash, nib and composition, and `wash_stages` glaze. It fails exactly
  `gallery.md:221`, and the corrected caption matches `ANGLES` and `THINS`.

## Should fix

1. **Build time is about 10× slower.** mkdocstrings converts docstrings with the site's
   Markdown extensions, so `auto_append` also runs on each of about 355 docstring conversions.
   abbr's block parser is roughly quadratic over a dense block of definitions. I measured a
   117-line abbreviations file on the real site: baseline 2.3 s, dense 27 s, and 4.0 s with a
   blank line between definitions. Make `abbreviations()` (plan.md:355-357) write one blank
   line between definitions. State in S1 that API-page docstrings also get tooltips
   (verified), and add `site/reference/maps/index.html` to S1's `grep -c '<abbr'` check.
2. **The gallery's How-to order is not nav order after S0.** The gallery has Write a theme,
   Change the route ink, Letter your own landmarks, Paint your own shapes, then Map from the
   command line (`gallery.md:125-165`). S0's nav puts Map from the command line second
   (plan.md:146-149). S3's own `test_the_gallery_lists_its_pages_in_nav_order` therefore
   fails, and S3's steps never say to reorder. Add a step: move "Map from the command line"
   to directly after "Write a theme".
3. **Contributor "In the code" paths are never checked, and two slices each write a
   resolver.** `GLOSSARY.md` is not a site page, so the 10 contributor rows' paths
   (plan.md:308-317) are never resolved. S2 writes the dotted-path resolver inside
   `test_docs_imports.py`, while S1 and S8 step 6 need the same semantics (import the longest
   module prefix, then `getattr`). Put `resolve_dotted(path) -> object` in S0's
   `site_pages.py`. Have `TestTheGlossary` assert that every In-the-code name resolves.
   Prescribe `Term.code: tuple[str, ...]` as bare dotted names (plan.md:328).
4. **The plan contradicts itself on example code lines.** "Every example's code lines" are
   left alone (plan.md:951), but S5 changes the code line `place_card.py:69` (plan.md:649).
   Add the carve-out, or an agent following the leave-alone list will refuse.
5. **The `pictures.md` fix is described incompletely** (plan.md:571-573).
   - The first block also differs at `scene.sheet` (`derwentwater.py:190`).
   - The check is a raw substring check, so the two-line block must keep the script's 8-space
     indentation.
   - The prose right after the block ("`inside` is the picture less its side margins",
     `pictures.md:33`) must then say `scene.inside`.

   State all three.
6. **Put `validation:` before `nav:` and keep `nav:` last.** `test_site.py:103` and the new
   `nav()` both read everything after `"\nnav:\n"` (plan.md:124, 150).
7. **`fenced_blocks` must handle indented fences.** `paint-your-own-shapes.md:16-51` has fences
   indented inside list items. Dedent each block's code by its fence's indent. Otherwise the
   import, signature and dotted-path tests read that code as prose, or skip it.
8. **Cross-slice reds at the S7 merge.** S2's, S3's and S6's tests scan every page but run in
   separate worktrees, so they first meet S4's and S5's edits at S7. S7 (plan.md:711-714)
   assigns only retired-word failures to the integrator. Say the integrator owns every red
   that appears after the merge, fixed in the page that red names.
9. **Commands are still unchecked.** "Tutorial code is the code that runs" is true only for
   quoted Python.
   - `test_how_to_commands.py` parses `pyntpot` commands on how-to pages only.
     `first-map.md:131` and `:152` are unchecked.
   - S4's new `place_card.py … --theme … --place ambleside --size 720` command
     (plan.md:603-604) is checked only for the script's existence.

   Add a generic `tests/docs` test over every site page. Every `pyntpot …` command line should
   parse with `build_parser()`. Every option in `uv run python examples/<s>.py …` should be an
   `add_argument` option string of that script, read from its AST. In S8, delete the how-to-only
   test as subsumed.
10. **The repository-link test misses `tree/main/` links.** S8 checks only `blob/main/<path>`
    (plan.md:856-858). The gallery's Places headings link `tree/main/tests/fixtures/...`
    (`gallery.md:247-271`), so include `tree/main/` too.
11. **Nothing tests that `includes/` is excluded.** mkdocs strict reports a page left out of
    the nav at INFO, not as a warning, so dropping the exclusion fails nothing. Assert it in
    `test_nav.py`.
12. **Move all the docs-prose tests or none.** The reason for moving two tests to `tests/docs`
    ("they check prose") applies equally to `test_how_to_commands.py`, `test_readme.py`,
    `test_docs_images.py` and `test_reference_keys.py`. Either move all of them in S8, or state
    why these four stay.

## Consider

- The "card → map where it means the picture" sweep across S2 to S5 has no check, and four
  parallel agents will judge it differently. Have S7 list every remaining `\bcards?\b` on site
  pages and review the list against the glossary's card definition.
- Tooltip forms with an apostrophe (`painter's pigment`) do not match `’`. There is none today;
  a one-line test (no `’` on site pages) keeps it that way.
- Nit: there are seven non-index tutorial pages, not six (plan.md:567; tasks.md:55).
- 006's plan is changing right now. S8's "rerun the overlap grep" (plan.md:964-965) has to be
  run against the merged 006, not the plan reviewed here.
