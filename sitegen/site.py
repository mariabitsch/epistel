"""What a build is: view models, file layout, writing the files.

``build_site(volume, out_dir)`` turns one parsed volume into a directory of
static files::

    index.html              every letter, grouped by correspondence
    brev/<letter>/index.html    one letter
    assets/site.css

The output directory is recreated from scratch on every build, and the same
input always produces byte-identical output.

This module also holds the small display decisions that are neither dates nor
markup -- what a letter is called, how a person's name reads in a sentence --
because that is what a view model is for.
"""

import os
import shutil

from . import dates, pages
from .tei_html import BodyRenderer

STATIC_DIRECTORY = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")

# Letters the volume's correspondence groups do not account for still get
# listed; the build reports how many, because it should never be more than 0.
UNGROUPED_HEADING = "Uden for brevvekslingerne"
UNGROUPED_ID = "uden-brevveksling"


def build_site(volume, out_dir):
    """Generate the whole site. Returns a small report for the build script."""
    renderer = BodyRenderer()
    views = [_letter_view(letter, renderer) for letter in _in_letter_order(volume)]
    sections = _sections(volume, views)
    section_of = {
        view["id"]: section for section in sections for view in section["letters"]
    }

    _reset(out_dir)
    _write(out_dir, ["index.html"], pages.index_page(volume, sections))
    for previous, view, following in _neighbours(views):
        _write(
            out_dir,
            ["brev", view["id"], "index.html"],
            pages.letter_page(view, previous, following, section_of.get(view["id"])),
        )
    _copy_static(out_dir)

    return {
        "letters": len(views),
        "sections": len(sections),
        "ungrouped": sum(
            1 for section in sections if section["id"] == UNGROUPED_ID
            for _ in section["letters"]
        ),
        "warnings": renderer.warnings(),
    }


# ---------------------------------------------------------------------------
# View models
# ---------------------------------------------------------------------------


def _letter_view(letter, renderer):
    """One letter, as a page needs it: no parser shapes past this point."""
    sender = letter.get("sender") or {}
    recipient = letter.get("recipient") or {}
    # The edition dates the act of sending; a received date would be a
    # different fact, and b1 records none.
    date = sender.get("date")
    return {
        "id": letter["id"],
        "title": "Brev %s" % letter["id"],
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
        "body": renderer.render(letter["body"], letter["id"]),
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
    """The index's groups, in the order the edition lists them."""
    by_id = {view["id"]: view for view in views}
    placed = set()
    sections = []
    for group in volume.get("groups", []):
        letters = [by_id[letter_id] for letter_id in group["letterIds"] if letter_id in by_id]
        placed.update(view["id"] for view in letters)
        if not letters:
            continue
        sections.append(
            {
                "id": group["id"],
                "heading": group["heading"] or "Uden titel",
                "notes": group.get("notes") or [],
                "letters": letters,
            }
        )
    orphans = [view for view in views if view["id"] not in placed]
    if orphans:
        sections.append(
            {
                "id": UNGROUPED_ID,
                "heading": UNGROUPED_HEADING,
                "notes": [],
                "letters": orphans,
            }
        )
    return sections


def _in_letter_order(volume):
    """Letters by number. The numbers are unique across the whole edition."""
    return sorted(volume["letters"], key=_letter_number)


def _letter_number(letter):
    identifier = letter["id"] or ""
    return (0, int(identifier), "") if identifier.isdigit() else (1, 0, identifier)


def _neighbours(views):
    """Yield ``(previous, view, following)`` for prev/next navigation."""
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
    """Copy the stylesheet in. Self-contained output: nothing is fetched."""
    target = os.path.join(out_dir, "assets")
    os.makedirs(target, exist_ok=True)
    for name in sorted(os.listdir(STATIC_DIRECTORY)):
        shutil.copyfile(os.path.join(STATIC_DIRECTORY, name), os.path.join(target, name))
