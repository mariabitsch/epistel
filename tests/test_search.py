"""Filtering and searching: the prebuilt data, and the page that survives without it.

Two things are being defended here. One is that the index the browser is
handed actually finds the letters it claims to -- built from the real corpus,
searched the way the script searches it. The other is that a reader with no
JavaScript loses nothing they can see: the letters are all in the document,
and the controls that would do nothing are not shown.
"""

import json
import os
import re
import tempfile
import unittest

from pipeline.context import load_context
from pipeline.corpus import parse_corpus
from sitegen import search
from sitegen.site import build_site

from .test_sitegen import hashed_asset, read_hashed

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VENDOR = os.path.join(ROOT, "data", "vendor")
CONTEXT = os.path.join(ROOT, "data", "context")

LETTERS = 336

# The whole corpus is a few megabytes of prose, and the index has to stay a
# download a reader would not notice. A ceiling, not a target: if the corpus
# grows past it, the shape of the index is the thing to reconsider, not the
# number.
INDEX_LIMIT = 600 * 1024


class FoldingTest(unittest.TestCase):
    """The one rule both halves of the search have to agree on."""

    def test_danish_letters_are_spelled_out(self):
        self.assertEqual("soeren", search.fold("Søren"))
        self.assertEqual("kjaerlighed", search.fold("Kjærlighed"))
        self.assertEqual("aaret", search.fold("Året"))

    def test_decorations_are_dropped(self):
        self.assertEqual("heloise", search.fold("Héloïse"))

    def test_tokens_skip_punctuation_and_single_letters(self):
        self.assertEqual({"jeg", "er", "til"}, search.tokens("Jeg er — a — til!"))

    def test_the_script_folds_the_same_way(self):
        """A drift between the two would silently stop finding letters."""
        with open(
            os.path.join(ROOT, "sitegen", "static", "search.js"), encoding="utf-8"
        ) as file:
            script = file.read()
        for letter, replacement in search._FOLDINGS:
            self.assertIn('/%s/g, "%s"' % (letter, replacement), script)


class SearchIndexTest(unittest.TestCase):
    """The index itself, built from the real corpus."""

    @classmethod
    def setUpClass(cls):
        cls.context = load_context(CONTEXT)
        cls.volumes = parse_corpus(VENDOR)
        cls.directory = tempfile.TemporaryDirectory()
        cls.result = build_site(cls.volumes, cls.directory.name, context=cls.context)
        cls.script = read_hashed(cls.directory.name, "search-index.js")
        cls.index = json.loads(
            cls.script[len("window.epistelSearchIndex=") :].rstrip().rstrip(";")
        )

    @classmethod
    def tearDownClass(cls):
        cls.directory.cleanup()

    @staticmethod
    def read_from(*parts):
        with open(os.path.join(*parts), encoding="utf-8") as file:
            return file.read()

    def read(self, *parts):
        return self.read_from(self.directory.name, *parts)

    def find(self, word):
        """Every letter slug matching one word, the way the script does it."""
        wanted = search.fold(word)
        positions = set()
        for name, entries in self.index["words"].items():
            if wanted in name:
                positions.update(entries)
        return {self.index["letters"][position] for position in positions}

    def test_the_index_covers_every_letter_exactly_once(self):
        self.assertEqual(LETTERS, len(self.index["letters"]))
        self.assertEqual(LETTERS, len(set(self.index["letters"])))

    def test_every_letter_page_the_index_names_exists(self):
        for slug in self.index["letters"]:
            self.assertTrue(
                os.path.exists(
                    os.path.join(self.directory.name, "brev", slug, "index.html")
                ),
                slug,
            )

    def test_a_word_from_a_known_letter_finds_that_letter(self):
        # Brev 1: the snuff box, and the professor in one slipper and one boot.
        self.assertEqual({"1"}, self.find("snustobaksdåse"))
        self.assertIn("1", self.find("Tøffel"))

    def test_the_summaries_are_searchable_too(self):
        """"afskedsgave" is Maria Notabene's word for brev 1, not the letter's own.

        The letter says a snuff box was given "til Afsked"; she calls it a
        farewell gift. A reader typing the modern word should still land on
        the letter, which is the whole reason the summaries are indexed.
        """
        letter = [
            view
            for volume in self.volumes
            for view in volume["letters"]
            if view["id"] == "1"
        ][0]
        self.assertNotIn("afskedsgave", search.fold(_plain(letter)))
        self.assertEqual({"1"}, self.find("afskedsgave"))

    def test_searching_is_insensitive_to_case_and_to_danish_spelling(self):
        self.assertEqual(self.find("SØREN"), self.find("soeren"))
        self.assertTrue(self.find("soeren"))

    def test_the_index_holds_no_markup(self):
        """Words only: no tags, no attributes, no entities, nothing to escape."""
        for word in self.index["words"]:
            self.assertRegex(word, r"^[0-9a-z]{2,}$")

    def test_the_index_is_small_enough_to_be_worth_downloading(self):
        self.assertLess(len(self.script.encode("utf-8")), INDEX_LIMIT)

    def test_the_index_is_one_assignment_and_nothing_else(self):
        self.assertTrue(self.script.startswith("window.epistelSearchIndex={"))
        self.assertEqual(1, self.script.count(";"))

    def test_the_index_is_deterministic(self):
        with tempfile.TemporaryDirectory() as other:
            build_site(self.volumes, other, context=self.context)
            self.assertEqual(self.script, read_hashed(other, "search-index.js"))

    def test_the_script_and_the_index_both_ship(self):
        for name in ("search.js", "search-index.js"):
            self.assertTrue(
                os.path.exists(hashed_asset(self.directory.name, name)), name
            )

    def test_the_script_fetches_the_index_by_its_hashed_name(self):
        """The lazy fetch must survive the renaming.

        ``search.js`` loads the index by URL at runtime; the build rewrites
        that reference to the hashed name before hashing the script itself,
        so the shipped pair can never drift apart.
        """
        script = read_hashed(self.directory.name, "search.js")
        index_name = os.path.basename(hashed_asset(self.directory.name, "search-index.js"))
        self.assertIn('"assets/%s"' % index_name, script)
        self.assertNotIn('"assets/search-index.js"', script)


class FacetTest(unittest.TestCase):
    """The three filter lists, from the real corpus."""

    @classmethod
    def setUpClass(cls):
        cls.context = load_context(CONTEXT)
        cls.volumes = parse_corpus(VENDOR)
        cls.directory = tempfile.TemporaryDirectory()
        build_site(cls.volumes, cls.directory.name, context=cls.context)
        with open(
            os.path.join(cls.directory.name, "index.html"), encoding="utf-8"
        ) as file:
            cls.index = file.read()

    @classmethod
    def tearDownClass(cls):
        cls.directory.cleanup()

    def options(self, name):
        block = self.index.split('id="finder-%s"' % name, 1)[1].split("</select>", 1)[0]
        return re.findall(r'<option value="([^"]*)">([^<]*)</option>', block)

    def test_every_letter_can_be_reached_by_its_sender_and_its_recipient(self):
        senders = {value for value, _ in self.options("afsender") if value}
        recipients = {value for value, _ in self.options("modtager") if value}
        for match in re.finditer(r'data-sender="([^"]*)" data-recipient="([^"]*)"', self.index):
            sender, recipient = match.group(1), match.group(2)
            self.assertTrue(not sender or sender in senders, sender)
            self.assertTrue(not recipient or recipient in recipients, recipient)

    def test_a_facet_shows_the_name_and_filters_on_the_editions_form(self):
        """The label is for reading, the value is for joining.

        "SK" is spelled out in the dropdown a reader looks at (Maria's
        call, korrektur 2026-07-28), while the option's value stays the
        edition's own correspDesc string -- which is what the rows carry
        in ``data-sender`` and what the script compares. Unfolding the
        label costs the filter nothing;
        ``test_every_letter_can_be_reached_by_its_sender_and_its_recipient``
        is the other half of this promise.
        """
        senders = dict(self.options("afsender"))
        self.assertIn("SK", senders)
        self.assertTrue(senders["SK"].startswith("Søren Kierkegaard ("), senders["SK"])
        self.assertNotIn("SK (", " ".join(senders.values()))
        self.assertIn('data-sender="SK"', self.index)

    def test_a_facet_never_offers_a_choice_that_returns_nothing(self):
        for name in ("afsender", "modtager", "aar"):
            for value, label in self.options(name):
                if not value:
                    continue
                count = int(re.search(r"\((\d+)\)$", label).group(1))
                self.assertEqual(
                    count, self.index.count('data-%s="%s"' % (_field(name), value)), label
                )

    def test_undated_letters_are_a_choice_of_their_own(self):
        years = dict(self.options("aar"))
        self.assertIn("udateret", years)
        self.assertEqual("Udateret (10)", years["udateret"])

    def test_a_letter_dated_only_to_a_span_of_years_is_filed_under_its_first(self):
        # Brev 39: "udateret [1846-47]" -- filed under 1846 and marked as an
        # approximation rather than pinned to a year the edition never gave.
        letter = [
            view
            for volume in self.volumes
            for view in volume["letters"]
            if view["id"] == "39"
        ][0]
        view = _letter_view(letter)
        self.assertEqual((1846, True), search.facet_year(view))
        self.assertEqual("1846", search.letter_filters(view)["year"])

    def test_a_letter_dated_to_the_day_is_not_marked_approximate(self):
        letter = [
            view
            for volume in self.volumes
            for view in volume["letters"]
            if view["id"] == "1"
        ][0]
        self.assertEqual((1829, False), search.facet_year(_letter_view(letter)))

    def test_the_year_list_runs_in_order(self):
        years = [value for value, _ in self.options("aar") if value.isdigit()]
        self.assertEqual(sorted(years), years)


class WithoutScriptTest(unittest.TestCase):
    """What the index page is when no script ever runs."""

    @classmethod
    def setUpClass(cls):
        cls.context = load_context(CONTEXT)
        cls.volumes = parse_corpus(VENDOR)
        cls.directory = tempfile.TemporaryDirectory()
        build_site(cls.volumes, cls.directory.name, context=cls.context)
        with open(
            os.path.join(cls.directory.name, "index.html"), encoding="utf-8"
        ) as file:
            cls.index = file.read()

    @classmethod
    def tearDownClass(cls):
        cls.directory.cleanup()

    def test_the_controls_are_hidden_until_a_script_shows_them(self):
        form = self.index.split("<form", 1)[1].split(">", 1)[0]
        self.assertIn(" hidden", form)
        self.assertIn('class="finder-empty" id="finder-empty" hidden', self.index)

    def test_hidden_really_hides_whatever_the_stylesheet_says(self):
        css = read_hashed(self.directory.name, "site.css")
        self.assertIn("[hidden] { display: none !important; }", css)

    def test_every_letter_is_in_the_document_and_visible(self):
        entries = re.findall(r'<li class="letter-entry"([^>]*)>', self.index)
        self.assertEqual(LETTERS, len(entries))
        for entry in entries:
            self.assertNotIn("hidden", entry)

    def test_the_script_never_blocks_the_page(self):
        script = os.path.basename(hashed_asset(self.directory.name, "search.js"))
        self.assertIn('<script src="assets/%s" defer></script>' % script, self.index)
        self.assertEqual(1, self.index.count("<script"))

    def test_no_other_page_carries_a_script(self):
        for parts in (
            ("brev", "1", "index.html"),
            ("personer", "index.html"),
            ("person", "olsen-regine", "index.html"),
            ("tidslinje", "index.html"),
        ):
            with open(
                os.path.join(self.directory.name, *parts), encoding="utf-8"
            ) as file:
                self.assertNotIn("<script", file.read())

    def test_the_page_never_builds_markup_out_of_data(self):
        script = read_hashed(self.directory.name, "search.js")
        self.assertNotIn("innerHTML", script)
        self.assertNotIn("insertAdjacentHTML", script)
        self.assertNotIn("document.write", script)


def _plain(letter):
    from pipeline.parse_tei import plain_text

    return plain_text(letter["body"])


def _letter_view(letter):
    from sitegen import dates

    sender = letter.get("sender") or {}
    return {
        "span": dates.span(sender.get("date")),
        "sender_raw": sender.get("name"),
        "recipient_raw": (letter.get("recipient") or {}).get("name"),
    }


def _field(name):
    return {"afsender": "sender", "modtager": "recipient", "aar": "year"}[name]


if __name__ == "__main__":
    unittest.main()
