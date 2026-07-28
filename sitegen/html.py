"""Escaping and element assembly.

Every piece of text that reaches a page goes through ``text()`` and every
attribute value through ``attributes()``. The letters are 19th century Danish
prose, so ampersands and angle brackets do turn up in the source; nothing may
be interpolated into HTML raw.
"""

import html as _html
import re

# CSS class names are derived from TEI attribute values (``rendition="#ind"``),
# so they are filtered down to characters that are valid in an identifier.
_CLASS_TOKEN = re.compile(r"[^A-Za-z0-9_-]+")

# Elements written without a closing tag.
VOID_ELEMENTS = frozenset(["br", "hr", "img", "input", "link", "meta"])


def text(value):
    """Escape text content. Quotes are left alone: they read better."""
    if value is None:
        return ""
    return _html.escape(str(value), quote=False)


def attributes(pairs):
    """Render an attribute mapping, skipping the ones whose value is None.

    ``{"class": "tei-p", "id": None}`` -> ``' class="tei-p"'``.
    """
    parts = []
    for name, value in pairs.items():
        if value is None or value is False:
            continue
        if value is True:
            parts.append(" %s" % name)
            continue
        parts.append(' %s="%s"' % (name, _html.escape(str(value), quote=True)))
    return "".join(parts)


def element(tag, inner="", **pairs):
    """Build one element. Attribute names come from keyword arguments.

    Python keywords and hyphenated attributes are written with a trailing
    underscore or underscores respectively: ``class_``, ``data_key``. The
    positional arguments are called ``tag`` and ``inner`` so that ``name`` --
    a real HTML attribute -- stays available as a keyword.
    """
    rendered = attributes({_attribute_name(key): value for key, value in pairs.items()})
    if tag in VOID_ELEMENTS:
        return "<%s%s>" % (tag, rendered)
    return "<%s%s>%s</%s>" % (tag, rendered, inner, tag)


def _attribute_name(key):
    return key.rstrip("_").replace("_", "-")


def classes(*names):
    """Join class names, dropping empties. Returns None when nothing is left.

    ``None`` means "no class attribute at all", which ``attributes()`` skips.
    """
    kept = [name for name in names if name]
    return " ".join(kept) or None


def class_token(value):
    """Turn a TEI attribute value into something usable as a class name."""
    return _CLASS_TOKEN.sub("-", str(value).lstrip("#")).strip("-")
