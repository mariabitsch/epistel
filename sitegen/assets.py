"""Fingerprinted assets: content-hashed names, references rewritten to match.

``write_assets(out_dir, search_index)`` puts everything the pages know as
``assets/`` into place -- the stylesheet, the fonts, the search script and
the prebuilt search index -- under names that carry a hash of their own
content: ``site.css`` ships as ``site.3f9a2c1e.css``. References *between*
assets are rewritten to the hashed names before the referring file is
itself hashed (the stylesheet's ``url(fonts/...)`` lines, the search
script's lazy fetch of the index), so a name always covers the exact bytes
shipped. The return value is the manifest the pages render their links
from: logical path -> hashed path, both relative to the site root.

Why names instead of headers alone: the HTML lives at stable URLs and must
revalidate on every visit, but a file whose name states its content can
never change behind its URL, so the host may serve it with a far-future
``Cache-Control`` (netlify.toml declares one for ``/assets/*``, and a test
holds the two sides together). Change an asset and its name changes with
it; every page is rewritten to the new name in the same build, which is
the entire cache-busting story. On a host that sends no such header the
site merely behaves as before -- the output stays host-agnostic.

Files nothing references by URL keep their plain names: the font licences
must remain findable beside the fonts they cover (the OFL asks for the
notice, not for a hash). Dotfiles and developer notes (``README.md``) stay
out of the build, as they always have.

Deterministic like the rest of the build: the hash is the first
``HASH_DIGITS`` hex digits of the content's sha256, so the same input
names -- and writes -- the same files, byte for byte.
"""

import hashlib
import os

STATIC_DIRECTORY = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")

# Eight hex digits: 32 bits of sha256, far beyond collision worries for a
# directory of a dozen files, and short enough to read in a URL.
HASH_DIGITS = 8

# The search index is generated per build, not copied from static/; this is
# the one logical name the script and the build must agree on.
SEARCH_INDEX = "search-index.js"

_EXCLUDED = ("README.md",)


def hashed_name(name, data):
    """``site.css`` plus its bytes -> ``site.3f9a2c1e.css``."""
    digest = hashlib.sha256(data).hexdigest()[:HASH_DIGITS]
    stem, extension = os.path.splitext(name)
    return "%s.%s%s" % (stem, digest, extension)


def write_assets(out_dir, search_index):
    """Write ``<out_dir>/assets`` and return the manifest for the pages.

    ``search_index`` is the prebuilt index script (``search.index_script``);
    everything else comes from ``static/``. Order matters and is handled
    here: fonts before the stylesheet, the index before the search script,
    because a referring file is hashed only after its references are
    rewritten.
    """
    assets_dir = os.path.join(out_dir, "assets")
    fonts_dir = os.path.join(assets_dir, "fonts")
    os.makedirs(fonts_dir, exist_ok=True)

    font_names = {}
    source_fonts = os.path.join(STATIC_DIRECTORY, "fonts")
    for name in sorted(os.listdir(source_fonts)):
        if name.startswith(".") or name in _EXCLUDED:
            continue
        with open(os.path.join(source_fonts, name), "rb") as file:
            data = file.read()
        if name.endswith(".woff2"):
            target = hashed_name(name, data)
            font_names[name] = target
        else:
            target = name  # the licences stay findable by name
        with open(os.path.join(fonts_dir, target), "wb") as file:
            file.write(data)

    index_name = hashed_name(SEARCH_INDEX, search_index.encode("utf-8"))
    _write_text(assets_dir, index_name, search_index)
    manifest = {"assets/%s" % SEARCH_INDEX: "assets/%s" % index_name}

    for name in sorted(os.listdir(STATIC_DIRECTORY)):
        path = os.path.join(STATIC_DIRECTORY, name)
        if name.startswith(".") or name in _EXCLUDED or os.path.isdir(path):
            continue
        with open(path, encoding="utf-8") as file:
            content = file.read()
        if name.endswith(".css"):
            for source_name, target in font_names.items():
                content = content.replace(
                    "fonts/%s" % source_name, "fonts/%s" % target
                )
        if name.endswith(".js"):
            content = content.replace(
                "assets/%s" % SEARCH_INDEX, "assets/%s" % index_name
            )
        target = hashed_name(name, content.encode("utf-8"))
        _write_text(assets_dir, target, content)
        manifest["assets/%s" % name] = "assets/%s" % target
    return manifest


def _write_text(directory, name, content):
    with open(
        os.path.join(directory, name), "w", encoding="utf-8", newline="\n"
    ) as file:
        file.write(content)
