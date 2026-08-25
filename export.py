#!/usr/bin/env python3
"""Write the JSON export: vendored TEI in, ``export/`` out.

    python3 export.py [output directory]

The data-layer counterpart to ``build.py``: same pipeline, but the product is
the corpus itself as typed JSON (see ``exporter.export`` for the format and
its guarantees) rather than this repository's own site. ``export/`` is
committed on purpose -- diffs are the review artifact, and the test suite
holds the committed copy against a fresh run -- so rerun this after any
change to the pipeline or the exporter.

Standard library only, no network, no state; the output directory is
recreated from scratch every time.
"""

import os
import sys

from exporter.export import export_data
from pipeline.corpus import parse_corpus
from pipeline.provenance import load_provenance

ROOT = os.path.dirname(os.path.abspath(__file__))
VENDOR = os.path.join(ROOT, "data", "vendor")


def main(argv):
    out_dir = argv[1] if len(argv) > 1 else os.path.join(ROOT, "export")

    volumes = parse_corpus(VENDOR)
    provenance = load_provenance(VENDOR)
    if provenance is None:
        print(
            "warning: no provenance record in data/vendor: the manifest "
            "will record no source pin"
        )
    else:
        print("export: source pinned to %s" % provenance["commit"])

    result = export_data(volumes, out_dir, provenance=provenance)
    print(
        "export: wrote %d letter envelopes across %d volumes to %s"
        % (result["letters"], result["volumes"], os.path.relpath(out_dir, ROOT))
    )
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
