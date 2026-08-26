"""The vendored illustrations as a dataset: ``export/images.json``.

The image *files* travel with the export already, copied beside the
letters so the TEI's own relative urls resolve. This module writes the
manifest that turns them into data a consumer can query without opening
a single XML file: what each file is, where it came from, where it sits
in the export, and every place the edition points at it.

It is the **vendor layer alone**. Every field is either the provenance
record's (upstream path, sha256) or the edition's own (the figure's
``@type``/``@rend``, its ``<head>`` captions, the page break's leaf).
Descriptions of our own would be an editorial layer with an author and a
different license; they are not here. The image ``id`` -- the vendored
file's path, ``"b1/ill_1.jpg"`` -- is the join key a future captions
dataset would use.

Layout
------

::

    {"images": [
       {"id": "b1/ill_1.jpg",
        "path": "letters/b1/ill_1.jpg",         # inside the export
        "source": {"path": "data/v1.9/b1/ill_1.jpg", "sha256": "..."},
        "figures":    [ ... ],   # <figure> occurrences, reading order
        "pageBreaks": [ ... ]},  # <pb facs> occurrences, reading order
       ...],
     "unshippedReferences": [ ... ]}

Both occurrence lists may be empty: two vendored files are referenced
nowhere in the vendored TEI, and several are referenced only from a page
break. ``letter``/``letterXmlId`` name the letter a reference sits in --
they join straight to ``letters/<volume>/<xmlId>.json`` -- and are
``null`` where it sits in no letter (the commentary's plate sections;
``ded``'s dedications).

``unshippedReferences`` is the honest remainder: references the export
ships no file for. Two causes, deliberately not distinguished by a field
because the export cannot know a third: ``ded``'s own plates are not
vendored (``ded`` is outside the corpus), and one reference is dangling
upstream (b241's letter 249 points at ``../b241/ill_k15.jpg``, which the
source repository does not hold at the pinned commit). Nothing is
repaired in either case.

Two ``graphic`` urls write their volume directory in uppercase
(``../B120/ill_31.jpg``). The url travels exactly as written while the
``id`` names the file that actually exists, because matching here is
case-insensitive -- the same stance the export takes everywhere else.
"""

from pipeline.images import find_image_references, resolve_reference

IMAGE_SUFFIXES = (".jpg", ".jpeg")


def image_manifest(files, vendor_dir):
    """Build the ``images.json`` payload. See the module docstring.

    ``files`` is ``pipeline.provenance.load_file_record`` output -- the
    record decides which files count as vendored images -- and
    ``vendor_dir`` is where the TEI is read from.
    """
    entries = {
        local: {
            "id": local,
            "path": "letters/%s" % local,
            "source": dict(entry),
            "figures": [],
            "pageBreaks": [],
        }
        for local, entry in files.items()
        if local.lower().endswith(IMAGE_SUFFIXES)
    }
    # The source spells one directory in uppercase; the lookup is
    # case-insensitive so the reference can stay as written.
    by_lowercase = {local.lower(): local for local in entries}

    unshipped = []
    for reference in find_image_references(vendor_dir):
        target = resolve_reference(reference["volume"], reference["url"])
        local = by_lowercase.get(target.lower())
        if local is None:
            unshipped.append(_unshipped(reference))
        elif reference["element"] == "figure":
            entries[local]["figures"].append(_figure(reference))
        else:
            entries[local]["pageBreaks"].append(_page_break(reference))

    return {
        "images": [entries[local] for local in sorted(entries)],
        "unshippedReferences": unshipped,
    }


def _figure(reference):
    """A ``<figure>`` occurrence: the plate as the edition prints it."""
    occurrence = {
        "volume": reference["volume"],
        "file": reference["file"],
        "xmlId": reference["xmlId"],
        "type": reference["type"],
        "rend": reference["rend"],
        "url": reference["url"],
        "head": list(reference["head"]),
        "figDesc": reference["figDesc"],
    }
    occurrence.update(_letter(reference))
    return occurrence


def _page_break(reference):
    """A ``<pb facs>`` occurrence: the manuscript leaf this file shows."""
    occurrence = {
        "volume": reference["volume"],
        "file": reference["file"],
        "xmlId": reference["xmlId"],
        "n": reference["n"],
        "rend": reference["rend"],
        "edRef": reference["edRef"],
        "facs": reference["url"],
    }
    occurrence.update(_letter(reference))
    return occurrence


def _unshipped(reference):
    """A reference the export ships no file for, named as the source wrote it."""
    occurrence = {
        "volume": reference["volume"],
        "file": reference["file"],
        "element": reference["element"],
        "url": reference["url"],
    }
    occurrence.update(_letter(reference))
    return occurrence


def _letter(reference):
    """The letter a reference sits in, or nulls where it sits in none.

    ``ded`` numbers dedications rather than letters, and the commentary
    gathers its plates outside any numbered division. Neither is turned
    into a letter it is not.
    """
    division = reference["division"] or {}
    if division.get("type") != "letter":
        return {"letter": None, "letterXmlId": None}
    return {"letter": division["n"], "letterXmlId": division["xmlId"]}
