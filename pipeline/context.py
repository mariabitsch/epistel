"""The editorial context layer: hand-curated JSON, read as it stands.

``pipeline.parse_tei`` turns the vendored TEI into data. This module does the
same job for the second, much smaller body of data the site shows -- the
curated datasets in ``data/context``: the books Kierkegaard published in his
lifetime, the addresses he lived at, Maria Notabene's summaries of the
letters, the biographies drawn out of the edition's own commentary, and two
join tables -- correspondent names to the people named in the letters
(``aliases.json``), and the commentary's persName keys to the bodies' where
the two key spaces drift apart (``bio_keys.json``).

They are a *different kind of truth* and the code keeps them apart on purpose:

* ``data/vendor`` is the edition's own TEI, CC0, never edited by us.
* ``data/context`` is our own editorial layer -- compiled by hand or with
  help, from named sources, with its own precision and its own disagreements
  recorded in each entry's ``note``. Every file says so itself in
  ``_meta.notFromTEI``.

Both arrive at the display through the same seam: structured data in, no
display decisions. This module reads, checks that the files hold what they
claim, and hands them on. It never fills a gap, rounds a date or resolves a
disagreement between sources -- the datasets say what they know, and saying it
is the display's job.

Every dataset is optional, one by one. A build with none of them is a smaller
but perfectly honest site (see ``sitegen.site.build_site``): the letters
themselves, the people the edition names in them, and a search over the text.
That is the point of keeping the editorial layer out of the TEI in the first
place -- each part of it has to be disposable on its own, not just as a block.

Result shape
------------

``load_context(dir)`` returns ``None`` when the directory holds none of the
datasets, and otherwise::

    {"publications": [...],      # the timeline's two datasets: both or neither
     "residences": [...],
     "summaries": {"b1/n1": "Søren bruger den første halve side ..."},
     "bios": {"Boesen, Emil Ferdinand": {"bio": ..., "sources": [...]}},
     "bios_without": {"Victor Eremita": "Not a biographical subject"},
     "aliases": {"SK": ["Kierkegaard, Søren Aabye"]},
     "aliases_unmapped": {"ukendt": "Udgaven kender ikke afsenderen ..."},
     "meta": {"publications": {...}, ...}}

The list-shaped files are turned into lookups here rather than in the display,
because the join key is a property of the data ("volume/xml:id", "the
edition's persName key") and not a display decision.
"""

import json
import os

# The timeline's two datasets: a list under the file's own name, plus "_meta".
# They stand or fall together -- a timeline with books and no addresses, or
# the other way round, would be a different page than the one that was
# designed -- so the pair is loaded as a pair.
DATASETS = {
    "publications": "publications.json",
    "residences": "residences.json",
}

# The datasets that hang off individual letters and people. Each one is
# optional on its own; the display simply has less to say without it.
SUMMARIES_FILE = "summaries.json"
BIOS_FILE = "bios.json"
BIO_KEYS_FILE = "bio_keys.json"
ALIASES_FILE = "aliases.json"


def load_context(context_dir):
    """Load the curated datasets. Returns ``None`` when there are none.

    The result keeps each dataset's ``_meta`` block, because it holds the
    things a reader is owed: how the dates were arrived at, which sources were
    used, and that this layer is not the edition speaking.
    """
    if not context_dir or not os.path.isdir(context_dir):
        return None

    context = {"meta": {}}
    timeline = [
        (name, os.path.join(context_dir, filename))
        for name, filename in DATASETS.items()
    ]
    if all(os.path.isfile(path) for _, path in timeline):
        for name, path in timeline:
            data = _read(path)
            entries = data.get(name)
            if not isinstance(entries, list) or not entries:
                raise ValueError("%s holds no %s" % (path, name))
            context[name] = entries
            context["meta"][name] = data.get("_meta") or {}

    _load_summaries(context, os.path.join(context_dir, SUMMARIES_FILE))
    _load_bios(context, os.path.join(context_dir, BIOS_FILE))
    _load_bio_keys(context, os.path.join(context_dir, BIO_KEYS_FILE))
    _load_aliases(context, os.path.join(context_dir, ALIASES_FILE))

    if len(context) == 1:
        return None
    return context


def summary_key(volume, xml_id):
    """The join key between a letter and its summary: volume plus ``xml:id``.

    Not the letter number: three letters in b171 are printed without one, and
    the ``xml:id`` is the only identifier every letter in the corpus has.
    """
    return "%s/%s" % (volume, xml_id)


def _load_summaries(context, path):
    """Maria Notabene's summaries, keyed by volume and ``xml:id``."""
    if not os.path.isfile(path):
        return
    data = _read(path)
    entries = data.get("summaries")
    if not isinstance(entries, list) or not entries:
        raise ValueError("%s holds no summaries" % path)
    context["summaries"] = {
        summary_key(entry["volume"], entry["xmlId"]): entry["summary"]
        for entry in entries
        if entry.get("summary")
    }
    context["meta"]["summaries"] = data.get("_meta") or {}


def _load_bios(context, path):
    """The biographies, keyed by the edition's own persName key.

    ``_meta.withoutBio`` is kept too, and it is not a leftover: it names the
    people the commentary was searched for and found nothing biographical
    about, with the reason. A person page can then say which kind of silence
    it is looking at.
    """
    if not os.path.isfile(path):
        return
    data = _read(path)
    entries = data.get("bios")
    if not isinstance(entries, list) or not entries:
        raise ValueError("%s holds no bios" % path)
    context["bios"] = {
        entry["key"]: {
            "bio": entry["bio"],
            "sources": entry.get("sources") or [],
            "sameAs": entry.get("sameAs") or [],
            "note": entry.get("note"),
        }
        for entry in entries
        if entry.get("bio")
    }
    meta = data.get("_meta") or {}
    context["bios_without"] = {
        entry["key"]: entry.get("reason")
        for entry in meta.get("withoutBio") or []
    }
    context["meta"]["bios"] = meta


def _load_bio_keys(context, path):
    """The curated bridge between the bodies' and the commentary's key spaces.

    ``bios.json`` is filed under kom.xml's persName keys; the person register
    is keyed by the letter bodies'. Where the two disagree (an inverted name,
    a rearranged surname, a missing comma), this table files the same bio
    under the body's key too, so the join in ``sitegen.persons`` stays a
    plain lookup. Loaded after the bios and meaningless without them: with
    ``bios.json`` gone, the bridge is quietly a no-op, which keeps each
    dataset disposable on its own. A bridge pointing at a bio that does not
    exist is a defect in the table, not a silence to preserve.
    """
    if not os.path.isfile(path):
        return
    data = _read(path)
    entries = data.get("bridges")
    if not isinstance(entries, list) or not entries:
        raise ValueError("%s holds no bridges" % path)
    context["meta"]["bio_keys"] = data.get("_meta") or {}
    bios = context.get("bios")
    if not bios:
        return
    for entry in entries:
        if entry["bioKey"] not in bios:
            raise ValueError(
                "%s bridges %r to %r, which holds no bio"
                % (path, entry["bodyKey"], entry["bioKey"])
            )
        bios[entry["bodyKey"]] = bios[entry["bioKey"]]


def _load_aliases(context, path):
    """The curated join between correspondent names and persName keys.

    Both halves are carried: what could be mapped, and what could not, with
    the reason. The display is expected to say so rather than quietly drop
    the letters it cannot place.
    """
    if not os.path.isfile(path):
        return
    data = _read(path)
    entries = data.get("aliases")
    if not isinstance(entries, list) or not entries:
        raise ValueError("%s holds no aliases" % path)
    context["aliases"] = {
        entry["form"]: list(entry["keys"]) for entry in entries if entry.get("keys")
    }
    context["aliases_unmapped"] = {
        entry["form"]: entry.get("reason") for entry in data.get("unmapped") or []
    }
    context["meta"]["aliases"] = data.get("_meta") or {}


def _read(path):
    with open(path, encoding="utf-8") as file:
        return json.load(file)
