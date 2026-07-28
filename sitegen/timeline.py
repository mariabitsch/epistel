"""One life on one linear scale: the timeline page's view model.

The page shows three bodies of data against the same vertical axis --

* the letters, from the edition's TEI (``pipeline.corpus``),
* the books, from the curated ``publications`` dataset,
* the addresses, from the curated ``residences`` dataset,

-- and its whole design problem is that they know their dates to very
different degrees. This module is where that is turned into geometry, and it
holds to two rules.

**A mark is as wide as the doubt.** A letter dated to the day is a line; one
dated to a month is a box the height of that month; one dated only to a year
is not placed on the day scale at all, because it has no place there. Those go
into the year's ``vague`` group, which the page draws as a set apart, marked
"ca.". Nothing is nudged to a plausible day to make the picture tidier.

**The scale is one year, everywhere.** Every position is a fraction of the year
it belongs to, and every year gets the same height on the page, so the four
years without a single letter or book take up exactly as much room as the four
that hold half the authorship. The one exception is that a year *stretches*
when its publications need more room than the scale gives them -- it never
shrinks, and no year is ever compressed to make space for another.

Coordinates are fractions of a year (0 at 1 January, 1 at 31 December) and the
stylesheet multiplies them by one height token. The only pixel numbers here are
``YEAR_HEIGHT_PX`` and ``CELL_HIT_PX``, which exist so that the slot layout
below can reason about how small a mark may get; they must agree with
``--tl-year`` and ``--tl-hit`` in ``static/site.css``.
"""

import datetime

from . import dates

# The height of one year on the page, and the smallest clickable height of a
# letter mark. Both are also CSS tokens -- see the module docstring.
YEAR_HEIGHT_PX = 176.0
CELL_HIT_PX = 11.0

# Longer than this, and a letter's date is a period rather than a moment: it
# gets no position on the day scale. Two months is the natural cut, because it
# is the widest thing the edition's month ranges ("maj-juni 1844") produce.
VAGUE_DAYS = 62

MIDDLE_DOT = " · "


def timeline_model(letters, context):
    """Build the whole page's view model.

    ``letters`` are letter views (``sitegen.site``): ``slug``, ``title``,
    ``sender``, ``recipient``, ``date_text`` and the ``span`` that
    ``sitegen.dates`` derived from the edition's date. ``context`` is the
    curated editorial layer (``pipeline.context``).
    """
    homes = [_home(entry) for entry in context["residences"]]
    _lay_out_homes(homes)
    works = _work_blocks(context["publications"])
    placed, undated = _split(letters)

    first, last = _extent(placed, works, homes)
    years = {
        year: {"year": year, "letters": [], "vague": [], "works": [], "homes": []}
        for year in range(first, last + 1)
    }

    for mark in placed:
        years[mark["start"].year]["letters" if mark["placed"] else "vague"].append(mark)
    for block in works:
        years[block["date"].year]["works"].append(block)
    for home in homes:
        for segment in _segments(home):
            years[segment["year"]]["homes"].append(segment)

    slots = 1
    home_slots = 1
    for year in years.values():
        year["letters"].sort(key=lambda mark: (mark["top"], mark["slug"]))
        year["vague"].sort(key=lambda mark: (mark["start"], mark["slug"]))
        year["works"].sort(key=lambda block: block["date"])
        _lay_out_works(year["works"], year["year"])
        slots = max(slots, _lay_out_slots(year["letters"]))
        home_slots = max(home_slots, 1 + max(
            (segment["slot"] for segment in year["homes"]), default=0
        ))

    return {
        "first_year": first,
        "last_year": last,
        "slots": slots,
        "home_slots": home_slots,
        "years": [years[year] for year in sorted(years)],
        "undated": undated,
        # The bands again, whole, for the register at the foot of the page:
        # the lane beside the rail has room for an address and a period, not
        # for the sources' disagreements about them.
        "homes": homes,
        "counts": {
            "letters": len(placed) + len(undated),
            "placed": len(placed),
            "undated": len(undated),
            "vague": sum(1 for mark in placed if not mark["placed"]),
            "publications": sum(len(block["entries"]) for block in works),
            "residences": len(homes),
        },
        "meta": context.get("meta") or {},
    }


# ---------------------------------------------------------------------------
# Letters
# ---------------------------------------------------------------------------


def _split(letters):
    """Letters that can be placed in a year, and letters the edition never dated."""
    placed, undated = [], []
    for view in letters:
        stretch = view.get("span")
        if stretch:
            placed.append(_letter_mark(view, stretch))
        else:
            undated.append(
                {
                    "slug": view["slug"],
                    "title": view["title"],
                    "correspondents": _correspondents(view),
                    "date_text": view["date_text"],
                }
            )
    return placed, undated


def _letter_mark(view, stretch):
    """One letter as a mark: where it sits, how wide the doubt is, what it says.

    ``placed`` is the decision the page's two letter groups are built on: a
    letter the edition dates within two months keeps a position on the day
    scale, and one dated to a year or a span of years does not.
    """
    start, end = stretch["start"], stretch["end"]
    days = (end - start).days
    placed = days <= VAGUE_DAYS and start.year == end.year
    top = _fraction(start)
    label = MIDDLE_DOT.join(
        [view["title"], view["date_text"], _correspondents(view)]
    )
    if stretch["open_end_raw"]:
        # The edition wrote an upper bound the parser could not read. Saying
        # so is the only honest thing left to do with it.
        label += MIDDLE_DOT + "kildens øvre grænse »%s« kan ikke læses" % (
            stretch["open_end_raw"]
        )
    return {
        "slug": view["slug"],
        # The edition's own letter number, which is what the "ca." group shows
        # instead of a position: a mark with no place needs a name.
        "number": view.get("number") or "?",
        "label": label,
        "start": start,
        "end": end,
        "placed": placed,
        "kind": "day" if days <= 1 else "span",
        "precision": stretch["precision"],
        "open_end": stretch["open_end"],
        "top": top,
        "height": max(0.0, _fraction(end) - top) if placed else 0.0,
        "slot": 0,
    }


def _correspondents(view):
    return "fra %s til %s" % (view["sender"], view["recipient"])


def _lay_out_slots(marks):
    """Give marks that overlap in time a column each. Returns the columns used.

    A letter dated to a month is a mark the height of that month, and eleven
    letters from May 1849 would otherwise be eleven marks in the same place.
    They are dealt the first free column instead, so the year's *width* on the
    page becomes its density -- a quiet year is one column wide, 1849 is
    eighteen. Nothing moves vertically: the time axis is never negotiated.

    Marks are measured with ``CELL_HIT_PX`` of slack, because a mark that is
    half a pixel tall still has to be a target a reader can hit.
    """
    free = []
    for mark in marks:
        top = mark["top"] * YEAR_HEIGHT_PX - CELL_HIT_PX / 2
        bottom = (mark["top"] + mark["height"]) * YEAR_HEIGHT_PX + CELL_HIT_PX / 2
        for column, taken in enumerate(free):
            if taken <= top:
                free[column] = bottom
                mark["slot"] = column
                break
        else:
            mark["slot"] = len(free)
            free.append(bottom)
    return max(len(free), 1)


# ---------------------------------------------------------------------------
# Publications
# ---------------------------------------------------------------------------


def _work_blocks(publications):
    """Group the books by publication day.

    Three titles came out on 16 October 1843 and two on 17 June 1844. Drawing
    them as three marks at the same height would be a stack of overlaps; the
    page draws them as one dated block holding three works, which is also what
    happened. The dataset's order is kept -- it is already chronological, and
    it is not this module's place to re-sort someone's editorial work.
    """
    blocks = []
    for publication in publications:
        date = datetime.date.fromisoformat(publication["date"]["iso"])
        entry = {
            "title": publication["title"],
            "pseudonym": publication["pseudonym"],
            # The dataset's own wording, kept whenever it says more than the
            # block's date does -- several entries cover a run of numbers or a
            # serial ("25. maj - 25. september 1855").
            "period": publication["date"]["raw"],
        }
        if blocks and blocks[-1]["date"] == date:
            blocks[-1]["entries"].append(entry)
            continue
        blocks.append(
            {
                "date": date,
                "date_text": _danish(date),
                "entries": [entry],
                "lead": 0.0,
                "span": 0.0,
            }
        )
    for block in blocks:
        for entry in block["entries"]:
            entry["period"] = (
                entry["period"] if entry["period"] != block["date_text"] else None
            )
    return blocks


def _lay_out_works(blocks, year):
    """Give each block the share of the year that runs until the next one.

    The stylesheet turns ``span`` into a minimum height, so a block reserves
    its own stretch of time and the next one starts where it should. Where the
    text needs more room than the time allows -- 1843 and 1844, six books each
    -- the blocks push each other down and the year grows. That is the one
    place the scale gives, and it gives by stretching, never by squeezing.
    """
    for index, block in enumerate(blocks):
        start = _fraction(block["date"])
        following = blocks[index + 1] if index + 1 < len(blocks) else None
        block["lead"] = start if index == 0 else 0.0
        block["span"] = (_fraction(following["date"]) if following else 1.0) - start


# ---------------------------------------------------------------------------
# Residences
# ---------------------------------------------------------------------------


def _home(entry):
    """One address, as a band with the dataset's own words for its period."""
    start = _boundary(entry["from"])
    end = _boundary(entry["to"])
    return {
        "address": entry["address"],
        "period": "%s – %s" % (entry["from"]["raw"], entry["to"]["raw"]),
        "approx": bool(entry.get("approx")),
        "note": entry.get("note"),
        "modern": entry.get("modernNote"),
        "start": start,
        "end": end,
        "slot": 0,
    }


def _boundary(value):
    """The first day of whatever the dataset names.

    Read the same way at both ends of a band, which is what makes the bands
    meet without overlapping: "til oktober 1844" and "fra oktober 1844" are the
    same move, so both land on 1 October 1844. Where the dataset knows only a
    year -- "efteråret 1837" -- the band begins at the first day of that year
    and is marked uncertain, rather than being moved to a day that would look
    precise and be invented.
    """
    parts = value["iso"].split("-")
    year = int(parts[0])
    month = int(parts[1]) if len(parts) > 1 else 1
    day = int(parts[2]) if len(parts) > 2 else 1
    return datetime.date(year, month, day)


def _segments(home):
    """Cut a band into one piece per year, so each year row can draw its share.

    The pieces know whether they are the band's first or its last, which is how
    the page draws one continuous band down several years: only the true ends
    get an end. The band's end is the first day it no longer covers, so a band
    that runs "til 1838" stops at the bottom of 1837 and adds no empty piece.
    """
    segments = []
    last_year = (home["end"] - datetime.timedelta(days=1)).year
    for year in range(home["start"].year, last_year + 1):
        top = _fraction(max(home["start"], datetime.date(year, 1, 1)))
        bottom = _fraction(home["end"]) if home["end"].year == year else 1.0
        starts = year == home["start"].year
        # He lived at Nytorv for twenty-four years, which is some three
        # thousand pixels of band. Naming it again every tenth year saves a
        # reader who scrolls into the middle of it from scrolling back -- but
        # only where the band runs the whole year, so a repeat can never land
        # on top of the label of a band beginning or ending that year.
        labelled = starts or (not year % 10 and top == 0.0 and bottom >= 1.0)
        segments.append(
            {
                "year": year,
                "address": home["address"],
                "period": home["period"],
                "approx": home["approx"],
                "top": top,
                "height": max(bottom - top, 0.0),
                "starts": starts,
                "labelled": labelled,
                "continued": labelled and not starts,
                "ends": year == last_year,
                "note": home["note"],
                "modern": home["modern"],
                "slot": home["slot"],
            }
        )
    return segments


def _lay_out_homes(homes):
    """Two addresses can overlap -- give the later one its own column.

    They overlap because the sources disagree, not because he lived in two
    places: "efteråret 1837" is a year-wide band, and the house he left on 1
    September 1837 is inside it. Drawing them side by side keeps both claims
    visible instead of choosing one.
    """
    free = []
    for home in sorted(homes, key=lambda home: home["start"]):
        for column, taken in enumerate(free):
            if taken <= home["start"]:
                free[column] = home["end"]
                home["slot"] = column
                break
        else:
            home["slot"] = len(free)
            free.append(home["end"])


# ---------------------------------------------------------------------------
# The scale
# ---------------------------------------------------------------------------


def _fraction(day):
    """Where a day sits in its own year, as 0.0 to 1.0."""
    first = datetime.date(day.year, 1, 1)
    length = (datetime.date(day.year, 12, 31) - first).days + 1
    return (day - first).days / length


def _extent(marks, works, homes):
    """The first and last year anything at all happens in."""
    starts = [mark["start"] for mark in marks] + [home["start"] for home in homes]
    ends = [mark["end"] for mark in marks] + [home["end"] for home in homes]
    starts += [block["date"] for block in works]
    ends += [block["date"] for block in works]
    return min(starts).year, max(ends).year


def _danish(day):
    return "%d. %s %d" % (day.day, dates.MONTHS[day.month], day.year)
