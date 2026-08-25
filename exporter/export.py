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
# number is what a release tag promises. 0.2.0: the schemas joined the
# export (schema/ + the manifest's "schemas" field) — additive.
SCHEMA_VERSION = "0.2.0"

# SPDX identifiers. The vendor-derived layers inherit the edition's CC0.
CC0 = "CC0-1.0"

# The edition's language; letters in other languages would override this
# per envelope (none in this corpus do).
LANGUAGE = "da"

# The curated editorial datasets (see pipeline.context), copied verbatim:
# their _meta blocks, source citations and recorded disagreements are the
# product. Maps file stem -> the key holding the entry list, for the
# manifest's counts.
CONTEXT_FILES = {
    "publications": "publications",
    "residences": "residences",
    "summaries": "summaries",
    "bios": "bios",
    "bio_keys": "bridges",
    "aliases": "aliases",
}

# The editorial layer has an author and, as yet, no chosen license. The
# manifest says so honestly; claiming CC0 here would be a false grant.
PENDING_LICENSE_NOTE = (
    "License pending: not yet chosen for this curated layer; "
    "all rights reserved until it is."
)


def export_data(volumes, out_dir, provenance=None, context_dir=None, files=None):
    """Write the export. Returns ``{"letters": ..., "volumes": ...,
    "context": ...}``.

    ``volumes`` is ``pipeline.corpus.parse_corpus`` output; ``provenance`` is
    ``pipeline.provenance.load_provenance`` output and may be ``None``, in
    which case the manifest honestly records no source pin. ``context_dir``
    points at the curated datasets; ``None``, or a directory holding none of
    them, yields a smaller but complete export -- each editorial layer is
    disposable on its own, exactly as it is for the site build. ``files`` is
    ``pipeline.provenance.load_file_record`` output: with it, each volume in
    ``volumes.json`` names its source files with upstream path and sha256,
    so the way back to the TEI needs no folder-listing and no convention;
    without it, ``source`` is honestly ``null``.
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

    context_layers = _copy_context(context_dir, out_dir)
    schemas = _copy_schemas(out_dir)

    _write(os.path.join(out_dir, "volumes.json"), _volume_index(volumes, files))
    _write(
        os.path.join(out_dir, "manifest.json"),
        _manifest(volumes, letters, provenance, context_layers, schemas),
    )
    return {
        "letters": letters,
        "volumes": len(volumes),
        "context": sorted(context_layers),
    }


def _copy_context(context_dir, out_dir):
    """Copy the curated files byte for byte; return manifest layer entries."""
    layers = {}
    if not context_dir or not os.path.isdir(context_dir):
        return layers
    for name, entries_key in CONTEXT_FILES.items():
        source = os.path.join(context_dir, name + ".json")
        if not os.path.isfile(source):
            continue
        with open(source, encoding="utf-8") as file:
            entries = json.load(file).get(entries_key)
        if not isinstance(entries, list):
            raise ValueError("%s holds no %s" % (source, entries_key))
        os.makedirs(os.path.join(out_dir, "context"), exist_ok=True)
        shutil.copyfile(source, os.path.join(out_dir, "context", name + ".json"))
        layers[name] = {
            "path": "context/%s.json" % name,
            "count": len(entries),
            "license": None,
            "licenseNote": PENDING_LICENSE_NOTE,
        }
    return layers


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


def _volume_index(volumes, files):
    """Titles, groups, document order and source files; warnings stay put."""
    return {
        "volumes": [
            {
                "volume": volume["volume"],
                "title": volume["title"],
                "shortTitle": volume["shortTitle"],
                "source": _volume_source(volume["volume"], files),
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


def _volume_source(volume_name, files):
    """The volume's source files from the provenance record, or ``None``.

    Filed by basename (``txt.xml``, ``kom.xml``): the reader learns what
    exists -- the commentary file included, which the export does not
    otherwise use -- without listing any folder.
    """
    if not files:
        return None
    prefix = volume_name + "/"
    source = {
        local[len(prefix):]: entry
        for local, entry in files.items()
        if local.startswith(prefix)
    }
    return source or None


def _copy_schemas(out_dir):
    """Publish the JSON Schemas (draft-07) with the data they describe.

    The source of truth is ``exporter/schemas/``; the copies land in
    ``schema/`` and the manifest points at them, so a consumer holds data
    and contract in the same download. Returns ``{name: relative path}``.
    """
    source_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "schemas")
    schema_dir = os.path.join(out_dir, "schema")
    os.makedirs(schema_dir)
    schemas = {}
    for name in sorted(os.listdir(source_dir)):
        if not name.endswith(".schema.json"):
            continue
        shutil.copyfile(
            os.path.join(source_dir, name), os.path.join(schema_dir, name)
        )
        schemas[name[: -len(".schema.json")]] = "schema/%s" % name
    return schemas


def _manifest(volumes, letters, provenance, context_layers, schemas):
    layers = {
        "letters": {"path": "letters/", "count": letters, "license": CC0},
        "volumes": {
            "path": "volumes.json",
            "count": len(volumes),
            "license": CC0,
        },
    }
    layers.update(sorted(context_layers.items()))
    return {
        "schemaVersion": SCHEMA_VERSION,
        "language": LANGUAGE,
        "source": provenance,
        "layers": layers,
        "schemas": schemas,
    }


def _write(path, data):
    with open(path, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=1)
        file.write("\n")
