"""The exported letter bodies: semantic HTML in a closed, documented
vocabulary.

Each letter's transcription is exported as a sidecar HTML fragment next to
its envelope. The vocabulary is the contract (see ``docs/export-format.md``):
HTML elements where HTML has the concept, TEI's own names as ``tei-*``
classes and ``data-*`` attributes where it does not. Apparatus stays *in* the
markup -- rejected readings, expansions and witness remarks carry ``hidden``
-- so the fragment reads as the letter reads in a bare browser while a richer
consumer still has everything.

The two guarantees these tests encode:

* **Nothing is lost, nothing is added**: the visible text of every fragment
  is exactly ``plain_text()`` of the parsed body, and the hidden apparatus
  is present rather than dropped.
* **The vocabulary is closed**: only the tags, classes and attributes the
  documentation names may appear. A new TEI element upstream makes this
  fail, so vocabulary growth is deliberate and documented, never silent.
"""

import os
import re
import shutil
import tempfile
import unittest
from html.parser import HTMLParser

from exporter.export import export_data
from pipeline.corpus import parse_corpus
from pipeline.parse_tei import plain_text
from pipeline.provenance import load_provenance

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VENDOR = os.path.join(ROOT, "data", "vendor")
FORMAT_DOC = os.path.join(ROOT, "docs", "export-format.md")

# The closed vocabulary, duplicated from docs/export-format.md on purpose --
# a change on either side must show up as a failing test, exactly like the
# å/ø/æ folding shared between Python and JS.
ALLOWED_TAGS = {
    "div", "p", "span", "i", "sup", "br",
    "table", "tr", "td", "aside", "figure", "figcaption",
}
ALLOWED_CLASSES = {
    "tei-div", "tei-p", "tei-head", "tei-opener", "tei-closer",
    "tei-postscript", "tei-trailer", "tei-salute", "tei-signed",
    "tei-dateline", "tei-lg", "tei-l", "tei-table", "tei-row", "tei-cell",
    "tei-note", "tei-figure", "tei-figDesc", "tei-graphic", "tei-hi",
    "tei-seg", "tei-persName", "tei-placeName", "tei-name", "tei-rs",
    "tei-ref", "tei-ptr", "tei-date", "tei-formula", "tei-supplied",
    "tei-unclear", "tei-corr", "tei-sic", "tei-add", "tei-del",
    "tei-choice", "tei-abbr", "tei-expan", "tei-app", "tei-lem", "tei-rdg",
    "tei-rdgGrp", "tei-witDetail", "tei-witStart", "tei-witEnd",
    "tei-pb", "tei-milestone",
}
ALLOWED_ATTRIBUTES = {
    "class", "hidden", "colspan", "rowspan",
    "data-anchored", "data-ana", "data-cert", "data-cols", "data-edref",
    "data-facs", "data-from", "data-instant", "data-key", "data-n",
    "data-notafter", "data-notation", "data-notbefore", "data-place",
    "data-reason", "data-rend", "data-rendition", "data-resp", "data-rows",
    "data-sameas", "data-source", "data-spanto", "data-target", "data-to",
    "data-type", "data-unit", "data-url", "data-varseq", "data-when",
    "data-wit",
}


class _Fragment(HTMLParser):
    """Reads a fragment back: visible text, hidden text, tags, classes."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.visible = []
        self.hidden = []
        self.tags = set()
        self.classes = set()
        self.attributes = set()
        self._hidden_depth = 0
        self._stack = []

    def handle_starttag(self, tag, attrs):
        self.tags.add(tag)
        names = dict(attrs)
        self.attributes.update(names)
        for token in (names.get("class") or "").split():
            self.classes.add(token)
        if tag == "br":
            return  # void; never closed
        hidden = "hidden" in names
        if hidden:
            self._hidden_depth += 1
        self._stack.append(hidden)

    def handle_endtag(self, tag):
        if self._stack and self._stack.pop():
            self._hidden_depth -= 1

    def handle_data(self, data):
        (self.hidden if self._hidden_depth else self.visible).append(data)


def _parse(fragment):
    parser = _Fragment()
    parser.feed(fragment)
    parser.close()
    return parser


def _find(nodes, type_, predicate=None):
    for node in nodes:
        if node.get("type") == type_ and (predicate is None or predicate(node)):
            return node
        found = _find(node.get("content", []), type_, predicate)
        if found is not None:
            return found
    return None


class ExportBodyTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.volumes = parse_corpus(VENDOR)
        cls.out = tempfile.mkdtemp(prefix="epistel-export-")
        export_data(cls.volumes, cls.out, provenance=load_provenance(VENDOR))
        cls.fragments = {}
        for volume in cls.volumes:
            for letter in volume["letters"]:
                path = os.path.join(
                    cls.out, "letters", volume["volume"], letter["xmlId"] + ".html"
                )
                with open(path, encoding="utf-8") as file:
                    content = file.read()
                # The file's own trailing newline is file hygiene, not text.
                cls.fragments[(volume["volume"], letter["xmlId"])] = (
                    content[:-1] if content.endswith("\n") else content
                )

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.out)

    def _fragment(self, volume, xml_id):
        return self.fragments[(volume, xml_id)]

    # -- completeness and the envelope link --------------------------------

    def test_every_letter_has_a_body_fragment_and_its_envelope_says_so(self):
        import json

        self.assertEqual(len(self.fragments), 336)
        for (volume, xml_id), fragment in self.fragments.items():
            self.assertTrue(fragment.strip(), "%s/%s is empty" % (volume, xml_id))
            path = os.path.join(self.out, "letters", volume, xml_id + ".json")
            with open(path, encoding="utf-8") as file:
                envelope = json.load(file)
            self.assertEqual(envelope["body"], xml_id + ".html")

    # -- nothing lost, nothing added ---------------------------------------

    def test_visible_text_is_exactly_the_reading_text(self):
        for volume in self.volumes:
            for letter in volume["letters"]:
                parsed = _parse(self._fragment(volume["volume"], letter["xmlId"]))
                self.assertEqual(
                    "".join(parsed.visible),
                    plain_text(letter["body"]),
                    "%s/%s" % (volume["volume"], letter["xmlId"]),
                )

    def test_expansions_are_present_but_hidden(self):
        # b1 letter 1 abbreviates "ell"; the editors expand it to "eller".
        # The fragment shows the abbreviation and carries the expansion.
        volume = self.volumes[0]
        letter = volume["letters"][0]
        choice = _find(letter["body"], "choice", lambda n: n.get("alternatives"))
        self.assertIsNotNone(choice)
        expansion = plain_text(choice["alternatives"])
        parsed = _parse(self._fragment(volume["volume"], letter["xmlId"]))
        self.assertIn(expansion, "".join(parsed.hidden))
        self.assertIn("tei-expan", self._fragment(volume["volume"], letter["xmlId"]))

    def test_rejected_readings_are_present_but_hidden(self):
        for volume in self.volumes:
            for letter in volume["letters"]:
                app = _find(letter["body"], "app", lambda n: n.get("variants"))
                if app is None:
                    continue
                variant_text = plain_text(app["variants"])
                if not variant_text:
                    continue
                parsed = _parse(self._fragment(volume["volume"], letter["xmlId"]))
                self.assertIn(variant_text, "".join(parsed.hidden))
                return
        self.fail("no app with a rejected reading found in the corpus")

    def test_witness_remarks_are_present_but_hidden(self):
        for volume in self.volumes:
            for letter in volume["letters"]:
                detail = _find(letter["body"], "witDetail", lambda n: n.get("note"))
                if detail is None:
                    continue
                parsed = _parse(self._fragment(volume["volume"], letter["xmlId"]))
                self.assertIn(detail["note"], "".join(parsed.hidden))
                return
        self.fail("no witDetail with a remark found in the corpus")

    # -- the closed vocabulary ---------------------------------------------

    def test_the_vocabulary_is_closed(self):
        for key, fragment in self.fragments.items():
            parsed = _parse(fragment)
            self.assertLessEqual(parsed.tags, ALLOWED_TAGS, key)
            self.assertLessEqual(parsed.classes, ALLOWED_CLASSES, key)
            self.assertLessEqual(parsed.attributes, ALLOWED_ATTRIBUTES, key)

    def test_the_format_documentation_names_every_used_class(self):
        with open(FORMAT_DOC, encoding="utf-8") as file:
            documentation = file.read()
        used = set()
        for fragment in self.fragments.values():
            used.update(_parse(fragment).classes)
        for name in sorted(used):
            self.assertIn(name, documentation, "%s is undocumented" % name)

    # -- source facts travelling through ------------------------------------

    def test_person_keys_travel_as_data_attributes(self):
        volume = self.volumes[0]
        for letter in volume["letters"]:
            person = _find(letter["body"], "persName", lambda n: n.get("key"))
            if person is None:
                continue
            fragment = self._fragment(volume["volume"], letter["xmlId"])
            self.assertIn('data-key="%s"' % person["key"], fragment)
            return
        self.fail("no keyed persName found in b1")

    def test_page_breaks_keep_both_pagination_series(self):
        edition, manuscript = None, None
        for volume in self.volumes:
            for letter in volume["letters"]:
                if edition is None:
                    edition = _find(letter["body"], "pb", lambda n: n.get("edRef"))
                    if edition is not None:
                        edition = (volume["volume"], letter["xmlId"], edition)
                if manuscript is None:
                    manuscript = _find(
                        letter["body"], "pb", lambda n: n.get("n") and not n.get("edRef")
                    )
                    if manuscript is not None:
                        manuscript = (volume["volume"], letter["xmlId"], manuscript)
        self.assertIsNotNone(edition)
        self.assertIsNotNone(manuscript)
        fragment = self._fragment(*edition[:2])
        self.assertIn('data-edref="%s"' % edition[2]["edRef"], fragment)
        fragment = self._fragment(*manuscript[:2])
        self.assertIn('data-n="%s"' % manuscript[2]["n"], fragment)

    def test_a_fragment_reads_like_the_letter_in_a_bare_browser(self):
        # The vocabulary's whole point, spot-checked: fragments carry no
        # scripts, no styles, no external references -- just markup and text.
        for fragment in self.fragments.values():
            self.assertNotIn("<script", fragment)
            self.assertNotIn("<style", fragment)
            self.assertNotIn("href=", fragment)
            self.assertNotIn("src=", fragment)


if __name__ == "__main__":
    unittest.main()
