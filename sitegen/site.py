"""What a build is: view models, file layout, writing the files.

``build_site(volumes, out_dir)`` turns the parsed corpus into a directory of
static files::

    index.html                  every letter, by volume and correspondence
    brev/<slug>/index.html      one letter
    assets/site.css             plus assets/fonts/ -- everything static/ holds

It takes a *list* of volumes and never asks how many there are, so a build of
one volume and a build of all fourteen go down the same path. The output
directory is recreated from scratch on every build, and the same input always
produces byte-identical output.

This module also holds the small display decisions that are neither dates nor
markup -- what a letter is called, what its URL is, how a person's name reads
in a sentence -- because that is what a view model is for.
"""

import collections
import os
import re
import shutil

from . import dates, pages
from .tei_html import BodyRenderer

STATIC_DIRECTORY = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")

# Letters a volume's correspondence groups do not account for still get
# listed; the build reports how many, because it should never be more than 0.
UNGROUPED_HEADING = "Uden for brevvekslingerne"
UNGROUPED_ID = "uden-brevveksling"

# A letter number as the edition writes it: 42, or 159.1 for a draft.
NUMBER = re.compile(r"^\d+(\.\d+)*$")


def build_site(volumes, out_dir):
    """Generate the whole site. Returns a small report for the build script."""
    renderer = BodyRenderer()
    books = [_book(volume, renderer) for volume in volumes]
    # The edition's own order: volume after volume, letters as printed.
    views = [view for book in books for view in book["letters"]]
    sections = [section for book in books for section in book["sections"]]
    section_of = {
        view["slug"]: section for section in sections for view in section["letters"]
    }

    _reset(out_dir)
    _write(out_dir, ["index.html"], pages.index_page(books))
    for previous, view, following in _neighbours(views):
        _write(
            out_dir,
            ["brev", view["slug"], "index.html"],
            pages.letter_page(view, previous, following, section_of.get(view["slug"])),
        )
    _copy_static(out_dir)

    return {
        "volumes": len(books),
        "letters": len(views),
        "sections": len(sections),
        "ungrouped": sum(
            len(section["letters"]) for section in sections if section["ungrouped"]
        ),
        "warnings": renderer.warnings(),
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


def _book(volume, renderer):
    """One volume, as the index and the letter pages need it."""
    identity = {
        "id": volume["volume"],
        "anchor": "bind-%s" % volume["volume"],
        "shortTitle": volume["shortTitle"] or volume["volume"].upper(),
        "title": volume["title"] or "Uden titel",
    }
    letters = [_letter_view(letter, identity, renderer) for letter in volume["letters"]]
    book = dict(identity)
    book["letters"] = letters
    book["sections"] = _sections(volume, letters)
    return book


def _letter_view(letter, book, renderer):
    """One letter, as a page needs it: no parser shapes past this point."""
    sender = letter.get("sender") or {}
    recipient = letter.get("recipient") or {}
    # The edition dates the act of sending; a received date would be a
    # different fact, and the corpus records none.
    date = sender.get("date")
    number = letter["id"]
    numbered = bool(NUMBER.match(number or ""))
    return {
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
        "place": (sender.get("place") or {}).get("name"),
        "note": sender.get("note"),
        "group_id": (letter.get("context") or {}).get("groupId"),
        "body": renderer.render(letter["body"], "%s/%s" % (book["id"], number)),
    }


def display_name(name):
    """Read a name the way a sentence does.

    The edition indexes people surname first ("Kierkegaard, P.C."), which is
    right for a register and wrong in "Fra Kierkegaard, P.C.". Turning it
    around is a display decision only: the source string travels with it (see
    ``pages._name``), and names without a comma -- "SK" -- are left alone.
    """
    if not name or name.count(",") != 1:
        return name
    family, _, given = name.partition(",")
    family, given = family.strip(), given.strip()
    if not family or not given:
        return name
    return "%s %s" % (given, family)


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
