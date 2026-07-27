#!/usr/bin/env python3
"""Build the static site: vendored TEI in, ``dist/`` out.

    python3 build.py [output directory]

This is the whole build, and it is the contract Netlify runs (see
``netlify.toml``). Standard library only, no network, no state: every vendored
letter volume is parsed, the pages are generated, and the output directory is
recreated from scratch every time.

Anything the pipeline or the renderer could not make sense of is printed as a
warning rather than swallowed -- unmodelled TEI elements keep their text on the
page, but the build says which ones they were. Warnings do not fail the build.
"""

import os
import sys

from pipeline.corpus import parse_corpus
from sitegen.site import build_site

ROOT = os.path.dirname(os.path.abspath(__file__))
VENDOR = os.path.join(ROOT, "data", "vendor")


def main(argv):
    out_dir = argv[1] if len(argv) > 1 else os.path.join(ROOT, "dist")

    print("build: parsing %s" % _relative(VENDOR))
    volumes = parse_corpus(VENDOR)
    for volume in volumes:
        for warning in volume["warnings"]:
            print(
                "warning: parser: %s letter %s: <%s>: %s"
                % (
                    volume["volume"],
                    warning["letterId"],
                    warning["tag"],
                    warning["message"],
                )
            )

    result = build_site(volumes, out_dir)
    for warning in result["warnings"]:
        print(
            "warning: renderer: unmodelled TEI element <%s> (%d %s, first seen "
            "in letter %s): text kept, markup not rendered"
            % (
                warning["tag"],
                warning["count"],
                "occurrence" if warning["count"] == 1 else "occurrences",
                warning["letterId"],
            )
        )
    if result["ungrouped"]:
        print(
            "warning: %d letters belong to no correspondence group"
            % result["ungrouped"]
        )

    for volume in volumes:
        print(
            "build: %-5s %-46s %3d breve"
            % (volume["volume"], volume["title"], len(volume["letters"]))
        )
    print(
        "build: %d letters in %d correspondence groups across %d volumes"
        % (result["letters"], result["sections"], result["volumes"])
    )
    print("build: wrote %d pages to %s" % (result["letters"] + 1, _relative(out_dir)))
    return 0


def _relative(path):
    return os.path.relpath(path, ROOT)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
