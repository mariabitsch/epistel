"""Which vendored volumes make up the letter corpus, and in what order.

``pipeline.parse_tei`` knows how to read one TEI file. This module knows what
"the corpus" is: the fourteen ``b*`` directories under ``data/vendor``, read in
the order the edition prints them. That order is not a display decision -- it
is how *Søren Kierkegaards Skrifter* numbers its letters -- so it lives here,
next to the parser, rather than in the site generator or the build script.

Volume order
------------

Each directory is named after the first letter number it holds (``b1``,
``b43``, ``b70`` ...), so sorting the names numerically reproduces the
edition's order. Nothing is hard-coded: whatever is vendored is what gets
built, which keeps the list from drifting away from ``data/vendor``.

Inside a volume the letters are kept in document order. That matters, because
the numbering is not quite a sequence to sort by: b127 prints nine drafts as
159.1-159.9 between letters 159 and 160, and b171 prints three cross-reference
stubs with no number at all (``@n="-"``). Document order puts each of them
exactly where the edition does.

The dedications
---------------

``data/vendor/ded`` is vendored but is not a letter volume, so the ``b*``
pattern leaves it out. Its TEI is a different document: dedications sit in
``<div type="dedication">`` inside ``<div type="work">``, grouped by the book
they were written in, and the file contains no ``correspDesc`` at all -- no
sender, no recipient, no correspondence context. Fitting it to the letter
model would mean a second metadata model, a second grouping model and a second
numbering space (its dedications are numbered from 1 again). See the build
brief: "include if cheap, skip if it complicates the model".
"""

import os
import re

from .parse_tei import parse_volume

# A letter volume's directory: "b" followed by its first letter number.
LETTER_VOLUME = re.compile(r"^b(\d+)$")

# The file inside a volume directory that holds the letters themselves.
TEXT_FILE = "txt.xml"


def volume_names(vendor_dir):
    """Vendored letter-volume directory names, in the edition's order."""
    names = [
        name
        for name in os.listdir(vendor_dir)
        if LETTER_VOLUME.match(name)
        and os.path.isfile(os.path.join(vendor_dir, name, TEXT_FILE))
    ]
    return sorted(names, key=_first_letter_number)


def volume_paths(vendor_dir):
    """Full paths to every vendored ``txt.xml``, in the edition's order."""
    return [
        os.path.join(vendor_dir, name, TEXT_FILE) for name in volume_names(vendor_dir)
    ]


def parse_corpus(vendor_dir):
    """Parse every letter volume. Returns a list of ``parse_volume`` results.

    Warnings stay on the volume that produced them, so a build can say which
    file it could not make sense of.
    """
    return [parse_volume(path) for path in volume_paths(vendor_dir)]


def _first_letter_number(name):
    return int(LETTER_VOLUME.match(name).group(1))
