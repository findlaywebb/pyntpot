"""Every link a page makes into this repository's `main` names a path that exists on the branch.

The pages are the site's pages and `README.md`. A link to
`https://github.com/findlaywebb/pyntpot/blob/main/<path>` names a file under the repository
root, and one to `…/tree/main/<path>` names a directory, the fragment dropped either way.
Relative links are the strict build's job, and links to anywhere else are not checked:
nothing here goes on the network.
"""

import re

from support import REPO_ROOT
from support.site_pages import links, site_pages

_REPOSITORY = re.compile(
    r"^https://github\.com/findlaywebb/pyntpot/(?P<kind>blob|tree)/main/(?P<path>[^#?]*)"
)


def test_every_repository_link_names_a_file_on_the_branch() -> None:
    """Each `blob/main/` link names an existing file and each `tree/main/` link an existing directory."""
    checked = 0
    missing: list[str] = []
    for page in [*site_pages(), REPO_ROOT / "README.md"]:
        for href in links(page.read_text()):
            found = _REPOSITORY.match(href)
            if found is None:
                continue
            checked += 1
            target = REPO_ROOT / found["path"]
            exists = target.is_file() if found["kind"] == "blob" else target.is_dir()
            if not exists:
                missing.append(f"{page.relative_to(REPO_ROOT).as_posix()}: {href}")
    assert checked, "no page links into the repository"
    assert missing == []
