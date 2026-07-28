"""What a build is: view models, file layout, writing the files.

``build_site(volumes, out_dir, context=None)`` turns the parsed corpus into a
directory of static files::

    index.html                  every letter, by volume and correspondence
    brev/<slug>/index.html      one letter
    personer/index.html         the register of everyone the letters name
    person/<slug>/index.html    one person
    tidslinje/index.html        the years, with the curated context layer
    om/index.html               what the site is, and who the presenter is
    assets/site.css             plus assets/fonts/ -- everything static/ holds
    assets/search-index.js      the prebuilt free-text index

It takes a *list* of volumes and never asks how many there are, so a build of
one volume and a build of all fourteen go down the same path. The output
directory is recreated from scratch on every build, and the same input always
produces byte-identical output.

``provenance`` is the record beside the vendored files (``pipeline.provenance``)
and reaches exactly one place: the Om page, which tells the reader which
upstream commit the TEI was taken at.

``context`` is the curated editorial layer (``pipeline.context``) and every
part of it is optional. Without the publications and residences there is no
timeline page and no link to one; without the summaries the index lists
letters without them; without the biographies the person pages say the
commentary had nothing. The letters, the people the edition names in them and
the search over their text come from the TEI alone -- that is the part that
cannot be thrown away.

This module also holds the small display decisions that are neither dates nor
markup -- what a letter is called, what its URL is -- because that is what a
view model is for.
"""

import collections
import os
import re
import shutil

from pipeline.context import summary_key
from pipeline.parse_tei import plain_text

from . import dates, pages, search
from .persons import build_register, person_keys, register_groups
# Re-exported: naming a person is a display decision, and it lives in
# ``sitegen.persons`` with the rest of them.
from .persons import display_name  # noqa: F401
from .tei_html import BodyRenderer
from .timeline import timeline_model

STATIC_DIRECTORY = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
FAVICON_DIRECTORY = os.path.join(os.path.dirname(os.path.abspath(__file__)), "favicon")

# Letters a volume's correspondence groups do not account for still get
# listed; the build reports how many, because it should never be more than 0.
UNGROUPED_HEADING = "Uden for brevvekslingerne"
UNGROUPED_ID = "uden-brevveksling"

# A letter number as the edition writes it: 42, or 159.1 for a draft.
NUMBER = re.compile(r"^\d+(\.\d+)*$")


def build_site(volumes, out_dir, context=None, provenance=None, links=None):
    """Generate the whole site. Returns a small report for the build script.

    Built in two passes, because a letter page links to the people it names
    and a person page links back to the letters. The first pass reads the
    parser's output into view models and works out who is in the corpus; only
    then are the letter bodies rendered, with the addresses of the person
    pages in hand.
    """
    context = context or {}
    views = []
    books = []
    for volume in volumes:
        book = _book(volume, context)
        books.append(book)
        # The edition's own order: volume after volume, letters as printed.
        views.extend(book["letters"])
    sections = [section for book in books for section in book["sections"]]
    section_of = {
        view["slug"]: section for section in sections for view in section["letters"]
    }

    register = build_register(views, context)
    by_key = {person["key"]: person for person in register}
    renderer = BodyRenderer(
        person_href=lambda key: _person_href(by_key, key, pages.LETTER_TO_ROOT)
    )
    for view in views:
        view["body"] = renderer.render(view.pop("body_nodes"), view["render_id"])

    timeline = timeline_model(views, context) if context.get("publications") else None
    index = search.search_index(views)
    has_timeline = bool(timeline)

    _reset(out_dir)
    _write(
        out_dir,
        ["index.html"],
        pages.index_page(books, search.facets(views), timeline=has_timeline, links=links),
    )
    for previous, view, following in _neighbours(views):
        _write(
            out_dir,
            ["brev", view["slug"], "index.html"],
            pages.letter_page(
                view,
                previous,
                following,
                section_of.get(view["slug"]),
                _person_links(by_key, view),
                timeline=has_timeline,
                links=links,
            ),
        )
    _write(
        out_dir,
        ["personer", "index.html"],
        pages.person_index_page(register_groups(register), register, timeline=has_timeline, links=links),
    )
    for person in register:
        _write(
            out_dir,
            ["person", person["slug"], "index.html"],
            pages.person_page(person, timeline=has_timeline, links=links),
        )
    if timeline:
        _write(out_dir, ["tidslinje", "index.html"], pages.timeline_page(timeline, links=links))
    # Always written, and never conditional on any dataset: the Om page is
    # what tells a reader this is a demonstration and who the presenter is.
    _write(
        out_dir,
        ["om", "index.html"],
        pages.about_page(provenance=provenance, timeline=has_timeline, links=links),
    )
    _copy_static(out_dir)
    _write(out_dir, ["assets", "search-index.js"], search.index_script(index))

    return {
        "volumes": len(books),
        "letters": len(views),
        "sections": len(sections),
        "ungrouped": sum(
            len(section["letters"]) for section in sections if section["ungrouped"]
        ),
        "warnings": renderer.warnings(),
        "timeline": timeline["counts"] if timeline else None,
        "people": len(register),
        "summaries": sum(1 for view in views if view["summary"]),
        "biographies": sum(1 for person in register if person["bio"]),
        "search_words": len(index["words"]),
    }


def _person_href(register, key, root):
    """Where a person's page is, seen from a page ``root`` steps down."""
    person = register.get(key)
    if not person:
        return None
    return "%sperson/%s/" % (root, person["slug"])


def _person_links(register, view):
    """The people behind one letter's sender and recipient, ready to link.

    A correspondent name the alias table could not place with confidence
    yields an empty list, and the metadata panel prints the name as text --
    which is what the edition gives us and all we can honestly show. Three
    names in the corpus are two people at once ("Schlegel, J.F. og Regine");
    they yield two, and the panel names both.
    """
    return {
        field: [
            {
                "label": register[key]["name"],
                "href": "%sperson/%s/" % (pages.LETTER_TO_ROOT, register[key]["slug"]),
            }
            for key in view["%s_keys" % field]
            if key in register
        ]
        for field in ("sender", "recipient")
    }


# ---------------------------------------------------------------------------
# View models
# ---------------------------------------------------------------------------


def letter_slug(letter, volume):
    """The URL segment a letter lives at.

    Normally the edition's own number, which is unique across the whole
    corpus -- ``brev/42/``, and ``brev/159.1/`` for a draft. Three letters in
    b171 are printed without one (``@n="-"``): they are cross-references to
    letters printed elsewhere, and all three would otherwise claim the same
    URL. Those fall back to the volume plus the letter's xml:id, which is
    unique inside its file, so no two letters can collide.
    """
    identifier = letter.get("id") or ""
    if NUMBER.match(identifier):
        return identifier
    return "%s-%s" % (volume, letter.get("xmlId") or "brev")


def _book(volume, context):
    """One volume, as the index and the letter pages need it."""
    identity = {
        "id": volume["volume"],
        "anchor": "bind-%s" % volume["volume"],
        "shortTitle": volume["shortTitle"] or volume["volume"].upper(),
        "title": volume["title"] or "Uden titel",
    }
    letters = [_letter_view(letter, identity, context) for letter in volume["letters"]]
    book = dict(identity)
    book["letters"] = letters
    book["sections"] = _sections(volume, letters)
    return book


def _letter_view(letter, book, context):
    """One letter, as a page needs it: no parser shapes past this point.

    The one exception is ``body_nodes``, which is the parser's tree waiting to
    be rendered: the renderer needs the register of people first, and the
    register is built from these same view models. ``build_site`` renders it
    and drops the key in its second pass, so nothing downstream ever sees it.
    """
    sender = letter.get("sender") or {}
    recipient = letter.get("recipient") or {}
    # The edition dates the act of sending; a received date would be a
    # different fact, and the corpus records none.
    date = sender.get("date")
    number = letter["id"]
    numbered = bool(NUMBER.match(number or ""))
    aliases = context.get("aliases") or {}
    view = {
        "slug": letter_slug(letter, book["id"]),
        "number": number,
        "numbered": numbered,
        # "Brev -" would read the edition's placeholder as if it were a name.
        # The three unnumbered letters say what they are instead.
        "title": "Brev %s" % number if numbered else "Brev uden nummer",
        "volume": book,
        "sender": display_name(sender.get("name")) or "ukendt afsender",
        "sender_raw": sender.get("name"),
        "recipient": display_name(recipient.get("name")) or "ukendt modtager",
        "recipient_raw": recipient.get("name"),
        "date_text": dates.format_date(date),
        "date_machine": dates.machine_value(date),
        "date_source": dates.provenance(date),
        # The same date as a stretch of days -- what the timeline places a
        # letter on. Everything the display knows about dates comes through
        # ``sitegen.dates``; no page reads a parser date dict itself.
        "span": dates.span(date),
        "place": (sender.get("place") or {}).get("name"),
        "note": sender.get("note"),
        "group_id": (letter.get("context") or {}).get("groupId"),
        # Who the letter names in its text, and who the curated alias table
        # says wrote and received it. An unmapped correspondent yields an
        # empty list, which is the honest answer and not a missing one.
        "person_keys": person_keys(letter["body"]),
        "sender_keys": aliases.get(sender.get("name"), []),
        "recipient_keys": aliases.get(recipient.get("name"), []),
        "summary": (context.get("summaries") or {}).get(
            summary_key(book["id"], letter.get("xmlId"))
        ),
        "plain_text": plain_text(letter["body"]),
        "body_nodes": letter["body"],
        "render_id": "%s/%s" % (book["id"], number),
    }
    view["filters"] = search.letter_filters(view)
    return view


def _sections(volume, views):
    """One volume's correspondence groups, in the order the edition lists them.

    Groups name their letters by number, and three letters have no number of
    their own, so the two lists are walked in step rather than looked up by
    key: both are in document order, which is the only thing that tells those
    three apart.
    """
    waiting = collections.defaultdict(collections.deque)
    for view in views:
        waiting[view["number"]].append(view)

    placed = set()
    sections = []
    for group in volume.get("groups", []):
        letters = []
        for identifier in group["letterIds"]:
            queue = waiting.get(identifier)
            if queue:
                letters.append(queue.popleft())
        placed.update(view["slug"] for view in letters)
        if not letters:
            continue
        sections.append(
            {
                # Group ids are file-local -- every volume has its own
                # correspContext1 -- so the anchor carries the volume.
                "id": "%s-%s" % (volume["volume"], group["id"]),
                "heading": group["heading"] or "Uden titel",
                "notes": group.get("notes") or [],
                "letters": letters,
                "ungrouped": False,
            }
        )
    orphans = [view for view in views if view["slug"] not in placed]
    if orphans:
        sections.append(
            {
                "id": "%s-%s" % (volume["volume"], UNGROUPED_ID),
                "heading": UNGROUPED_HEADING,
                "notes": [],
                "letters": orphans,
                "ungrouped": True,
            }
        )
    return sections


def _neighbours(views):
    """Yield ``(previous, view, following)`` for prev/next navigation.

    The sequence runs across the whole corpus, so the last letter of one
    volume leads straight into the first of the next -- which is how the
    edition numbers them.
    """
    for index, view in enumerate(views):
        yield (
            views[index - 1] if index > 0 else None,
            view,
            views[index + 1] if index + 1 < len(views) else None,
        )


# ---------------------------------------------------------------------------
# Files
# ---------------------------------------------------------------------------


def _reset(out_dir):
    shutil.rmtree(out_dir, ignore_errors=True)
    os.makedirs(out_dir, exist_ok=True)


def _write(out_dir, parts, content):
    path = os.path.join(out_dir, *parts)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as file:
        file.write(content)


def _copy_static(out_dir):
    """Copy ``static/`` in: the stylesheet, the fonts, and the fonts' licences.

    Self-contained output -- the built site fetches nothing at runtime, so the
    typography has to travel with it, and the OFL requires its notice to
    travel with the typography. Developer notes (``README.md``) and dotfiles
    stay in the repository: they are not part of the site. Copied by content
    only, no timestamps, so two builds of the same input agree.
    """
    shutil.copytree(
        STATIC_DIRECTORY,
        os.path.join(out_dir, "assets"),
        copy_function=shutil.copyfile,
        ignore=shutil.ignore_patterns(".*", "README.md"),
        dirs_exist_ok=True,
    )
    # The icons land at the *root*, beside index.html: /favicon.ico is
    # where a browser guesses before it has read a page. The pages still
    # declare them relatively -- see ``pages._document`` -- so the site
    # keeps working from any directory of any static host.
    shutil.copytree(
        FAVICON_DIRECTORY,
        out_dir,
        copy_function=shutil.copyfile,
        ignore=shutil.ignore_patterns(".*", "README.md"),
        dirs_exist_ok=True,
    )
