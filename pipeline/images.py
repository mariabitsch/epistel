"""Find every reference to an illustration file in the vendored TEI.

``pipeline.parse_tei`` reads one volume's letters; this module reads the
same files (and ``kom.xml`` beside them, and ``ded``, which the corpus
excludes) for one narrow purpose: to list the places where the edition
points at an image file. It is the vendor-layer input to the export's
image manifest -- ``exporter.images`` joins these references to the files
``data/vendor/PROVENANCE.md`` vouches for.

The edition points at an image in exactly two ways:

* ``<figure>`` -- a plate the edition prints, with the file on a
  ``<graphic url="...">`` child, an optional ``@type`` (only the two
  shared vignettes carry one) and ``@rend`` (``recto``/``verso``/
  ``opening``), and its caption in one or more ``<head>`` children.
* ``<pb facs="...">`` -- a page break whose manuscript leaf is
  reproduced by that file. A page break has no caption.

Result shape
------------

``find_image_references(vendor_dir)`` returns one record per reference,
in reading order per file, volumes sorted, ``txt.xml`` before ``kom.xml``::

    {"element": "figure",           # or "pb": the element that points
     "volume": "b1",
     "file": "txt.xml",
     "xmlId": "ill_1",              # the figure's / page break's xml:id
     "type": None,                  # figure @type ("vignet")
     "rend": "verso",
     "n": None,                     # pb @n: the leaf ("1r", "2v")
     "edRef": None,                 # pb @edRef: the pagination series
     "url": "../b1/ill_1.jpg",      # graphic @url / pb @facs, verbatim
     "head": ["1. Brev 2, bl. [2v], udskrift"],
     "figDesc": None,               # the figure's description, if any
     "division": {"type": "letter", "n": "2", "xmlId": "n2"}}

Every key is always present; ``None`` (or ``[]``) where the source says
nothing. ``division`` is the innermost numbered ``<div>`` around the
reference -- a letter in the corpus volumes, a ``dedication`` in ``ded``,
and ``None`` for the commentary's plate sections, which sit in no
numbered division at all.

Nothing is repaired. Two ``graphic`` urls write their own volume
directory in uppercase (``../B120/ill_31.jpg``); ``resolve_reference``
returns what the source wrote, uppercase included, and leaves matching
case-insensitively to the consumer. One ``@facs`` is dangling upstream
(b241's letter 249 points at ``../b241/ill_k15.jpg``, which the source
repository does not hold): it is recorded like any other reference, and
the export's manifest says plainly that no file answers it.
"""

import os
import posixpath
import xml.etree.ElementTree as ET

from .parse_tei import XML_ID, _local_name, _text_of

# The two files a vendored directory holds, in reading order: the letters
# first, then the edition's commentary on them.
TEI_FILES = ("txt.xml", "kom.xml")

# Image file extensions the edition uses. Everything else a url could name
# is not an image and is left alone.
IMAGE_SUFFIXES = (".jpg", ".jpeg")


def find_image_references(vendor_dir):
    """List every image reference in the vendored TEI. See the module docs."""
    references = []
    for volume in sorted(os.listdir(vendor_dir)):
        volume_dir = os.path.join(vendor_dir, volume)
        if not os.path.isdir(volume_dir):
            continue
        for filename in TEI_FILES:
            path = os.path.join(volume_dir, filename)
            if not os.path.isfile(path):
                continue
            root = ET.parse(path).getroot()
            references.extend(_references_in(root, volume, filename))
    return references


def resolve_reference(volume, url):
    """Turn a reference into a vendor-relative path, exactly as written.

    The edition writes its urls relative to the volume's own directory
    (``../b1/ill_1.jpg`` from inside ``b1``), so resolving one needs the
    volume it was written in. The result keeps the source's spelling --
    ``../B120/ill_31.jpg`` resolves to ``B120/ill_31.jpg``, uppercase and
    all -- because repairing a path would be repairing the source. Match
    case-insensitively instead.
    """
    return posixpath.normpath(posixpath.join(volume, url))


def _references_in(root, volume, filename):
    """Walk one TEI document in reading order, collecting references."""
    divisions = _numbered_divisions(root)
    references = []
    for element in root.iter():
        tag = _local_name(element)
        if tag == "figure":
            references.extend(_figure(element, volume, filename, divisions))
        elif tag == "pb" and _is_image(element.get("facs")):
            references.append(_page_break(element, volume, filename, divisions))
    return references


def _figure(figure, volume, filename, divisions):
    """One record per ``<graphic>`` under a figure; the figure describes it."""
    heads = [_text_of(child) for child in figure if _local_name(child) == "head"]
    descriptions = [
        _text_of(child) for child in figure if _local_name(child) == "figDesc"
    ]
    records = []
    for graphic in figure.iter():
        if _local_name(graphic) != "graphic" or not _is_image(graphic.get("url")):
            continue
        records.append(
            {
                "element": "figure",
                "volume": volume,
                "file": filename,
                "xmlId": figure.get(XML_ID),
                "type": figure.get("type"),
                "rend": figure.get("rend"),
                "n": None,
                "edRef": None,
                "url": graphic.get("url"),
                "head": [head for head in heads if head],
                "figDesc": descriptions[0] if descriptions else None,
                "division": divisions.get(figure),
            }
        )
    return records


def _page_break(page_break, volume, filename, divisions):
    return {
        "element": "pb",
        "volume": volume,
        "file": filename,
        "xmlId": page_break.get(XML_ID),
        "type": None,
        "rend": page_break.get("rend"),
        "n": page_break.get("n"),
        "edRef": page_break.get("edRef"),
        "url": page_break.get("facs"),
        "head": [],
        "figDesc": None,
        "division": divisions.get(page_break),
    }


def _numbered_divisions(root):
    """Map each element to the innermost numbered ``<div>`` around it.

    ElementTree has no parent pointers, so the enclosing division is
    carried down a single walk instead, keyed by the element itself. Only
    a ``<div>`` with an ``@n`` counts: that is what the edition numbers
    (letters, dedications), and it is what a consumer can join on.
    """
    divisions = {}
    _descend(root, None, divisions)
    return divisions


def _descend(element, division, divisions):
    if _local_name(element) == "div" and element.get("n"):
        division = {
            "type": element.get("type"),
            "n": element.get("n"),
            "xmlId": element.get(XML_ID),
        }
    divisions[element] = division
    for child in element:
        _descend(child, division, divisions)


def _is_image(url):
    return bool(url) and url.lower().endswith(IMAGE_SUFFIXES)
