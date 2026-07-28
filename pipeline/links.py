"""The external-link table: the addresses the built site may point at.

``data/links.json`` is the one list of external addresses -- today the CC0
deed every footer carries and the two provenance addresses on the Om page.
It exists so that changing the site's link policy is a data edit picked up
in two places at once: the page generator renders anchors from it, and the
test suite derives its self-containment allowlists from it. Change or
remove an entry and both follow; leave a page pointing at a removed
address and the tests say so.

Result shape
------------

``load_links(path)`` returns ``None`` when the file does not exist, and
otherwise::

    {"links": [{"id": "cc0-deed", "href": "https://...", "label": "CC0 1.0",
                "rel": "license", "scope": "footer"}, ...],
     "meta": {...}}

``scope`` says where a link belongs: ``"footer"`` on every page,
``"om"`` on the Om page only. The pages look entries up by ``id`` (an
anchor needs a place in a sentence, not just permission to exist); an
entry that is missing degrades the anchor to plain text, so a build
without the table names the same facts and points nowhere.

Like every dataset outside ``data/vendor``, the table is ours and
disposable, and says so in ``_meta``.
"""

import json
import os

REQUIRED_FIELDS = ("id", "href", "label", "rel", "scope")


def load_links(path):
    """Load the link table. Returns ``None`` when there is no file."""
    if not path or not os.path.isfile(path):
        return None
    with open(path, encoding="utf-8") as file:
        data = json.load(file)
    entries = data.get("links")
    if not isinstance(entries, list) or not entries:
        raise ValueError("%s holds no links" % path)
    seen = set()
    for entry in entries:
        for field in REQUIRED_FIELDS:
            if not entry.get(field):
                raise ValueError(
                    "%s: link %r is missing %r" % (path, entry.get("id"), field)
                )
        if entry["id"] in seen:
            raise ValueError("%s: duplicate link id %r" % (path, entry["id"]))
        seen.add(entry["id"])
    return {"links": entries, "meta": data.get("_meta") or {}}
