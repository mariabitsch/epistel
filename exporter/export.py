"""Write the corpus as typed JSON: the raw-data layer's public product.

``sitegen`` consumes the pipeline to build this repository's own site. This
module consumes the same pipeline to build ``export/`` -- the same data
offered to *other* displays: letter envelopes, a volume index and a manifest,
in a documented, versioned format. The export makes no display decisions and
repairs nothing; whatever the parser preserves (malformed dates, missing
headings, unnumbered stubs) travels through verbatim.

Layout
------

::

    export/
      manifest.json            schemaVersion, provenance, a license per layer
      volumes.json             volume titles, groups, document order, warnings
      letters/<vol>/<xmlId>.json   one envelope per letter

Letters are filed by volume plus ``xml:id`` -- the only identifier every
letter in the corpus has (three b171 stubs carry no number). The public
letter number travels inside the envelope as ``number``, ``"-"`` included.
Document order is recorded in ``volumes.json``; the envelope files on disk
carry no order of their own.

Envelopes are the **vendor layer only**: raw correspondent names, dates with
their uncertainty intact, no editorial joins. Resolved person keys, summaries
and the other curated datasets are exported as their own collections, so this
one stays buildable -- and honest -- without ``data/context``.

The output is deterministic: same input, byte-identical files, no timestamps.
Provenance is the pinned upstream commit, not a build date. That is what
makes committing ``export/`` meaningful -- diffs are reviewable, and the test
suite can hold the committed copy against a fresh run.
"""

import json
import os
import shutil

from .body import render_body

# Bumped when the shape of the export changes. Consumers pin releases; this
# number is what a release tag promises.
SCHEMA_VERSION = "0.1.0"

# SPDX identifiers. The vendor-derived layers inherit the edition's CC0.
CC0 = "CC0-1.0"

# The edition's language; letters in other languages would override this
# per envelope (none in this corpus do).
LANGUAGE = "da"


def export_data(volumes, out_dir, provenance=None):
    """Write the export. Returns ``{"letters": ..., "volumes": ...}``.

    ``volumes`` is ``pipeline.corpus.parse_corpus`` output; ``provenance`` is
    ``pipeline.provenance.load_provenance`` output and may be ``None``, in
    which case the manifest honestly records no source pin.
    """
    if os.path.isdir(out_dir):
        shutil.rmtree(out_dir)
    os.makedirs(out_dir)

    letters = 0
    for volume in volumes:
        volume_dir = os.path.join(out_dir, "letters", volume["volume"])
        os.makedirs(volume_dir)
        for letter in volume["letters"]:
            _write(
                os.path.join(volume_dir, letter["xmlId"] + ".json"),
                _envelope(volume, letter),
            )
            fragment = render_body(letter["body"])
            with open(
                os.path.join(volume_dir, letter["xmlId"] + ".html"),
                "w",
                encoding="utf-8",
            ) as file:
                file.write(fragment + "\n")
            letters += 1

    _write(os.path.join(out_dir, "volumes.json"), _volume_index(volumes))
    _write(
        os.path.join(out_dir, "manifest.json"),
        _manifest(volumes, letters, provenance),
    )
    return {"letters": letters, "volumes": len(volumes)}


def _envelope(volume, letter):
    """One letter's metadata, exactly as the parser preserved it."""
    return {
        "volume": volume["volume"],
        "xmlId": letter["xmlId"],
        "number": letter["id"],
        "heading": letter["heading"],
        "sender": letter["sender"],
        "recipient": letter["recipient"],
        "context": letter["context"],
        "body": letter["xmlId"] + ".html",
    }


def _volume_index(volumes):
    """Titles, groups and document order; warnings stay on their volume."""
    return {
        "volumes": [
            {
                "volume": volume["volume"],
                "title": volume["title"],
                "shortTitle": volume["shortTitle"],
                "groups": volume["groups"],
                "letters": [
                    {
                        "volume": volume["volume"],
                        "xmlId": letter["xmlId"],
                        "number": letter["id"],
                    }
                    for letter in volume["letters"]
                ],
                "warnings": volume["warnings"],
            }
            for volume in volumes
        ]
    }


def _manifest(volumes, letters, provenance):
    return {
        "schemaVersion": SCHEMA_VERSION,
        "language": LANGUAGE,
        "source": provenance,
        "layers": {
            "letters": {"path": "letters/", "count": letters, "license": CC0},
            "volumes": {
                "path": "volumes.json",
                "count": len(volumes),
                "license": CC0,
            },
        },
    }


def _write(path, data):
    with open(path, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=1)
        file.write("\n")
