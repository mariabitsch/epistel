"""Where the vendored TEI came from, read from the file that records it.

``data/vendor/PROVENANCE.md`` is this project's record of the upstream source:
the repository the files were copied from and the exact commit they were taken
at. The Om page tells the reader the same two facts, and the two must not be
able to drift apart -- so the page is built from the record rather than from a
constant somebody would eventually forget to update.

``load_provenance(vendor_dir)`` returns ``{"repository": ..., "commit": ...}``,
or ``None`` when there is no record at all. A build without it is still a
complete site: the Om page then names the upstream repository (which is also
the project's own prose) but claims no pin, because a pin it cannot verify
would be worse than none.
"""

import os
import re

FILENAME = "PROVENANCE.md"

# The record is Markdown written for humans; these two lines are the machine-
# readable part of it, and the test suite asserts that they stay findable.
_REPOSITORY = re.compile(r"\*\*Upstream repository:\*\*\s*(\S+)")
_COMMIT = re.compile(r"\*\*Pinned upstream commit:\*\*\s*`([0-9a-f]{7,40})`")


def load_provenance(vendor_dir):
    """Read the provenance record beside the vendored files. May return None."""
    path = os.path.join(vendor_dir, FILENAME)
    if not os.path.isfile(path):
        return None
    with open(path, encoding="utf-8") as file:
        recorded = file.read()
    repository = _REPOSITORY.search(recorded)
    commit = _COMMIT.search(recorded)
    if not repository or not commit:
        raise ValueError(
            "%s does not record an upstream repository and a pinned commit" % path
        )
    return {
        "repository": repository.group(1).rstrip("."),
        "commit": commit.group(1),
    }
