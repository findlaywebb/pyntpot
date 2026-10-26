# The docs could show a term's definition where it is used

**What exists today.** `GLOSSARY.md` holds the canonical terms, and the docs link to it.
A reader meeting "granulation" or "nib plate" on a page has to follow the link to learn
what it means.

**What the feature would add.** Definitions drawn from the one glossary into the page that
uses the term: a hover or footnote on the term's first use, and a short "Terms on this page"
box, all generated at build time so the glossary stays the single source.

**Why it is not a defect.** Linking to one glossary keeps one definition per term, which
is the rule; this keeps that rule and saves the reader the jump.

**Possible shape.** A MkDocs abbreviations file or a small plugin generated from
`GLOSSARY.md`, so a term's first use on a page shows its definition; a test that every
generated definition matches the glossary text.
