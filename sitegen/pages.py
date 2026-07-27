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


def index_page(volume, sections):
    """The front page: every letter, grouped by correspondence."""
    count = sum(len(section["letters"]) for section in sections)
    intro = element(
        "p",
        "Søren Kierkegaards breve, læst direkte fra den TEI-kodede udgave "
        "<i>Søren Kierkegaards Skrifter</i>. Denne demonstration viser bindet "
        + element("strong", "%s — %s" % (text(volume["shortTitle"]), text(volume["title"])))
        + ": %s, ordnet efter brevveksling." % _letter_count(count),
        class_="lead",
    )
    body = element("h1", "Breve") + intro
    body += "".join(_section(section) for section in sections)
    return _document(
        title="Breve",
        main=body,
        root=INDEX_TO_ROOT,
        description="Kierkegaards breve fra %s, vist fra offentlige TEI-filer."
        % volume["shortTitle"],
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
    article += element("div", view["body"], class_="transcription", lang="da")
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


def _section(section):
    heading = element("h2", text(section["heading"]))
    notes = "".join(
        element("p", text(note), class_="group-note")
        for note in section["notes"]
        if note != section["heading"]
    )
    count = element("p", _letter_count(len(section["letters"])), class_="group-count")
    entries = "".join(_entry(view) for view in section["letters"])
    return element(
        "section",
        heading + notes + count + element("ol", entries, class_="letter-list"),
        class_="correspondence",
        id=section["id"],
    )


def _entry(view):
    """One line in the index: a linked heading and the bare facts."""
    heading = element(
        "h3", element("a", text(view["title"]), href="brev/%s/" % view["id"])
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
    return _definition_list(rows, class_name="letter-meta")


def _sequence_navigation(previous, following):
    links = ""
    if previous:
        links += element(
            "a",
            "← Forrige brev (%s)" % text(previous["id"]),
            href=_letter_href(previous),
            rel="prev",
            class_="nav-previous",
        )
    if following:
        links += element(
            "a",
            "Næste brev (%s) →" % text(following["id"]),
            href=_letter_href(following),
            rel="next",
            class_="nav-next",
        )
    if not links:
        return ""
    return element("nav", links, class_="letter-nav", aria_label="Breve i rækkefølge")


def _same_correspondence(view, section):
    """All letters of this correspondence, in letter-number order.

    The current letter is included in its place so the reader can see
    where they stand in the exchange — as marked text, never as a link
    to itself.
    """
    if not section or len(section["letters"]) < 2:
        return ""
    items = ""
    for other in section["letters"]:
        date = element("span", " · " + text(other["date_text"]), class_="muted")
        if other["id"] == view["id"]:
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
    return "../%s/" % view["id"]


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
