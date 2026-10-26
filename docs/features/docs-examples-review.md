# Every example could be reviewed for clarity and code smells

**What exists today.** The examples in `examples/` paint every image in the docs, and the
tutorials quote them. They were written and critiqued for the pictures they make, and the
prose round fixed the pages around them, but no pass has read every script as code a
newcomer copies: its names, its nesting, how its settings are grouped, and whether a hard
passage is hard because of the prose, the code or the terms.

**What the feature would add.** One review of every example script and the page that
quotes it, recording for each unclear passage whether the cause is the prose, the code or
the terminology, then fixing it where it lies: smells in the code (long functions, deep
nesting, loose module constants that belong together, magic numbers), weak prose, or a term
that needs a better name or a glossary entry.

**Why it is not a defect.** The examples run, are tested and paint the pinned images; this
is about how well they teach.

**Possible shape.** A checklist per script (names say what a thing is, three to four levels
of nesting at most, settings grouped in a small dataclass or a dict where they belong
together, no unexplained numbers), a findings table under `specs/`, and fixes in small
slices that keep every docs image pin exact unless a picture is meant to change.
