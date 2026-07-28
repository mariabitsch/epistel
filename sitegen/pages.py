"""Whole HTML documents, as plain Python string functions.

No template engine: the site has three page types, and a function that returns
a string is easier to read -- and to throw away -- than a dependency. Every
value that comes from the data passes through ``sitegen.html`` on its way in.

The pages take view models (built in ``sitegen.site`` and ``sitegen.timeline``),
not parser output, so this module contains no knowledge of TEI. All links are
relative, because the built site has to work from any directory of any static
host.
"""

from .html import classes, element, text

SITE_TITLE = "epistel"
SITE_TAGLINE = "demonstrationsvisning"

# Where each page type sits, and what it takes to get back to the root.
INDEX_TO_ROOT = ""
LETTER_TO_ROOT = "../../"
TIMELINE_TO_ROOT = "../"

# The site's two destinations. The timeline is only one of them when the
# curated datasets were built with it -- see ``sitegen.site.build_site``.
INDEX_NAV = "breve"
TIMELINE_NAV = "tidslinje"


def index_page(books, timeline=False):
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
        timeline=timeline,
        here=INDEX_NAV,
    )


def letter_page(view, previous, following, section, timeline=False):
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
        timeline=timeline,
        here=INDEX_NAV,
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


def _document(title, main, root, description, body_class=None, timeline=False, here=None):
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
    """Two links in the header band, and only while there are two places to go.

    The timeline is built from the curated datasets in ``data/context``; a
    build without them is a smaller site, and a smaller site must not offer a
    link to a page it never wrote.
    """
    if not timeline:
        return ""
    destinations = [
        (INDEX_NAV, "Breve", root or "./"),
        (TIMELINE_NAV, "Tidslinje", "%stidslinje/" % root),
    ]
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
