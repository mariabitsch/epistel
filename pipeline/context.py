"""The editorial context layer: hand-curated JSON, read as it stands.

``pipeline.parse_tei`` turns the vendored TEI into data. This module does the
same job for the second, much smaller body of data the site shows -- the
curated datasets in ``data/context``: the books Kierkegaard published in his
lifetime, and the addresses he lived at.

They are a *different kind of truth* and the code keeps them apart on purpose:

* ``data/vendor`` is the edition's own TEI, CC0, never edited by us.
* ``data/context`` is our own editorial layer -- compiled by hand from named
  sources, with its own precision and its own disagreements recorded in each
  entry's ``note``. Every file says so itself in ``_meta.notFromTEI``.

Both arrive at the display through the same seam: structured data in, no
display decisions. This module reads, checks that the files hold what they
claim, and hands them on. It never fills a gap, rounds a date or resolves a
disagreement between sources -- the datasets say what they know, and saying it
is the display's job.

The layer is optional. A build without it is a smaller but perfectly honest
site (see ``sitegen.site.build_site``), which is the point of keeping the
editorial layer out of the TEI in the first place.
"""

import json
import os

# One file per dataset, each a JSON object of "_meta" plus a list under its
# own name -- the name is also the key the site knows the dataset by.
DATASETS = {
    "publications": "publications.json",
    "residences": "residences.json",
}


def load_context(context_dir):
    """Load the curated datasets. Returns ``None`` when they are not there.

    The result keeps each dataset's ``_meta`` block, because it holds the
    things a reader is owed: how the dates were arrived at, which sources were
    used, and that this layer is not the edition speaking.
    """
    if not context_dir or not os.path.isdir(context_dir):
        return None

    context = {"meta": {}}
    for name, filename in DATASETS.items():
        path = os.path.join(context_dir, filename)
        if not os.path.isfile(path):
            return None
        with open(path, encoding="utf-8") as file:
            data = json.load(file)
        entries = data.get(name)
        if not isinstance(entries, list) or not entries:
            raise ValueError("%s holds no %s" % (path, name))
        context[name] = entries
        context["meta"][name] = data.get("_meta") or {}
    return context
