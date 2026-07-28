"""The people in the letters: who they are, and which letters they are in.

The edition marks every person it recognises in a letter's text with
``<persName key="Boesen, Emil Ferdinand">``, and names the sender and the
recipient of each letter in ``correspDesc``. Those are two different registers
-- the first normalised, the second written the way the edition's own headings
read ("Boesen, Emil", "SK", "Kierkegaard, P.C.") -- and the TEI joins them
nowhere. ``data/context/aliases.json`` is our curated join between them, and
this module is where it is applied.

What comes out is one view model per person::

    {"key": "Boesen, Emil Ferdinand",   # the edition's own index form
     "name": "Emil Ferdinand Boesen",   # the same name, read as a sentence
     "slug": "boesen-emil-ferdinand",   # ASCII, deterministic, unique
     "bio": "...", "sources": ["b79:b-1804"], "same_as": [...],
     "no_bio_reason": None,
     "sent": [view, ...], "received": [view, ...], "mentioned": [view, ...]}

Three rules the module keeps:

* **A person exists because the TEI says so.** The register is built from
  ``persName/@key`` in the letter bodies, never from the curated files. The
  biographies are an editorial layer laid on top of it, and a person with no
  biography still gets a page -- with their letters, and a line saying the
  commentary had nothing.
* **An unmapped correspondent name is left unmapped.** A letter whose sender
  or recipient could not be joined to a person with confidence appears on
  nobody's list. The alias file records why, form by form.
* **The slug is derived, not chosen.** Same key in, same URL out, on any
  machine, in any build. Collisions are an error rather than a silent
  overwrite -- see ``assign_slugs``.
"""

import re
import unicodedata

# Danish letters that are not a decorated Latin letter but a letter of their
# own, and their conventional two-letter transliterations. Applied before
# Unicode decomposition, which would otherwise turn "ø" into a bare "o" and
# "Bøhme" and "Bohme" into the same URL.
TRANSLITERATIONS = (
    ("æ", "ae"),
    ("ø", "oe"),
    ("å", "aa"),
    ("ä", "ae"),
    ("ö", "oe"),
    ("ü", "ue"),
    ("ß", "ss"),
)

_NOT_SLUG = re.compile(r"[^a-z0-9]+")

# Where æ, ø and å belong in the alphabet: at the end of it, after z, which is
# where a Danish reader looks for them. "}" and "~" sort after "z" in code
# point order, so a plain sort does the right thing once the letters are
# swapped for them.
_COLLATION = {"æ": "}1", "ä": "}1", "ø": "}2", "ö": "}2", "å": "}3"}


def slug(key):
    """The URL segment a person lives at. Deterministic, ASCII, lowercase.

    ``"Kierkegaard, Søren Aabye"`` -> ``"kierkegaard-soeren-aabye"``. Keys
    that hold no letters or digits at all -- the edition has a few
    correspondents signed only with punctuation -- would come out empty, so
    they fall back to ``"person"`` and are disambiguated by ``assign_slugs``.
    """
    value = key.strip().lower()
    for letter, replacement in TRANSLITERATIONS:
        value = value.replace(letter, replacement)
    value = unicodedata.normalize("NFKD", value)
    value = "".join(char for char in value if not unicodedata.combining(char))
    return _NOT_SLUG.sub("-", value).strip("-") or "person"


def assign_slugs(keys):
    """Map every key to a unique slug. Returns ``{key: slug}``.

    Two different people can transliterate to the same string -- the edition
    indexes both "Moltke, O.J." and "Moltke, O. J." would be one example --
    and one of them silently taking the other's page is the kind of bug that
    is only found by a reader. So a repeat is resolved by numbering, in sorted
    key order, which makes the result the same on every machine and every
    build. The corpus currently produces no collisions at all; the numbering
    exists so that the day it does is not the day a page disappears.
    """
    assigned = {}
    taken = {}
    for key in sorted(keys):
        base = slug(key)
        count = taken.get(base, 0) + 1
        taken[base] = count
        assigned[key] = base if count == 1 else "%s-%d" % (base, count)
    return assigned


def sort_key(key):
    """Alphabetical order as a Danish register has it: æ, ø and å after z."""
    folded = key.casefold()
    folded = "".join(_COLLATION.get(char, char) for char in folded)
    folded = unicodedata.normalize("NFKD", folded)
    folded = "".join(char for char in folded if not unicodedata.combining(char))
    return (folded, key)


def initial(key):
    """The letter a person is filed under in the register.

    The first letter of the key, upper-cased, with decorations removed so
    that "Éiríksson" files under E. Æ, Ø and Å keep their own place at the end
    of the alphabet; a key that starts with something else -- a signature like
    "e – e", an initial-only "C.R." -- files under the same character it
    starts with, because inventing a group for it would be a guess about who
    the person was.
    """
    first = key.strip()[:1].upper()
    if first in ("Æ", "Ø", "Å"):
        return first
    stripped = "".join(
        char
        for char in unicodedata.normalize("NFKD", first)
        if not unicodedata.combining(char)
    )
    return stripped or first


def person_keys(nodes):
    """Every ``persName/@key`` in a body tree, in the order they are read.

    Distinct, and in document order rather than sorted: the order a person is
    first named in a letter is a fact about the letter. One ``persName`` in
    the corpus (b127, letter 148) carries ``key=""`` -- an empty key is not a
    person, and it is skipped.
    """
    found = []
    seen = set()

    def walk(items):
        for node in items:
            if "text" in node:
                continue
            if node.get("type") == "persName":
                key = node.get("key")
                if key and key not in seen:
                    seen.add(key)
                    found.append(key)
            walk(node.get("content") or [])

    walk(nodes)
    return found


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


def build_register(views, context=None):
    """Every person the letters name, with their letters. Sorted by key.

    ``views`` are the letter view models from ``sitegen.site``; each one
    carries the persName keys of its body and the keys its sender and
    recipient were joined to. Nothing is looked up in the TEI here -- the
    parser's shapes stop at the view model, and this module works from it.
    """
    context = context or {}
    bios = context.get("bios") or {}
    without = context.get("bios_without") or {}

    keys = set()
    for view in views:
        keys.update(view["person_keys"])
        keys.update(view["sender_keys"])
        keys.update(view["recipient_keys"])

    slugs = assign_slugs(keys)
    people = {
        key: {
            "key": key,
            "name": display_name(key),
            "slug": slugs[key],
            "bio": (bios.get(key) or {}).get("bio"),
            "sources": (bios.get(key) or {}).get("sources") or [],
            "same_as": (bios.get(key) or {}).get("sameAs") or [],
            "no_bio_reason": without.get(key),
            "sent": [],
            "received": [],
            "mentioned": [],
        }
        for key in keys
    }

    for view in views:
        for key in view["sender_keys"]:
            people[key]["sent"].append(view)
        for key in view["recipient_keys"]:
            people[key]["received"].append(view)
        for key in view["person_keys"]:
            people[key]["mentioned"].append(view)

    return [people[key] for key in sorted(keys, key=sort_key)]


def register_groups(register):
    """The register cut into the letter bands a gallery hangs it in."""
    groups = []
    for person in register:
        letter = initial(person["key"])
        if not groups or groups[-1]["letter"] != letter:
            groups.append({"letter": letter, "anchor": _anchor(letter), "people": []})
        groups[-1]["people"].append(person)
    return groups


def _anchor(letter):
    return "bogstav-%s" % (slug(letter) or "andet")
