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
SITE_TAGLINE = "demonstrationsvisning"

# Where each page type sits, and what it takes to get back to the root.
INDEX_TO_ROOT = ""
LETTER_TO_ROOT = "../../"
PERSON_TO_ROOT = "../../"
PERSON_INDEX_TO_ROOT = "../"
TIMELINE_TO_ROOT = "../"

# The site's destinations. The timeline is only one of them when the curated
# datasets were built with it -- see ``sitegen.site.build_site``.
INDEX_NAV = "breve"
PERSONS_NAV = "personer"
TIMELINE_NAV = "tidslinje"

# Who wrote the summaries, said once on the page that shows them. She is a
# presenter, not a source: the Om page says so plainly.
PRESENTER = "Victoria Eremita"


def index_page(books, facets, timeline=False):
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
    body += _finder(facets)
    body += _volume_navigation(books)
    body += "".join(_book(book) for book in books)
    return _document(
        title="Breve",
        main=body,
        root=INDEX_TO_ROOT,
        description="Søren Kierkegaards %s i %s, vist fra offentlige TEI-filer."
        % (_letter_count(count), _volume_count(len(books))),
        timeline=timeline,
        here=INDEX_NAV,
        scripts=["assets/search.js"],
    )


def letter_page(view, previous, following, section, person_links, timeline=False):
    """One letter: what it is, what it says, and what it belongs with."""
    header = element(
        "p",
        element("a", "← Alle breve", href=LETTER_TO_ROOT),
        class_="crumb",
    )
    header += element("h1", text(view["title"]))
    header += _metadata(view, section, person_links)

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
        timeline=timeline,
        here=INDEX_NAV,
    )


# ---------------------------------------------------------------------------
# Index parts
# ---------------------------------------------------------------------------


def _intro(books, count, summaries):
    """What the reader is looking at -- as many volumes as were built.

    Written from the list, not from a sentence about one volume, so a build of
    b1 alone and a build of the whole corpus both describe themselves
    truthfully. The same goes for the summaries: they are named only when
    there are some, because a build without the curated layer must not
    promise them.
    """
    lead = (
        "Søren Kierkegaards breve, læst direkte fra den TEI-kodede udgave "
        "<i>Søren Kierkegaards Skrifter</i>. Denne demonstration viser "
        + element(
            "strong", "%s i %s" % (_letter_count(count), _volume_count(len(books)))
        )
        + ", ordnet efter bind og brevveksling."
    )
    if summaries:
        lead += (
            " De korte resuméer under brevene er skrevet af %s og hører ikke "
            "til udgaven." % text(PRESENTER)
        )
    return element("p", lead, class_="lead")


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
        "Ingen breve matcher. Prøv et andet ord, eller ryd filtrene.",
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
        "Breve, som udgaven kun daterer til et år eller til en periode, står "
        "under det tidligste år, de kan tilhøre. Datoen ved hvert brev siger, "
        "hvad udgaven faktisk ved."
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
    """One line in the index: a linked heading, the bare facts, the resumé.

    The filter values travel on the element as ``data-`` attributes so that
    narrowing the list is a matter of hiding rows that are already on the
    page. Nothing is ever built from a string of data at runtime.
    """
    heading = element(
        "h4", element("a", text(view["title"]), href="brev/%s/" % view["slug"])
    )
    filters = view["filters"]
    return element(
        "li",
        heading + _facts(view) + _summary(view),
        class_="letter-entry",
        data_slug=view["slug"],
        data_sender=filters["sender"],
        data_recipient=filters["recipient"],
        data_year=filters["year"],
    )


def _facts(view):
    return _definition_list(
        [
            ("Fra", _name(view["sender"], view["sender_raw"])),
            ("Til", _name(view["recipient"], view["recipient_raw"])),
            ("Dateret", _date(view)),
        ],
        class_name="letter-meta",
    )


def _summary(view):
    """Victoria's two sentences about the letter, in her own register.

    Not on the letter page: there the letter speaks for itself. Here, where a
    reader is choosing what to read, a presenter is welcome -- and she is
    marked as one. The three letters the edition prints as bare
    cross-references have no summary, and get none.
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


def _metadata(view, section, person_links=None):
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
# People
# ---------------------------------------------------------------------------


def person_index_page(groups, register, timeline=False):
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
        title="Personer",
        main=body,
        root=PERSON_INDEX_TO_ROOT,
        description="%s, som Søren Kierkegaards breve nævner ved navn."
        % _person_count(len(register)),
        timeline=timeline,
        here=PERSONS_NAV,
    )


def _person_index_intro(count, with_bio):
    lead = (
        "Alle, som brevene nævner ved navn — "
        + element("strong", _person_count(count))
        + ", som udgaven selv har mærket op i brevteksterne. Registret skelner "
        "ikke mellem levende og litterære: står navnet i et brev, står "
        "personen her."
    )
    if with_bio:
        lead += (
            " %d af dem har en kort biografi, hentet ud af udgavens egen "
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


def person_page(person, timeline=False):
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
        "Breve sendt",
        "Breve, som udgaven angiver %s som afsender af." % person["name"],
    )
    article += _person_letters(
        person["received"],
        "Breve modtaget",
        "Breve, som udgaven angiver %s som modtager af." % person["name"],
    )
    article += _person_letters(
        person["mentioned"],
        "Nævnt i brevene",
        "Breve, hvor navnet står i selve brevteksten.",
    )
    return _document(
        title=person["name"],
        main=element("article", article, class_="person"),
        root=PERSON_TO_ROOT,
        description="%s i Søren Kierkegaards breve: %s."
        % (person["name"], _person_summary(person)),
        timeline=timeline,
        here=PERSONS_NAV,
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
            "Udgavens kommentar nævner personen, men uden biografiske "
            "oplysninger at bygge en note på."
        )
    else:
        line = "Kommentaren giver ingen biografisk note."
    return element(
        "section",
        element("p", line, class_="person-bio person-bio--none"),
        class_="person-biography",
    )


def _person_letters(views, heading, note):
    """One of a person's three lists of letters, in the edition's own order."""
    if not views:
        return ""
    items = "".join(
        element(
            "li",
            element("a", text(view["title"]), href="%sbrev/%s/" % (PERSON_TO_ROOT, view["slug"]))
            + element(
                "span",
                " · " + text(view["date_text"]),
                class_="muted",
            )
            + element(
                "span",
                " · fra %s til %s" % (text(view["sender"]), text(view["recipient"])),
                class_="person-letter-pair",
            ),
        )
        for view in views
    )
    return element(
        "section",
        element("h2", text(heading))
        + element("p", text(note), class_="group-note")
        + element("p", _letter_count(len(views)), class_="group-count")
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


def timeline_page(model):
    """The letters against the books and the addresses, on one linear scale.

    The page is a stack of years, each of them the same height, each holding
    four lanes: where he lived, the letters he sent, the letters the edition
    can only date to a year, and what he published. ``sitegen.timeline`` has
    already decided every position; this function only writes them down.

    Nothing here moves after the page is served -- the marks are elements with
    two custom properties, and the stylesheet does the arithmetic. There is no
    script on the page, so there is nothing to fail.
    """
    counts = model["counts"]
    body = element("h1", "Tidslinje")
    body += _timeline_intro(model)
    body += _timeline_legend()
    body += _timeline_rail(model)
    body += _undated(model["undated"])
    body += _home_register(model["homes"])
    body += _dataset_note(model["meta"])
    return _document(
        title="Tidslinje",
        main=body,
        root=TIMELINE_TO_ROOT,
        description="Søren Kierkegaards %s, %d skrifter og %d bopæle fra %d til "
        "%d på én lineær tidsskala."
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
    )


def _timeline_intro(model):
    counts = model["counts"]
    lead = element(
        "p",
        "Søren Kierkegaards liv fra %d til %d på én skala: brevene fra den "
        "TEI-kodede udgave, sat op mod de skrifter han fik udgivet, og de "
        "adresser han boede på. Hvert år fylder det samme, så de tavse år "
        "fylder lige så meget som de travle."
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
    rows = [
        ("Streg", "brev, som udgaven daterer til dagen."),
        (
            "Åben kasse",
            "brev, som udgaven kun daterer til måneden. Kassen dækker hele "
            "måneden, fordi det er alt, kilden siger.",
        ),
        (
            "ca.",
            "brev, som udgaven kun daterer til året eller til en periode over "
            "flere år. Det har ingen plads på dagskalaen og står derfor "
            "samlet for sig ud for året.",
        ),
        (
            "Udfyldt rude",
            "skrift udgivet under Kierkegaards eget navn. Rykket helt ud til "
            "skinnen.",
        ),
        (
            "Åben rude",
            "skrift udgivet under pseudonym. Rykket ind, med pseudonymets navn "
            "under titlen.",
        ),
        (
            "Bånd",
            "bopæl. Stiplet kant betyder, at kilderne er uenige om perioden, "
            "eller at de kun kender året.",
        ),
    ]
    note = element(
        "p",
        "Skalaen er lineær: hvert år er lige højt. Et år strækkes kun, hvor "
        "årets udgivelser fylder mere end året — aldrig omvendt, og aldrig på "
        "de stille års bekostning. Breve uden nogen datering står nederst på "
        "siden.",
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


def _timeline_rail(model):
    head = element(
        "div",
        "".join(
            element("span", text(label), class_="tl-head-%s" % lane)
            for lane, label in (
                ("axis", "År"),
                ("homes", "Bopæl"),
                ("letters", "Breve"),
                ("vague", "Kun år"),
                ("works", "Udgivelser"),
            )
        ),
        class_="tl-head",
        aria_hidden="true",
    )
    years = "".join(_timeline_year(year) for year in model["years"])
    return element(
        "div",
        head + years,
        class_="tl",
        style=_style(slots=model["slots"], homes=model["home_slots"]),
    )


def _timeline_year(year):
    inner = element("h2", text("%d" % year["year"]), class_="tl-axis")
    inner += _homes(year["homes"])
    inner += _letters(year["letters"], year["year"])
    inner += _vague(year["vague"], year["year"])
    inner += _works(year["works"])
    return element(
        "section",
        inner,
        # Every tenth year gets a stronger rule: a scale a reader can count by
        # without reading every label.
        class_=classes("tl-year", "tl-year--decade" if not year["year"] % 10 else None),
        id="aar-%d" % year["year"],
    )


def _homes(segments):
    """One year's slice of the bands. Only a band's first year is labelled."""
    bands = ""
    for segment in segments:
        band = element(
            "span",
            "",
            class_="tl-home-band",
            aria_hidden="true",
        )
        label = ""
        if segment["labelled"]:
            label = element(
                "p",
                element("b", text(segment["address"]), class_="tl-home-address")
                + element(
                    "span",
                    text(segment["period"])
                    + (" (fortsat)" if segment["continued"] else ""),
                    class_="tl-home-period",
                )
                + (
                    element("span", "usikker datering", class_="tl-approx")
                    if segment["approx"] and segment["starts"]
                    else ""
                ),
                class_="tl-home-label",
            )
        bands += element(
            "div",
            band + label,
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
            aria_label="Breve, som udgaven kun daterer til %d eller til en "
            "periode fra %d" % (year, year),
        ),
        class_="tl-vague",
    )


def _works(blocks):
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
        entries = "".join(_work(entry) for entry in block["entries"])
        items += element(
            "li",
            element(
                "p",
                element("time", text(block["date_text"]), datetime=block["date"].isoformat()),
                class_="tl-work-date",
            )
            + element("ul", entries, class_="tl-work-list"),
            class_="tl-work",
            style=_style(lead=block["lead"], span=block["span"]),
        )
    return element("ol", items, class_="tl-works")


def _work(entry):
    pseudonym = entry["pseudonym"]
    inner = element("span", "", class_="tl-work-mark", aria_hidden="true")
    inner += element("b", text(entry["title"]), class_="tl-work-title")
    inner += element(
        "span",
        "Pseudonym: %s" % text(pseudonym) if pseudonym else "Signeret",
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
    return rendered


def _letter_count(count):
    return "%d brev" % count if count == 1 else "%d breve" % count


def _volume_count(count):
    return "%d bind" % count


def _document(
    title,
    main,
    root,
    description,
    body_class=None,
    timeline=False,
    here=None,
    scripts=(),
):
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
    body += "".join(
        element("script", "", src="%s%s" % (root, source), defer=True)
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

    Breve and Personer both come out of the TEI and are always there. The
    timeline is built from the curated datasets in ``data/context``; a build
    without them is a smaller site, and a smaller site must not offer a link
    to a page it never wrote.
    """
    destinations = [
        (INDEX_NAV, "Breve", root or "./"),
        (PERSONS_NAV, "Personer", "%spersoner/" % root),
    ]
    if timeline:
        destinations.append((TIMELINE_NAV, "Tidslinje", "%stidslinje/" % root))
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
