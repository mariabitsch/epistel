"""Tests for the display layer.

The parser has its own suite; these cover the two places where the site
generator makes real decisions -- precision-honest Danish dates and the TEI
body renderer -- plus one end-to-end build of the whole site.

The date tests use literal date dicts in the shape documented in
``pipeline.parse_tei``: the display layer must work off that contract, not off
the parser's internals.
"""

import datetime
import os
import re
import tempfile
import unittest

from pipeline.context import load_context
from pipeline.corpus import parse_corpus
from pipeline.parse_tei import parse_volume, plain_text
from sitegen import dates
from sitegen.site import STATIC_DIRECTORY, build_site, display_name, letter_slug
from sitegen.tei_html import BodyRenderer
from sitegen.timeline import timeline_model

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VENDOR = os.path.join(REPO_ROOT, "data", "vendor")
VENDORED_B1 = os.path.join(VENDOR, "b1", "txt.xml")
CONTEXT = os.path.join(REPO_ROOT, "data", "context")


def date(raw, not_after=None, source=None):
    """Build a parser-shaped date dict from ``yyyymmdd`` strings."""
    value = _point(raw)
    value["notBefore"] = None
    value["notAfter"] = _point(not_after) if not_after else None
    value["source"] = source
    value["text"] = None
    return value


def _point(raw):
    year, month, day = int(raw[0:4]), int(raw[4:6]), int(raw[6:8])
    value = {"raw": raw, "year": year, "month": None, "day": None}
    value["iso"] = "%04d" % year
    value["precision"] = "year"
    if month:
        value["month"] = month
        value["iso"] += "-%02d" % month
        value["precision"] = "month"
        if day:
            value["day"] = day
            value["iso"] += "-%02d" % day
            value["precision"] = "day"
    return value


class DateFormattingTest(unittest.TestCase):
    def test_day_precision_reads_as_a_danish_date(self):
        self.assertEqual(dates.format_date(date("18290308")), "8. marts 1829")

    def test_month_precision_names_the_month_only(self):
        self.assertEqual(dates.format_date(date("18481200")), "december 1848")

    def test_year_precision_shows_the_year_only(self):
        self.assertEqual(dates.format_date(date("18370000")), "1837")

    def test_a_missing_date_says_so_in_danish(self):
        self.assertEqual(dates.format_date(None), "udateret")

    def test_zero_padding_never_leaks_into_the_display(self):
        for raw in ("18481200", "18370000"):
            self.assertNotIn("00", dates.format_date(date(raw)))
            self.assertNotIn("-", dates.format_date(date(raw)))

    def test_year_range_within_a_century_is_abbreviated(self):
        self.assertEqual(
            dates.format_date(date("18460000", not_after="18470000")), "1846–47"
        )

    def test_year_range_across_centuries_stays_full(self):
        self.assertEqual(
            dates.format_date(date("17990000", not_after="18010000")),
            "1799–1801",
        )

    def test_two_days_in_one_month_share_month_and_year(self):
        self.assertEqual(
            dates.format_date(date("18430118", not_after="18430119")),
            "18.–19. januar 1843",
        )

    def test_two_days_in_one_year_share_the_year(self):
        self.assertEqual(
            dates.format_date(date("18430205", not_after="18430306")),
            "5. februar – 6. marts 1843",
        )

    def test_a_range_across_years_spells_out_both_ends(self):
        self.assertEqual(
            dates.format_date(date("18460416", not_after="18540416")),
            "16. april 1846 – 16. april 1854",
        )

    def test_an_identical_not_after_is_not_a_range(self):
        self.assertEqual(
            dates.format_date(date("18290308", not_after="18290308")),
            "8. marts 1829",
        )

    def test_editorial_provenance_is_named_when_the_source_says_so(self):
        self.assertEqual(
            dates.provenance(date("18420227", source="stamp")),
            "[dateret efter poststempel]",
        )
        self.assertEqual(
            dates.provenance(date("18481200", source="supplied")),
            "[redaktionelt dateret]",
        )
        self.assertIsNone(dates.provenance(date("18290308")))

    def test_machine_readable_value_only_for_a_single_point_in_time(self):
        self.assertEqual(dates.machine_value(date("18481200")), "1848-12")
        self.assertIsNone(
            dates.machine_value(date("18460000", not_after="18470000"))
        )


class BodyRendererTest(unittest.TestCase):
    def render(self, nodes):
        return BodyRenderer().render(nodes)

    def test_text_is_escaped(self):
        self.assertEqual(
            self.render([{"text": "Fenger & <Broder>"}]),
            "Fenger &amp; &lt;Broder&gt;",
        )

    def test_attribute_values_are_escaped(self):
        html = self.render(
            [
                {
                    "type": "persName",
                    "key": 'Kierkegaard, "P.C."',
                    "sameAs": None,
                    "content": [{"text": "Peter"}],
                }
            ]
        )
        self.assertIn("&quot;", html)
        self.assertNotIn('key="Kierkegaard, "P.C.""', html)

    def test_a_paragraph_becomes_a_paragraph(self):
        html = self.render(
            [{"type": "p", "rend": None, "rendition": "#ind", "content": [{"text": "Hej"}]}]
        )
        self.assertIn("<p", html)
        self.assertIn("Hej", html)

    def test_manuscript_and_print_page_breaks_are_told_apart(self):
        manuscript = self.render(
            [{"type": "pb", "n": "1v", "rend": "supplied", "edRef": None, "facs": None,
              "content": []}]
        )
        printed = self.render(
            [{"type": "pb", "n": "11", "rend": None, "edRef": "#SKS", "facs": None,
              "content": []}]
        )
        self.assertIn("1v", manuscript)
        self.assertIn("11", printed)
        self.assertNotEqual(
            _title_of(manuscript), _title_of(printed), "page markers need different titles"
        )

    def test_apparatus_variants_stay_out_of_the_reading_text(self):
        html = self.render(
            [
                {
                    "type": "app",
                    "content": [
                        {"type": "lem", "wit": None, "varSeq": None,
                         "content": [{"text": "Du"}]}
                    ],
                    "variants": [
                        {"type": "rdg", "wit": None, "varSeq": None,
                         "content": [{"text": "du"}]}
                    ],
                }
            ]
        )
        self.assertIn("Du", html)
        self.assertNotIn(">du<", html)

    def test_a_witness_remark_is_not_part_of_the_letter(self):
        html = self.render(
            [{"type": "witDetail", "wit": "#Ms.", "resp": None, "note": "ms. beskadiget"}]
        )
        self.assertEqual(html, "")

    def test_verse_lines_are_kept_apart(self):
        html = self.render(
            [
                {
                    "type": "lg",
                    "rend": None,
                    "rendition": None,
                    "content": [
                        {"type": "l", "rend": None, "rendition": None,
                         "content": [{"text": "Det er en liden Tid,"}]},
                        {"type": "l", "rend": None, "rendition": None,
                         "content": [{"text": "Saa har jeg vunden,"}]},
                    ],
                }
            ]
        )
        self.assertIn("Det er en liden Tid,", html)
        self.assertIn("Saa har jeg vunden,", html)
        self.assertNotIn("Tid,Saa", html.replace(" ", ""))

    def test_an_unhandled_element_keeps_its_text_and_is_reported(self):
        renderer = BodyRenderer()
        html = renderer.render(
            [{"type": "gizmo", "content": [{"text": "vigtig tekst"}]}]
        )
        self.assertIn("vigtig tekst", html)
        self.assertEqual([w["tag"] for w in renderer.warnings()], ["gizmo"])

    def test_an_authors_footnote_is_set_apart_from_the_letter(self):
        renderer = BodyRenderer()
        html = renderer.render(
            [
                {
                    "type": "note",
                    "subtype": "author",
                    "place": "bottom",
                    "anchored": None,
                    "resp": None,
                    "content": [
                        {"type": "seg", "subtype": "refMarker", "rend": None,
                         "rendition": None, "content": [{"text": "1"}]},
                        {"type": "p", "rend": None, "rendition": None,
                         "content": [{"text": "Anm: snurrigt nok."}]},
                    ],
                }
            ]
        )
        self.assertIn("Anm: snurrigt nok.", html)
        self.assertIn("tei-note", html)
        # A footnote holds paragraphs, so it cannot render as one.
        self.assertNotIn("<p><p", html)
        self.assertEqual([], renderer.warnings())

    def test_a_formula_keeps_its_digits_inline(self):
        renderer = BodyRenderer()
        html = renderer.render(
            [{"type": "formula", "notation": "mathml", "content": [{"text": "165"}]}]
        )
        self.assertIn("165", html)
        self.assertIn("tei-formula", html)
        self.assertEqual([], renderer.warnings())

    def test_pointers_into_other_editions_render_nothing_and_do_not_warn(self):
        """<milestone> and <ptr> are empty markers, not text.

        milestone points into the entry numbering of *Breve og Aktstykker*;
        ptr points at illustration files this site does not ship. Neither
        carries a character of the letter -- see
        ``SkippedMarkupCarriesNoTextTest``, which checks that against the
        whole corpus rather than taking it on trust.
        """
        renderer = BodyRenderer()
        html = renderer.render(
            [
                {"type": "milestone", "unit": "entry", "subtype": None, "n": "65",
                 "edRef": "#BogA", "spanTo": None, "content": []},
                {"type": "ptr", "subtype": "figure", "target": "#ill_3",
                 "content": []},
            ]
        )
        self.assertEqual("", html)
        self.assertEqual([], renderer.warnings())


class SkippedMarkupCarriesNoTextTest(unittest.TestCase):
    """Evidence for every element the renderer is allowed to drop.

    The renderer's one hard rule is that nothing carrying text disappears.
    Five TEI elements render to nothing: they are markers and pointers, not
    words. This test reads the whole corpus and fails the moment one of them
    turns up with a character inside it.
    """

    SILENT = ["milestone", "ptr", "graphic", "witStart", "witEnd", "figDesc"]

    @classmethod
    def setUpClass(cls):
        cls.volumes = parse_corpus(VENDOR)

    def test_the_silent_elements_hold_no_text_anywhere_in_the_corpus(self):
        found = {tag: 0 for tag in self.SILENT}
        for volume in self.volumes:
            for letter in volume["letters"]:
                for tag in self.SILENT:
                    for node in _nodes_of_type(letter["body"], tag):
                        found[tag] += 1
                        self.assertEqual(
                            "",
                            plain_text(node).strip(),
                            "%s/%s: <%s> carries text"
                            % (volume["volume"], letter["id"], tag),
                        )
        # If the edition ever stops using one of these, drop it from the list
        # rather than leaving an untested exemption behind.
        for tag, count in found.items():
            self.assertGreater(count, 0, "<%s> no longer occurs" % tag)


def _nodes_of_type(nodes, wanted):
    found = []
    for node in nodes:
        if node.get("type") == wanted:
            found.append(node)
        for key in ("content", "variants", "alternatives"):
            found.extend(_nodes_of_type(node.get(key, []), wanted))
    return found


def _title_of(html):
    marker = 'title="'
    start = html.index(marker) + len(marker)
    return html[start : html.index('"', start)]


class SiteBuildTest(unittest.TestCase):
    """One end-to-end build of a single volume, checked as a reader would.

    A one-volume build is still a legal build: the display takes whatever
    volumes it is handed. Keeping this case makes sure b1 -- the volume every
    detail of the design was worked out against -- stays exactly as it was.
    """

    @classmethod
    def setUpClass(cls):
        cls.volume = parse_volume(VENDORED_B1)
        cls.directory = tempfile.TemporaryDirectory()
        cls.result = build_site([cls.volume], cls.directory.name)

    @classmethod
    def tearDownClass(cls):
        cls.directory.cleanup()

    def read(self, *parts):
        with open(os.path.join(self.directory.name, *parts), encoding="utf-8") as file:
            return file.read()

    def test_every_letter_gets_a_page(self):
        self.assertEqual(self.result["letters"], 42)
        for number in range(1, 43):
            self.assertTrue(
                os.path.exists(
                    os.path.join(self.directory.name, "brev", str(number), "index.html")
                ),
                "missing page for letter %d" % number,
            )

    def test_the_index_links_every_letter(self):
        index = self.read("index.html")
        for number in range(1, 43):
            self.assertIn('href="brev/%d/"' % number, index)

    def test_the_index_is_grouped_by_correspondence(self):
        index = self.read("index.html")
        self.assertIn("P.C. Kierkegaard", index)
        self.assertIn("Julie Thomsen", index)

    def test_a_letter_page_shows_its_transcription(self):
        self.assertIn("Kjære Broder!", self.read("brev", "1", "index.html"))

    def test_a_letter_page_states_sender_recipient_and_date(self):
        page = self.read("brev", "1", "index.html")
        self.assertIn("Fra", page)
        self.assertIn("Til", page)
        self.assertIn("8. marts 1829", page)

    def test_a_broken_source_heading_is_not_shown_as_the_date(self):
        page = self.read("brev", "39", "index.html")
        self.assertIn("1846–47", page)
        self.assertNotIn("· til familien", page)

    def test_letters_link_to_their_neighbours(self):
        page = self.read("brev", "2", "index.html")
        self.assertIn('href="../1/"', page)
        self.assertIn('href="../3/"', page)

    def test_letters_link_to_the_rest_of_their_correspondence(self):
        page = self.read("brev", "40", "index.html")
        self.assertIn("Samme brevveksling", page)
        self.assertIn('href="../41/"', page)

    def test_the_current_letter_is_listed_in_its_correspondence_as_text(self):
        # The reader should see where they stand in the exchange: the
        # current letter appears in its place in the list, but as text
        # with a marker, never as a link to itself.
        page = self.read("brev", "40", "index.html")
        self.assertIn("← dette brev", page)
        self.assertNotIn('href="../40/"', page)

    def test_no_raw_data_artifacts_reach_the_pages(self):
        pages = [self.read("index.html")] + [
            self.read("brev", str(number), "index.html") for number in range(1, 43)
        ]
        for page in pages:
            self.assertNotIn("None", page)
            self.assertNotIn("1848-12-00", page)
            self.assertNotIn("18481200", page)

    def test_pages_are_self_contained(self):
        for page in (self.read("index.html"), self.read("brev", "1", "index.html")):
            self.assertNotIn("http://", page)
            self.assertNotIn("https://", page.replace("https://creativecommons.org", ""))
            self.assertNotIn('href="/', page)
            self.assertNotIn('src="/', page)

    def test_the_index_gives_every_correspondence_a_heading_block(self):
        # The group's heading, its note and its count are one unit -- the
        # design hangs them as a single band above the letters.
        index = self.read("index.html")
        self.assertEqual(
            index.count('<div class="group-head">'),
            index.count('<section class="correspondence"'),
        )

    def test_the_stylesheet_ships_with_the_site(self):
        self.assertTrue(
            os.path.exists(os.path.join(self.directory.name, "assets", "site.css"))
        )

    def test_the_fonts_ship_with_the_site(self):
        """Self-hosted typography, copied byte for byte.

        The site must look the same on a machine that has never heard of
        Google Fonts, so the woff2 files travel with it.
        """
        source = os.path.join(STATIC_DIRECTORY, "fonts")
        shipped = os.path.join(self.directory.name, "assets", "fonts")
        names = sorted(name for name in os.listdir(source) if name.endswith(".woff2"))
        self.assertTrue(names, "no webfonts are vendored")
        for name in names:
            with open(os.path.join(source, name), "rb") as file:
                original = file.read()
            self.assertEqual(original[:4], b"wOF2", "%s is not a woff2 file" % name)
            with open(os.path.join(shipped, name), "rb") as file:
                self.assertEqual(file.read(), original, "%s changed in transit" % name)

    def test_every_vendored_font_carries_its_licence(self):
        shipped = os.listdir(os.path.join(self.directory.name, "assets", "fonts"))
        self.assertTrue([name for name in shipped if name.startswith("OFL-")])

    def test_the_stylesheet_fetches_nothing_at_runtime(self):
        assets = os.path.join(self.directory.name, "assets")
        with open(os.path.join(assets, "site.css"), encoding="utf-8") as file:
            css = file.read()
        self.assertNotIn("@import", css)
        references = [
            reference.strip("'\" ") for reference in re.findall(r"url\(([^)]+)\)", css)
        ]
        self.assertTrue(references, "the stylesheet loads no fonts")
        for reference in references:
            self.assertFalse(
                reference.startswith(("http", "//", "/")),
                "%s is not a self-contained reference" % reference,
            )
            self.assertTrue(
                os.path.exists(os.path.join(assets, reference)),
                "%s is missing from the built site" % reference,
            )

    def test_the_build_is_deterministic(self):
        with tempfile.TemporaryDirectory() as other:
            build_site([self.volume], other)
            for parts in (("index.html",), ("brev", "1", "index.html")):
                with open(os.path.join(other, *parts), encoding="utf-8") as file:
                    self.assertEqual(file.read(), self.read(*parts))


class LetterSlugTest(unittest.TestCase):
    """A letter's URL segment: the edition's number, or something safe."""

    def test_a_numbered_letter_is_its_number(self):
        self.assertEqual("42", letter_slug({"id": "42", "xmlId": "n42"}, "b1"))

    def test_a_sub_numbered_draft_keeps_its_dotted_number(self):
        self.assertEqual(
            "159.1", letter_slug({"id": "159.1", "xmlId": "n159.1"}, "b127")
        )

    def test_an_unnumbered_letter_falls_back_to_volume_and_xml_id(self):
        # Three letters in b171 are printed with @n="-". They may not all
        # answer to /brev/-/.
        self.assertEqual(
            "b171-n171a", letter_slug({"id": "-", "xmlId": "n171a"}, "b171")
        )
        self.assertEqual(
            "b171-na", letter_slug({"id": "-", "xmlId": "na"}, "b171")
        )


class CorpusSiteBuildTest(unittest.TestCase):
    """The whole corpus, built once and read the way a visitor would read it."""

    @classmethod
    def setUpClass(cls):
        cls.volumes = parse_corpus(VENDOR)
        cls.directory = tempfile.TemporaryDirectory()
        cls.result = build_site(cls.volumes, cls.directory.name)
        with open(
            os.path.join(cls.directory.name, "index.html"), encoding="utf-8"
        ) as file:
            cls.index = file.read()

    @classmethod
    def tearDownClass(cls):
        cls.directory.cleanup()

    def read(self, *parts):
        with open(os.path.join(self.directory.name, *parts), encoding="utf-8") as file:
            return file.read()

    # -- coverage ---------------------------------------------------------

    def test_every_letter_in_the_corpus_gets_a_page(self):
        self.assertEqual(336, self.result["letters"])
        self.assertEqual(14, self.result["volumes"])
        for number in (1, 42, 43, 119, 160, 207, 318):
            self.assertTrue(
                os.path.exists(
                    os.path.join(self.directory.name, "brev", str(number), "index.html")
                ),
                "missing page for letter %d" % number,
            )

    def test_the_unnumbered_letters_get_pages_of_their_own(self):
        for slug in ("b171-n171a", "b171-n176a", "b171-na"):
            self.assertTrue(
                os.path.exists(
                    os.path.join(self.directory.name, "brev", slug, "index.html")
                ),
                "missing page for %s" % slug,
            )

    def test_no_two_letters_claim_the_same_page(self):
        directories = os.listdir(os.path.join(self.directory.name, "brev"))
        self.assertEqual(336, len(directories))
        self.assertEqual(336, len(set(directories)))

    def test_the_index_links_every_letter_page(self):
        for slug in ("1", "43", "159.1", "280.1", "318", "b171-na"):
            self.assertIn('href="brev/%s/"' % slug, self.index)

    def test_the_renderer_understood_every_element_in_the_corpus(self):
        self.assertEqual([], self.result["warnings"])

    def test_no_letter_is_left_outside_a_correspondence(self):
        self.assertEqual(0, self.result["ungrouped"])

    # -- the index at corpus scale ---------------------------------------

    def test_the_index_is_grouped_by_volume(self):
        for anchor, title in (
            ("bind-b1", "Familien Kierkegaard"),
            ("bind-b79", "Emil Boesen"),
            ("bind-b308", "Læserinder"),
        ):
            self.assertIn('id="%s"' % anchor, self.index)
            self.assertIn(title, self.index)

    def test_a_volume_navigation_links_every_volume(self):
        self.assertIn('class="volume-nav"', self.index)
        for volume in self.volumes:
            self.assertIn('href="#bind-%s"' % volume["volume"], self.index)

    def test_correspondence_anchors_are_unique_across_volumes(self):
        # correspContext1 exists in all fourteen files; the index has to keep
        # its anchors apart or every letter page links to the wrong section.
        anchors = re.findall(r'<section class="correspondence" id="([^"]+)"', self.index)
        self.assertEqual(len(anchors), len(set(anchors)))
        self.assertIn("b1-correspContext1", anchors)
        self.assertIn("b171-correspContext1", anchors)

    def test_the_intro_describes_the_whole_corpus_not_one_volume(self):
        lead = re.search(r'<p class="lead">(.*?)</p>', self.index, re.S).group(1)
        self.assertNotIn("Denne demonstration viser bindet", lead)
        self.assertIn("336", lead)
        self.assertIn("14", lead)

    def test_the_index_still_hangs_each_correspondence_in_its_band(self):
        self.assertEqual(
            self.index.count('<div class="group-head">'),
            self.index.count('<section class="correspondence"'),
        )

    # -- letter pages ------------------------------------------------------

    def test_prev_and_next_cross_volume_boundaries(self):
        # 42 is the last letter of b1 and 43 the first of b43: in the
        # edition they are consecutive, so the reader walks straight through.
        page = self.read("brev", "42", "index.html")
        self.assertIn('href="../41/"', page)
        self.assertIn('href="../43/"', page)
        first = self.read("brev", "1", "index.html")
        self.assertNotIn('rel="prev"', first)
        last = self.read("brev", "318", "index.html")
        self.assertNotIn('rel="next"', last)

    def test_the_sequence_follows_the_edition_not_the_number(self):
        # 159.1-159.9 are drafts printed between letters 159 and 160.
        page = self.read("brev", "159.1", "index.html")
        self.assertIn('href="../159/"', page)
        self.assertIn('href="../159.2/"', page)

    def test_a_letter_names_the_volume_it_was_printed_in(self):
        page = self.read("brev", "262", "index.html")
        self.assertIn("B259", page)
        self.assertIn("J.L.A. Kolderup-Rosenvinge", page)
        self.assertIn('href="../../#bind-b259"', page)

    def test_same_correspondence_stays_inside_the_volume(self):
        """b79 is one correspondence: all 41 letters to and from Emil Boesen.

        The sequence navigation walks out of the volume (letter 79 follows
        letter 78, which is in b70); the correspondence list does not.
        """
        page = self.read("brev", "79", "index.html")
        self.assertIn("Samme brevveksling", page)
        siblings = page.split('<ul class="sibling-list">', 1)[1].split("</ul>", 1)[0]
        linked = re.findall(r'href="\.\./([^/]+)/"', siblings)
        self.assertEqual(40, len(linked))
        self.assertEqual(
            [], [slug for slug in linked if not 79 <= int(slug) <= 119]
        )
        # The previous letter is in another volume: reachable, but not listed
        # as part of this correspondence.
        self.assertIn('href="../78/" rel="prev"', page)

    def test_an_unnumbered_letter_says_so_rather_than_showing_a_dash(self):
        page = self.read("brev", "b171-n171a", "index.html")
        self.assertIn("uden nummer", page)
        self.assertNotIn("Brev -", page)
        self.assertIn("se Brev 193", page)

    def test_a_letter_with_no_text_in_the_source_says_so(self):
        """An empty sheet of paper would read as a fault in the display.

        The three b171 stubs record a letter the edition prints elsewhere:
        sender, recipient and date, and no transcription. The page says that
        rather than showing an empty transcription card.
        """
        page = self.read("brev", "b171-n171a", "index.html")
        self.assertIn("Udgaven trykker ingen brevtekst her", page)
        self.assertNotIn('class="transcription"', page)

    def test_every_other_letter_does_have_a_transcription(self):
        without = [
            entry
            for entry in sorted(os.listdir(os.path.join(self.directory.name, "brev")))
            if 'class="transcription"' not in self.read("brev", entry, "index.html")
        ]
        self.assertEqual(["b171-n171a", "b171-n176a", "b171-na"], without)

    def test_an_authors_footnote_reaches_the_page(self):
        page = self.read("brev", "65", "index.html")
        self.assertIn("tei-note", page)
        self.assertIn("medens det er uhøfligt betræffende Noget", page)

    # -- fidelity ----------------------------------------------------------

    def test_letters_from_three_volumes_read_exactly_as_transcribed(self):
        """Every character of the transcription, in order, on the page.

        Compared without whitespace. The display drops the blank blocks the
        edition uses for space on the sheet (``<p rend="decoration">`` around
        an empty figure, empty openers and closers), which carry no characters
        but do carry the line breaks around them -- so the *spacing* between
        blocks differs by design while the text cannot. Word boundaries inside
        a block are covered by the renderer's own tests and by the substrings
        checked here.
        """
        samples = {
            ("b1", "1"): "Kjære Broder!",
            ("b79", "82"): "Tak skal Du have for Dit Brev",
            ("b259", "262"): "De erindrer vel sagtens det fortræffelige Sted",
            ("b308", "310"): None,
        }
        by_volume = {volume["volume"]: volume for volume in self.volumes}
        for (volume_name, identifier), expected in samples.items():
            letter = [
                l
                for l in by_volume[volume_name]["letters"]
                if l["id"] == identifier
            ][0]
            transcription = _transcription_text(self.read("brev", identifier, "index.html"))
            source = plain_text(letter["body"])
            self.assertEqual(
                re.sub(r"\s", "", source),
                re.sub(r"\s", "", transcription),
                "%s/%s" % (volume_name, identifier),
            )
            if expected:
                self.assertIn(expected, transcription)

    def test_no_raw_data_artifacts_reach_any_page(self):
        pages = [self.index]
        for entry in sorted(os.listdir(os.path.join(self.directory.name, "brev"))):
            pages.append(self.read("brev", entry, "index.html"))
        for page in pages:
            self.assertNotIn("None", page)
            self.assertNotIn("18481200", page)
            self.assertNotRegex(page, r"\d{4}-\d{2}-00")

    def test_every_page_is_self_contained(self):
        pages = [self.index]
        for entry in sorted(os.listdir(os.path.join(self.directory.name, "brev"))):
            pages.append(self.read("brev", entry, "index.html"))
        for page in pages:
            stripped = page.replace("https://creativecommons.org", "")
            self.assertNotIn("http://", stripped)
            self.assertNotIn("https://", stripped)
            self.assertNotIn('href="/', page)
            self.assertNotIn('src="/', page)

    def test_the_corpus_build_is_deterministic(self):
        with tempfile.TemporaryDirectory() as other:
            build_site(self.volumes, other)
            for parts in (("index.html",), ("brev", "262", "index.html")):
                with open(os.path.join(other, *parts), encoding="utf-8") as file:
                    self.assertEqual(file.read(), self.read(*parts))


def _transcription_text(page):
    """The reading text of a built letter page, tags and entities removed.

    Page-break chips are the display's own addition -- the marker "[9]" is not
    in the transcription -- so they come out again before comparing with the
    parser's ``plain_text``. Whitespace is normalised on both sides, because
    the line wrapping of the XML file was never part of the text.
    """
    inner = page.split('<div class="transcription" lang="da">', 1)[1]
    for closer in ('<nav class="letter-nav"', '<section class="same-correspondence"',
                   "</article>"):
        if closer in inner:
            inner = inner.split(closer, 1)[0]
            break
    inner = inner.rstrip()[: -len("</div>")]
    inner = re.sub(r'<span class="tei-pb[^"]*"[^>]*>.*?</span>', "", inner)
    inner = re.sub(r"<[^>]+>", "", inner)
    inner = inner.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
    return _collapse(inner)


def _collapse(value):
    return re.sub(r"\s+", " ", value).strip()


class DateSpanTest(unittest.TestCase):
    """Every day a date could mean -- what the timeline places a letter on.

    ``format_date`` says the same thing in words; ``span`` says it in days, so
    a mark can be as wide as the edition's uncertainty and no wider.
    """

    def test_a_day_is_a_single_day(self):
        self.assertEqual(
            {
                "start": datetime.date(1829, 3, 8),
                "end": datetime.date(1829, 3, 8),
                "precision": "day",
                "open_end": False,
                "open_end_raw": None,
            },
            dates.span(date("18290308")),
        )

    def test_a_month_covers_the_whole_month(self):
        stretch = dates.span(date("18481200"))
        self.assertEqual(datetime.date(1848, 12, 1), stretch["start"])
        self.assertEqual(datetime.date(1848, 12, 31), stretch["end"])
        self.assertEqual("month", stretch["precision"])

    def test_a_year_covers_the_whole_year(self):
        stretch = dates.span(date("18370000"))
        self.assertEqual(datetime.date(1837, 1, 1), stretch["start"])
        self.assertEqual(datetime.date(1837, 12, 31), stretch["end"])

    def test_a_range_reaches_from_the_first_day_to_the_last(self):
        stretch = dates.span(date("18460000", not_after="18470000"))
        self.assertEqual(datetime.date(1846, 1, 1), stretch["start"])
        self.assertEqual(datetime.date(1847, 12, 31), stretch["end"])

    def test_an_unreadable_upper_bound_is_reported_not_guessed(self):
        """b43 letter 50: ``notAfter="1847000"``, seven digits, unreadable.

        The edition means *some* time after 1846 -- the display may not
        invent which, so the mark stays inside 1846 and says its end is open.
        """
        broken = date("18460000")
        broken["notAfter"] = {
            "raw": "1847000",
            "iso": None,
            "precision": None,
            "year": None,
            "month": None,
            "day": None,
        }
        stretch = dates.span(broken)
        self.assertEqual(datetime.date(1846, 1, 1), stretch["start"])
        self.assertEqual(datetime.date(1846, 12, 31), stretch["end"])
        self.assertTrue(stretch["open_end"])
        self.assertEqual("1847000", stretch["open_end_raw"])

    def test_a_letter_the_edition_never_dated_has_no_span(self):
        self.assertIsNone(dates.span(None))
        self.assertIsNone(
            dates.span(
                {
                    "raw": None,
                    "iso": None,
                    "precision": None,
                    "year": None,
                    "month": None,
                    "day": None,
                    "notBefore": None,
                    "notAfter": None,
                    "source": "undated",
                    "text": None,
                }
            )
        )


def letter(slug, raw=None, not_after=None):
    """A letter as the timeline model consumes it: view fields only."""
    value = date(raw, not_after=not_after) if raw else None
    return {
        "slug": slug,
        "number": slug,
        "title": "Brev %s" % slug,
        "sender": "SK",
        "recipient": "Emil Boesen",
        "date_text": dates.format_date(value),
        "span": dates.span(value),
    }


def letter_for(parsed, volume):
    """The same fields ``sitegen.site`` puts in a letter view, for one letter."""
    sender = parsed.get("sender") or {}
    recipient = parsed.get("recipient") or {}
    value = sender.get("date")
    return {
        "slug": letter_slug(parsed, volume),
        "number": parsed["id"],
        "title": "Brev %s" % parsed["id"],
        "sender": display_name(sender.get("name")) or "ukendt afsender",
        "recipient": display_name(recipient.get("name")) or "ukendt modtager",
        "date_text": dates.format_date(value),
        "span": dates.span(value),
    }


class TimelineModelTest(unittest.TestCase):
    """The timeline's view model, built from the real curated datasets."""

    @classmethod
    def setUpClass(cls):
        cls.context = load_context(CONTEXT)
        cls.volumes = parse_corpus(VENDOR)
        cls.letters = [
            letter_for(parsed, volume["volume"])
            for volume in cls.volumes
            for parsed in volume["letters"]
        ]
        cls.model = timeline_model(cls.letters, cls.context)

    def years(self):
        return {year["year"]: year for year in self.model["years"]}

    def test_the_scale_runs_from_the_first_year_to_the_last_without_gaps(self):
        model = self.model
        self.assertEqual(1813, model["first_year"])
        self.assertEqual(1855, model["last_year"])
        self.assertEqual(
            list(range(1813, 1856)), [year["year"] for year in model["years"]]
        )

    def test_every_letter_is_placed_once_or_named_as_undated(self):
        placed = [
            mark["slug"]
            for year in self.model["years"]
            for mark in year["letters"] + year["vague"]
        ]
        undated = [entry["slug"] for entry in self.model["undated"]]
        self.assertEqual(len(placed), len(set(placed)), "a letter is on the rail twice")
        self.assertEqual(326, len(placed))
        self.assertEqual(10, len(undated))
        self.assertEqual(336, len(placed) + len(undated))
        self.assertEqual(set(), set(placed) & set(undated))

    def test_a_mark_never_reaches_outside_its_year(self):
        for year in self.model["years"]:
            for mark in year["letters"]:
                self.assertGreaterEqual(mark["top"], 0)
                self.assertLessEqual(mark["top"] + mark["height"], 1.0001)

    def test_marks_that_overlap_in_time_are_given_different_slots(self):
        for year in self.model["years"]:
            taken = {}
            for mark in sorted(year["letters"], key=lambda m: m["top"]):
                bottom = taken.get(mark["slot"])
                if bottom is not None:
                    self.assertLessEqual(
                        bottom,
                        mark["top"] + 0.0001,
                        "two letters share a slot in %d" % year["year"],
                    )
                taken[mark["slot"]] = mark["top"] + mark["height"]

    def test_a_letter_known_only_by_year_gets_no_place_on_the_day_scale(self):
        model = timeline_model(
            [letter("42", "18370000"), letter("43", "18370308")], self.context
        )
        year = {y["year"]: y for y in model["years"]}[1837]
        self.assertEqual(["42"], [mark["slug"] for mark in year["vague"]])
        self.assertEqual(["43"], [mark["slug"] for mark in year["letters"]])

    def test_a_letter_spanning_years_is_listed_once_in_the_first_year(self):
        model = timeline_model([letter("39", "18460000", not_after="18470000")], self.context)
        years = {y["year"]: y for y in model["years"]}
        self.assertEqual(["39"], [mark["slug"] for mark in years[1846]["vague"]])
        self.assertEqual([], years[1847]["vague"])
        self.assertIn("1846–47", years[1846]["vague"][0]["label"])

    def test_every_publication_reaches_the_model_in_date_order(self):
        titles = [
            entry["title"]
            for year in self.model["years"]
            for block in year["works"]
            for entry in block["entries"]
        ]
        self.assertEqual(38, len(titles))
        self.assertEqual(
            [publication["title"] for publication in self.context["publications"]],
            titles,
        )

    def test_publications_of_one_day_are_one_block(self):
        year = self.years()[1843]
        blocks = {block["date_text"]: block for block in year["works"]}
        self.assertIn("16. oktober 1843", blocks)
        self.assertEqual(3, len(blocks["16. oktober 1843"]["entries"]))
        signing = [entry["pseudonym"] for entry in blocks["16. oktober 1843"]["entries"]]
        self.assertIn(None, signing, "the signed discourse of that day is missing")
        self.assertIn("Johannes de silentio", signing)

    def test_two_publications_a_day_apart_stay_two_blocks(self):
        year = self.years()[1845]
        self.assertEqual(
            ["29. april 1845", "30. april 1845"],
            [block["date_text"] for block in year["works"]],
        )

    def test_the_two_stays_at_nytorv_stay_two_bands(self):
        bands = [
            band
            for year in self.model["years"]
            for band in year["homes"]
            if band["starts"]
        ]
        nytorv = [band for band in bands if band["address"].startswith("Nytorv 2")]
        self.assertEqual(2, len(nytorv))
        self.assertEqual(9, len(bands), "every residence begins exactly once")

    def test_the_last_band_stops_where_the_dataset_stops(self):
        year = self.years()[1855]
        ending = [band for band in year["homes"] if band["ends"]]
        self.assertEqual(1, len(ending))
        # 2 October 1855, not 31 December and not his death in November.
        self.assertAlmostEqual(274 / 365, ending[0]["top"] + ending[0]["height"], places=2)

    def test_an_uncertain_period_is_flagged_rather_than_smoothed(self):
        # Five of the nine periods carry "approx": true in the dataset --
        # Løvstræde, Kultorvet, both Nørregade addresses and Østerbro.
        flagged = {
            band["address"]
            for year in self.model["years"]
            for band in year["homes"]
            if band["approx"] and band["starts"]
        }
        self.assertEqual(5, len(flagged))
        self.assertEqual(
            5, sum(1 for home in self.model["homes"] if home["approx"])
        )

    def test_the_widest_year_sets_the_width_of_the_letter_lane(self):
        widest = max(
            (mark["slot"] for year in self.model["years"] for mark in year["letters"]),
            default=0,
        )
        self.assertEqual(widest + 1, self.model["slots"])


class TimelinePageTest(unittest.TestCase):
    """The built timeline page, read the way a visitor would read it."""

    @classmethod
    def setUpClass(cls):
        cls.context = load_context(CONTEXT)
        cls.volumes = parse_corpus(VENDOR)
        cls.directory = tempfile.TemporaryDirectory()
        cls.result = build_site(cls.volumes, cls.directory.name, context=cls.context)
        cls.page = cls.read_from(cls.directory.name, "tidslinje", "index.html")

    @classmethod
    def tearDownClass(cls):
        cls.directory.cleanup()

    @staticmethod
    def read_from(*parts):
        with open(os.path.join(*parts), encoding="utf-8") as file:
            return file.read()

    def read(self, *parts):
        return self.read_from(self.directory.name, *parts)

    def test_the_page_is_built(self):
        self.assertIn("Tidslinje", self.page)

    def test_every_publication_is_on_the_page(self):
        for publication in self.context["publications"]:
            self.assertIn(_escape(publication["title"]), self.page)

    def test_every_residence_is_on_the_page(self):
        for residence in self.context["residences"]:
            self.assertIn(_escape(residence["address"]), self.page)

    def test_every_year_of_the_life_gets_its_own_row(self):
        for year in range(1813, 1856):
            self.assertIn(">%d<" % year, self.page)

    def test_every_letter_links_to_its_page(self):
        linked = set(re.findall(r'href="\.\./brev/([^/"]+)/"', self.page))
        self.assertEqual(336, len(linked))
        for slug in ("1", "42", "159.1", "318", "b171-na"):
            self.assertIn(slug, linked)

    def test_undated_letters_are_named_rather_than_placed(self):
        section = self.page.split('id="udaterede"', 1)[1]
        self.assertIn("uden datering", section.lower())
        self.assertEqual(10, len(re.findall(r'href="\.\./brev/', section)))

    def test_the_unreadable_upper_bound_is_shown_to_the_reader(self):
        self.assertIn("1847000", self.page)

    def test_the_legend_explains_the_marks_in_danish(self):
        legend = self.page.split('class="tl-legend"', 1)[1].split("</dl>", 1)[0]
        for word in ("dag", "måned", "år", "pseudonym"):
            self.assertIn(word, legend.lower())

    def test_pseudonymity_is_never_carried_by_colour_alone(self):
        # Every pseudonymous work names its pseudonym in text, and every
        # signed one says so: shape and words, never hue.
        self.assertEqual(12, self.page.count('class="tl-work-name">Pseudonym'))
        self.assertEqual(26, self.page.count('class="tl-work-name">Signeret'))

    def test_no_raw_data_artifacts_reach_the_page(self):
        self.assertNotIn("None", self.page)
        self.assertNotIn("null", self.page)
        self.assertNotRegex(self.page, r"\d{4}-\d{2}-00")
        self.assertNotRegex(self.page, r">\s*1[89]\d{2}-\d{2}-\d{2}\s*<")

    def test_the_page_is_self_contained(self):
        stripped = self.page.replace("https://creativecommons.org", "")
        self.assertNotIn("http://", stripped)
        self.assertNotIn("https://", stripped)
        self.assertNotIn('href="/', self.page)
        self.assertNotIn("<script", self.page)

    def test_the_site_navigation_reaches_the_timeline_from_every_page(self):
        index = self.read("index.html")
        letter = self.read("brev", "1", "index.html")
        self.assertIn('href="tidslinje/"', index)
        self.assertIn('href="../../tidslinje/"', letter)
        self.assertIn('href="../"', self.page)
        for page in (index, letter, self.page):
            self.assertIn('class="site-nav"', page)
            self.assertIn('aria-current="page"', page)

    def test_the_build_is_deterministic(self):
        with tempfile.TemporaryDirectory() as other:
            build_site(self.volumes, other, context=self.context)
            self.assertEqual(
                self.page, self.read_from(other, "tidslinje", "index.html")
            )

    def test_a_build_without_the_curated_datasets_still_works(self):
        """The editorial layer is optional: no context, no timeline, no links.

        The TEI is the truth the site cannot do without; publications and
        residences are added on top and may be thrown away.
        """
        with tempfile.TemporaryDirectory() as other:
            build_site(self.volumes, other)
            self.assertFalse(os.path.exists(os.path.join(other, "tidslinje")))
            index = self.read_from(other, "index.html")
            self.assertNotIn("tidslinje", index)


class SummaryTest(unittest.TestCase):
    """Victoria's summaries: in the index, and nowhere else.

    Maria's decision, and the reason is worth writing down: choosing what to
    read is where a presenter helps, and reading is where she gets in the way.
    So the summary sits under the letter in the list and is absent from the
    letter's own page.
    """

    SUMMARIES = 333
    STUBS = ("b171-n171a", "b171-n176a", "b171-na")

    @classmethod
    def setUpClass(cls):
        cls.context = load_context(CONTEXT)
        cls.volumes = parse_corpus(VENDOR)
        cls.directory = tempfile.TemporaryDirectory()
        cls.result = build_site(cls.volumes, cls.directory.name, context=cls.context)
        cls.index = cls.read_from(cls.directory.name, "index.html")

    @classmethod
    def tearDownClass(cls):
        cls.directory.cleanup()

    @staticmethod
    def read_from(*parts):
        with open(os.path.join(*parts), encoding="utf-8") as file:
            return file.read()

    def read(self, *parts):
        return self.read_from(self.directory.name, *parts)

    def test_every_summary_reaches_the_index(self):
        self.assertEqual(self.SUMMARIES, self.result["summaries"])
        self.assertEqual(
            self.SUMMARIES, self.index.count('class="letter-summary"')
        )

    def test_a_summary_sits_under_the_letter_it_belongs_to(self):
        entry = self.index.split('data-slug="1"', 1)[1].split("</li>", 1)[0]
        self.assertIn("snustobaksdåse i afskedsgave", entry)

    def test_a_summary_never_reaches_the_letters_own_page(self):
        page = self.read("brev", "1", "index.html")
        self.assertNotIn("snustobaksdåse i afskedsgave", page)
        self.assertNotIn("letter-summary", page)

    def test_a_letter_with_no_summary_is_given_none(self):
        # The three cross-reference stubs in b171 print no text, so there is
        # nothing to summarise and nothing is invented.
        for slug in self.STUBS:
            entry = self.index.split('data-slug="%s"' % slug, 1)[1].split("</li>", 1)[0]
            self.assertNotIn("letter-summary", entry)

    def test_the_index_says_whose_voice_the_summaries_are(self):
        lead = self.index.split('class="lead"', 1)[1].split("</p>", 1)[0]
        self.assertIn("Victoria Eremita", lead)
        self.assertIn("hører ikke til udgaven", lead)

    def test_a_build_without_the_summaries_promises_none(self):
        with tempfile.TemporaryDirectory() as other:
            result = build_site(self.volumes, other)
            self.assertEqual(0, result["summaries"])
            index = self.read_from(other, "index.html")
            self.assertNotIn("letter-summary", index)
            self.assertNotIn("Victoria Eremita", index)


def _escape(value):
    return value.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


if __name__ == "__main__":
    unittest.main()
