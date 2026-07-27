"""Tests for the display layer.

The parser has its own suite; these cover the two places where the site
generator makes real decisions -- precision-honest Danish dates and the TEI
body renderer -- plus one end-to-end build of the whole site.

The date tests use literal date dicts in the shape documented in
``pipeline.parse_tei``: the display layer must work off that contract, not off
the parser's internals.
"""

import os
import tempfile
import unittest

from pipeline.parse_tei import parse_volume
from sitegen import dates
from sitegen.site import build_site
from sitegen.tei_html import BodyRenderer

VENDORED_B1 = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data",
    "vendor",
    "b1",
    "txt.xml",
)


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


def _title_of(html):
    marker = 'title="'
    start = html.index(marker) + len(marker)
    return html[start : html.index('"', start)]


class SiteBuildTest(unittest.TestCase):
    """One end-to-end build, checked the way a reader would check it."""

    @classmethod
    def setUpClass(cls):
        cls.volume = parse_volume(VENDORED_B1)
        cls.directory = tempfile.TemporaryDirectory()
        cls.result = build_site(cls.volume, cls.directory.name)

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

    def test_the_stylesheet_ships_with_the_site(self):
        self.assertTrue(
            os.path.exists(os.path.join(self.directory.name, "assets", "site.css"))
        )

    def test_the_build_is_deterministic(self):
        with tempfile.TemporaryDirectory() as other:
            build_site(self.volume, other)
            for parts in (("index.html",), ("brev", "1", "index.html")):
                with open(os.path.join(other, *parts), encoding="utf-8") as file:
                    self.assertEqual(file.read(), self.read(*parts))


if __name__ == "__main__":
    unittest.main()
