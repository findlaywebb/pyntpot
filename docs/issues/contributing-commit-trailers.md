# CONTRIBUTING forbids co-authorship trailers that the branch commits carry

`CONTRIBUTING.md`, section "Commits", says "No co-authorship trailers." The
commits on `p6-docs` carry `Co-Authored-By:` and `Claude-Session:` trailers,
because the plan for this phase tells each slice commit to end with the
attribution trailers the session gives (`git log --format=%B 92b011c..HEAD`
shows them on every commit of the branch).

The prose audit corrects text to match what the repo does, but which of the two
is meant is a policy choice, not a fact the code settles, so it left the
sentence as it is.

Possible fix: the maintainer picks one. Either drop the line from
`CONTRIBUTING.md` (and say which trailers commits carry), or keep it and stop
adding trailers from the next branch on.
