"""Parse a TEI volume of Kierkegaard's letters into display-agnostic JSON.

This module is the seam of the project: it turns the vendored, read-only TEI
files (``data/vendor/<volume>/txt.xml``) into plain data structures that any
display layer can render. It makes no display decisions -- no HTML, no CSS
class names, no Danish labels. It also never repairs the source: whatever the
edition encodes is what comes out, with raw values kept next to anything
derived from them.

Result shape
------------

``parse_volume(path)`` returns::

    {
      "volume": "b1",                     # the volume directory's name
      "title": "Familien Kierkegaard",    # from the TEI header
      "shortTitle": "B1",
      "groups": [                         # <div type="correspondance">
        {"id": "correspContext1",
         "heading": "P.C. Kierkegaard",   # <head type="topText" n="...">
         "notes": ["Peter Christian Kierkegaard"],
         "letterIds": ["1", "2", ...]},
      ],
      "letters": [
        {"id": "1",                       # @n: the letter number, unique
                                          #     across the whole edition
         "xmlId": "n1",
         "correspDescId": "correspDesc1",
         "heading": "Fra SK · 8. marts 1829 · til P.C. Kierkegaard",
         "sender":    {"name": ..., "date": ..., "place": ..., "note": ...},
         "recipient": {"name": ..., "date": ..., "place": ..., "note": ...},
         "context": {"groupId": ..., "sameAs": ..., "notes": [...]},
         "body": [node, ...]},
      ],
      "warnings": [{"letterId": ..., "tag": ..., "message": ...}],
    }

Dates keep the source string and add a derived reading::

    {"raw": "18481200", "iso": "1848-12", "precision": "month",
     "year": 1848, "month": 12, "day": None,
     "notBefore": None, "notAfter": None, "source": "supplied", "text": None}

The edition writes dates as ``yyyymmdd`` without separators and pads unknown
parts with zeroes, so ``18481200`` means "December 1848" and ``18370000``
means "1837". ``precision`` says which it is; ``iso`` is truncated to match.
A date the parser cannot read keeps its ``raw`` value, gets ``iso: None`` and
raises a warning. A missing date is ``None``, never a guess.

Body nodes
----------

A letter body is a tree of nodes, close to the TEI but normalised:

* text:    ``{"text": "Kjære "}``
* element: ``{"type": "p", "rend": None, "rendition": "#ind", "content": [...]}``

Every element node has a ``type`` (the TEI element name) and a ``content``
list, so a display can walk the tree without knowing every tag. TEI's own
``@type`` attribute is emitted as ``subtype`` because ``type`` names the node.
Only attributes the parser declares in ``ELEMENT_ATTRIBUTES`` are carried
over, and they are always present -- ``None`` when the source omits them.

Three kinds of node deliberately keep text *out* of ``content``, because that
text is editorial apparatus rather than part of the letter as it reads:

* ``app``    -- ``content`` holds the established reading (``lem``), while
               rejected readings (``rdg``, ``rdgGrp``) go to ``variants``.
* ``choice`` -- ``content`` holds the abbreviation as written (``abbr``),
               while the editors' expansions (``expan``) go to
               ``alternatives``.
* ``witDetail`` -- an editorial remark about the manuscript ("ms.
               beskadiget"); its text goes to ``note`` and it has no
               ``content`` at all.

That way ``plain_text()`` -- and any naive renderer -- yields the reading
text, while a richer display can still show the apparatus.

TEI elements this parser does not model are still emitted, generically, with
their text intact, and each one is reported in ``warnings`` so nothing
disappears unnoticed.
"""

import os
import re
import xml.etree.ElementTree as ET

TEI_NAMESPACE = "http://www.tei-c.org/ns/1.0"
XML_ID = "{http://www.w3.org/XML/1998/namespace}id"

_WHITESPACE = re.compile(r"\s+")

# TEI attributes carried into the output, per element. TEI's @type is renamed
# to "subtype" on the way out; the node's own "type" holds the element name.
ELEMENT_ATTRIBUTES = {
    # Block structure of a letter.
    "div": ("type", "n"),
    "head": ("type", "n"),
    "opener": ("rend", "rendition"),
    "closer": ("rend", "rendition"),
    "salute": ("rend", "rendition"),
    "signed": ("rend", "rendition"),
    "dateline": ("rend", "rendition"),
    "postscript": ("rend", "rendition"),
    "trailer": ("type", "rend", "rendition"),
    "p": ("rend", "rendition"),
    "lg": ("rend", "rendition"),
    "l": ("rend", "rendition"),
    "lb": ("rend", "rendition"),
    "table": ("cols", "rows", "rend", "rendition"),
    "row": ("rend", "rendition"),
    "cell": ("cols", "rows", "rend", "rendition"),
    # Pagination and other pointers into the physical/printed witnesses.
    "pb": ("n", "rend", "edRef", "facs"),
    "milestone": ("unit", "type", "n", "edRef", "spanTo"),
    "figure": ("type", "rend"),
    "graphic": ("url",),
    "ptr": ("type", "target"),
    "ref": ("type", "target"),
    # Inline text.
    "hi": ("rend", "rendition"),
    "seg": ("type", "rend", "rendition"),
    "persName": ("key", "sameAs"),
    "placeName": ("key", "sameAs"),
    "name": ("key", "sameAs"),
    "rs": ("type", "key"),
    "date": ("when", "notBefore", "notAfter", "from", "to", "source"),
    "formula": ("notation",),
    "note": ("type", "resp"),
    # Editorial and genetic markup.
    "add": ("instant", "place", "rend", "rendition"),
    "del": ("instant", "rend", "rendition"),
    "supplied": ("reason", "resp", "rend", "rendition"),
    "unclear": ("reason", "cert", "rend", "rendition"),
    "corr": ("resp", "rend", "rendition"),
    "sic": ("rend", "rendition"),
    "choice": (),
    "abbr": ("rend", "rendition"),
    "expan": ("ana", "rend", "rendition"),
    # Text-critical apparatus.
    "app": (),
    "lem": ("wit", "varSeq"),
    "rdg": ("wit", "varSeq"),
    "rdgGrp": ("rend", "rendition"),
    "witDetail": ("wit", "resp"),
    "witStart": ("n", "rend", "rendition"),
    "witEnd": ("n", "rend", "rendition"),
}

# Elements whose children are other elements: whitespace between them is
# layout in the XML file, not part of the text, so it is dropped. Everywhere
# else whitespace is collapsed to single spaces and kept, because it separates
# words in mixed content.
STRUCTURAL_ELEMENTS = frozenset(
    [
        "app",
        "body",
        "choice",
        "closer",
        "div",
        "figure",
        "lg",
        "opener",
        "postscript",
        "rdgGrp",
        "row",
        "salute",
        "signed",
        "table",
        "trailer",
    ]
)

# Elements whose text is an editorial remark about the manuscript rather than
# part of the letter: emitted as "note", never as "content".
ANNOTATION_ELEMENTS = frozenset(["witDetail"])


def parse_volume(path):
    """Parse one vendored TEI volume file into a JSON-serializable dict.

    The volume name is taken from the containing directory, e.g.
    ``data/vendor/b1/txt.xml`` -> ``"b1"``.
    """
    root = ET.parse(path).getroot()
    volume = os.path.basename(os.path.dirname(os.path.abspath(path)))
    return parse_tei(root, volume)


def parse_tei(root, volume):
    """Parse an already-loaded TEI document. See the module docstring."""
    warnings = _Warnings()
    corresp_descs = _index_by_xml_id(root, "correspDesc")
    corresp_contexts = _index_by_xml_id(root, "correspContext")

    letters = [
        _parse_letter(div, corresp_descs, warnings)
        for div in _descendants(root, "div", type="letter")
    ]
    groups = [
        _parse_group(div, corresp_contexts)
        for div in _descendants(root, "div", type="correspondance")
    ]

    title, short_title = _parse_titles(root)
    return {
        "volume": volume,
        "title": title,
        "shortTitle": short_title,
        "groups": groups,
        "letters": letters,
        "warnings": warnings.as_list(),
    }


def plain_text(nodes):
    """Flatten body nodes to their reading text.

    Used by the tests and by whatever builds the search index. Apparatus kept
    outside ``content`` (variants, expansions, witness remarks) is skipped, so
    the result reads like the letter does.
    """
    if isinstance(nodes, dict):
        nodes = [nodes]
    parts = []
    for node in nodes:
        if "text" in node:
            parts.append(node["text"])
        else:
            parts.append(plain_text(node.get("content", [])))
    return "".join(parts)


# --------------------------------------------------------------------------
# Volume level
# --------------------------------------------------------------------------


def _parse_titles(root):
    """Return (title, short title) from the TEI header's titleStmt.

    b1's titleStmt holds three titles: the series (@level="s"), the volume's
    own title, and a short form (@type="short").
    """
    title = None
    short_title = None
    title_stmt = _first(_descendants(root, "titleStmt"))
    if title_stmt is None:
        return title, short_title
    for element in _children(title_stmt, "title"):
        if element.get("type") == "short":
            short_title = short_title or _text_of(element)
        elif element.get("level") is None:
            # @level="s" marks the series title ("Søren Kierkegaards
            # Skrifter"); the unmarked one names this volume.
            title = title or _text_of(element)
    return title, short_title


def _parse_group(div, corresp_contexts):
    """Parse a <div type="correspondance"> -- one correspondent's letters."""
    group_id = _strip_hash(div.get("corresp"))
    context = corresp_contexts.get(group_id)
    return {
        "id": group_id,
        "heading": _heading_of(div, "topText"),
        "notes": _context_notes(context),
        "letterIds": [
            letter.get("n") for letter in _descendants(div, "div", type="letter")
        ],
    }


# --------------------------------------------------------------------------
# Letter level
# --------------------------------------------------------------------------


def _parse_letter(div, corresp_descs, warnings):
    """Parse a <div type="letter">, metadata and transcription together."""
    letter_id = div.get("n")
    corresp_desc_id = _strip_hash(div.get("corresp"))
    corresp_desc = corresp_descs.get(corresp_desc_id)
    if corresp_desc is None:
        warnings.add(
            letter_id,
            "correspDesc",
            "letter %s references %s, which is not in the TEI header"
            % (letter_id, corresp_desc_id),
        )

    # The letter's heading lives in @n on <head type="letterHeader"/>, which
    # has no text content of its own. It is lifted out of the body so displays
    # do not have to special-case an empty element.
    heading_element = _find_head(div, "letterHeader")

    return {
        "id": letter_id,
        "xmlId": div.get(XML_ID),
        "correspDescId": corresp_desc_id,
        "heading": heading_element.get("n") if heading_element is not None else None,
        "sender": _correspondent(corresp_desc, "sent", letter_id, warnings),
        "recipient": _correspondent(corresp_desc, "received", letter_id, warnings),
        "context": _letter_context(corresp_desc),
        "body": _content(div, letter_id, warnings, skip=heading_element),
    }


def _correspondent(corresp_desc, action_type, letter_id, warnings):
    """Parse one <correspAction> ("sent" or "received") into a correspondent.

    Returns ``None`` when the edition records no such action at all, so that a
    missing sender stays visibly missing.
    """
    if corresp_desc is None:
        return None
    action = None
    for candidate in _children(corresp_desc, "correspAction"):
        if candidate.get("type") == action_type:
            action = candidate
            break
    if action is None:
        return None

    name = _first(_children(action, "name"))
    place = _first(_children(action, "placeName"))
    note = _first(_children(action, "note"))
    return {
        "name": _text_of(name),
        "date": _parse_date(_first(_children(action, "date")), letter_id, warnings),
        "place": _place(place),
        "note": _text_of(note),
    }


def _place(element):
    """Place of sending/receipt, if the edition records one (b1 does not)."""
    if element is None:
        return None
    return {"name": _text_of(element), "key": element.get("key")}


def _letter_context(corresp_desc):
    """Link a letter to the correspondence group it belongs to.

    Each <correspContext> either carries its own id (the first letter of a
    group) or points at that first one with @sameAs. Both cases resolve to the
    same group id, which is what <div type="correspondance"> references.
    """
    if corresp_desc is None:
        return {"groupId": None, "sameAs": None, "notes": []}
    context = _first(_children(corresp_desc, "correspContext"))
    if context is None:
        return {"groupId": None, "sameAs": None, "notes": []}
    same_as = context.get("sameAs")
    return {
        "groupId": _strip_hash(same_as) if same_as else context.get(XML_ID),
        "sameAs": same_as,
        "notes": _context_notes(context),
    }


def _context_notes(context):
    """Free-text paragraphs of a <correspContext>, empty ones dropped."""
    if context is None:
        return []
    notes = []
    for paragraph in _children(context, "p"):
        text = _text_of(paragraph)
        if text:
            notes.append(text)
    return notes


# --------------------------------------------------------------------------
# Dates
# --------------------------------------------------------------------------


def _parse_date(element, letter_id, warnings):
    """Parse a <date> into raw + derived values, or ``None`` if absent."""
    if element is None:
        return None
    date = _date_value(element.get("when"), letter_id, warnings)
    if date is None:
        date = _empty_date_value()
    date["notBefore"] = _date_value(element.get("notBefore"), letter_id, warnings)
    date["notAfter"] = _date_value(element.get("notAfter"), letter_id, warnings)
    date["source"] = element.get("source")
    date["text"] = _text_of(element)
    return date


def _empty_date_value():
    return {
        "raw": None,
        "iso": None,
        "precision": None,
        "year": None,
        "month": None,
        "day": None,
    }


def _date_value(raw, letter_id, warnings):
    """Read one date string.

    The edition writes ``yyyymmdd`` and zero-pads what it does not know, so
    ``18481200`` is a month and ``18370000`` a year. Dash-separated ISO forms
    are accepted too, in case other volumes use them.
    """
    if not raw:
        return None
    value = _empty_date_value()
    value["raw"] = raw

    digits = raw.replace("-", "")
    if not digits.isdigit() or len(digits) not in (4, 6, 8):
        warnings.add(
            letter_id, "date", "unreadable date %r kept as raw value only" % raw
        )
        return value

    year = int(digits[0:4])
    month = int(digits[4:6]) if len(digits) >= 6 else 0
    day = int(digits[6:8]) if len(digits) >= 8 else 0

    value["year"] = year
    value["iso"] = "%04d" % year
    value["precision"] = "year"
    if month:
        value["month"] = month
        value["iso"] += "-%02d" % month
        value["precision"] = "month"
        if day:
            value["day"] = day
            value["iso"] += "-%02d" % day
            value["precision"] = "day"
    return value


# --------------------------------------------------------------------------
# Body
# --------------------------------------------------------------------------


def _content(element, letter_id, warnings, skip=None):
    """Turn an element's mixed content into a list of nodes."""
    structural = _local_name(element) in STRUCTURAL_ELEMENTS
    nodes = []
    _append_text(nodes, element.text, structural)
    for child in element:
        if child is not skip:
            nodes.append(_node(child, letter_id, warnings))
        _append_text(nodes, child.tail, structural)
    return nodes


def _append_text(nodes, raw, structural):
    """Append a text node, collapsing the XML file's line wrapping."""
    if not raw:
        return
    text = _WHITESPACE.sub(" ", raw)
    if structural and not text.strip():
        return
    nodes.append({"text": text})


def _node(element, letter_id, warnings):
    """Turn one element into a node."""
    tag = _local_name(element)

    if tag in ANNOTATION_ELEMENTS:
        node = _attributes(element, tag)
        node["note"] = _text_of(element)
        return node

    if tag not in ELEMENT_ATTRIBUTES:
        warnings.add(
            letter_id,
            tag,
            "unhandled TEI element <%s>; its text is kept but its markup is "
            "not modelled" % tag,
        )

    node = _attributes(element, tag)
    node["content"] = _content(element, letter_id, warnings)

    if tag == "app":
        # Keep the established reading in the flow, the rejected ones beside it.
        node["content"], node["variants"] = _split(node["content"], ("lem",))
    elif tag == "choice":
        # Keep the abbreviation as written, the editors' expansion beside it.
        node["content"], node["alternatives"] = _split(node["content"], ("abbr",))
    return node


def _split(nodes, primary_types):
    """Split a node list into (primary, secondary) by node type.

    Bare text nodes always stay in the primary list: text the encoding put
    directly inside an <app> or <choice> is part of the letter, and dropping
    it out of the reading flow would lose it.
    """
    primary = []
    secondary = []
    for node in nodes:
        if "text" in node or node.get("type") in primary_types:
            primary.append(node)
        else:
            secondary.append(node)
    return primary, secondary


def _attributes(element, tag):
    """Start a node with its type and the attributes declared for that tag."""
    node = {"type": tag}
    for name in ELEMENT_ATTRIBUTES.get(tag, ()):
        # TEI's @type would collide with the node's own "type".
        node["subtype" if name == "type" else name] = element.get(name)
    return node


# --------------------------------------------------------------------------
# Small XML helpers
# --------------------------------------------------------------------------


class _Warnings:
    """Collects one entry per distinct problem, in the order found."""

    def __init__(self):
        self._seen = set()
        self._entries = []

    def add(self, letter_id, tag, message):
        key = (letter_id, tag, message)
        if key in self._seen:
            return
        self._seen.add(key)
        self._entries.append(
            {"letterId": letter_id, "tag": tag, "message": message}
        )

    def as_list(self):
        return list(self._entries)


def _local_name(element):
    """Element name without its namespace."""
    tag = element.tag
    if isinstance(tag, str) and tag.startswith("{"):
        return tag.split("}", 1)[1]
    return tag


def _descendants(element, tag, **attributes):
    """All descendants with the given local name and attribute values."""
    return [
        found
        for found in element.iter()
        if _local_name(found) == tag
        and all(found.get(key) == value for key, value in attributes.items())
    ]


def _children(element, tag):
    """Direct children with the given local name."""
    return [child for child in element if _local_name(child) == tag]


def _index_by_xml_id(element, tag):
    """Map xml:id -> element for every descendant with the given local name."""
    return {
        found.get(XML_ID): found
        for found in _descendants(element, tag)
        if found.get(XML_ID)
    }


def _first(elements):
    return elements[0] if elements else None


def _find_head(element, head_type):
    for child in _children(element, "head"):
        if child.get("type") == head_type:
            return child
    return None


def _heading_of(element, head_type):
    head = _find_head(element, head_type)
    return head.get("n") if head is not None else None


def _text_of(element):
    """All text under an element, whitespace collapsed; ``None`` if empty."""
    if element is None:
        return None
    text = _WHITESPACE.sub(" ", "".join(element.itertext())).strip()
    return text or None


def _strip_hash(reference):
    """Turn a TEI pointer like ``#correspDesc1`` into a bare id."""
    if not reference:
        return None
    return reference[1:] if reference.startswith("#") else reference
