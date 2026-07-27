"""Parse a TEI volume's scholarly commentary into display-agnostic JSON.

Companion to ``parse_tei``: that module reads the letters
(``data/vendor/<volume>/txt.xml``), this one reads the commentary beside them
(``data/vendor/<volume>/kom.xml``). Both are vendored, read-only truth, and
this module keeps to the same rules -- no display decisions, no repairs, raw
values kept next to anything derived from them.

The commentary is the edition's scholarly apparatus: for each glossed phrase
in a letter, a note that identifies people, places, books and allusions. It is
the grounding data for person biographies, so the person keys it carries are
the join key of the whole person index and are never abbreviated or cleaned.

How a letter reaches its commentary: letters in ``txt.xml`` point here with
``<ref type="commentary" target="kom.xml#b-9">``, so a note's ``id`` is the
join. This parser reads only ``kom.xml`` and resolves no cross-file links.

Result shape
------------

``parse_commentary(path)`` returns::

    {
      "volume": "b1",                     # the volume directory's name
      "notes": [
        {"id": "b-9",                     # @xml:id, unique within the volume
         "n": "9,29",                     # @n: "page,line" into the printed
                                          #     edition -- NOT unique, two
                                          #     notes can gloss one line
         "lemma": "Henrichsen har forladt Borgerdydsskolen ... til Helsingør",
         "text": "Rudolph Johannes Frederik Henrichsen (1800-71), da. ...",
         "paragraphs": ["Rudolph Johannes ..."],
         "subLemmas": ["Borgerdydsskolen:"],
         "persNames": [{"key": "Henrichsen, Rudolph Johannes Frederik",
                        "text": "Rudolph Johannes Frederik Henrichsen",
                        "n": "*", "isSubject": True, "sameAs": None}],
         "placeNames": [{"key": "Borgerdydskolen",
                         "text": "Borgerdydsskolen", "sameAs": None}],
         "noteRefs": [{"target": "b-13", "n": "10,8"}],
         "refs": [{"type": "map", "target": "../kort/kbh_B1.htm",
                   "n": "kbh", "rend": None, "text": "se kort 2, B1"}],
         "bibleRefs": [{"key": None, "text": "Sl 6,3"}],
         "figures": [{"url": "../b1/ill_k2.jpg", "caption": "2. Sær..."}]},
      ],
      "warnings": [{"noteId": ..., "tag": ..., "message": ...}],
    }

Lemma and prose
---------------

Every note is ``<label>`` + ``<p>``. The label holds the **lemma** -- the
phrase from the letter that is being glossed, quoted from the transcription
(long ones elided with " ... "). The paragraph holds the commentary prose.
They are separate fields because they are different kinds of text: the lemma
is the letter's words, the prose is the editors'.

Three notes in the corpus (b43 b-2072, b259 b-1396, b276 b-5451) split their
prose over two ``<p>`` elements, mid-sentence. ``paragraphs`` keeps them
apart, ``text`` joins them with a space -- which is how they read -- and the
split is reported as a warning so the oddity stays visible.

``subLemmas`` is **derived**, not encoded as such: within the prose the
edition sets further glossed phrases in bold (``<hi rendition="#bol">``),
usually followed by a colon, to start a new gloss inside the same note
("... til Helsingør. -- Borgerdydsskolen: københavnsk privatskole ...").
The source marks only the rendition; reading it as "another lemma" is this
parser's inference. The strings themselves are raw.

Names
-----

``persNames`` and ``placeNames`` list **one entry per occurrence**, in
document order, so a name mentioned twice under one key appears twice (51
notes do this corpus-wide, 23 of them with differing surface forms). Nothing
is deduplicated, because the surface forms differ and are evidence. Callers
that want distinct keys take a set:

    mentions = [note for note in commentary["notes"]
                if any(p["key"] == wanted for p in note["persNames"])]

Every ``persName`` in the corpus carries ``@key`` (3926 of 3926 verified);
only 519 of 2507 ``placeName`` elements do, so a place key is often ``None``.
A ``persName`` without a key is reported as a warning rather than dropped.

``@sameAs`` is **not** a pointer here: it holds an alternative name string in
the same "Efternavn, Fornavn" form (key "Kierkegaard, Henriette", sameAs
"Kierkegaard, Jette"). It is kept raw; resolving aliases is not this parser's
job.

``isSubject`` is derived from ``@n="*"``, which the edition puts on the person
a note actually identifies -- the one whose biography follows. The raw ``n``
is kept beside it. The reading is an inference, but a well-supported one: 285
of 312 starred names are immediately followed by "(birth-death", against 101
of 3614 unstarred ones.

Apparatus kept out of the reading text
--------------------------------------

``figure`` (7 notes) wraps an illustration and its caption inside the prose
paragraph. Caption text would otherwise read as commentary, so figures are
lifted out into ``figures`` (url + caption) and excluded from ``text``.

Everything else stays in the reading text as the edition wrote it, including
the empty parentheses left by ``<ptr/>`` cross-references ("ty. by i Sachsen
()."): the source puts the brackets there, and a display fills them with a
link. Their targets are in ``noteRefs`` -- all 2262 of them resolve to a note
in the same file.

TEI elements this parser does not model are still flattened into the reading
text, and each one is reported in ``warnings`` so nothing disappears
unnoticed.
"""

import os
import re
import xml.etree.ElementTree as ET

TEI_NAMESPACE = "http://www.tei-c.org/ns/1.0"
XML_ID = "{http://www.w3.org/XML/1998/namespace}id"

_WHITESPACE = re.compile(r"\s+")

# The only <note type> the commentary files use. Anything else is a surprise.
COMMENTARY_TYPE = "commentary"

# Inline elements the parser understands inside a note. Their text belongs in
# the reading flow; the interesting ones are also collected into their own
# fields. Anything outside this set raises a warning.
INLINE_ELEMENTS = frozenset(
    [
        "hi",  # rendition only: italics for titles, bold for sub-lemmas
        "persName",
        "placeName",
        "ptr",  # empty cross-reference to another note in this file
        "ref",  # reference out of this file (maps, other volumes, ...)
        "rs",  # referring string; in this corpus always a bible reference
        "formula",  # notation="mathml"; its text is a plain number
        "name",
        "title",
        "orgName",
        "bibl",
        "date",
    ]
)

# Elements whose text is apparatus around the prose rather than prose: lifted
# into their own field and excluded from the reading text.
APPARATUS_ELEMENTS = frozenset(["figure"])

# The rendition the edition uses for a glossed phrase (in a label: the lemma;
# inside the prose: a further lemma). One occurrence carries a trailing space,
# so renditions are compared stripped.
LEMMA_RENDITION = "#bol"


def parse_commentary(path):
    """Parse one vendored commentary file into a JSON-serializable dict.

    The volume name is taken from the containing directory, e.g.
    ``data/vendor/b1/kom.xml`` -> ``"b1"``.
    """
    root = ET.parse(path).getroot()
    volume = os.path.basename(os.path.dirname(os.path.abspath(path)))
    return parse_kom(root, volume)


def parse_kom(root, volume):
    """Parse an already-loaded commentary document. See the module docstring."""
    warnings = _Warnings()
    notes = [
        _parse_note(element, warnings)
        for element in _descendants(root, "note")
    ]
    _check_unique_ids(notes, warnings)
    return {"volume": volume, "notes": notes, "warnings": warnings.as_list()}


# --------------------------------------------------------------------------
# Note level
# --------------------------------------------------------------------------


def _parse_note(element, warnings):
    """Parse one <note type="commentary"> into a note dict."""
    note_id = element.get(XML_ID)
    if not note_id:
        warnings.add(None, "note", "note without xml:id; it cannot be linked")
    if element.get("type") != COMMENTARY_TYPE:
        warnings.add(
            note_id,
            "note",
            "unexpected note type %r; parsed as commentary anyway"
            % element.get("type"),
        )
    if not element.get("n"):
        warnings.add(note_id, "note", "note without @n page/line reference")

    labels = _children(element, "label")
    paragraphs = _children(element, "p")
    if len(labels) != 1:
        warnings.add(
            note_id, "label", "note has %d <label> elements, expected 1"
            % len(labels)
        )
    if len(paragraphs) != 1:
        warnings.add(
            note_id,
            "p",
            "note has %d <p> elements, expected 1; they are joined into one "
            "reading text" % len(paragraphs),
        )
    _check_children(element, ("label", "p"), note_id, warnings)

    prose = [_flatten(p) for p in paragraphs]
    note = {
        "id": note_id,
        "n": element.get("n"),
        "lemma": _flatten(labels[0]) if labels else None,
        "paragraphs": [text for text in prose if text],
        "text": " ".join(text for text in prose if text),
        "subLemmas": _sub_lemmas(paragraphs),
        "persNames": [],
        "placeNames": [],
        "noteRefs": [],
        "refs": [],
        "bibleRefs": [],
        "figures": [],
    }
    _collect(element, note, note_id, warnings)
    return note


def _sub_lemmas(paragraphs):
    """Bold runs inside the prose: the edition's further glossed phrases.

    Derived from ``@rendition``, see the module docstring. Bold inside a label
    is the lemma itself and is not collected here.
    """
    found = []
    for paragraph in paragraphs:
        for element in paragraph.iter():
            if _local_name(element) != "hi":
                continue
            if (element.get("rendition") or "").strip() != LEMMA_RENDITION:
                continue
            text = _flatten(element)
            if text:
                found.append(text)
    return found


def _collect(element, note, note_id, warnings):
    """Walk a note and file every element the parser models into its field.

    Names are collected from the whole note, labels included, so a name in a
    lemma would still reach the person index.
    """
    for child in element.iter():
        tag = _local_name(child)
        if tag == "persName":
            note["persNames"].append(_person(child, note_id, warnings))
        elif tag == "placeName":
            note["placeNames"].append(_place(child))
        elif tag == "ptr":
            note["noteRefs"].append(_note_ref(child, note_id, warnings))
        elif tag == "ref":
            note["refs"].append(_ref(child))
        elif tag == "rs":
            note["bibleRefs"].append(_bible_ref(child, note_id, warnings))
        elif tag == "figure":
            note["figures"].append(_figure(child))


def _person(element, note_id, warnings):
    """One <persName>: the join key of the person index, kept complete."""
    key = element.get("key")
    if not key:
        # Two names in the corpus carry key="" (b241 b-3238 "Bera", b43
        # b-2072 "C. Michelet"). The empty string is kept as the source wrote
        # it; only the warning says it cannot be joined on.
        warnings.add(
            note_id,
            "persName",
            "persName %r has @key=%r and cannot join the person index"
            % (_flatten(element), key),
        )
    mark = element.get("n")
    return {
        "key": key,
        "text": _flatten(element),
        "n": mark,
        # The edition stars the person a note identifies; see the docstring.
        "isSubject": mark == "*",
        "sameAs": element.get("sameAs"),
    }


def _place(element):
    """One <placeName>. Most carry no @key; that stays ``None``, not a guess."""
    return {
        "key": element.get("key"),
        "text": _flatten(element),
        "sameAs": element.get("sameAs"),
    }


def _note_ref(element, note_id, warnings):
    """A <ptr> cross-reference to another note in the same file."""
    target = element.get("target")
    if element.get("type") != COMMENTARY_TYPE:
        warnings.add(
            note_id,
            "ptr",
            "cross-reference of unexpected type %r" % element.get("type"),
        )
    if not target or not target.startswith("#"):
        warnings.add(
            note_id, "ptr", "cross-reference target %r is not local" % target
        )
    return {"target": _strip_hash(target), "n": element.get("n")}


def _ref(element):
    """A <ref> out of this file: a map, another volume, an introduction."""
    return {
        "type": element.get("type"),
        "target": element.get("target"),
        "n": element.get("n"),
        "rend": element.get("rend"),
        "text": _flatten(element),
    }


def _bible_ref(element, note_id, warnings):
    """A <rs>: in this corpus always type="bible" (164 of 164 verified)."""
    if element.get("type") != "bible":
        warnings.add(
            note_id,
            "rs",
            "referring string of unexpected type %r kept as a bible reference"
            % element.get("type"),
        )
    return {"key": element.get("key"), "text": _flatten(element)}


def _figure(element):
    """An illustration inside the prose: url plus caption, kept out of text."""
    graphic = _first(_children(element, "graphic"))
    captions = [_flatten(head) for head in _children(element, "head")]
    return {
        "url": graphic.get("url") if graphic is not None else None,
        "caption": " ".join(text for text in captions if text) or None,
    }


# --------------------------------------------------------------------------
# Text flattening
# --------------------------------------------------------------------------


def _flatten(element, skip=APPARATUS_ELEMENTS):
    """All text under an element as one reading line, apparatus excluded.

    Whitespace is collapsed because the XML wraps lines for legibility. Text
    inside ``skip`` elements is left out, but the text *after* them is kept.
    """
    parts = []
    _gather(element, parts, skip)
    return _collapse("".join(parts))


def _gather(element, parts, skip):
    if _local_name(element) in skip:
        return
    if element.text:
        parts.append(element.text)
    for child in element:
        _gather(child, parts, skip)
        # A skipped child still separates the text around it.
        if child.tail:
            parts.append(child.tail)


def _collapse(text):
    return _WHITESPACE.sub(" ", text).strip()


# --------------------------------------------------------------------------
# Structural checks
# --------------------------------------------------------------------------


def _check_children(element, expected, note_id, warnings):
    """Warn about any element inside a note the parser does not model."""
    for child in element.iter():
        if child is element:
            continue
        tag = _local_name(child)
        if tag in expected or tag in INLINE_ELEMENTS or tag in APPARATUS_ELEMENTS:
            continue
        if tag in ("graphic", "head") and _inside_apparatus(element, child):
            continue
        warnings.add(
            note_id,
            tag,
            "unhandled TEI element <%s>; its text is kept in the reading text "
            "but its markup is not modelled" % tag,
        )


def _inside_apparatus(root, wanted):
    """True if an element sits inside a figure (where captions belong)."""
    for candidate in root.iter():
        if _local_name(candidate) not in APPARATUS_ELEMENTS:
            continue
        for descendant in candidate.iter():
            if descendant is wanted:
                return True
    return False


def _check_unique_ids(notes, warnings):
    seen = set()
    for note in notes:
        note_id = note["id"]
        if note_id in seen:
            warnings.add(
                note_id, "note", "duplicate note id %r" % note_id
            )
        seen.add(note_id)


# --------------------------------------------------------------------------
# Small XML helpers
# --------------------------------------------------------------------------


class _Warnings:
    """Collects one entry per distinct problem, in the order found."""

    def __init__(self):
        self._seen = set()
        self._entries = []

    def add(self, note_id, tag, message):
        key = (note_id, tag, message)
        if key in self._seen:
            return
        self._seen.add(key)
        self._entries.append(
            {"noteId": note_id, "tag": tag, "message": message}
        )

    def as_list(self):
        return list(self._entries)


def _local_name(element):
    """Element name without its namespace."""
    tag = element.tag
    if isinstance(tag, str) and tag.startswith("{"):
        return tag.split("}", 1)[1]
    return tag


def _descendants(element, tag):
    """All descendants with the given local name."""
    return [found for found in element.iter() if _local_name(found) == tag]


def _children(element, tag):
    """Direct children with the given local name."""
    return [child for child in element if _local_name(child) == tag]


def _first(elements):
    return elements[0] if elements else None


def _strip_hash(reference):
    """Turn a TEI pointer like ``#b-13`` into a bare id."""
    if not reference:
        return None
    return reference[1:] if reference.startswith("#") else reference
