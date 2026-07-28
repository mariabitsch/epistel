"""Filtering and searching the index, decided at build time.

Everything a reader can narrow the letter index by is worked out here, while
the whole corpus is in memory, and shipped as finished data:

* ``facets(views)`` -- the three lists the filter controls are built from
  (sender, recipient, year), each value with the number of letters behind it.
  The page renders them as ordinary ``<select>`` elements, so the browser does
  the hard parts of the interaction and there is nothing to re-render.
* ``search_index(views)`` -- an inverted index from folded word to the letters
  that contain it, built from the reading text of each letter (the parser's
  ``plain_text``) and from Maria Notabene's summary where there is one.

The index is inverted rather than a bundle of letter texts because it is a
third of the size: the corpus is 668 000 characters of prose, but only about
twelve and a half thousand distinct words, and a word that occurs four hundred
times is stored once. Nothing in it is HTML -- markup would neither be
searched nor shown, and would double the download for nothing.

Folding
-------

``fold()`` is the one rule both sides of the search have to agree on, and
``static/search.js`` implements exactly the same one: lower case, then æ -> ae,
ø -> oe, å -> aa, then decorations dropped. It means "Soren" finds "Søren" and
"Kaerlighed" finds "Kjærlighed", which is how a Danish reader types when the
keyboard is not helping. Any change here is a change there.
"""

import json
import re
import unicodedata

from .persons import display_name, sort_key

# Two letters is the shortest thing worth indexing: single letters match
# almost everything and would cost more than they find.
MINIMUM_TOKEN = 2

_WORD = re.compile(r"[0-9a-z]+")

# Same three letters as ``persons.TRANSLITERATIONS``, and for the same reason:
# they are letters in their own right, not decorated vowels, so the Unicode
# decomposition below must not be allowed to see them first.
_FOLDINGS = (
    ("æ", "ae"),
    ("ø", "oe"),
    ("å", "aa"),
    ("ä", "ae"),
    ("ö", "oe"),
    ("ü", "ue"),
    ("ß", "ss"),
)

UNDATED_VALUE = "udateret"


def fold(value):
    """Lower case, Danish letters spelled out, decorations dropped."""
    folded = value.lower()
    for letter, replacement in _FOLDINGS:
        folded = folded.replace(letter, replacement)
    folded = unicodedata.normalize("NFKD", folded)
    return "".join(char for char in folded if not unicodedata.combining(char))


def tokens(value):
    """The distinct searchable words of a string, folded."""
    return {word for word in _WORD.findall(fold(value)) if len(word) >= MINIMUM_TOKEN}


def facet_year(view):
    """``(year, approximate)`` for the year filter, or ``(None, False)``.

    A letter is filed under the first year it could have been written in --
    the edition's ``notBefore`` -- and marked approximate when the edition
    does not actually pin it to that year: when it only knows the year, when
    the span it gives runs across a new year, or when the upper bound it wrote
    cannot be read. Filing it under one year and saying "ca." is the honest
    version; filing it under none would lose it, and filing it under several
    would count it twice.
    """
    stretch = view.get("span")
    if not stretch:
        return None, False
    approximate = (
        stretch["start"].year != stretch["end"].year
        or stretch["precision"] == "year"
        or stretch["open_end"]
    )
    return stretch["start"].year, approximate


def facets(views):
    """The three filter lists, each value with its letter count.

    Sender and recipient are filtered on the edition's own name form -- the
    string in ``correspDesc`` -- because that is what distinguishes one
    correspondent from another in the source. The label beside it is the same
    name read as a sentence.
    """
    return {
        "senders": _correspondent_facet(views, "sender_raw", "sender"),
        "recipients": _correspondent_facet(views, "recipient_raw", "recipient"),
        "years": _year_facet(views),
    }


def _correspondent_facet(views, raw_field, display_field):
    counts = {}
    labels = {}
    for view in views:
        value = view[raw_field]
        if not value:
            # The edition names no one. "ukendt afsender" is the display's
            # word for it, and it is not a name to filter by.
            continue
        counts[value] = counts.get(value, 0) + 1
        labels[value] = display_name(value) or value
    return [
        {"value": value, "label": labels[value], "count": counts[value]}
        for value in sorted(counts, key=lambda value: sort_key(labels[value]))
    ]


def _year_facet(views):
    """Every year that holds a letter, plus the letters no year can hold.

    Years with no letters are left out: this is a filter, not a scale, and an
    option that can only ever return nothing is a dead end. The timeline is
    where the empty years are shown, because there they mean something.
    """
    counts = {}
    approximate = set()
    undated = 0
    for view in views:
        year, approximate_year = facet_year(view)
        if year is None:
            undated += 1
            continue
        counts[year] = counts.get(year, 0) + 1
        if approximate_year:
            approximate.add(year)
    entries = [
        {
            "value": "%d" % year,
            "label": "%d" % year,
            "count": counts[year],
            "approximate": year in approximate,
        }
        for year in sorted(counts)
    ]
    if undated:
        entries.append(
            {
                "value": UNDATED_VALUE,
                "label": "Udateret",
                "count": undated,
                "approximate": False,
            }
        )
    return entries


def letter_filters(view):
    """What one letter is filtered by, as the values the facets offer.

    Returned as a small mapping so that the page and the script agree on the
    names without either of them knowing how the other works.
    """
    year, _ = facet_year(view)
    return {
        "sender": view["sender_raw"] or "",
        "recipient": view["recipient_raw"] or "",
        "year": "%d" % year if year is not None else UNDATED_VALUE,
    }


def search_index(views):
    """The prebuilt free-text index. ``{"letters": [...], "words": {...}}``.

    ``letters`` are the letters' URL slugs in index order; ``words`` maps a
    folded word to the positions in that list where it occurs. Positions are
    sorted, the words are sorted, and nothing is derived from the environment,
    so two builds of the same corpus write the same bytes.
    """
    postings = {}
    slugs = []
    for position, view in enumerate(views):
        slugs.append(view["slug"])
        text = view["plain_text"]
        if view.get("summary"):
            # The summaries are searchable too: they are often where a
            # letter's subject is said in modern Danish, and the letters
            # themselves never say "forlovelse" the way a reader types it.
            text = "%s\n%s" % (text, view["summary"])
        for word in tokens(text):
            postings.setdefault(word, []).append(position)
    return {
        "letters": slugs,
        "words": {word: postings[word] for word in sorted(postings)},
    }


def index_script(index):
    """The index as a script that hands itself to the page.

    A plain ``.json`` file would have to be fetched, and ``fetch`` is refused
    on ``file://`` -- the built site has to work when it is opened from a
    directory, not only when it is served. A script assigning one global has
    no such problem, costs one line in the page, and is loaded only when a
    reader actually searches (see ``static/search.js``).
    """
    payload = json.dumps(
        index, ensure_ascii=False, separators=(",", ":"), sort_keys=True
    )
    return "window.epistelSearchIndex=%s;\n" % payload
