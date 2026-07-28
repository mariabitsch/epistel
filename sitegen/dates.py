"""Parser date dicts -> Danish date strings that never claim too much.

The edition knows some letters to the day, some to the month, some only to the
year, and some only within a span of years. The parser preserves that in
``precision`` and ``notAfter`` (see ``pipeline.parse_tei``); this module is
where it becomes something a reader sees:

    ``18290308``              -> "8. marts 1829"
    ``18481200``              -> "december 1848"
    ``18370000``              -> "1837"
    ``18460000``/``18470000`` -> "1846–47"
    no date at all            -> "udateret"

Zero-padded parts of a date are never shown, and a date is never rounded up
into a precision the edition did not claim.

``span()`` says the same thing in days rather than words: the first and last
day a letter could have been written, which is what a timeline needs to draw a
mark no narrower than the edition's certainty.
"""

import calendar
import datetime

MONTHS = [
    None,
    "januar",
    "februar",
    "marts",
    "april",
    "maj",
    "juni",
    "juli",
    "august",
    "september",
    "oktober",
    "november",
    "december",
]

UNDATED = "udateret"

EN_DASH = "–"

# How the edition says it arrived at a date (@source on <date>), in Danish.
SOURCES = {
    "stamp": "dateret efter poststempel",
    "supplied": "redaktionelt dateret",
    "suppliedYear": "årstal redaktionelt bestemt",
}


def format_date(date):
    """Format a date dict for reading. Never returns an empty string."""
    if not date:
        return UNDATED

    start = date if date.get("precision") else date.get("notBefore")
    end = date.get("notAfter")

    if not _is_readable(start):
        if _is_readable(end):
            return _point(end)
        if date.get("raw"):
            # A date string the parser could not read: show it as the source
            # wrote it rather than guess at what it meant.
            return "%s [kildens datering: %s]" % (UNDATED, date["raw"])
        return UNDATED

    if _is_readable(end) and _parts(end) != _parts(start):
        return _range(start, end)
    return _point(start)


def provenance(date):
    """Bracketed note about *how* the edition dated the letter, or None."""
    source = (date or {}).get("source")
    if not source:
        return None
    return "[%s]" % SOURCES.get(source, "dateret efter kilden: %s" % source)


def machine_value(date):
    """The ``datetime`` attribute value, or None when there is no single point.

    A range has no single machine-readable value, and HTML's ``<time>`` must
    not be given one it cannot mean.
    """
    if not date or not date.get("iso"):
        return None
    end = date.get("notAfter")
    if _is_readable(end) and _parts(end) != _parts(date):
        return None
    return date["iso"]


def span(date):
    """The stretch of days a date could mean, or None when there is no date.

    Returns ``{"start", "end", "precision", "open_end"}`` -- two
    ``datetime.date`` objects, the precision of the *lower* bound, and whether
    the edition wrote an upper bound the parser could not read.

    A month becomes its whole month and a year its whole year, because that is
    all the edition claims; ``notAfter`` extends the far end. One letter in b43
    carries ``notAfter="1847000"`` -- seven digits, unreadable. Guessing 1847
    would put a date in the edition's mouth, so the span stays inside the year
    that *is* readable and ``open_end`` tells the display to say the rest.
    """
    if not date:
        return None

    lower = date if date.get("precision") else date.get("notBefore")
    upper = date.get("notAfter")
    start = _first_day(lower)
    if start is None:
        # Only the upper bound is readable: it is the one thing we know.
        lower, upper = upper, None
        start = _first_day(lower)
        if start is None:
            return None

    end = _last_day(upper) or _last_day(lower)
    if end < start:
        # An upper bound before the lower one is a defect in the source, not
        # a span; keep the lower bound and let it stand alone.
        end = _last_day(lower)
    unreadable = upper.get("raw") if upper and not upper.get("precision") else None
    return {
        "start": start,
        "end": end,
        "precision": lower["precision"],
        "open_end": bool(unreadable),
        # What the edition wrote where the upper bound should be. Kept so the
        # page can quote it rather than quietly drop a fact it cannot use.
        "open_end_raw": unreadable,
    }


def _first_day(value):
    if not _is_readable(value):
        return None
    return datetime.date(value["year"], value.get("month") or 1, value.get("day") or 1)


def _last_day(value):
    if not _is_readable(value):
        return None
    precision = value["precision"]
    if precision == "day":
        return datetime.date(value["year"], value["month"], value["day"])
    if precision == "month":
        last = calendar.monthrange(value["year"], value["month"])[1]
        return datetime.date(value["year"], value["month"], last)
    return datetime.date(value["year"], 12, 31)


def year_of(date):
    """The year a letter sorts and filters by, or None."""
    if not date:
        return None
    return date.get("year") or (date.get("notBefore") or {}).get("year")


def _is_readable(value):
    return bool(value) and bool(value.get("precision"))


def _parts(value):
    return (value.get("year"), value.get("month"), value.get("day"))


def _point(value):
    precision = value["precision"]
    if precision == "day":
        return "%d. %s %d" % (value["day"], MONTHS[value["month"]], value["year"])
    if precision == "month":
        return "%s %d" % (MONTHS[value["month"]], value["year"])
    return "%d" % value["year"]


def _range(start, end):
    """Format two endpoints as one span, without repeating what they share."""
    if start["year"] != end["year"]:
        if start["precision"] == end["precision"] == "year":
            if start["year"] // 100 == end["year"] // 100:
                # Same century: "1846–47" reads better than "1846–1847".
                return "%d%s%02d" % (start["year"], EN_DASH, end["year"] % 100)
            return "%d%s%d" % (start["year"], EN_DASH, end["year"])
        return _spanned(_point(start), _point(end))

    if start["precision"] == end["precision"] == "day":
        if start["month"] == end["month"]:
            return "%d.%s%d. %s %d" % (
                start["day"],
                EN_DASH,
                end["day"],
                MONTHS[start["month"]],
                start["year"],
            )
        return _spanned(
            "%d. %s" % (start["day"], MONTHS[start["month"]]),
            "%d. %s %d" % (end["day"], MONTHS[end["month"]], end["year"]),
        )

    if start["precision"] == end["precision"] == "month":
        return _spanned(MONTHS[start["month"]], "%s %d" % (MONTHS[end["month"]], end["year"]))

    return _spanned(_point(start), _point(end))


def _spanned(start, end):
    return "%s %s %s" % (start, EN_DASH, end)
