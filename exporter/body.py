"""A letter's body nodes -> a semantic HTML fragment in the export
vocabulary.

The display renderer (``sitegen.tei_html``) decides what a letter looks like
on *this* site: tooltips, links, page-break glyphs, what to skip. This module
is its display-agnostic sibling for the export, and it follows two rules the
display does not:

* **Everything travels.** Nothing is skipped and nothing is dropped: empty
  blocks, pointers, illustrations' file references, witness remarks --
  whatever the parser preserved is in the fragment. Apparatus that is not
  part of the reading text (rejected readings, editorial expansions, witness
  remarks) is emitted with HTML's ``hidden`` attribute: invisible in a bare
  browser, present for any consumer.
* **No display opinions.** HTML elements are used where HTML has the concept
  (``p``, ``table``, ``br``, ``aside``, ``figure``, ``i``, ``sup``);
  everything else is a neutral ``span``/``div``. TEI's own names carry the
  semantics: every element wears ``class="tei-<element>"`` and its TEI
  attributes as ``data-*``, values verbatim. No Danish, no links, no CSS.

The vocabulary is closed and documented in ``docs/export-format.md``;
``tests.test_export_body`` holds fragment and documentation together. An
element this module does not know still renders (as a ``span`` with its
``tei-*`` class and its text), which makes a new upstream element a loud,
failing conformance test rather than a silent gap.
"""

from html import escape

from pipeline.parse_tei import ELEMENT_ATTRIBUTES

# TEI element -> HTML element, where HTML has the concept. Everything not
# named here is a span. ``head`` inside ``figure`` becomes ``figcaption``
# (handled in the walk); ``hi`` upgrades to ``i``/``sup`` when the source's
# rendition says italics or superscript -- HTML-native typography, still
# wearing its class and raw rendition.
TAG_FOR = {
    "div": "div",
    "opener": "div",
    "closer": "div",
    "postscript": "div",
    "trailer": "div",
    "salute": "div",
    "signed": "div",
    "dateline": "div",
    "lg": "div",
    "p": "p",
    "table": "table",
    "row": "tr",
    "cell": "td",
    "note": "aside",
    "figure": "figure",
}

# Table spans are an HTML concept: emitted as real colspan/rowspan so the
# grid renders as the source lays it out.
_CELL_SPANS = {"cols": "colspan", "rows": "rowspan"}


def render_body(nodes):
    """Render a letter's body nodes to a fragment string."""
    return "".join(_node(node) for node in nodes)


def _node(node, tag_override=None, hidden=False):
    if "text" in node:
        return escape(node["text"], quote=False)

    type_ = node.get("type")
    if type_ == "lb":
        return "<br>"
    if type_ == "app":
        return _apparatus(node, node.get("variants", ()))
    if type_ == "choice":
        return _apparatus(node, node.get("alternatives", ()))
    if type_ == "witDetail":
        # The parser keeps the remark in ``note``; apparatus, so hidden.
        return _element("span", node, escape(node.get("note") or "", quote=False),
                        hidden=True)

    inner = "".join(
        _node(child, tag_override="figcaption")
        if type_ == "figure" and child.get("type") == "head"
        else _node(child)
        for child in node.get("content", [])
    )
    return _element(_tag(node, tag_override), node, inner, hidden=hidden)


def _apparatus(node, aside):
    """``app``/``choice``: the reading text in the flow, the rest hidden."""
    reading = "".join(_node(child) for child in node.get("content", []))
    rest = "".join(_node(child, hidden=True) for child in aside)
    return _element("span", node, reading + rest)


def _tag(node, override):
    if override:
        return override
    type_ = node.get("type")
    if type_ == "hi":
        renditions = (node.get("rendition") or "").split()
        if "#sup" in renditions:
            return "sup"
        if "#ita" in renditions:
            return "i"
    return TAG_FOR.get(type_, "span")


def _element(tag, node, inner, hidden=False):
    type_ = node.get("type")
    parts = ['<%s class="tei-%s"' % (tag, escape(type_, quote=True))]
    if hidden:
        parts.append(" hidden")
    for name in ELEMENT_ATTRIBUTES.get(type_, ()):
        # The parser renames TEI's @type to "subtype" so the node's own
        # "type" can hold the element name; on the way out it is data-type
        # again, because the fragment speaks TEI.
        key = "subtype" if name == "type" else name
        value = node.get(key)
        if value is None:
            continue
        if type_ == "cell" and name in _CELL_SPANS:
            attribute = _CELL_SPANS[name]
        else:
            attribute = "data-%s" % name.lower()
        parts.append(' %s="%s"' % (attribute, escape(str(value), quote=True)))
    parts.append(">%s</%s>" % (inner, tag))
    return "".join(parts)
