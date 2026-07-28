"""A letter's body node tree -> HTML.

The parser hands over a tree of nodes, each with a ``type`` (the TEI element
name) and a ``content`` list. This module walks that tree and decides what each
node looks like on a page. It knows nothing about files or layout: it returns a
string of HTML for a list of nodes.

The rules it follows:

* Nothing that carries text is ever dropped. Elements this renderer does not
  model still get their text rendered, and are reported in ``warnings()`` so
  the build can say out loud what it did not understand.
* Apparatus is not part of the reading text. The parser keeps rejected
  readings and editorial expansions outside ``content``; this renderer simply
  never looks at them, and skips ``witDetail`` (a remark about the manuscript)
  entirely. A later slice can surface both -- the data is still there.
* TEI attributes that carry meaning survive as class names and ``data-``
  attributes (``rendition="#ind"`` -> ``r-ind``, ``persName/@key`` ->
  ``data-key``), so a design has something to work with without touching this
  file.
* The only address this renderer knows is the one it is handed: a named
  person becomes a link when ``person_href`` returns one for their key, and a
  span when it does not. No other element links anywhere.
"""

from .html import class_token, classes, element, text

# Wrappers whose content is already the reading text: render straight through.
TRANSPARENT = frozenset(["app", "lem", "choice", "abbr"])

# Elements that render to nothing, because they hold no text at all -- they
# are editorial apparatus, or markers pointing at material this site does not
# reproduce:
#
#   witDetail   a remark about the manuscript ("ms. beskadiget"); the parser
#               already keeps it out of ``content`` and in ``note``
#   witStart/   the start and end of a witness's coverage
#   witEnd
#   graphic     an illustration file, not shipped
#   figDesc     a description of that illustration (empty in this corpus)
#   ptr         a pointer to an illustration, or to a footnote printed
#               elsewhere on the page
#   milestone   a pointer into the entry numbering of another edition
#               (@edRef="#BogA", Kierkegaard's *Breve og Aktstykker*), or an
#               ellipsis marker inside the apparatus
#
# Dropping markup is only safe while it stays empty, so the claim is tested
# against every letter in the corpus rather than assumed -- see
# ``tests.test_sitegen.SkippedMarkupCarriesNoTextTest``.
SKIPPED = frozenset(
    [
        "witDetail",
        "witStart",
        "witEnd",
        "graphic",
        "figDesc",
        "ptr",
        "milestone",
    ]
)

# TEI element -> (HTML element, base class). Prose blocks: an empty one is
# dropped, because the source uses them for blank space and flourishes.
BLOCKS = {
    "div": ("div", "tei-div"),
    "p": ("p", "tei-p"),
    "opener": ("div", "tei-opener"),
    "closer": ("div", "tei-closer"),
    "postscript": ("div", "tei-postscript"),
    "trailer": ("div", "tei-trailer"),
    "salute": ("div", "tei-salute"),
    "signed": ("div", "tei-signed"),
    "dateline": ("div", "tei-dateline"),
    "lg": ("div", "tei-lg"),
    # A verse or address line. A span (styled as a block) so it stays legal
    # inside every container the edition puts it in.
    "l": ("span", "tei-l"),
    "head": ("h3", "tei-head"),
}

# Layout tables -- envelope addresses, not data -- so they are hidden from
# assistive technology, and empty cells are kept to preserve the grid.
TABLE_ELEMENTS = {
    "table": ("table", "tei-table"),
    "row": ("tr", "tei-row"),
    "cell": ("td", "tei-cell"),
}

# TEI element -> (base class, TEI attribute -> HTML data attribute).
INLINE = {
    "seg": ("tei-seg", {}),
    "persName": ("tei-persName", {"key": "data-key"}),
    "placeName": ("tei-placeName", {"key": "data-key"}),
    "name": ("tei-name", {"key": "data-key"}),
    "rs": ("tei-rs", {"key": "data-key"}),
    # Commentary lives in kom.xml, which this site does not ship yet, so a
    # reference renders as plain text with its target kept for later.
    "ref": ("tei-ref", {"target": "data-target"}),
    "date": ("tei-date", {"when": "data-when"}),
    # A number the edition sets as a formula -- always a date written as a
    # fraction ("16/5 44"), of which the TEI keeps only the digits. Rendered
    # as the digits it holds; reconstructing the fraction would be a guess.
    "formula": ("tei-formula", {"notation": "data-notation"}),
    "supplied": ("tei-supplied", {}),
    "unclear": ("tei-unclear", {}),
    "corr": ("tei-corr", {}),
    "sic": ("tei-sic", {}),
    "add": ("tei-add", {}),
    "del": ("tei-del", {}),
}

# What a text-critical mark means, said where the reader's pointer is.
# The letter page's Tegnforklaring says the same in visible words (see
# ``pages._mark_legend``); a hover should not know less than the page.
MARK_TITLES = {
    "supplied": "Udfyldt af udgiverne",
    "unclear": "Usikker læsning i kilden",
    "corr": "Rettet af udgiverne",
    "add": "Tilføjet i kilden, typisk over linjen",
}

# The edition's own words for #lat: "Latin hand, in SKS rendered
# sans-serif". The letters are otherwise in the Gothic hand.
LATIN_HAND_TITLE = "Latinsk hånd, hvor brevet ellers er gotisk"


class BodyRenderer:
    """Renders letter bodies and remembers what it could not model.

    One renderer can render many letters; the warnings accumulate across all
    of them so a build can report once, per element type.

    ``person_href`` is optional and is the only thing the renderer knows about
    the rest of the site: given a ``persName/@key``, it returns the address of
    that person's page, or ``None``. Without it -- a build with no person
    pages -- named people render exactly as they did before, as spans. The
    renderer never builds a URL itself.
    """

    def __init__(self, person_href=None):
        self._unhandled = {}
        self._letter_id = None
        self._person_href = person_href

    def render(self, nodes, letter_id=None):
        """Render a list of nodes. ``letter_id`` only improves warnings."""
        if letter_id is not None:
            self._letter_id = letter_id
        return "".join(self._node(node) for node in nodes)

    def warnings(self):
        """One entry per unmodelled element type, in alphabetical order."""
        return [self._unhandled[tag] for tag in sorted(self._unhandled)]

    # ------------------------------------------------------------------
    # The walk
    # ------------------------------------------------------------------

    def _node(self, node):
        if "text" in node:
            return text(node["text"])

        type_ = node.get("type")
        if type_ in SKIPPED:
            return ""
        if type_ in TRANSPARENT:
            return self._children(node)
        if type_ == "lb":
            return "<br>"
        if type_ == "pb":
            return self._page_break(node)
        if type_ == "figure":
            return self._figure(node)
        if type_ == "hi":
            return self._highlight(node)
        if type_ == "ref":
            return self._reference(node)
        if type_ == "note":
            return self._note(node)
        if type_ == "persName":
            return self._person(node)
        if type_ in BLOCKS:
            return self._block(node)
        if type_ in TABLE_ELEMENTS:
            return self._table_part(node)
        if type_ in INLINE:
            return self._inline(node)
        return self._unmodelled(node)

    def _children(self, node):
        return self.render(node.get("content", []))

    # ------------------------------------------------------------------
    # Node kinds
    # ------------------------------------------------------------------

    def _block(self, node):
        html_element, base = BLOCKS[node["type"]]
        inner = self._children(node)
        if not inner.strip():
            # Blank verso pages, decoration rules, empty openers: the source
            # uses empty blocks for space on the paper. No text is lost.
            return ""
        return element(html_element, inner, class_=self._classes(node, base))

    def _table_part(self, node):
        html_element, base = TABLE_ELEMENTS[node["type"]]
        presentation = "presentation" if node["type"] == "table" else None
        return element(
            html_element,
            self._children(node),
            class_=self._classes(node, base),
            role=presentation,
        )

    def _inline(self, node):
        base, data_attributes = INLINE[node["type"]]
        pairs = {}
        for source, target in data_attributes.items():
            if node.get(source):
                pairs[target.replace("-", "_")] = node[source]
        title = MARK_TITLES.get(node["type"])
        if title:
            pairs["title"] = title
        return element(
            "span", self._children(node), class_=self._classes(node, base), **pairs
        )

    def _person(self, node):
        """A named person: a link to their page when the site has one.

        The link is deliberately not announced. A letter can name thirty-four
        people, and thirty-four coloured, underlined runs would turn a page of
        prose into a speckled field -- so the anchor takes the same ink and
        the same hairline the name already had, and only says it is a link
        when the reader points at it or reaches it with the keyboard. The
        stylesheet carries that; here the tag simply changes.

        One ``persName`` in the corpus carries an empty key, and the edition
        never nests one inside another, so there is no anchor to nest.
        """
        href = self._person_href(node["key"]) if self._person_href and node.get("key") else None
        if not href:
            return self._inline(node)
        return element(
            "a",
            self._children(node),
            class_=self._classes(node, INLINE["persName"][0]),
            href=href,
            data_key=node["key"],
        )

    def _reference(self, node):
        """A pointer into the commentary -- plain text, for now.

        The commentary lives in ``kom.xml``, which this site does not vendor
        yet, so there is nothing to link to. b1 alone has 759 of these; a span
        per reference would put markup with no behaviour between almost every
        other word. Other kinds of reference keep their target.
        """
        if node.get("subtype") == "commentary":
            return self._children(node)
        return self._inline(node)

    def _highlight(self, node):
        """``hi`` -- the source's own emphasis, kept as close as HTML allows."""
        inner = self._children(node)
        renditions = _rendition_tokens(node)
        class_ = self._classes(node, "tei-hi")
        if "sup" in renditions:
            return element("sup", inner, class_=class_)
        if "ita" in renditions:
            return element("em", inner, class_=class_)
        # #und/#dun (under- and double underlining) and #lat (Latin script in
        # a Gothic text) are carried as classes; the stylesheet decides. The
        # hand switch alone gets a tooltip: a face change explains itself to
        # nobody.
        if "lat" in renditions:
            return element("span", inner, class_=class_, title=LATIN_HAND_TITLE)
        return element("span", inner, class_=class_)

    def _page_break(self, node):
        """A small marker for a page or leaf boundary, kept out of the way.

        The edition paginates twice over: the leaves of the manuscript and the
        pages of the printed SKS volume (``@edRef``). The marker looks the
        same either way; the tooltip says which one it is.
        """
        number = node.get("n")
        if node.get("edRef"):
            base = "tei-pb tei-pb--print"
            title = "Sideskift i %s-udgaven" % class_token(node["edRef"])
        else:
            base = "tei-pb tei-pb--manuscript"
            title = "Nyt blad i manuskriptet"
            if node.get("rend") == "supplied":
                title += ", bladnummer tilføjet af udgiverne"
        if number:
            title = "%s: %s" % (title, number)
        return element("span", text("[%s]" % (number or "·")), class_=base, title=title)

    def _note(self, node):
        """A footnote the letter's author wrote, at the foot of the sheet.

        Seven letters in the corpus carry one. It is the writer's own text,
        not editorial apparatus, so it stays on the page -- set apart, the way
        it is set apart on the paper. It holds paragraphs of its own, so it
        cannot be an inline span; ``aside`` says what it is.

        ``@anchored="false"`` (one letter, b234) records that the edition
        found no reference marker for the note in the text. Carried through as
        a data attribute rather than shown, so the fact is not lost.
        """
        inner = self._children(node)
        if not inner.strip():
            return ""
        return element(
            "aside",
            inner,
            class_=self._classes(node, "tei-note"),
            data_anchored=node.get("anchored"),
        )

    def _figure(self, node):
        """Illustrations are not shipped; a caption, if any, still is."""
        caption = None
        for child in node.get("content", []):
            if child.get("type") == "head":
                caption = self._children(child)
        if not caption or not caption.strip():
            return ""
        return element(
            "span",
            caption,
            class_="tei-figure-caption",
            title="Billedtekst; illustrationen er ikke gengivet i denne visning",
        )

    def _unmodelled(self, node):
        """Keep the text, remember the tag, tell the build about it."""
        type_ = node.get("type") or "?"
        entry = self._unhandled.setdefault(
            type_, {"tag": type_, "count": 0, "letterId": self._letter_id}
        )
        entry["count"] += 1
        return self._children(node)

    # ------------------------------------------------------------------

    def _classes(self, node, base):
        """Base class plus whatever the TEI attributes say about this node."""
        names = [base]
        if node.get("subtype"):
            names.append("%s--%s" % (base.split()[0], class_token(node["subtype"])))
        if node.get("rend"):
            names.append("rend-%s" % class_token(node["rend"]))
        names.extend("r-%s" % token for token in _rendition_tokens(node))
        return classes(*names)


def _rendition_tokens(node):
    """``rendition="#bag #bundkant"`` -> ``["bag", "bundkant"]``."""
    return [class_token(token) for token in (node.get("rendition") or "").split()]
