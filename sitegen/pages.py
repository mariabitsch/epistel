"""Whole HTML documents, as plain Python string functions.

No template engine: the site has five page types, and a function that returns
a string is easier to read -- and to throw away -- than a dependency. Every
value that comes from the data passes through ``sitegen.html`` on its way in.

The pages take view models (built in ``sitegen.site``, ``sitegen.persons``,
``sitegen.search`` and ``sitegen.timeline``), not parser output, so this
module contains no knowledge of TEI. All links are relative, because the built
site has to work from any directory of any static host.

The one page with a script on it is the letter index, and it is written so
that the script is an addition and not a requirement: the filter and search
controls are in the markup with ``hidden`` on them, and ``static/search.js``
takes it off. A reader with no JavaScript gets the full list of every letter,
which is the page's actual content, and is never shown a control that would
do nothing.
"""

from .html import classes, element, text

SITE_TITLE = "epistel"

# What the pages are about, for the browser tab and the search result --
# every <title> except the letters' carries it, because "Personer ❖ epistel"
# says nothing to anyone outside the site (Maria's SEO ruling, 2026-08-03).
CORPUS_TITLE = "Søren Kierkegaards breve"
SITE_TAGLINE = "demonstrationsvisning"

# Where each page type sits, and what it takes to get back to the root.
INDEX_TO_ROOT = ""
LETTER_TO_ROOT = "../../"
PERSON_TO_ROOT = "../../"
PERSON_INDEX_TO_ROOT = "../"
TIMELINE_TO_ROOT = "../"
ABOUT_TO_ROOT = "../"

# The site's destinations. The timeline is only one of them when the curated
# datasets were built with it -- see ``sitegen.site.build_site``.
INDEX_NAV = "breve"
PERSONS_NAV = "personer"
TIMELINE_NAV = "tidslinje"
ABOUT_NAV = "om"

# Who wrote the summaries and the front page's welcome, said once on each page
# that carries her. She is a presenter, not a source: the Om page says so
# plainly, and names her as fiction.
PRESENTER = "Maria Notabene"

# The addresses the built site points at all come from ``data/links.json``
# (see ``pipeline.links``), threaded into every page as ``links``. A page
# asks for an entry by id where its sentence needs the anchor; without the
# entry the sentence keeps its words and loses the link. No address is
# hardcoded here, so removing one from the table removes it from the site.


def _linked(links, link_id, fallback_label, href=None):
    """The anchor a sentence asks for, or its words with no address.

    ``href`` overrides the table's address when a truer one exists -- the
    Om page prefers the repository PROVENANCE.md actually records over the
    table's copy of it (a guard test keeps the two in agreement).
    """
    entry = next(
        (e for e in (links or {}).get("links", ()) if e["id"] == link_id), None
    )
    if not entry:
        return text(fallback_label)
    return element(
        "a", text(entry["label"]), href=href or entry["href"], rel=entry["rel"]
    )


def index_page(books, facets, timeline=False, links=None, assets=None):
    """The front page: every letter, by volume and then by correspondence.

    One page for the whole corpus. The edition's own two levels of order are
    the two levels of the page -- the volume it was printed in, and the
    correspondence it belongs to -- so a reader who knows the edition can find
    a letter the way they would in print. The filter and search controls sit
    above that list and narrow it in place; they never rebuild it.
    """
    count = sum(len(book["letters"]) for book in books)
    summaries = sum(1 for book in books for view in book["letters"] if view["summary"])
    body = element("h1", "Breve") + _intro(books, count, summaries)
    body += _presentation()
    body += _finder(facets)
    body += _volume_navigation(books)
    body += "".join(_book(book) for book in books)
    return _document(
        title=CORPUS_TITLE,
        main=body,
        root=INDEX_TO_ROOT,
        description="Søren Kierkegaards %s i %s, vist fra offentlige TEI-filer."
        % (_letter_count(count), _volume_count(len(books))),
        timeline=timeline,
        here=INDEX_NAV,
        scripts=["assets/search.js"],
        links=links,
        assets=assets,
    )


def letter_page(view, previous, following, section, person_links, timeline=False, links=None, assets=None):
    """One letter: what it is, what it says, and what it belongs with."""
    header = element(
        "p",
        element("a", "← Alle breve", href=LETTER_TO_ROOT),
        class_="crumb",
    )
    header += element("h1", text(view["title"]))
    header += _metadata(view, section, person_links, links=links)

    article = element("header", header)
    transcription = _transcription(view)
    article += transcription + _mark_legend(transcription)
    article += _sequence_navigation(previous, following)
    article += _same_correspondence(view, section)

    return _document(
        # The letter's own names go in the title; the description holds the
        # rest -- date first, then the resumé when this build wrote one.
        title="%s: %s til %s"
        % (view["title"], view["sender"], view["recipient"]),
        main=element("article", article, class_="letter"),
        root=LETTER_TO_ROOT,
        description="%s, %s til %s, %s.%s"
        % (
            view["title"],
            view["sender"],
            view["recipient"],
            view["date_text"],
            " %s" % view["summary"] if view["summary"] else "",
        ),
        timeline=timeline,
        here=INDEX_NAV,
        links=links,
        assets=assets,
    )


# ---------------------------------------------------------------------------
# Index parts
# ---------------------------------------------------------------------------


def _intro(books, count, summaries):
    """What the reader is looking at -- as many volumes as were built.

    Maria's lead #3 (2026-08-03, replacing her 2026-07-29 original): the
    group count leaves the lead -- structure is the list's own job right
    below -- "bevarede" carries the grounded hint of loss, and the
    pseudonym is introduced through the house's own tradition rather than
    the word itself; the disclosure proper is one click away on /om/.
    Still written from the list, not from a sentence about one volume, so
    a build of b1 alone and a build of the whole corpus both describe
    themselves truthfully -- "af 336 bevarede breve", never "de 336": the
    definite article would claim completeness a partial build does not
    have. The presenter and her resumé enter only when there are some; a
    build without the curated layer must not promise them, and without
    that introduction the handover sentence would have no one to hand
    over to.
    """
    lead = (
        "Dette er en søgbar visning af %s fra "
        % _preserved_letter_count(count)
        + element("i", "Søren Kierkegaards Skrifter")
        + ", læst direkte fra den videnskabelige udgaves egne filer og med "
        "dens dateringer, forbehold og huller bevaret."
    )
    if summaries:
        lead += (
            " Men det er mere end det: i husets egen pseudonyme tradition "
            "står %s i døren med et kort resumé til hvert brev – ingen "
            "fortolkning, blot nok til at man ved, hvilken dør man åbner. "
            "Hun har skrevet et forord, naturligvis." % text(PRESENTER)
        )
    return element("p", lead, class_="lead")


def _presentation():
    """The front page's foreword, in the presenter's own voice.

    The site's one editorial moment. It comes *after* the factual lead on
    purpose: the demonstration says what it is before an invented person says
    anything at all, so a reader who skips the foreword has still been told
    the truth, and one who reads it meets a hostess rather than an authority.

    Rewritten 2026-07-29 with Maria: a real foreword under its own heading,
    hinting the arc from child to near-death instead of retelling anecdotes.
    Every concrete thing in it is in a letter -- the apologising schoolboy
    in letter 1, the engagement and the authorship in letter 22, the grave
    plot with room for one more name in letter 39, the father's colic in
    letter 23, the aunt in Jutland in letter 29, the cousin who would like
    a visit in letter 40. Nothing here is invented but her, and her
    signature links to the Om page section that says so.

    The foreword no longer names the summaries or the timeline (the lead
    carries the first, the navigation the second), so it is true in every
    build, with or without the curated datasets -- no parameters needed.
    """
    body = element("h2", "Forord")
    body += element("p", "Et forord skal holde døren, ikke holde tale. Så kun dette:")
    body += element(
        "p",
        "Den første, du møder, er en skoledreng, der undskylder, at han "
        "aldrig skriver. Siden er han forlovet, siden er han forfatter, og i "
        "et udateret brev gør han familiens gravsted i stand på skrift og "
        "lader der blive plads på tavlen til ét navn mere. Rundt om ham "
        "skriver de andre: en far om sin kolik, en faster i Jylland om sin "
        "sorg, en kusine, der bare gerne vil have besøg. Hovedpersoner i "
        "deres egne breve, i godt selskab.",
    )
    body += element(
        "p",
        "Bladr, søg, følg et år eller et menneske. God fornøjelse derinde. "
        "Og kommer du til at holde af dem, så er vi to.",
    )
    body += element(
        "p",
        element("a", text(PRESENTER), href="%som/#notabene" % INDEX_TO_ROOT),
        class_="presentation-sign",
    )
    return element(
        "section", body, class_="presentation", aria_label="Forord", lang="da"
    )


def _finder(facets):
    """The filter and search controls: markup first, behaviour later.

    Everything here is ordinary HTML -- three selects, a search field and a
    reset button -- rendered with ``hidden`` on the form. ``search.js`` takes
    the attribute off, which is the whole of the progressive enhancement: a
    reader without JavaScript never sees a control, and the list below is
    complete without one. The options are built at build time from the corpus,
    so the script has no lists of its own and nothing to fetch before the
    filters work.
    """
    fields = _search_field()
    fields += _facet_field("afsender", "Afsender", facets["senders"])
    fields += _facet_field("modtager", "Modtager", facets["recipients"])
    fields += _facet_field("aar", "År", facets["years"], note=_year_note(facets["years"]))
    form = element("div", fields, class_="finder-fields")
    form += element(
        "div",
        element(
            "p",
            element("span", "", class_="finder-count")
            + element("span", "", class_="finder-terms"),
            class_="finder-status",
            role="status",
            aria_live="polite",
        )
        + element(
            "button",
            "Ryd",
            type="reset",
            class_="finder-reset",
        ),
        class_="finder-foot",
    )
    return element(
        "form",
        form,
        class_="finder",
        id="finder",
        role="search",
        aria_label="Filtrér og søg i brevene",
        hidden=True,
    ) + element(
        "p",
        "Ingen breve svarer til søgningen.",
        class_="finder-empty",
        id="finder-empty",
        hidden=True,
    )


def _search_field():
    return element(
        "div",
        element("label", "Søg i brevtekst og resumé", for_="finder-query")
        + element(
            "input",
            type="search",
            id="finder-query",
            name="q",
            autocomplete="off",
            spellcheck="false",
            placeholder="fx snustobaksdåse",
        ),
        class_="finder-field finder-field--query",
    )


def _facet_field(name, label, values, note=None):
    """One ``<select>``, with every value the corpus actually holds.

    The counts are in the option text because a reader choosing a filter is
    owed the size of what they are choosing, and because a facet that would
    return nothing is never offered in the first place.
    """
    options = element("option", "Alle", value="")
    for entry in values:
        options += element(
            "option",
            "%s (%d)" % (text(entry["label"]), entry["count"]),
            value=entry["value"],
        )
    note_id = "finder-%s-note" % name if note else None
    field = element(
        "div",
        element("label", text(label), for_="finder-%s" % name)
        + element(
            "select",
            options,
            id="finder-%s" % name,
            name=name,
            aria_describedby=note_id,
        ),
        class_="finder-field",
    )
    if not note:
        return field
    # The note sits outside the field so it can run the full width of the
    # panel rather than down a column, and is tied back to the control it
    # explains by ``aria-describedby``.
    return field + element("p", text(note), class_="finder-note", id=note_id)


def _year_note(years):
    """Preserve uncertainty: say how the imprecise dates were filed.

    A year filter has to put every letter in exactly one year, and the edition
    does not always give one -- "1846-47", "1837", a postmark it will not
    vouch for. They go under the earliest year they could belong to, which is
    a decision, so the decision is written down next to the control rather
    than left for the reader to discover by being surprised.
    """
    if not any(entry.get("approximate") for entry in years):
        return None
    return (
        "Breve, som SKS kun daterer til et år eller til en periode, står "
        "under det tidligste år, de kan tilhøre. Datoen ved hvert brev siger, "
        "hvad SKS faktisk ved."
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
        aria_label="Grupper",
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


# The date/pair separator in a row's meta line. A no-break space glues it
# to the word before it and an ordinary space follows, so a narrow-width
# wrap breaks *after* the dot -- before the date or "fra" -- and never
# leaves "·" to open a line on its own (Maria's call, Småting backlog).
ROW_SEPARATOR = " · "


def _entry(view):
    """One row in the index: the same relaxed row every list on the site uses.

    Maria's call (2026-07-28): the index's technical FRA/TIL/DATERET grid
    gave way to the person pages' row -- title · date, the pair line, the
    resumé, all inside one <a>. The date is the honest short form; the
    bracketed provenance notes and the person links live on the letter
    page, where the reader lands next.

    The filter values travel on the <li> as ``data-`` attributes so that
    narrowing the list is a matter of hiding rows that are already on the
    page. Nothing is ever built from a string of data at runtime, and the
    layout inside the link never touches them.
    """
    filters = view["filters"]
    return element(
        "li",
        element(
            "a",
            element(
                "span",
                element("span", text(view["title"]), class_="sibling-title")
                + element(
                    "span", ROW_SEPARATOR + text(view["date_text"]), class_="muted"
                )
                + element(
                    "span",
                    ROW_SEPARATOR + "fra %s til %s"
                    % (text(view["sender"]), text(view["recipient"])),
                    class_="person-letter-pair",
                ),
                class_="sibling-head",
            )
            + _summary(view),
            href="brev/%s/" % view["slug"],
            class_="sibling-link",
        ),
        class_="letter-entry",
        data_slug=view["slug"],
        data_sender=filters["sender"],
        data_recipient=filters["recipient"],
        data_year=filters["year"],
    )


# The text-critical marks a transcription can carry that no reader can be
# expected to decode unaided: (needle in the rendered transcription,
# class the legend sample wears, what the mark means). The needle for the
# Latin hand is a rendition token and matches any element carrying it.
TRANSCRIPTION_MARKS = (
    ('class="tei-supplied', "tei-supplied", "udfyldt af udgiverne, hvor kilden mangler"),
    ('class="tei-unclear', "tei-unclear", "usikker læsning i kilden"),
    ('class="tei-corr', "tei-corr", "rettet af udgiverne"),
    ('class="tei-add', "tei-add", "tilføjet i kilden, typisk over linjen"),
    (" r-lat", "tei-hi r-lat", "skrevet med latinsk hånd, hvor brevet ellers er gotisk"),
)


def _mark_legend(transcription):
    """A quiet Tegnforklaring for the marks this letter actually carries.

    Maria's call (2026-07-28): the text-critical marks stay -- they are the
    edition's own honesty -- and the reader is told what they mean. Each
    legend line *wears* its mark, so the sample is the explanation and
    meaning is never carried by decoration alone. Collapsed by default;
    ``<details>`` needs no script. A letter with no marks gets no legend.
    """
    present = [
        (sample, label)
        for needle, sample, label in TRANSCRIPTION_MARKS
        if needle in transcription
    ]
    if not present:
        return ""
    items = "".join(
        element("li", element("span", label, class_=sample))
        for sample, label in present
    )
    return element(
        "details",
        element("summary", "Tegnforklaring")
        + element("ul", items, class_="mark-legend-list"),
        class_="mark-legend",
    )


def _summary(view):
    """The presenter's two sentences about the letter, in her own register.

    Under every letter list -- the index, a letter's "Samme brevveksling",
    a person's three lists (Maria's decision, 2026-07-28; it was the index
    alone at first): wherever a reader is choosing what to read, a
    presenter is welcome, and she is marked as one. Every row of a list
    carries its resumé -- the current letter's included (Maria's second
    revision, same day) -- but she never sits *above* a transcription:
    there the letter speaks for itself. Even the three letters the edition
    prints as bare cross-references carry one (Maria, 2026-08-02): the
    letter exists, printed under another letter's number, and the resumé
    points at the right door -- grounded in Brev 193/194, where SKS prints
    the text (see summaries.json's _meta.stubGrounding).
    """
    if not view["summary"]:
        return ""
    return element("p", text(view["summary"]), class_="letter-summary", lang="da")


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


def _edition_link(view, links):
    """One quiet deep link to the letter's own place at the publisher's.

    The address comes from the link table's template entry (Maria's
    crediting decision, 2026-08-03): group root ``sks-{dir}-txt-root``,
    anchor ``#n{number}`` -- the scheme verified against tekster.kb.dk
    2026-08-01, sub-numbers verbatim. The three unnumbered stubs have no
    anchor at the publisher's and link to the group root instead. Without
    the table the row is simply absent: the transcription itself never
    depended on it.
    """
    entry = next(
        (e for e in (links or {}).get("links", ()) if e["id"] == "sks-letter"),
        None,
    )
    if not entry or not entry.get("template"):
        return None
    href = entry["template"].format(
        volume=view["volume"]["id"], number=view["number"]
    )
    if view["numbered"]:
        label = "Brevet hos %s" % entry["label"]
    else:
        href = href.split("#", 1)[0]
        label = "Gruppen hos %s" % entry["label"]
    return element("a", text(label), href=href, rel=entry["rel"])


def _metadata(view, section, person_links=None, links=None):
    """The panel above the transcription -- correspDesc, never the heading.

    The edition's own letter headings are a display string that is sometimes
    damaged in the source (letter 39 is missing everything but its recipient),
    so this panel is built from the structured fields instead.

    Sender and recipient become links when the curated alias table joined them
    to a person the letters name; when it could not, the name stands as text.
    A letter written to "familien" or from "ukendt" is not a person, and the
    panel says exactly as much as the edition does.
    """
    person_links = person_links or {}
    rows = [
        ("Fra", _name(view["sender"], view["sender_raw"], person_links.get("sender"))),
        (
            "Til",
            _name(view["recipient"], view["recipient_raw"], person_links.get("recipient")),
        ),
        ("Datering", _date(view)),
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
    # Which of the edition's correspondence groups the letter belongs to --
    # the reader's way back into the index at the right place. "Gruppe" is
    # the edition's own word (Maria, 2026-08-03); "Bind" was wrong, the
    # letters are one volume of SKS (28).
    volume = view["volume"]
    rows.append(
        (
            "Gruppe",
            element(
                "a",
                "%s – %s" % (text(volume["shortTitle"]), text(volume["title"])),
                href="%s#%s" % (LETTER_TO_ROOT, volume["anchor"]),
            ),
        )
    )
    edition = _edition_link(view, links)
    if edition:
        rows.append(("SKS", edition))
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
    where they stand in the exchange – as marked text, never as a link
    to itself.
    """
    if not section or len(section["letters"]) < 2:
        return ""
    items = ""
    for other in section["letters"]:
        date = element(
            "span", ROW_SEPARATOR + text(other["date_text"]), class_="muted"
        )
        if other["slug"] == view["slug"]:
            # The reader's own position: marked on the date's line, never a
            # link to itself -- and its resumé stays (Maria, 2026-07-28):
            # the row should read like every other row in the exchange.
            head = element(
                "span",
                element("span", text(other["title"]), class_="sibling-title")
                + date
                + element("span", " ← dette brev", class_="current-marker"),
                class_="sibling-head",
            )
            items += element(
                "li",
                head + _summary(other),
                class_="current",
                aria_current="page",
            )
        else:
            # One block, one address: title, date and resumé all travel
            # inside the <a>, so the whole entry is clickable (Maria,
            # 2026-07-28) -- the reader can aim at the sentence that
            # tempted them, not just the number.
            head = element(
                "span",
                element("span", text(other["title"]), class_="sibling-title") + date,
                class_="sibling-head",
            )
            items += element(
                "li",
                element(
                    "a",
                    head + _summary(other),
                    href=_letter_href(other),
                    class_="sibling-link",
                ),
            )
    return element(
        "section",
        element(
            "div",
            element("h2", "Samme brevveksling")
            + element("p", text(section["heading"]), class_="group-note"),
            class_="list-head",
        )
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
# People
# ---------------------------------------------------------------------------


def person_index_page(groups, register, timeline=False, links=None, assets=None):
    """Everyone the letters name, hung letter band by letter band.

    The register is the edition's own: every name it marked up in a letter's
    text, exactly as it keyed it. That includes the people Kierkegaard wrote
    to, the people he wrote about, and the figures he argued with on paper --
    Sokrates, Don Giovanni's Elvira, Robinson Crusoe. Sorting them into "real"
    and "not" would be our judgement laid over the edition's, so the register
    keeps them all and says so.
    """
    with_bio = sum(1 for person in register if person["bio"])
    body = element("h1", "Personer")
    body += _person_index_intro(len(register), with_bio)
    body += _letter_navigation(groups)
    body += "".join(_person_group(group) for group in groups)
    return _document(
        title="Personer – %s" % CORPUS_TITLE,
        main=body,
        root=PERSON_INDEX_TO_ROOT,
        description="%s, som Søren Kierkegaards breve nævner ved navn."
        % _person_count(len(register)),
        timeline=timeline,
        here=PERSONS_NAV,
        links=links,
        assets=assets,
    )


def _person_index_intro(count, with_bio):
    lead = (
        "Alle, som brevene nævner ved navn – "
        + element("strong", _person_count(count))
        + ", som SKS selv har mærket op i brevteksterne. Registret skelner "
        "ikke mellem virkelige og litterære: står navnet i et brev, står "
        "personen her."
    )
    if with_bio:
        lead += (
            " %d af dem har en kort biografi, skrevet ud af SKS' egen "
            "kommentar." % with_bio
        )
    return element("p", lead, class_="lead")


def _letter_navigation(groups):
    """The alphabet as a jump list -- one anchor per band that has people."""
    items = "".join(
        element(
            "li",
            element("a", text(group["letter"]), href="#%s" % group["anchor"]),
        )
        for group in groups
    )
    return element(
        "nav",
        element("ol", items, class_="alphabet-list"),
        class_="alphabet-nav",
        aria_label="Bogstaver",
    )


def _person_group(group):
    entries = "".join(_person_entry(person) for person in group["people"])
    return element(
        "section",
        element("div", element("h2", text(group["letter"])), class_="alphabet-head")
        + element("ul", entries, class_="person-list"),
        class_="person-band",
        id=group["anchor"],
    )


def _person_entry(person):
    """One name in the register, with what the site can say about them."""
    marks = []
    letters = _person_letter_count(person)
    if letters:
        marks.append(_letter_count(letters))
    marks.append("biografi" if person["bio"] else "ingen biografi")
    return element(
        "li",
        element(
            "a", text(person["name"]), href="../person/%s/" % person["slug"]
        )
        + element(
            "span",
            " · ".join(text(mark) for mark in marks),
            class_=classes("person-marks", None if person["bio"] else "person-marks--bare"),
        ),
        class_="person-entry",
    )


def person_page(person, timeline=False, links=None, assets=None):
    """One person: who the commentary says they were, and their letters."""
    header = element(
        "p",
        element("a", "← Alle personer", href="%spersoner/" % PERSON_TO_ROOT),
        class_="crumb",
    )
    header += element("h1", text(person["name"]))
    header += _person_identity(person)

    article = element("header", header)
    article += _biography(person)
    article += _person_letters(
        person["sent"],
        "Breve fra %s" % person["name"],
        "Breve, hvor SKS angiver %s som afsender." % person["name"],
    )
    article += _person_letters(
        person["received"],
        "Breve til %s" % person["name"],
        "Breve, hvor SKS angiver %s som modtager." % person["name"],
    )
    article += _person_letters(
        person["mentioned"],
        "Breve, hvor %s er nævnt" % person["name"],
        "Breve, hvor navnet står i selve brevteksten.",
    )
    return _document(
        title="%s – %s" % (person["name"], CORPUS_TITLE),
        main=element("article", article, class_="person"),
        root=PERSON_TO_ROOT,
        description="%s i Søren Kierkegaards breve: %s."
        % (person["name"], _person_summary(person)),
        timeline=timeline,
        here=PERSONS_NAV,
        links=links,
        assets=assets,
    )


def _person_identity(person):
    """The edition's own index form, and the other names it files them under."""
    rows = [("Opslagsform", element("span", text(person["key"]), class_="person-key"))]
    if person["same_as"]:
        # Married and maiden names, nicknames: the commentary records them as
        # the same person, and a reader looking for "Jette" should see why
        # this page is the answer.
        rows.append(
            (
                "Også kaldt",
                element(
                    "span",
                    " · ".join(text(name) for name in person["same_as"]),
                    class_="person-aka",
                ),
            )
        )
    return _definition_list(rows, class_name="person-meta")


def _biography(person):
    """The commentary's note about a person, or an honest line saying there is none.

    The bio is not the edition speaking: it is drawn out of the edition's
    commentary and rewritten, so the source note is named beneath it. Where
    the commentary has nothing, the page says that too. A person with no
    biography is not an incomplete page; it is a fact about what the edition
    annotates -- and there are two kinds of it. Some people the commentary
    never treats as a subject at all; thirteen it does mention, without
    saying anything biographical, and the dataset records each of them by
    name. The page tells the two apart rather than flattening them.
    """
    if person["bio"]:
        block = element("p", text(person["bio"]), class_="person-bio")
        if person["sources"]:
            block += element(
                "p",
                "Efter kommentaren i SKS: %s"
                % " · ".join(text(source) for source in person["sources"]),
                class_="person-source",
            )
        return element("section", block, class_="person-biography")
    if person["no_bio_reason"]:
        line = (
            "SKS' kommentar nævner personen, men uden biografiske "
            "oplysninger."
        )
    else:
        line = "SKS' kommentar giver ingen biografisk note om personen."
    return element(
        "section",
        element("p", line, class_="person-bio person-bio--none"),
        class_="person-biography",
    )


def _person_letters(views, heading, note):
    """One of a person's three lists of letters, in the edition's own order."""
    if not views:
        return ""
    # The same one-block-one-address rule as "Samme brevveksling": the
    # whole entry, resumé included, is the link (Maria, 2026-07-28).
    items = "".join(
        element(
            "li",
            element(
                "a",
                element(
                    "span",
                    element("span", text(view["title"]), class_="sibling-title")
                    + element(
                        "span",
                        ROW_SEPARATOR + text(view["date_text"]),
                        class_="muted",
                    )
                    + element(
                        "span",
                        ROW_SEPARATOR + "fra %s til %s"
                        % (text(view["sender"]), text(view["recipient"])),
                        class_="person-letter-pair",
                    ),
                    class_="sibling-head",
                )
                + _summary(view),
                href="%sbrev/%s/" % (PERSON_TO_ROOT, view["slug"]),
                class_="sibling-link",
            ),
        )
        for view in views
    )
    # The same card as "Samme brevveksling" (Maria, 2026-07-28): one head
    # band over one list, so the two section types are one design.
    return element(
        "section",
        element(
            "div",
            element("h2", text(heading))
            + element("p", text(note), class_="group-note")
            + element("p", _letter_count(len(views)), class_="group-count"),
            class_="list-head",
        )
        + element("ul", items, class_="sibling-list"),
        class_="person-letters",
    )


def _person_letter_count(person):
    slugs = {
        view["slug"]
        for group in ("sent", "received", "mentioned")
        for view in person[group]
    }
    return len(slugs)


def _person_summary(person):
    parts = []
    for group, label in (("sent", "sendt"), ("received", "modtaget")):
        if person[group]:
            parts.append("%s %s" % (_letter_count(len(person[group])), label))
    if person["mentioned"]:
        parts.append("nævnt i %s" % _letter_count(len(person["mentioned"])))
    return ", ".join(parts) or "ingen breve"


def _person_count(count):
    return "1 person" if count == 1 else "%d personer" % count


# ---------------------------------------------------------------------------
# Timeline
# ---------------------------------------------------------------------------


def timeline_page(model, links=None, assets=None):
    """The letters against the books and the addresses, on one linear scale.

    The page is a stack of years, each of them the same height, holding three
    lanes beside the scale -- where he lived, the letters he sent, and the
    letters the edition can only date to a year -- with what he published
    under the year strip, at every width (option A, Maria 2026-07-29).
    ``sitegen.timeline`` has already decided every position; this function
    only writes them down.

    Nothing here moves after the page is served -- the marks are elements with
    two custom properties, and the stylesheet does the arithmetic. There is no
    script on the page, so there is nothing to fail. The rotate prompt is in
    the markup at every width too; the stylesheet decides when the strip is
    too wide for the screen and swaps them.
    """
    counts = model["counts"]
    body = element("h1", "Tidslinje")
    body += _timeline_intro(model)
    body += _timeline_legend()
    body += element(
        "p",
        "Tidslinjen er for bred til skærmen på højkant. Vend telefonen, så "
        "folder den sig ud.",
        class_="tl-rotate",
    )
    body += _timeline_rail(model, links=links)
    body += _undated(model["undated"])
    body += _home_register(model["homes"])
    body += _dataset_note(model["meta"])
    return _document(
        title="Tidslinje – %s" % CORPUS_TITLE,
        main=body,
        root=TIMELINE_TO_ROOT,
        description="Søren Kierkegaards %s, %d skrifter og %d bopæle på én "
        "lineær tidsskala fra %d til %d."
        % (
            _letter_count(counts["letters"]),
            counts["publications"],
            counts["residences"],
            model["first_year"],
            model["last_year"],
        ),
        body_class="page-timeline",
        timeline=True,
        here=TIMELINE_NAV,
        links=links,
        assets=assets,
    )


def _timeline_intro(model):
    counts = model["counts"]
    # Not "his life from 1813": the scale begins at the first preserved
    # letter (Maria, 2026-07-29 -- no empty childhood years), and the words
    # above the rail say exactly what the reader gets. The years stay
    # derived from the model, so the sentence can never drift from the page.
    lead = element(
        "p",
        "Søren Kierkegaards liv fra det første bevarede brev i %d til hans "
        "død i %d, på én skala: brevene fra den TEI-kodede udgave, sat op "
        "mod de skrifter, han fik udgivet, og de adresser, han boede på. "
        "Hvert år fylder det samme, så de tavse år fylder lige så meget som "
        "de travle."
        % (model["first_year"], model["last_year"]),
        class_="lead",
    )
    figures = [
        ("%d" % counts["placed"], "breve placeret i et år"),
        ("%d" % counts["undated"], "breve uden datering"),
        ("%d" % counts["publications"], "skrifter udgivet i hans levetid"),
        ("%d" % counts["residences"], "bopæle"),
    ]
    lead += element(
        "ul",
        "".join(
            element("li", element("b", text(number)) + " " + text(label))
            for number, label in figures
        ),
        class_="tl-figures",
    )
    return lead


def _timeline_legend():
    """What the marks mean, said once, in Danish.

    Every distinction on the page is drawn twice -- as a shape and as words --
    so none of them depends on telling two colours apart.
    """
    # One punctuation rule, here and in the letter page's Tegnforklaring
    # (Maria, korrektur 2026-07-28): a fragment gets no full stop, a whole
    # sentence gets one. Where a line is two fragments they are joined with a
    # dash rather than a stop, so a full stop on this page always means a
    # sentence has ended.
    rows = [
        ("Streg", "brev, som SKS daterer til dagen"),
        (
            # Not "Åben kasse": there is no filled box to tell it apart from,
            # so the adjective carried nothing (Maria, korrektur item 29). The
            # ruder keep theirs -- there åben/udfyldt *is* the distinction.
            "Kasse",
            "brev, som SKS kun daterer til måneden. Kassen dækker hele "
            "måneden, fordi det er alt, kilden siger.",
        ),
        (
            # The lane is called "Kun år" at the head of the rail, so the
            # legend calls it that too (Maria, korrektur 2026-07-28). The
            # chips on the page are drawn with "ca." on them, so the mark
            # itself opens the explanation -- a reader must be able to look
            # up what is actually printed beside the year.
            "Kun år",
            "»ca.« – brev, som SKS kun daterer til året eller til en "
            "periode over flere år. Breve, som kun har et årstal, står for "
            "sig selv ud for året.",
        ),
        (
            "Udfyldt rude",
            "skrift udgivet under Kierkegaards eget navn – sat yderst til "
            "venstre, ud for årstallet",
        ),
        (
            "Åben rude",
            "skrift udgivet under pseudonym – sat lidt ind, med pseudonymets "
            "navn under titlen",
        ),
        (
            "Bånd",
            "bopæl. Stiplet kant betyder, at kilderne er uenige om perioden, "
            "eller at de kun kender året.",
        ),
    ]
    # No stretch exception any more: the works sit under their year at every
    # width, so the scale is perfectly uniform (option A, Maria 2026-07-29).
    note = element(
        "p",
        "Skalaen er lineær: hvert år er lige højt. Årets udgivelser står "
        "under årstallet, og breve uden datering står nederst på siden.",
        class_="tl-legend-note",
    )
    return element(
        "section",
        element("h2", "Tegnforklaring", class_="tl-legend-heading")
        + element(
            "dl",
            "".join(
                element("div", element("dt", text(mark)) + element("dd", text(meaning)))
                for mark, meaning in rows
            ),
            class_="tl-legend",
        )
        + note,
        class_="tl-legend-box",
        aria_label="Tegnforklaring",
    )


def _timeline_rail(model, links=None):
    # No "Udgivelser" label: the works lane sits under the year, not beside
    # it, so it has no column of its own in the head. The homes span stays as
    # a hidden placeholder -- the head is auto-placed, and a missing span in
    # the middle would slide every label after it into the wrong lane.
    head = element(
        "div",
        "".join(
            element("span", text(label), class_="tl-head-%s" % lane)
            for lane, label in (
                ("axis", "År"),
                ("homes", "Bopæl"),
                ("letters", "Breve"),
                ("vague", "Kun år"),
            )
        ),
        class_="tl-head",
        aria_hidden="true",
    )
    years = "".join(_timeline_year(year, links=links) for year in model["years"])
    return element(
        "div",
        head + years,
        class_="tl",
        style=_style(slots=model["slots"]),
    )


def _timeline_year(year, links=None):
    inner = element("h2", text("%d" % year["year"]), class_="tl-axis")
    inner += _homes(year["homes"])
    inner += _letters(year["letters"], year["year"])
    inner += _vague(year["vague"], year["year"])
    inner += _works(year["works"], links=links)
    return element(
        "section",
        inner,
        # Every tenth year gets a stronger rule: a scale a reader can count by
        # without reading every label.
        class_=classes("tl-year", "tl-year--decade" if not year["year"] % 10 else None),
        id="aar-%d" % year["year"],
    )


def _homes(segments):
    """One year's slice of the bands: a hairline of sea-green, no words.

    The addresses live in the register at the foot of the page, at every
    width (option A, Maria 2026-07-29) -- the bands are the part that is on
    the scale, so they are the part that stays beside it.
    """
    bands = ""
    for segment in segments:
        band = element(
            "span",
            "",
            class_="tl-home-band",
            aria_hidden="true",
        )
        bands += element(
            "div",
            band,
            class_=classes(
                "tl-home",
                "tl-home--starts" if segment["starts"] else None,
                "tl-home--ends" if segment["ends"] else None,
                "tl-home--approx" if segment["approx"] else None,
            ),
            style=_style(
                top=segment["top"], height=segment["height"], slot=segment["slot"]
            ),
        )
    return element("div", bands, class_="tl-homes")


def _letters(marks, year):
    """The comb: one mark per letter the edition dates within its year.

    A mark is a line when the day is known and an open box the height of the
    month when it is not, so its size is the edition's certainty. Marks that
    would sit on top of each other are dealt columns to the right, which is why
    a year like 1849 is wide and a quiet year is a single line of ticks.
    """
    if not marks:
        return element("div", "", class_="tl-letters")
    items = ""
    for mark in marks:
        items += element(
            "li",
            element(
                "a",
                "",
                href="../brev/%s/" % mark["slug"],
                title=mark["label"],
                aria_label=mark["label"],
            ),
            class_="tl-letter tl-letter--%s" % mark["kind"],
            style=_style(top=mark["top"], height=mark["height"], slot=mark["slot"]),
        )
    return element(
        "ul",
        items,
        class_="tl-letters",
        aria_label="Breve dateret i %d" % year,
    )


def _vague(marks, year):
    """Letters the edition places in a year but not in a day.

    They are set apart, marked "ca." and given their letter numbers, because
    the one thing the page must not do is put them somewhere on the day scale
    where they would look as if they were known to the day.
    """
    if not marks:
        return element("div", "", class_="tl-vague")
    items = "".join(
        element(
            "li",
            element(
                "a",
                text(mark["number"]),
                href="../brev/%s/" % mark["slug"],
                title=mark["label"],
                aria_label=mark["label"],
            ),
            class_="tl-vague-item",
        )
        for mark in marks
    )
    return element(
        "div",
        element("p", "ca.", class_="tl-vague-mark", aria_hidden="true")
        + element(
            "ul",
            items,
            class_="tl-vague-list",
            aria_label="Breve, som SKS kun daterer til %d eller til en "
            "periode, der begynder i %d" % (year, year),
        ),
        class_="tl-vague",
    )


def _works(blocks, links=None):
    """The publications: one block per day something came out.

    Three books came out on 16 October 1843 and two on 17 June 1844, so a block
    can hold more than one title. Pseudonymous works are set in from the rail
    with an open marker and their pseudonym named; signed ones stand at the
    rail with a filled one. Two encodings, no colour.
    """
    if not blocks:
        return element("div", "", class_="tl-works")
    items = ""
    for block in blocks:
        entries = "".join(_work(entry, links) for entry in block["entries"])
        items += element(
            "li",
            element(
                "p",
                element("time", text(block["date_text"]), datetime=block["date"].isoformat()),
                class_="tl-work-date",
            )
            + element("ul", entries, class_="tl-work-list"),
            class_="tl-work",
        )
    return element("ol", items, class_="tl-works")


def _work(entry, links=None):
    pseudonym = entry["pseudonym"]
    inner = element("span", "", class_="tl-work-mark", aria_hidden="true")
    inner += element(
        "b", _work_title(entry, links), class_="tl-work-title"
    )
    inner += element(
        "span",
        "Pseudonym: %s" % text(pseudonym) if pseudonym else "Eget navn",
        class_="tl-work-name",
    )
    if entry["period"]:
        # The dataset's own wording, where it says more than one date can:
        # a serial in four parts, a run of nine numbers, a year of articles.
        inner += element("span", text(entry["period"]), class_="tl-work-period")
    return element(
        "li",
        inner,
        class_="tl-work-item tl-work-item--%s"
        % ("pseudonym" if pseudonym else "signed"),
    )


def _work_title(entry, links):
    """The title, linked to the SKS account of its own dating when it can be.

    Every publication's date follows the edition's tekstredegørelse, and the
    dataset carries the address per entry (Maria's crediting decision,
    2026-08-03). Only addresses under the link table's declared
    tekster.kb.dk prefix become anchors; every other source stays named in
    the dataset and unlinked on the page, so no page points anywhere the
    table has not permitted.
    """
    permit = next(
        (e for e in (links or {}).get("links", ()) if e["id"] == "sks-txr"),
        None,
    )
    if permit:
        href = next(
            (
                source.get("url")
                for source in entry.get("sources", ())
                if (source.get("url") or "").startswith(permit["href"])
            ),
            None,
        )
        if href:
            return element(
                "a", text(entry["title"]), href=href, rel=permit["rel"]
            )
    return text(entry["title"])


def _undated(letters):
    """The ten letters no year can hold. Named, since they cannot be placed."""
    items = "".join(
        element(
            "li",
            element("a", text(view["title"]), href="../brev/%s/" % view["slug"])
            + element("span", " · " + text(view["correspondents"]), class_="muted"),
        )
        for view in letters
    )
    return element(
        "section",
        element("h2", "Breve uden datering")
        + element(
            "p",
            "Udgaven daterer ikke disse %d breve. De kan ikke placeres på "
            "skalaen, og de er ikke gættet ind i et år." % len(letters),
            class_="tl-section-note",
        )
        + element("ul", items, class_="tl-undated-list"),
        class_="tl-section",
        id="udaterede",
    )


def _home_register(homes):
    """The bands in words: the address, the period, and what is uncertain."""
    rows = ""
    for home in homes:
        detail = element("span", text(home["period"]), class_="tl-home-period")
        if home["approx"]:
            detail += element("span", "usikker datering", class_="tl-approx")
        if home["modern"]:
            detail += element("span", text(home["modern"]), class_="tl-home-modern")
        if home["approx"] and home["note"]:
            # Why it is uncertain is the interesting part, and it is the one
            # thing the lane beside the rail has no room for.
            detail += element("span", text(home["note"]), class_="tl-home-note")
        rows += element(
            "div", element("dt", text(home["address"])) + element("dd", detail)
        )
    return element(
        "section",
        element("h2", "Bopæle")
        + element("dl", rows, class_="tl-home-register"),
        class_="tl-section",
        id="bopaele",
    )


def _dataset_note(meta):
    """Where the two curated datasets come from, and what they are not."""
    parts = ""
    for name, heading in (
        ("publications", "Udgivelser"),
        ("residences", "Bopæle"),
    ):
        block = meta.get(name) or {}
        inner = element("h3", text(heading))
        if block.get("datingPrinciple"):
            inner += element("p", text(block["datingPrinciple"]))
        sources = block.get("generalSources") or []
        if sources:
            inner += element(
                "ul",
                "".join(
                    element("li", text(source.get("work") or ""))
                    for source in sources
                ),
                class_="tl-source-list",
            )
        parts += element("div", inner, class_="tl-dataset")
    return element(
        "section",
        element("h2", "Om datasættene")
        + element(
            "p",
            "Udgivelser og bopæle er et redaktionelt lag: håndkurateret, "
            "kildebelagt og lagt oven på udgaven. De stammer ikke fra de "
            "TEI-filer, brevene er læst fra, og de kan bestrides og skiftes ud "
            "uden at røre ved brevteksten.",
            class_="tl-section-note",
        )
        + parts,
        class_="tl-section",
        id="datasaet",
    )


# ---------------------------------------------------------------------------
# Om
# ---------------------------------------------------------------------------


# The number of automated tests the Om page claims to have behind it. It is
# a fact about this repository, so it is written here rather than counted at
# build time -- and a test counts the suite with unittest discovery and
# compares it with the built page, so the sentence cannot go stale quietly.
AUTOMATED_TESTS = 413

# The figures the Om page states about the site it belongs to. Every one of
# them is recounted from the built pages in the test suite
# (``test_every_number_the_om_page_claims_matches_the_built_site``), because
# a page that counts itself wrong is exactly the kind of small lie this
# demonstration cannot afford.
BUILT_PAGES = 638
LETTERS = 336
PERSON_PAGES = 298
BIOGRAPHIES = 143
SUMMARIES = 336
LETTERS_ON_THE_SCALE = 326
LETTERS_WITHOUT_A_DATE = 10
PUBLICATIONS = 38
RESIDENCES = 9


def about_page(provenance=None, timeline=False, links=None, assets=None):
    """What the site is, where the text comes from, and who the hostess is.

    Rule 5 of the build brief lives here: the demonstration has to be
    recognisable as a demonstration inside a minute, without anyone feeling
    taken in. So this page states the source and its licence, the code's
    licence, where the vendored copy came from, and -- plainly -- that Maria
    Notabene is invented and that the site was built with AI assistance.

    The text is Maria's, approved 2026-08-03, and it is hardcoded here like
    every other page's prose: the build is offline and reads no manuscript.
    Every claim about the world outside the letters carries a note marker
    into the source list at the foot of the page, and every address in it
    comes from ``data/links.json`` by id, so a build without the table keeps
    the words and loses only the anchors.

    ``provenance`` is ``pipeline.provenance.load_provenance``'s dict or None.
    Without it the page still names the upstream repository -- that is the
    project's own prose -- but drops the sentence about the release the copy
    was taken from and the two records that back it: a chain the build cannot
    verify against the record beside the files would be worse than none.
    Since 2026-08-03 the commit itself is not printed here at all; it lives
    in the technical notes, and a test holds those to ``PROVENANCE.md``.
    """
    body = element("h1", "Om")
    body += _about_lead(links)
    body += _about_research()
    body += _about_originals(provenance, links=links)
    body += _about_display()
    body += _about_presenter()
    body += _about_code(links)
    body += _about_notes(provenance, links=links)
    return _document(
        title="Om – %s" % CORPUS_TITLE,
        main=element("div", body, class_="prose"),
        root=ABOUT_TO_ROOT,
        description="Hvad epistel er, hvor teksten kommer fra, hvilke licenser "
        "der gælder, og hvem Maria Notabene er.",
        timeline=timeline,
        here=ABOUT_NAV,
        links=links,
        assets=assets,
    )


def _note(number):
    """A footnote marker: the smallest thing that can carry a source.

    The markers and the list at the foot are generated from the same
    numbering, and a test checks that neither side has an entry the other
    does not -- a page whose sources cannot be reached is a page without
    sources.
    """
    return element("sup", element("a", "%d" % number, href="#note-%d" % number))


def _about_lead(links):
    """What this is, whose text it stands on, and what it is not.

    No section wrapper and no heading: the opening belongs to the h1, the
    way it did before this page grew sections.
    """
    body = element(
        "p",
        "<i>epistel</i> er en uafhængig demonstrationsvisning af Søren "
        "Kierkegaards breve. Den bygger på forskningsprojektet <i>Søren "
        "Kierkegaards Skrifter</i> (SKS), som Det Kgl. Bibliotek gør "
        "tilgængeligt to steder: som læsbar tekstsamling på "
        + _linked(links, "publishers-edition", "tekster.kb.dk/sks")
        + " og som rå datafiler i repositoriet "
        + _linked(links, "upstream-repository", "kb-dk/SKS_tei")
        + ". Datafilerne ligger under "
        + _linked(links, "cc0-deed", "CC0 1.0")
        + " – et fuldt afkald på ophavsret, og dermed netop den licens, der "
        "gør et forsøg som dette muligt uden at spørge nogen om lov. "
        "<i>epistel</i> er ikke en udgivelse fra Det Kgl. Bibliotek eller fra "
        "udgiverne bag SKS, og visningen har ingen anden autoritet end den, "
        "kilderne selv har.",
        class_="lead",
    )
    body += element(
        "p",
        "Ønsket har været at bygge en engagerende læseoplevelse som et tyndt "
        "og udskifteligt formidlingslag oven på et datalag, man ikke selv "
        "ejer – og at gøre det billigt og vedligeholdelsesfrit. Der er ingen "
        "server bag <i>epistel</i> og ingen database. En automatiseret proces "
        "læser kildefilerne igennem på et halvt sekund og efterlader %d "
        "færdige HTML-sider, som en hvilken som helst webserver kan levere. "
        "Det er både en pointe og en spareøvelse: værdien i en tekstsamling "
        "ligger i dens rådata, og visninger oven på dem bør være billige at "
        "bygge, billige at drive og trygge at kassere. Vil nogen om ti år "
        "lave noget helt andet med de samme filer, koster det kun arbejdet. "
        "Denne visning må gerne smides væk. Originalfilerne i SKS må ikke."
        % BUILT_PAGES,
    )
    body += element(
        "p",
        "<i>epistel</i> er lavet af én person i samarbejde med et virtuelt "
        "team på cirka 100 AI-agenter i Claude Code over en lille uges tid – "
        "så langt er der fra det første til det sidste commit. Mere end "
        "halvdelen af agenterne har haft til opgave at skrive og verificere "
        "formidlingstekster og at finde og efterprøve kilder.",
    )
    return body


def _about_research():
    """Whose work this stands on: the archive, the centre, the edition.

    None of it happened here, and the page says so in that order -- the
    papers were public for a century and a half before anyone annotated
    them. Every date in this section carries a note marker.
    """
    body = element("h2", "Forskningsprojektet")
    body += element(
        "p",
        "Brevene er ikke fundet på et loft. De har ligget offentligt i "
        "halvandet århundrede: Kierkegaards efterladte papirer blev skænket "
        "til Universitetsbiblioteket ved gavebrev af 31. maj 1875 af hans "
        "bror, biskop P.C. Kierkegaard – biblioteket modtog manuskripterne i "
        "juli samme år – og fulgte i 1938 med bibliotekets "
        "håndskriftsamlinger over i Det Kgl. Bibliotek. Blandt dem er "
        "brevene." + _note(1),
    )
    body += element(
        "p",
        "Selve annoteringen er nyere. Søren Kierkegaard Forskningscenteret "
        "blev oprettet i 1993 (eller 1994 – kilderne er ikke enige)"
        + _note(2)
        + " og finansieret af Danmarks Grundforskningsfond med bevillinger "
        "fra Kulturministeriet og Ministeriet for Videnskab, Teknologi og "
        "Udvikling. Opgaven var en ny, tekstkritisk og annoteret udgave af "
        "alt, hvad Kierkegaard har skrevet. I 1997 indledtes udgivelsen af "
        "<i>Søren Kierkegaards Skrifter</i> i 55 bind – 28 tekstbind med 27 "
        "tilhørende kommentarbind – og det sidste bind udkom i 2013."
        + _note(3),
    )
    body += element(
        "p",
        "Det er kommentarbindene, der gør SKS-udgaven til det, den er. Her "
        "ligger tekstredegørelserne, der gør rede for hvert enkelt skrifts "
        "overlevering og datering, og de kommentarer, der oversætter "
        "citaterne, opløser forkortelserne og identificerer de mennesker, "
        "gadenavne og bogtitler, som Kierkegaard og hans brevvekslende "
        "omgangskreds kunne nøjes med at antyde. Brevene udgør bind 28, "
        "<i>Breve og dedikationer</i>, der udkom i 2013 og dermed sluttede "
        "værket; redaktionen tæller Niels Jørgen Cappelørn, Joakim Garff, "
        "Johnny Kondrup, Karsten Kynde, Tonny Aagaard Olesen og Steen "
        "Tullberg." + _note(4) + " Det er det arbejde, alt her hviler på; "
        "det er ikke gjort her, og det kunne ikke gøres her.",
    )
    body += element(
        "p",
        "Den digitale udgave flyttede for nylig fra forskningscenterets eget "
        "sks.dk til Det Kgl. Biblioteks tekstportal i et samarbejde mellem de "
        "to, og sks.dk lukkede endeligt 1. maj 2023. Visningen er ny, "
        "datamaterialet det samme." + _note(5) + " Det er den flytning, der "
        "har efterladt teksterne dér, hvor <i>epistel</i> kan nå dem – hos en "
        "institution, hvis opgave er at bevare, og i et format, der kan læses "
        "af andet end øjne.",
    )
    return element("section", body, id="forskningsprojektet")


def _about_originals(provenance, links=None):
    """The files themselves: the format, the copy, the corpus, the marks.

    The provenance paragraph is the one part of the page that depends on
    the build: with a record beside the vendored files it says where the
    copy came from and links the two documents that spell the chain out;
    without one it says only what can be seen -- the copy lies unchanged
    in the project.
    """
    body = element("h2", "Originalteksterne")
    body += element(
        "p",
        "Formatet hedder TEI, Text Encoding Initiative – retningslinjer "
        "udviklet og vedligeholdt af et internationalt konsortium, som "
        "biblioteker, museer, forlag og forskere siden 1994 har brugt, når en "
        "tekstudgave skal kodes til videnskabelig brug."
        + _note(6)
        + " Det interessante ved TEI er ikke, at teksten bliver "
        "maskinlæsbar – det bliver enhver tekstfil – men at <i>redaktionens "
        "arbejde</i> bliver det. Når SKS-udgaven daterer et brev, står "
        "dateringen i filen som en oplysning med sin egen usikkerhed og sin "
        "egen begrundelse; når en person nævnes, står vedkommende med den "
        "normaliserede navneform, registret bruger; når udgiverne har rettet "
        "en skrivefejl eller opløst en forkortelse, står både det, der stod, "
        "og det, de gjorde ved det. Materialet blev oversat til TEI fra sit "
        "oprindelige format af Karsten Kynde med bidrag fra Sigfrid "
        "Lundberg." + _note(7),
    )
    kept = (
        "<i>epistel</i> læser brevene direkte fra de filer, uden mellemled og "
        "uden rettelser. Kopien ligger uændret i projektet"
    )
    if provenance:
        kept += (
            ", hentet fra én bestemt udgivelse af filerne, og hvert led i "
            "kæden fra kilde til side kan efterprøves – den er skrevet ned i "
            "projektets "
            + _linked(links, "provenance-record", "proveniensdokument")
            + " og gengivet led for led i de "
            + _linked(links, "technical-notes", "indholdstekniske noter")
            + " i repoet."
        )
    else:
        kept += "."
    body += element("p", kept)
    body += element(
        "p",
        "Fjorten grupper af korrespondancer, ordnet som SKS-udgaven ordner "
        "dem: efter modtagerkreds, fra familien over studiefællerne og Emil "
        "Boesen til Regine Olsen, familien Lund, Rasmus Nielsen og til sidst "
        "læserinderne. Det giver %d breve fra 1829 til 1855 – de fleste "
        "skrevet af Kierkegaard eller til ham, enkelte mellem andre i kredsen "
        "om ham." % LETTERS,
    )
    body += element(
        "p",
        "Det tekstkritiske apparat følger med teksten. På hver brevside "
        "markerer <i>epistel</i> med tilbageholdenhed, hvad udgiverne har "
        "gjort – rettet, tilføjet, noteret et skift til latinsk hånd – og "
        "forklarer mærkerne i en tegnforklaring under brevet. Kommentarer, "
        "indledninger og tekstredegørelser er derimod gengivet i deres "
        "helhed i SKS på Det Kgl. Biblioteks tekstportal, og <i>epistel</i> "
        "linker til den kommenterede udgave overalt.",
    )
    body += element(
        "p",
        "Til gengæld holder visningen fast i kildens usikkerhed. Et brev, der "
        "kun kan dateres til en måned, står som »december 1848« og ikke som "
        "en opdigtet dag; et brev, SKS-udgaven daterer efter poststemplet, "
        "siger det. Brev 39 har mistet sin overskrift i kilden; det siger "
        "resuméet ligeud, og brevsiden gengiver i stedet udgavens egen note, "
        "»udateret [1846-47]«. Ét sted i materialet er en øvre tidsgrænse "
        "skrevet forkert og kan ikke læses maskinelt; visningen citerer den, "
        "som den står, i stedet for at gætte. Uvished er historisk oplysning, "
        "ikke en fejl, der skal pyntes væk – og en visning, der glatter den "
        "ud, fortæller mindre end kilden, ikke mere.",
    )
    return element("section", body, id="originalteksterne")


def _about_display():
    """The four things the display adds: the list, the people, the scale, her.

    Every figure in here is a claim about the build the reader is looking
    at, and every one of them is recounted from the built pages by the
    suite.
    """
    body = element("h2", "Formidlingen")
    body += element(
        "p",
        "Brevoversigten er visningens omdrejningspunkt. Man kan søge i den, "
        "og man kan filtrere efter afsender, modtager og år. Søgningen kører "
        "i browseren på et indeks, der bygges færdigt sammen med siderne, så "
        "der ikke skal spørges nogen server om noget; den folder æ, ø og å "
        "ud, så <i>Soren</i> finder <i>Søren</i> og <i>Kaerlighed</i> finder "
        "<i>Kjærlighed</i>. Kontrollerne folder sig først ud, når browseren "
        "kan drive dem; er JavaScript slået fra, vises de slet ikke, og alle "
        "%d breve står der stadig som almindelig tekst." % LETTERS,
    )
    body += element(
        "p",
        "Persongalleriet er SKS-udgavens eget. Enhver, som SKS selv har "
        "mærket op med navn i en brevtekst, får sin side – %d i alt – med de "
        "breve, vedkommende har skrevet, modtaget og er nævnt i. På %d af "
        "siderne står desuden en kort biografi skrevet ud af udgavens egen "
        "kommentar, med henvisning til den note, den bygger på. Har "
        "kommentaren intet at sige om personen, siger siden det i stedet for "
        "at gætte. Det er i øvrigt her, brevene begynder at ligne noget andet "
        "end enkeltdokumenter: Henriette Lunds side samler de fjorten breve, "
        "hendes onkel skrev til hende – hendes fødselsdag den 12. november "
        "vender tilbage i flere af dem – og de læses i træk som en lille "
        "roman." % (PERSON_PAGES, BIOGRAPHIES),
    )
    body += element(
        "p",
        "Tidslinjen sætter livet op på én lineær skala fra det første "
        "bevarede brev i 1829 til Kierkegaards død i 1855: %d breve placeret "
        "i et år, %d uden datering, %d skrifter udgivet i hans levetid og %d "
        "bopæle. Hvert år fylder det samme, så de tavse år fylder lige så "
        "meget som de travle – hvilket er hele grunden til at lave sådan en."
        % (
            LETTERS_ON_THE_SCALE,
            LETTERS_WITHOUT_A_DATE,
            PUBLICATIONS,
            RESIDENCES,
        ),
    )
    body += element(
        "p",
        "Og så er der det lag, der egentlig var anledningen. Under hvert brev "
        "i hver liste står to linjer om, hvad der er i det. De skal gøre det "
        "muligt at læse sig igennem brevene som en sammenhængende tekst i "
        "stedet for at klikke sig rundt i en atomiseret database – at vide, "
        "hvad man går ind til, uden at få pointen røbet. De er skrevet af "
        "%s." % text(PRESENTER),
    )
    return element("section", body, id="formidlingen")


def _about_presenter():
    """The disclosure. Plain Danish, no hedging, and no small print.

    The section id is an address the front page's signature links at, so
    it may not move. The last paragraph is the page's promise to keep
    checking itself, and it names a number a test recounts.
    """
    body = element("h2", text(PRESENTER))
    body += element(
        "p",
        "Hun var ikke planlagt. Hun voksede ud af arbejdet som et ekko af "
        "Kierkegaards eget pseudonymgalleri: et navn på titelbladet, som hele "
        "København alligevel kunne regne ud, hvem var. Og det skal siges rent "
        "ud: hun findes ikke; hun er opdigtet til lejligheden.",
    )
    body += element(
        "p",
        "Fornavnet er lånt med et blink fra hende, der har bygget siden, "
        "efternavnet fra Nicolaus Notabene, som i <i>Forord</i> (1844) kun "
        "måtte skrive forord, fordi hans kone anså det for ægteskabelig "
        "utroskab at skrive bøger."
        + _note(8)
        + " Nu har en efterkommer taget pennen, og hun skriver stadig kun "
        "forord: forsidens velkomst er et forord, og de %d resuméer i "
        "brevoversigten er %d små forord. Bogen skriver hun aldrig – brevene "
        "er bogen." % (SUMMARIES, SUMMARIES),
    )
    body += element(
        "p",
        "Metafiktionen angår kun værtinden, aldrig materialet. Hun påstår "
        "aldrig at have fundet, ejet, arvet eller reddet et eneste brev, og "
        "hun opdigter ikke en kilde, en datering eller en anekdote. Hendes "
        "tone er beskrevet i en stemmeguide, der ligger i projektet: moderne "
        "rigsdansk, konkret, med citater i kildens egen retskrivning; en let "
        "ironi, der kun må pege mod hende selv, mod tidens afstand og mod "
        "udgivervanerne – aldrig mod brevskriverne, for der er sorg, sygdom, "
        "gæld og døde søskende i de her breve. Og der er ét sted, hun aldrig "
        "sidder: oven over en brevtekst. Dér har brevet ordet.",
    )
    body += element(
        "p",
        "Resuméerne og biografierne er skrevet med hjælp fra Claude (AI) "
        "efter den stemmeguide og med en metode, der er værd at nævne, fordi "
        "den er hele forskellen på formidling og opdigt: hver tekst er "
        "skrevet alene på grundlag af det, den handler om – resuméet på "
        "brevets egen tekst, biografien på udgavens kommentarnoter – og "
        "derefter sendt gennem en modlæsningsrunde, hvor en anden model havde "
        "én instruks: udefrakommende viden gælder ikke, og selv en sand "
        "påstand flages, hvis den ikke står i grundlaget. Det, modlæsningen "
        "fandt, er rettet med præcis de noter, den pegede på, og læst igennem "
        "igen, til der ikke var flere flag. Var en biografi for lang, blev "
        "den trimmet ved at fjerne ord, aldrig ved at skrive nye. Selve "
        "modlæsningens rå output ligger i projektet som dokumentation.",
    )
    body += element(
        "p",
        "Og fordi det er kode, står afgørelserne ikke kun i en "
        "hensigtserklæring: visningen har %d automatiske tests, der blandt "
        "andet holder øje med, at det angivne commit ikke kan skride fra det, "
        "der faktisk ligger i mappen, og at siden bliver ved med at sige de "
        "sande ting om sig selv." % AUTOMATED_TESTS,
    )
    return element("section", body, id="notabene")


def _about_code(links):
    body = element("h2", "<i>epistel</i>s kildekode")
    body += element(
        "p",
        "Generatoren er skrevet i Python og bruger ikke andet end "
        "standardbiblioteket. Siderne er HTML og CSS skrevet til "
        "lejligheden, uden frameworks, og én lille JavaScript-fil klarer "
        "søgning og filtre. Hele kildekoden ligger offentligt på GitHub som "
        + _linked(links, "project-repository", "mariabitsch/epistel")
        + " under MIT-licensen: brug den, ændr den, byg noget bedre af den. "
        "Kopien af TEI-filerne beholder sin egen CC0-status, og Maria "
        "Notabenes tekster – resuméerne og biografierne – er "
        + _linked(links, "cc-by-nc-sa-deed", "CC BY-NC-SA 4.0")
        + ": del dem gerne, med navn, ikke-kommercielt og på samme vilkår. "
        "MIT gælder kun koden.",
    )
    body += element("p", "God fornøjelse!")
    return element("section", body, id="kildekode")


def _about_notes(provenance, links=None):
    """The sources, numbered, at the foot of the page.

    Everything the page asserts about the world outside the letters is
    footnoted here, disagreements included: two sources give two founding
    years for the research centre, and the note says so rather than
    choosing one. The addresses are looked up by id like every other link
    on the site, so a build without the table keeps the citations and
    loses the anchors -- which is the right way round for a source list.
    """
    repository = (provenance or {}).get("repository")
    notes = [
        "»Ved gavebrev af 31. maj 1875 skænkede P.C. Kierkegaard papirerne "
        "til Universitetsbiblioteket, som i juli samme år modtog "
        "manuskripterne.« Det Kgl. Bibliotek: »Trusler og Tyvekoster – Søren "
        "Kierkegaard-arkivet«, www2.kb.dk, bevaret i KB's eget webarkiv "
        "(2010), "
        + _linked(links, "kb-archived-kierkegaard-page", "wayback-01.kb.dk")
        + ". Overførslen 1938 tillige i KB's nuværende "
        "»Håndskriftsamlingens historie«, "
        + _linked(links, "kb-manuscript-collection-history", "kb.dk")
        + ". (UNESCO Memory of the World-formularen fra 1997 daterer løsere "
        "overgangen »after the Second World War«; KB's egne to sider er "
        "enige om 1938, og de er fulgt her.)",
        "Oprettelsesåret 1993: Niels Jørgen Cappelørn, »Søren Kierkegaard "
        "Forskningscenteret«, "
        + _linked(links, "lex-research-centre", "lex.dk")
        + ". Oprettelsesåret 1994: »den til formålet af Danmarks "
        "Grundforskningsfond i 1994 oprettede Søren Kierkegaard "
        "Forskningscenter«, <i>Magasin fra Det Kongelige Bibliotek</i>, "
        + _linked(links, "magasin-research-centre", "tidsskrift.dk")
        + ". Uenigheden gengives åbent i stedet for at vælge ét år.",
        "Finansiering, formål, 55 bind, 1997–2013: lex.dk (jf. note 2); "
        "fordelingen 28 tekstbind + 27 kommentarbind: Københavns "
        "Universitet, Søren Kierkegaard Forskningscenteret, "
        + _linked(links, "skc-department", "teol.ku.dk")
        + ".",
        "Bind 28/K28, <i>Breve og dedikationer</i>, 2013; »mere end 300 "
        "breve til og fra Kierkegaard« fordelt på »14 grupper af "
        "korrespondancer«; redaktionen: Gads Forlag, "
        + _linked(links, "gads-volume-28", "gad.dk")
        + ", og SKS' elektroniske udgave, "
        + _linked(links, "sks-electronic-edition", "sks.etxt.dk")
        + ".",
        "»SKS flytter til Det Kgl. Bibliotek«, Københavns Universitet, "
        + _linked(links, "skc-move-announcement", "teol.ku.dk")
        + " – flytningen i samarbejde mellem SKC og KB; sks.dk lukkede "
        "1. maj 2023; »visningen er ny, datamaterialet det samme«.",
        "TEI Consortium, "
        + _linked(links, "tei-consortium", "tei-c.org")
        + " – Text Encoding Initiative; retningslinjerne brugt siden 1994 af "
        "biblioteker, museer, forlag og forskere.",
        _linked(links, "upstream-repository", "kb-dk/SKS_tei", href=repository)
        + ", README – »translated into TEI from the original kn1 format by "
        "Karsten Kynde with some contributions from Sigfrid Lundberg«; "
        "repositoriets licens CC0-1.0.",
        "»At være Forfatter, naar man er Ægtemand, siger hun, er aabenbar "
        "Utroskab …« – Nicolaus Notabene, <i>Forord</i> (1844), i SKS på Det "
        "Kgl. Biblioteks tekstportal, "
        + _linked(links, "forord-text", "tekster.kb.dk")
        + ". (Citatet i noten er parafrasens belæg; sætningen fortsætter i "
        "kilden.)",
    ]
    body = element("h2", "Noter")
    body += element(
        "ol",
        "".join(
            element("li", note, id="note-%d" % number)
            for number, note in enumerate(notes, start=1)
        ),
        class_="om-notes",
    )
    return element("section", body, id="noter")


def _style(**values):
    """Positions as custom properties: the stylesheet does the arithmetic."""
    parts = []
    for name, value in values.items():
        rendered = "%d" % value if isinstance(value, int) else "%.4f" % value
        parts.append("--%s:%s" % (name, rendered))
    return ";".join(parts)


# ---------------------------------------------------------------------------
# Shared bits
# ---------------------------------------------------------------------------


def _definition_list(rows, class_name):
    body = "".join(
        element("div", element("dt", label) + element("dd", value)) for label, value in rows
    )
    return element("dl", body, class_=class_name)


def _name(display, raw, links=None):
    """A person's name, with the edition's own index form kept alongside.

    One person behind the name: the name becomes the link. Two -- the edition
    addresses three letters to a couple or a pair of children -- the name
    stays as it is written and both people are named after it, because
    "Sophie Lund og Carl Lund" is one string that cannot be cut in half.
    Nobody: plain text, as before.
    """
    rendered = element("span", text(display), data_name=raw)
    if not links:
        return rendered
    if len(links) == 1:
        return element(
            "a", text(display), href=links[0]["href"], data_name=raw, class_="person-link"
        )
    return rendered + element(
        "span",
        " · ".join(
            element("a", text(link["label"]), href=link["href"], class_="person-link")
            for link in links
        ),
        class_="person-both",
    )


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
    span = view.get("span")
    if span and span["open_end_raw"]:
        # The edition wrote an upper bound the parser could not read (b43/50:
        # notAfter="1847000"). The timeline already quotes it; the page must
        # not pretend the edition claimed nothing.
        rendered += element(
            "span",
            " [kildens øvre grænse »%s« kan ikke læses]" % text(span["open_end_raw"]),
            class_="date-provenance",
        )
    return rendered


def _letter_count(count):
    return "%d brev" % count if count == 1 else "%d breve" % count


def _preserved_letter_count(count):
    # The lead's word (Maria's lead #3, 2026-08-03): "bevarede" is the
    # grounded hint that most of the correspondence never reached us.
    return "%d bevaret brev" % count if count == 1 else "%d bevarede breve" % count


def _volume_count(count):
    # "Gruppe" is the edition's own word for the fourteen divisions of the
    # letters (Gads: "14 grupper af korrespondancer"); the letters together
    # are one volume of SKS, 28 -- so "bind" said something false here.
    # Singular matters: a partial build of one directory must describe
    # itself truthfully too (see _intro's docstring).
    return "%d gruppe" % count if count == 1 else "%d grupper" % count


def _resolved(logical, assets):
    """A logical asset path through the manifest; itself when absent."""
    return (assets or {}).get(logical, logical)


def _document(
    title,
    main,
    root,
    description,
    body_class=None,
    timeline=False,
    here=None,
    scripts=(),
    links=None,
    assets=None,
):
    """The shell every page shares.

    ``assets`` is the manifest from ``sitegen.assets``: logical path ->
    content-hashed path, both relative to the site root. Every asset
    reference a page renders -- the stylesheet, the scripts -- goes through
    it, so the pages always point at the names the build actually wrote.
    Without a manifest the logical names stand as they are, which is what a
    directly-rendered page in a test gets.

    The <title> and the social metadata are the page's face away from the
    site (Maria's SEO ruling, 2026-08-03): the title must say what the page
    is with no context -- letters name their correspondents, every other
    page names the corpus -- and ❖ separates page from site in the tab.
    Open Graph carries the same strings and nothing more: og:url and
    og:image demand an absolute address, and the built output stays
    host-agnostic on purpose, so they are deliberately absent.
    """
    head = (
        element("meta", charset="utf-8")
        + element("meta", name="viewport", content="width=device-width, initial-scale=1")
        + element("meta", name="description", content=description)
        + element("title", "%s ❖ %s" % (text(title), SITE_TITLE))
        + element("meta", property="og:title", content=title)
        + element("meta", property="og:description", content=description)
        + element("meta", property="og:type", content="website")
        + element("meta", property="og:site_name", content=SITE_TITLE)
        + element("meta", property="og:locale", content="da_DK")
        + element("meta", name="twitter:card", content="summary")
        + element(
            "link",
            rel="stylesheet",
            href="%s%s" % (root, _resolved("assets/site.css", assets)),
        )
        # Maria's icon set, declared relatively like every other address
        # on the site; the files sit at the root (see site._copy_static).
        + element(
            "link",
            rel="icon",
            href="%sfavicon.ico" % root,
            sizes="16x16 32x32 48x48",
        )
        + element(
            "link",
            rel="icon",
            type="image/png",
            sizes="32x32",
            href="%sfavicon-32x32.png" % root,
        )
        + element(
            "link",
            rel="icon",
            type="image/png",
            sizes="16x16",
            href="%sfavicon-16x16.png" % root,
        )
        + element("link", rel="apple-touch-icon", href="%sapple-touch-icon.png" % root)
        + element("link", rel="manifest", href="%ssite.webmanifest" % root)
    )
    header = element(
        "header",
        element("p", element("a", SITE_TITLE, href=root or "./"), class_="site-title")
        + element("p", SITE_TAGLINE, class_="site-tagline")
        + _navigation(root, timeline, here),
        class_="site-header",
    )
    footer = element(
        "footer",
        element(
            "p",
            "Teksten stammer fra den TEI-kodede udgave af "
            "<i>Søren Kierkegaards Skrifter</i>, der er offentligt tilgængelig "
            "under "
            + _linked(links, "cc0-deed", "CC0 1.0")
            + ". Denne visning er en uafhængig demonstration – ikke en udgivelse "
            "fra udgiverne bag SKS – og er bygget med hjælp fra Claude (AI).",
        ),
        class_="site-footer",
    )
    skip = element("a", "Spring til indhold", href="#indhold", class_="skip-link")
    body = skip + header + element("main", main, id="indhold") + footer
    body += "".join(
        element("script", "", src="%s%s" % (root, _resolved(source, assets)), defer=True)
        for source in scripts
    )
    return (
        "<!doctype html>\n"
        + element(
            "html",
            element("head", head) + element("body", body, class_=body_class),
            lang="da",
        )
        + "\n"
    )


def _navigation(root, timeline, here):
    """The links in the header band -- only to pages this build actually wrote.

    Breve, Personer and Om are on every build: the first two come out of the
    TEI, and the third is what makes the demonstration honest, so it may never
    be optional. The timeline is built from the curated datasets in
    ``data/context``; a build without them is a smaller site, and a smaller
    site must not offer a link to a page it never wrote.
    """
    destinations = [
        (INDEX_NAV, "Breve", root or "./"),
        (PERSONS_NAV, "Personer", "%spersoner/" % root),
    ]
    if timeline:
        destinations.append((TIMELINE_NAV, "Tidslinje", "%stidslinje/" % root))
    destinations.append((ABOUT_NAV, "Om", "%som/" % root))
    links = "".join(
        element(
            "a",
            label,
            href=href,
            aria_current="page" if name == here else None,
        )
        for name, label, href in destinations
    )
    return element("nav", links, class_="site-nav", aria_label="Sider")
