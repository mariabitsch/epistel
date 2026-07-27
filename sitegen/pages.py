"""Whole HTML documents, as plain Python string functions.

No template engine: the site has two page types, and a function that returns a
string is easier to read -- and to throw away -- than a dependency. Every value
that comes from the data passes through ``sitegen.html`` on its way in.

The pages take view models (built in ``sitegen.site``), not parser output, so
this module contains no knowledge of TEI. All links are relative, because the
built site has to work from any directory of any static host.
"""

from .html import element, text

SITE_TITLE = "epistel"
SITE_TAGLINE = "demonstrationsvisning"

# Where each page type sits, and what it takes to get back to the root.
INDEX_TO_ROOT = ""
LETTER_TO_ROOT = "../../"


def index_page(books):
    """The front page: every letter, by volume and then by correspondence.

    One page for the whole corpus. The edition's own two levels of order are
    the two levels of the page -- the volume it was printed in, and the
    correspondence it belongs to -- so a reader who knows the edition can find
    a letter the way they would in print. Filtering and search are a later
    slice; this page is the plain list they will filter.
    """
    count = sum(len(book["letters"]) for book in books)
    body = element("h1", "Breve") + _intro(books, count) + _volume_navigation(books)
    body += "".join(_book(book) for book in books)
    return _document(
        title="Breve",
        main=body,
        root=INDEX_TO_ROOT,
        description="Søren Kierkegaards %s i %s, vist fra offentlige TEI-filer."
        % (_letter_count(count), _volume_count(len(books))),
    )


def letter_page(view, previous, following, section):
    """One letter: what it is, what it says, and what it belongs with."""
    header = element(
        "p",
        element("a", "← Alle breve", href=LETTER_TO_ROOT),
        class_="crumb",
    )
    header += element("h1", text(view["title"]))
    header += _metadata(view, section)

    article = element("header", header)
    article += _transcription(view)
    article += _sequence_navigation(previous, following)
    article += _same_correspondence(view, section)

    return _document(
        title=view["title"],
        main=element("article", article, class_="letter"),
        root=LETTER_TO_ROOT,
        description="%s: fra %s til %s, %s."
        % (view["title"], view["sender"], view["recipient"], view["date_text"]),
    )


# ---------------------------------------------------------------------------
# Index parts
# ---------------------------------------------------------------------------


def _intro(books, count):
    """What the reader is looking at -- as many volumes as were built.

    Written from the list, not from a sentence about one volume, so a build of
    b1 alone and a build of the whole corpus both describe themselves
    truthfully.
    """
    return element(
        "p",
        "Søren Kierkegaards breve, læst direkte fra den TEI-kodede udgave "
        "<i>Søren Kierkegaards Skrifter</i>. Denne demonstration viser "
        + element(
            "strong", "%s i %s" % (_letter_count(count), _volume_count(len(books)))
        )
        + ", ordnet efter bind og brevveksling.",
        class_="lead",
    )


def _volume_navigation(books):
    """A jump list to each volume's section. Fourteen anchors, no script."""
    if len(books) < 2:
        return ""
    items = "".join(
        element(
            "li",
            element(
                "a",
                element("b", text(book["shortTitle"])) + " " + text(book["title"]),
                href="#%s" % book["anchor"],
            ),
        )
        for book in books
    )
    return element(
        "nav",
        element("ol", items, class_="volume-list"),
        class_="volume-nav",
        aria_label="Bind",
    )


def _book(book):
    """One volume: a band naming it, then its correspondences."""
    heading = element(
        "h2",
        element("b", text(book["shortTitle"])) + " " + text(book["title"]),
    )
    count = element(
        "p", _letter_count(len(book["letters"])), class_="volume-count"
    )
    return element(
        "section",
        element("div", heading + count, class_="volume-head")
        + "".join(_section(section) for section in book["sections"]),
        class_="volume",
        id=book["anchor"],
    )


def _section(section):
    """One correspondence: who it is with, and every letter in it.

    Heading, note and count are wrapped as one block, because they are one
    thing -- the label on the group -- and the design sets them as a band
    above the letters rather than as three loose paragraphs.

    A correspondence sits inside a volume, so its heading is an ``h3``: the
    document outline is h1 Breve / h2 volume / h3 correspondence / h4 letter.
    The band looks the same as it did when there was only one volume.
    """
    heading = element("h3", text(section["heading"]))
    notes = "".join(
        element("p", text(note), class_="group-note")
        for note in section["notes"]
        if note != section["heading"]
    )
    count = element("p", _letter_count(len(section["letters"])), class_="group-count")
    entries = "".join(_entry(view) for view in section["letters"])
    return element(
        "section",
        element("div", heading + notes + count, class_="group-head")
        + element("ol", entries, class_="letter-list"),
        class_="correspondence",
        id=section["id"],
    )


def _entry(view):
    """One line in the index: a linked heading and the bare facts."""
    heading = element(
        "h4", element("a", text(view["title"]), href="brev/%s/" % view["slug"])
    )
    return element("li", heading + _summary(view), class_="letter-entry")


def _summary(view):
    return _definition_list(
        [
            ("Fra", _name(view["sender"], view["sender_raw"])),
            ("Til", _name(view["recipient"], view["recipient_raw"])),
            ("Dateret", _date(view)),
        ],
        class_name="letter-meta",
    )


# ---------------------------------------------------------------------------
# Letter parts
# ---------------------------------------------------------------------------


def _transcription(view):
    """The letter as it reads -- or a plain sentence when the edition has none.

    Three letters in b171 are printed as cross-references: the edition records
    who wrote to whom and when, and prints the text under another number. An
    empty sheet of paper would read as a fault in the display, so the page
    says what the source holds instead. The edition's own pointer ("se Brev
    193") is already in the metadata panel above, as the source's words.
    """
    if view["body"].strip():
        return element("div", view["body"], class_="transcription", lang="da")
    return element(
        "p", "Udgaven trykker ingen brevtekst her.", class_="no-transcription"
    )


def _metadata(view, section):
    """The panel above the transcription -- correspDesc, never the heading.

    The edition's own letter headings are a display string that is sometimes
    damaged in the source (letter 39 is missing everything but its recipient),
    so this panel is built from the structured fields instead.
    """
    rows = [
        ("Fra", _name(view["sender"], view["sender_raw"])),
        ("Til", _name(view["recipient"], view["recipient_raw"])),
        ("Dateret", _date(view)),
    ]
    if view["place"]:
        rows.append(("Sted", text(view["place"])))
    if view["note"]:
        # The edition sometimes parks a fragment of its own display string
        # here (letter 39 keeps "· udateret [1846-47]" in a <note>). Shown
        # verbatim, but labelled as the source's words rather than ours.
        rows.append(("Note i kilden", element("span", text(view["note"]), class_="source-note")))
    if section:
        rows.append(
            (
                "Brevveksling",
                element(
                    "a",
                    text(section["heading"]),
                    href="%s#%s" % (LETTER_TO_ROOT, section["id"]),
                ),
            )
        )
    # Which of the edition's volumes printed this letter -- the reader's way
    # back into the index at the right place.
    volume = view["volume"]
    rows.append(
        (
            "Bind",
            element(
                "a",
                "%s — %s" % (text(volume["shortTitle"]), text(volume["title"])),
                href="%s#%s" % (LETTER_TO_ROOT, volume["anchor"]),
            ),
        )
    )
    return _definition_list(rows, class_name="letter-meta")


def _sequence_navigation(previous, following):
    """Previous and next in the edition's order, across volume boundaries.

    Letter 42 closes b1 and letter 43 opens b43; the edition numbers them one
    after the other, so the reader walks straight through. The three letters
    the edition prints without a number are named rather than numbered.
    """
    links = ""
    if previous:
        links += element(
            "a",
            "← Forrige brev%s" % _in_brackets(previous),
            href=_letter_href(previous),
            rel="prev",
            class_="nav-previous",
        )
    if following:
        links += element(
            "a",
            "Næste brev%s →" % _in_brackets(following),
            href=_letter_href(following),
            rel="next",
            class_="nav-next",
        )
    if not links:
        return ""
    return element("nav", links, class_="letter-nav", aria_label="Breve i rækkefølge")


def _same_correspondence(view, section):
    """All letters of this correspondence, in the order the edition prints them.

    A correspondence never crosses a volume: the edition groups letters by
    who they were exchanged with, and that is what a volume is made of. So
    this list stays inside one volume while prev/next runs through them all.

    The current letter is included in its place so the reader can see
    where they stand in the exchange — as marked text, never as a link
    to itself.
    """
    if not section or len(section["letters"]) < 2:
        return ""
    items = ""
    for other in section["letters"]:
        date = element("span", " · " + text(other["date_text"]), class_="muted")
        if other["slug"] == view["slug"]:
            items += element(
                "li",
                text(other["title"])
                + date
                + element("span", " ← dette brev", class_="current-marker"),
                class_="current",
                aria_current="page",
            )
        else:
            items += element(
                "li",
                element("a", text(other["title"]), href=_letter_href(other)) + date,
            )
    return element(
        "section",
        element("h2", "Samme brevveksling")
        + element("p", text(section["heading"]), class_="group-note")
        + element("ul", items, class_="sibling-list"),
        class_="same-correspondence",
    )


def _letter_href(view):
    """Letter to letter: both live in ``brev/``, so one step up is enough."""
    return "../%s/" % view["slug"]


def _in_brackets(view):
    """" (42)" for a numbered letter, nothing for one the edition left blank."""
    return " (%s)" % text(view["number"]) if view["numbered"] else ""


# ---------------------------------------------------------------------------
# Shared bits
# ---------------------------------------------------------------------------


def _definition_list(rows, class_name):
    body = "".join(
        element("div", element("dt", label) + element("dd", value)) for label, value in rows
    )
    return element("dl", body, class_=class_name)


def _name(display, raw):
    """A person's name, with the edition's own index form kept alongside."""
    return element("span", text(display), data_name=raw)


def _date(view):
    if view["date_machine"]:
        rendered = element(
            "time", text(view["date_text"]), datetime=view["date_machine"]
        )
    else:
        rendered = element("span", text(view["date_text"]))
    if view["date_source"]:
        rendered += element(
            "span", " " + text(view["date_source"]), class_="date-provenance"
        )
    return rendered


def _letter_count(count):
    return "%d brev" % count if count == 1 else "%d breve" % count


def _volume_count(count):
    return "%d bind" % count


def _document(title, main, root, description):
    """The shell every page shares."""
    head = (
        element("meta", charset="utf-8")
        + element("meta", name="viewport", content="width=device-width, initial-scale=1")
        + element("meta", name="description", content=description)
        + element("title", "%s · %s" % (text(title), SITE_TITLE))
        + element("link", rel="stylesheet", href="%sassets/site.css" % root)
    )
    header = element(
        "header",
        element("p", element("a", SITE_TITLE, href=root or "./"), class_="site-title")
        + element("p", SITE_TAGLINE, class_="site-tagline"),
        class_="site-header",
    )
    footer = element(
        "footer",
        element(
            "p",
            "Teksten stammer fra den TEI-kodede udgave af "
            "<i>Søren Kierkegaards Skrifter</i>, der er offentligt tilgængelig "
            "under "
            + element(
                "a",
                "CC0 1.0",
                href="https://creativecommons.org/publicdomain/zero/1.0/deed.da",
                rel="license",
            )
            + ". Denne visning er en uafhængig demonstration — ikke en udgivelse "
            "fra udgiverne bag SKS — og er bygget med hjælp fra Claude (AI).",
        ),
        class_="site-footer",
    )
    skip = element("a", "Spring til indhold", href="#indhold", class_="skip-link")
    body = skip + header + element("main", main, id="indhold") + footer
    return (
        "<!doctype html>\n"
        + element("html", element("head", head) + element("body", body), lang="da")
        + "\n"
    )
