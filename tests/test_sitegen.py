"""Tests for the display layer.

The parser has its own suite; these cover the two places where the site
generator makes real decisions -- precision-honest Danish dates and the TEI
body renderer -- plus one end-to-end build of the whole site.

The date tests use literal date dicts in the shape documented in
``pipeline.parse_tei``: the display layer must work off that contract, not off
the parser's internals.
"""

import datetime
import json
import os
import re
import tempfile
import unittest

from pipeline.context import load_context
from pipeline.corpus import parse_corpus
from pipeline.links import load_links
from pipeline.parse_tei import parse_volume, plain_text
from pipeline.provenance import load_provenance
from sitegen import dates
from sitegen.site import STATIC_DIRECTORY, build_site, display_name, letter_slug
from sitegen.tei_html import BodyRenderer
from sitegen.timeline import CELL_HIT_PX, YEAR_HEIGHT_PX, timeline_model

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VENDOR = os.path.join(REPO_ROOT, "data", "vendor")
VENDORED_B1 = os.path.join(VENDOR, "b1", "txt.xml")
CONTEXT = os.path.join(REPO_ROOT, "data", "context")
LINKS_PATH = os.path.join(REPO_ROOT, "data", "links.json")


def _links_data():
    with open(LINKS_PATH, encoding="utf-8") as file:
        return json.load(file)


# Self-containment, page by page. Every page the build writes is a closed
# system: the only addresses pointing off the site are the ones declared in
# ``data/links.json`` -- the CC0 deed in the footer, which is the licence the
# text is published under and belongs wherever the text goes, and the Om
# page's provenance addresses, because provenance without links is not
# provenance. The allowlists are *derived* from that file rather than retyped
# here: removing a link from the table makes any page still pointing at it
# fail, which is the point of having the table.
_DECLARED_LINKS = _links_data()["links"]
FOOTER_LINKS = tuple(
    entry["href"] for entry in _DECLARED_LINKS if entry["scope"] == "footer"
)
ABOUT_LINKS = FOOTER_LINKS + tuple(
    entry["href"] for entry in _DECLARED_LINKS if entry["scope"] == "om"
)
# Template entries declare a common prefix as their href; stripping the
# prefix removes the scheme, which is all assert_self_contained looks for,
# so the same mechanism covers per-letter addresses without new machinery.
BREV_LINKS = FOOTER_LINKS + tuple(
    entry["href"] for entry in _DECLARED_LINKS if entry["scope"] == "brev"
)
TIMELINE_LINKS = FOOTER_LINKS + tuple(
    entry["href"] for entry in _DECLARED_LINKS if entry["scope"] == "tidslinje"
)
# This project's own repository, read from the table like every other
# address: the Om page links its two records (PROVENANCE.md and the
# technical notes) as files inside it.
PROJECT_REPOSITORY = next(
    entry["href"] for entry in _DECLARED_LINKS if entry["id"] == "project-repository"
)


def assert_self_contained(case, page, allowed=FOOTER_LINKS):
    """No page fetches anything, and no page links off-site un-declared."""
    stripped = page
    for link in allowed:
        stripped = stripped.replace(link, "")
    case.assertNotIn("http://", stripped)
    case.assertNotIn("https://", stripped)
    case.assertNotIn('href="/', page)
    case.assertNotIn('src="/', page)


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
            assert_self_contained(self, page)

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

    def test_the_pagination_chips_and_place_underlines_stay_quiet(self):
        """Maria's call (2026-07-28): apparatus, not reading matter.

        The two pagination series ('printhenvisninger') and the place-name
        underline are upstream annotation a reader of the letters does not
        need. Nothing is dropped from the data -- the spans and their
        classes stay in the markup for a display that wants them back --
        but the stylesheet keeps them quiet.
        """
        css = self.read("assets", "site.css")
        self.assertRegex(css, r"\.tei-pb\s*\{\s*display:\s*none")
        self.assertNotRegex(css, r"\.tei-placeName[^}]*border-bottom:\s*1px")
        page = self.read("brev", "1", "index.html")
        self.assertIn('class="tei-pb', page)
        self.assertIn('class="tei-placeName', page)

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


class FaviconTest(unittest.TestCase):
    """Maria's icon set: shipped at the site root, linked relatively.

    The files come from ``sitegen/favicon`` and land beside ``index.html``,
    because that is where a browser guesses first; the pages still declare
    them with relative links, so the site keeps working from any directory
    of any static host. The manifest is held to the same rule: no absolute
    paths, and it names the site.
    """

    FILES = (
        "favicon.ico",
        "favicon-16x16.png",
        "favicon-32x32.png",
        "apple-touch-icon.png",
        "android-chrome-192x192.png",
        "android-chrome-512x512.png",
        "site.webmanifest",
    )

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

    def test_every_icon_file_lands_at_the_site_root(self):
        for name in self.FILES:
            self.assertTrue(
                os.path.exists(os.path.join(self.directory.name, name)), name
            )

    def test_every_page_declares_the_icons_relatively(self):
        index = self.read("index.html")
        letter = self.read("brev", "1", "index.html")
        self.assertIn('href="favicon-32x32.png"', index)
        self.assertIn('href="apple-touch-icon.png"', index)
        self.assertIn('href="site.webmanifest"', index)
        self.assertIn('href="../../favicon-32x32.png"', letter)
        self.assertIn('href="../../favicon.ico"', letter)

    def test_the_manifest_names_the_site_and_points_nowhere_absolute(self):
        manifest = json.loads(self.read("site.webmanifest"))
        self.assertEqual("epistel", manifest["name"])
        self.assertEqual("epistel", manifest["short_name"])
        for icon in manifest["icons"]:
            self.assertFalse(icon["src"].startswith("/"), icon["src"])


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
        # Maria's ruling (2026-08-03): the fourteen divisions are called
        # "grupper" everywhere the reader meets them -- the edition's own
        # word (Gads: "14 grupper af korrespondancer"); "bind" was wrong,
        # the letters are one volume of SKS (28). Old #bind-* anchors die
        # with the rename, accepted at the demo stage.
        for anchor, title in (
            ("gruppe-b1", "Familien Kierkegaard"),
            ("gruppe-b79", "Emil Boesen"),
            ("gruppe-b308", "Læserinder"),
        ):
            self.assertIn('id="%s"' % anchor, self.index)
            self.assertIn(title, self.index)

    def test_a_volume_navigation_links_every_volume(self):
        self.assertIn('class="volume-nav"', self.index)
        self.assertIn('aria-label="Grupper"', self.index)
        for volume in self.volumes:
            self.assertIn('href="#gruppe-%s"' % volume["volume"], self.index)

    def test_correspondence_anchors_are_unique_across_volumes(self):
        # correspContext1 exists in all fourteen files; the index has to keep
        # its anchors apart or every letter page links to the wrong section.
        anchors = re.findall(r'<section class="correspondence" id="([^"]+)"', self.index)
        self.assertEqual(len(anchors), len(set(anchors)))
        self.assertIn("b1-correspContext1", anchors)
        self.assertIn("b171-correspContext1", anchors)

    def test_the_intro_describes_the_whole_corpus_not_one_volume(self):
        # Maria chose lead #3 (2026-08-03): the group count leaves the lead
        # (structure is the list's job), "bevarede" carries the grounded
        # hint of loss, and the edition's uncertainty is named as kept.
        lead = re.search(r'<p class="lead">(.*?)</p>', self.index, re.S).group(1)
        self.assertIn("søgbar visning", lead)
        self.assertIn("336 bevarede breve", lead)
        self.assertIn("<i>Søren Kierkegaards Skrifter</i>", lead)
        self.assertIn("dateringer, forbehold og huller bevaret", lead)
        self.assertNotIn("grupper", lead)

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

    def test_a_letter_names_the_group_it_belongs_to(self):
        page = self.read("brev", "262", "index.html")
        self.assertIn("<dt>Gruppe</dt>", page)
        self.assertNotIn("<dt>Bind</dt>", page)
        self.assertIn("B259", page)
        self.assertIn("J.L.A. Kolderup-Rosenvinge", page)
        self.assertIn('href="../../#gruppe-b259"', page)

    def test_a_build_without_the_links_table_shows_no_edition_row(self):
        # This class builds without links.json on purpose: the SKS row is
        # an anchor and nothing but, so without the table it is absent
        # rather than degraded to text pointing nowhere.
        page = self.read("brev", "43", "index.html")
        self.assertNotIn("<dt>SKS</dt>", page)

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

    def test_the_unreadable_upper_bound_of_b43_50_reaches_its_page(self):
        """b43/50: ``notAfter="1847000"``, seven digits, unreadable.

        The timeline already quotes the defect; the letter page silently
        dropped it, showing plain "1846" as if the edition had claimed no
        upper bound at all. The page must say what the source wrote.
        """
        page = self.read("brev", "50", "index.html")
        self.assertIn("1846", page)
        self.assertIn("»1847000«", page)
        self.assertIn("kan ikke læses", page)

    def test_every_other_letter_does_have_a_transcription(self):
        without = [
            entry
            for entry in sorted(os.listdir(os.path.join(self.directory.name, "brev")))
            if 'class="transcription"' not in self.read("brev", entry, "index.html")
        ]
        self.assertEqual(["b171-n171a", "b171-n176a", "b171-na"], without)

    def test_a_letter_with_marks_explains_them_in_a_legend(self):
        """Maria's call (2026-07-28): the text-critical marks stay, and the
        reader is told what they mean -- a quiet per-letter Tegnforklaring
        listing only the marks that actually occur, each line wearing its
        own mark, so meaning is never carried by decoration alone.
        """
        page = self.read("brev", "159.1", "index.html")
        self.assertIn("Tegnforklaring", page)
        self.assertIn("tilføjet i kilden", page)
        self.assertIn('title="Tilføjet i kilden', page)

    def test_the_closer_and_the_dateline_stand_as_text_not_exhibits(self):
        """Maria's call (2026-07-29): no boxes around salutations and dates.

        The signature block and the dateline stood in bordered, shaded
        boxes -- museum treatment the words do not need. They stand as the
        surrounding text now, still set to the right the way they sit on
        the sheet. The classes stay in the markup for a display that wants
        the boxes back.
        """
        css = self.read("assets", "site.css")
        for selector in (r"\.tei-signed", r"\.tei-dateline"):
            self.assertNotRegex(css, selector + r"[^{]*\{[^}]*background")
            self.assertNotRegex(css, selector + r"[^{]*\{[^}]*border")
        # Prefix match: the signed block also carries its source layout
        # class (r-bagind), and both must survive the un-boxing.
        page = self.read("brev", "29", "index.html")
        self.assertIn('class="tei-signed', page)
        self.assertIn('class="tei-dateline', page)

    def test_the_added_text_mark_is_discreet_and_sits_over_the_line(self):
        """Maria's call (2026-07-29): the add mark must not look like a link.

        It wore an ochre wash and a solid bottom border -- link costume.
        Now it is as quiet as the other apparatus marks: a dotted hairline
        like unclear's, distinguished by position rather than colour -- it
        sits OVER the run, because that is what it means: added in the
        source, typically above the line. The tooltip still says so.
        """
        css = self.read("assets", "site.css")
        self.assertNotRegex(css, r"\.tei-add\s*\{[^}]*background")
        self.assertNotRegex(css, r"\.tei-add\s*\{[^}]*border-bottom")
        self.assertRegex(css, r"\.tei-add\s*\{[^}]*border-top:\s*1px\s+dotted")
        page = self.read("brev", "29", "index.html")
        self.assertIn('class="tei-add"', page)
        self.assertIn('title="Tilføjet i kilden', page)

    def test_the_latin_hand_is_explained_where_it_occurs(self):
        # Letter 1 switches to the Latin hand; the edition's own convention
        # ('Latin hand, in SKS rendered sans-serif') deserves words.
        page = self.read("brev", "1", "index.html")
        self.assertIn("latinsk hånd", page)

    def test_the_legend_and_the_tooltip_say_the_hand_the_same_way(self):
        """One mark, one word (Maria, korrektur 2026-07-28).

        The legend said "latinsk hånd" and the hover said "latinsk skrift"
        for the same switch of hand. They are both good Danish and that was
        the whole problem: a reader who reads the legend and then hovers
        must not be told two things. "Hånd" wins -- it is the paleographic
        pair to "gotisk".
        """
        page = self.read("brev", "1", "index.html")
        self.assertIn("skrevet med latinsk hånd, hvor brevet ellers er gotisk", page)
        self.assertIn('title="Latinsk hånd, hvor brevet ellers er gotisk"', page)
        self.assertNotIn("latinsk skrift", page)

    def test_a_letter_with_no_marks_carries_no_legend(self):
        page = self.read("brev", "10", "index.html")
        self.assertNotIn("Tegnforklaring", page)

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
            assert_self_contained(self, page)

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
    for closer in ('<details class="mark-legend"', '<nav class="letter-nav"',
                   '<section class="same-correspondence"', "</article>"):
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

    def test_the_scale_belongs_to_the_letters_and_the_works(self):
        """From the first preserved letter, 1829, to the last year, 1855.

        Maria's call (2026-07-29): no empty childhood years -- the scale
        starts where the letters and the works start, not where a
        residence dataset happens to begin. 1829 is derived, not chosen:
        brev 1 is dated 8 March 1829.
        """
        model = self.model
        self.assertEqual(1829, model["first_year"])
        self.assertEqual(1855, model["last_year"])
        self.assertEqual(
            list(range(1829, 1856)), [year["year"] for year in model["years"]]
        )

    def test_a_band_older_than_the_scale_is_clipped_not_dropped(self):
        """Nytorv began in 1813; the scale begins in 1829.

        The band enters the page already running -- no top cap, because
        1829 is not its true beginning -- and the register at the foot
        still tells the whole period, so nothing is silently lost.
        """
        first = {y["year"]: y for y in self.model["years"]}[1829]
        nytorv = [b for b in first["homes"] if b["address"].startswith("Nytorv 2")]
        self.assertEqual(1, len(nytorv))
        self.assertFalse(nytorv[0]["starts"])
        self.assertEqual(0.0, nytorv[0]["top"], "the band runs from the very top")
        periods = [home["period"] for home in self.model["homes"]]
        self.assertIn("5. maj 1813 – 1. september 1837", periods)

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
        # Eight of the nine residences begin on the scale; the first stay
        # at Nytorv began in 1813 and enters it already running, so only
        # the return in 1844 draws a beginning.
        bands = [
            band
            for year in self.model["years"]
            for band in year["homes"]
            if band["starts"]
        ]
        nytorv = [band for band in bands if band["address"].startswith("Nytorv 2")]
        self.assertEqual(1, len(nytorv))
        self.assertEqual(8, len(bands), "every residence on the scale begins once")
        addresses = {
            band["address"] for year in self.model["years"] for band in year["homes"]
        }
        self.assertEqual(2, len([a for a in addresses if a.startswith("Nytorv 2")]))

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

    def test_every_mark_is_a_finger_sized_target(self):
        """The slot layout deals columns with 24 px of vertical slack.

        24 CSS pixels is WCAG 2.5.8's minimum target size, and it is also
        Maria's wish (2026-07-28): letter marks a finger can hit. The slack
        is what lets the hit area grow invisibly around a mark that is
        drawn as a 3 px line -- the columns guarantee no two targets in a
        lane ever come closer than this.
        """
        self.assertEqual(24.0, CELL_HIT_PX)

    def test_the_python_pixels_and_the_stylesheet_tokens_agree(self):
        """The coupling the backlog warns about, held by a test.

        ``timeline.py`` reasons in pixels when it deals the slot columns;
        ``site.css`` draws in rem. If either side changes alone, marks
        overlap or waste a lane -- so the numbers are read from the
        stylesheet and compared, at 16 px to the rem.
        """
        with open(
            os.path.join(STATIC_DIRECTORY, "site.css"), encoding="utf-8"
        ) as file:
            css = file.read()
        tokens = {
            name: float(value)
            for name, value in re.findall(r"(--tl-[a-z]+):\s*([\d.]+)rem", css)
        }
        self.assertEqual(CELL_HIT_PX, 16 * tokens["--tl-hit"])
        self.assertEqual(YEAR_HEIGHT_PX, 16 * tokens["--tl-year"])
        # The column is exactly one hit area wide: targets in neighbouring
        # columns sit side by side, so the horizontal spacing is the cell.
        self.assertEqual(tokens["--tl-hit"], tokens["--tl-cell"])

    def test_the_letter_lane_fits_the_shared_shell(self):
        """21 columns is the most the real corpus needs at 24 px of slack.

        21 x 1.5rem is a 31.5rem letter lane, which is what fits inside
        the site's shared 46rem shell once the works sit under the year
        (option A, Maria 2026-07-29). If a new corpus pushes past 21, the
        geometry has to be renegotiated, not silently overflowed.
        """
        self.assertLessEqual(self.model["slots"], 21)


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

    def test_both_legends_punctuate_by_the_same_rule(self):
        """A full stop on either Tegnforklaring means a sentence has ended.

        Maria's rule (korrektur 2026-07-28): a fragment gets no full stop,
        a whole sentence gets one -- and the timeline's legend and the
        letter page's legend follow it alike, since they share a name and
        a reader reads both. Checked mechanically: an explanation that
        holds a sentence boundary ends in a stop, and one that does not,
        does not.
        """
        timeline = re.findall(
            r"<dd>(.*?)</dd>",
            self.page.split('class="tl-legend"', 1)[1].split("</dl>", 1)[0],
        )
        letter = re.findall(
            r"<li><span[^>]*>(.*?)</span></li>",
            self.read("brev", "159.1", "index.html")
            .split('class="mark-legend-list"', 1)[1]
            .split("</ul>", 1)[0],
        )
        self.assertEqual(6, len(timeline))
        self.assertTrue(letter)
        for explanation in timeline + letter:
            has_sentence = ". " in explanation
            self.assertEqual(
                has_sentence, explanation.endswith("."), explanation
            )

    def test_every_publication_is_on_the_page(self):
        for publication in self.context["publications"]:
            self.assertIn(_escape(publication["title"]), self.page)

    def test_every_residence_is_on_the_page(self):
        for residence in self.context["residences"]:
            self.assertIn(_escape(residence["address"]), self.page)

    def test_every_year_of_the_scale_gets_its_own_row(self):
        for year in range(1829, 1856):
            self.assertIn('id="aar-%d"' % year, self.page)
        # And none before the first preserved letter: the childhood years
        # held nothing but a residence band (Maria, 2026-07-29).
        for year in (1813, 1820, 1828):
            self.assertNotIn('id="aar-%d"' % year, self.page)

    def test_the_intro_names_the_scale_honestly(self):
        # Not "his life from 1813": the page begins at the first preserved
        # letter, and the words above the rail must say exactly that.
        self.assertIn("første bevarede brev", self.page)
        self.assertNotIn("liv fra 1813", self.page)

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

    def test_the_lane_and_the_legend_agree_and_the_drawn_mark_is_explained(self):
        """One name for the lane, and the printed mark still looked up.

        The rail's head said "Kun år" and the legend said "ca." for the
        same lane (Maria's call, korrektur 2026-07-28: "Kun år" is the
        shared name). But the chips beside the years are drawn with "ca."
        on them, so that text has to stay findable in the legend -- a
        reader looks up what is printed, not what we call it internally.
        """
        legend = self.page.split('class="tl-legend"', 1)[1].split("</dl>", 1)[0]
        self.assertIn("<dt>Kun år</dt>", legend)
        self.assertNotIn("<dt>ca.</dt>", legend)
        self.assertIn("»ca.«", legend)
        # The lane head is the other half of the pair, and still drawn.
        self.assertIn('class="tl-head-vague">Kun år', self.page)
        self.assertIn('class="tl-vague-mark" aria-hidden="true">ca.', self.page)

    def test_pseudonymity_is_never_carried_by_colour_alone(self):
        # Every pseudonymous work names its pseudonym in text, and every
        # signed one says so: shape and words, never hue.
        self.assertEqual(12, self.page.count('class="tl-work-name">Pseudonym'))
        self.assertEqual(26, self.page.count('class="tl-work-name">Eget navn'))

    def test_the_rail_carries_no_address_labels(self):
        """Addresses live in the register at the foot, at every width.

        Option A (Maria, 2026-07-29): one layout everywhere, and the band
        lane is a hairline, so the rail has no room for names. The bands
        stay -- they are the part that is on the scale -- and the register
        still names every address.
        """
        self.assertNotIn("tl-home-label", self.page)
        register = self.page.split('class="tl-home-register"', 1)[1]
        for residence in self.context["residences"]:
            self.assertIn(_escape(residence["address"]), register)

    def test_no_year_reserves_time_for_its_works(self):
        """The scale is uniform: works sit under the year, at every width.

        Option A dissolves the one exception the scale used to have -- a
        year stretching for its publications. No block reserves a share of
        the year any more, so the custom properties that carried it are
        gone, and so is the head label of the lane that no longer exists
        beside the strip.
        """
        # With the colon: the custom properties. Without it the assertion
        # would trip over the month box's class name, tl-letter--span.
        self.assertNotIn("--lead:", self.page)
        self.assertNotIn("--span:", self.page)
        self.assertNotIn("tl-head-works", self.page)

    def test_the_legend_no_longer_promises_a_stretch(self):
        self.assertNotIn("strækkes", self.page)
        self.assertIn("hvert år er lige højt", self.page)

    def test_a_portrait_phone_is_asked_to_turn(self):
        """Maria's simplification (2026-07-29): no third layout below the
        strip's minimum width -- a friendly line asks for landscape. The
        prompt is in the markup at every width; the stylesheet decides
        when it shows and when the rail hides.
        """
        self.assertIn('class="tl-rotate"', self.page)
        self.assertIn("Vend telefonen", self.page)
        self.assertIn(".tl-rotate", self.read("assets", "site.css"))

    def test_the_timeline_keeps_the_shared_shell(self):
        # Option A's second wish: the page at the site's shared width, so
        # a landscape phone holds the whole strip. No page-local override.
        self.assertNotRegex(
            self.read("assets", "site.css"), r"page-timeline[^}]*--shell"
        )

    def test_no_raw_data_artifacts_reach_the_page(self):
        self.assertNotIn("None", self.page)
        self.assertNotIn("null", self.page)
        self.assertNotRegex(self.page, r"\d{4}-\d{2}-00")
        self.assertNotRegex(self.page, r">\s*1[89]\d{2}-\d{2}-\d{2}\s*<")

    def test_the_page_is_self_contained(self):
        assert_self_contained(self, self.page)
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
    """Maria Notabene's summaries: under every letter *list*, never over a text.

    Maria's decision, revised 2026-07-28 (it was "index only" first): the
    summaries are the site's formidling layer -- a bare "Brev 34" invites
    nobody, her two lines do. So every list a reader chooses from carries
    them: the index, "Samme brevveksling" on the letter pages, and the
    three lists on a person's page -- every row, the current letter's
    included. She still never sits above a transcription: reading is
    where a presenter gets in the way, and there the letter has the word.
    """

    SUMMARIES = 336
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

    def test_an_index_entry_is_one_clickable_block_in_the_shared_row_style(self):
        """Maria's call (2026-07-28): one list design across the site.

        The front page's technical FRA/TIL/DATERET grid gives way to the
        person pages' relaxed rows -- title · date, the pair line, the
        resumé, all inside one <a>. The search attributes stay on the
        <li>, untouched by the layout.
        """
        entry = self.index.split('data-slug="1"', 1)[1].split("</li>", 1)[0]
        self.assertIn('class="sibling-link"', entry)
        self.assertIn("fra Søren Kierkegaard til P.C. Kierkegaard", entry)
        anchor = entry.split("</a>", 1)[0]
        self.assertIn("snustobaksdåse i afskedsgave", anchor)
        self.assertNotIn("letter-meta", entry)

    def test_the_middot_separator_never_opens_a_wrapped_line(self):
        """Småting (backlog): '·' must stay glued to the word before it.

        A no-break space precedes the dot and an ordinary space follows
        it, so a narrow-width wrap breaks *after* the dot -- before the
        date or "fra" -- and the separator itself never opens a line.
        """
        entry = self.index.split('data-slug="1"', 1)[1].split("</li>", 1)[0]
        self.assertIn(
            'Brev 1</span><span class="muted"> · 8. marts 1829', entry
        )
        self.assertIn(
            '1829</span><span class="person-letter-pair">'
            " · fra Søren Kierkegaard til P.C. Kierkegaard",
            entry,
        )

        siblings = self.read("brev", "2", "index.html").split("Samme brevveksling", 1)[1]
        self.assertIn(
            'Brev 1</span><span class="muted"> · 8. marts 1829', siblings
        )

        person = self.read("person", "kierkegaard-peter-christian", "index.html")
        received = person.split(
            "Breve til Peter Christian Kierkegaard", 1
        )[1].split("</section>", 1)[0]
        self.assertIn(
            'Brev 1</span><span class="muted"> · 8. marts 1829', received
        )

    def test_a_summary_follows_the_letter_into_its_siblings_lists(self):
        # Brev 2 is in the same correspondence as brev 1: its page's
        # "Samme brevveksling" list carries brev 1's summary.
        page = self.read("brev", "2", "index.html")
        siblings = page.split("Samme brevveksling", 1)[1]
        self.assertIn("snustobaksdåse i afskedsgave", siblings)

    def test_a_sibling_entry_is_one_clickable_block(self):
        """Maria's call (2026-07-28): the whole block is the link.

        Title, date and resumé travel inside one <a>, so the reader can
        aim at the sentence that tempted them, not just the number.
        """
        siblings = self.read("brev", "2", "index.html").split("Samme brevveksling", 1)[1]
        anchor = siblings.split('href="../1/"', 1)[1].split("</a>", 1)[0]
        self.assertIn("snustobaksdåse i afskedsgave", anchor)

    def test_a_summary_reaches_the_letter_lists_of_a_person_page(self):
        # P.C. Kierkegaard received brev 1; his page's list says what it is.
        page = self.read("person", "kierkegaard-peter-christian", "index.html")
        received = page.split(
            "Breve til Peter Christian Kierkegaard", 1
        )[1].split("</section>", 1)[0]
        self.assertIn("snustobaksdåse i afskedsgave", received)
        anchor = received.split('href="../../brev/1/"', 1)[1].split("</a>", 1)[0]
        self.assertIn("snustobaksdåse i afskedsgave", anchor)

    def test_the_current_letter_carries_its_own_summary_in_its_list(self):
        # Maria's revision (2026-07-28): the current letter's row keeps its
        # marker, loses no resumé, and still links nowhere.
        siblings = self.read("brev", "1", "index.html").split("Samme brevveksling", 1)[1]
        current = siblings.split('aria-current="page"', 1)[1].split("</li>", 1)[0]
        self.assertIn("← dette brev", current)
        self.assertIn("snustobaksdåse i afskedsgave", current)
        self.assertNotIn("<a ", current)

    def test_the_cross_reference_stubs_carry_pointing_summaries(self):
        """Maria's ruling (2026-08-02): the stubs get resumés after all.

        The three b171 stubs are the edition's cross-references: the letter
        exists, printed under another letter's number (Carl's on the verso
        of Sophie's sheet as Brev 193; Jette's and Wilhelm's under Brev 194).
        Notabene's resumé points at the right door instead of standing
        silent -- grounded in the letters where SKS prints the text, not
        invented. With these three, every letter row carries a resumé.
        """
        for slug, fragment in (
            ("b171-n171a", "bagsiden af Sophies ark"),
            ("b171-n176a", "deler nummer med Wilhelms"),
            ("b171-na", "dux"),
        ):
            entry = self.index.split('data-slug="%s"' % slug, 1)[1].split("</li>", 1)[0]
            self.assertIn("letter-summary", entry)
            self.assertIn(fragment, entry)

    def test_the_index_says_whose_voice_the_summaries_are(self):
        """The lead stands the presenter in the door, in the house's way.

        Maria's lead #3 (2026-08-03, replacing her 2026-07-29 original):
        the pseudonym is introduced through "husets egen pseudonyme
        tradition" rather than the word "pseudonymet" -- the disclosure
        proper is one click away on /om/ -- and the resumé promises no
        interpretation, "blot nok til at man ved, hvilken dør man åbner".
        The handover sentence is untouchable.
        """
        lead = self.index.split('class="lead"', 1)[1].split("</p>", 1)[0]
        self.assertIn("pseudonyme tradition", lead)
        self.assertIn("Maria Notabene", lead)
        self.assertIn("resumé til hvert brev", lead)
        self.assertIn("hvilken dør man åbner", lead)
        self.assertIn("Hun har skrevet et forord, naturligvis.", lead)
        self.assertNotIn("hører ikke til udgaven", self.index)

    def test_a_build_without_the_summaries_promises_none(self):
        """No summaries, no sentence about summaries.

        She still welcomes the reader -- the welcome is prose in the
        generator, not data -- but the lead must not credit her with 333
        resumés that this build did not write.
        """
        with tempfile.TemporaryDirectory() as other:
            result = build_site(self.volumes, other)
            self.assertEqual(0, result["summaries"])
            index = self.read_from(other, "index.html")
            self.assertNotIn("letter-summary", index)
            lead = index.split('class="lead"', 1)[1].split("</p>", 1)[0]
            self.assertNotIn("Maria Notabene", lead)
            self.assertNotIn("resuméer", lead)


class PresenterTest(unittest.TestCase):
    """The one invented thing on the site, and the page that owns up to it.

    Maria Notabene writes the front page's welcome and the 336 summaries. The
    site's honesty rests on two things being true at once: she is the only
    fiction here -- no invented source, date or anecdote anywhere -- and the
    page that says so is one click away from her, in plain Danish.

    These tests hold the parts of that promise a build can actually check:
    that she is on the front page, that the Om page exists and names the
    source, the licences, the records behind the vendored copy and the AI
    assistance, and that the reader can get there from any page.
    """

    @classmethod
    def setUpClass(cls):
        cls.context = load_context(CONTEXT)
        cls.provenance = load_provenance(VENDOR)
        cls.links = load_links(LINKS_PATH)
        cls.volumes = parse_corpus(VENDOR)
        cls.directory = tempfile.TemporaryDirectory()
        cls.result = build_site(
            cls.volumes,
            cls.directory.name,
            context=cls.context,
            provenance=cls.provenance,
            links=cls.links,
        )
        cls.index = cls.read_from(cls.directory.name, "index.html")
        cls.about = cls.read_from(cls.directory.name, "om", "index.html")

    @classmethod
    def tearDownClass(cls):
        cls.directory.cleanup()

    @staticmethod
    def read_from(*parts):
        with open(os.path.join(*parts), encoding="utf-8") as file:
            return file.read()

    def read(self, *parts):
        return self.read_from(self.directory.name, *parts)

    def welcome(self):
        """Just her block on the front page, so the assertions cannot drift."""
        return self.index.split('class="presentation"', 1)[1].split("</section>", 1)[0]

    # -- the front page ---------------------------------------------------

    def test_the_front_page_carries_her_welcome(self):
        self.assertIn('class="presentation"', self.index)
        self.assertIn("Maria Notabene", self.index)

    def test_the_welcome_is_a_foreword_and_says_so(self):
        # Maria's direction (2026-07-29): the foreword always carries a
        # heading, like the letters it stands in front of.
        self.assertIn("<h2>Forord</h2>", self.welcome())

    def test_the_welcome_draws_the_arc_from_schoolboy_to_grave(self):
        """Concrete, and every one of them checkable against a letter.

        The apologising schoolboy is letter 1, the engagement letter 22, the
        authorship letter 22 too, the grave plot with room for one more name
        letter 39, the father's colic letter 23, the aunt in Jutland letter
        29 and the cousin who would like a visit letter 40. Maria's revision
        of 2026-07-29: the foreword hints the arc from child to near-death
        instead of retelling anecdotes, and the other writers stand around
        him as principals of their own letters.
        """
        welcome = self.welcome()
        self.assertIn("skoledreng", welcome)
        self.assertIn("plads på tavlen til ét navn mere", welcome)
        self.assertIn("en far om sin kolik", welcome)
        self.assertIn("en faster i Jylland", welcome)
        self.assertIn("en kusine", welcome)

    def test_the_welcome_says_what_a_reader_can_do_here(self):
        """Browse, search, follow a year or a person -- and nothing more.

        Decided 2026-07-29: the publisher reference waits for the
        crediting-links decision, and the timeline is reached through the
        navigation rather than promised here.
        """
        welcome = self.welcome().lower()
        self.assertIn("bladr", welcome)
        self.assertIn("søg", welcome)
        self.assertIn("følg et år eller et menneske", welcome)
        self.assertNotIn("udgiveren", welcome)

    def test_the_welcome_closes_in_relation_not_information(self):
        # The farewell Maria chose: reading here is something the reader
        # and the hostess may end up doing together.
        self.assertIn("så er vi to", self.welcome())

    def test_the_foreword_is_set_in_the_letters_own_frame(self):
        """Maria's typography direction (2026-07-29), held structurally.

        The foreword is a letter to the reader, so it is set as one: the
        transcriptions' paper frame, their opening face on its heading and
        their closing mark -- as *shared* CSS rules, one selector list per
        piece, so the foreword and the letters cannot drift apart silently.
        The old 34rem cap is gone with it: the foreword sits at the same
        measure the letters do.
        """
        with open(
            os.path.join(STATIC_DIRECTORY, "site.css"), encoding="utf-8"
        ) as file:
            rules = re.findall(r"([^{}]+)\{([^{}]*)\}", file.read())
        self.assertTrue(
            any(
                ".transcription" in sel and ".presentation" in sel
                for sel, body in rules
                if "background: var(--paper)" in body
            ),
            "the letter frame rule no longer covers the foreword",
        )
        self.assertTrue(
            any(
                ".transcription::after" in sel and ".presentation::after" in sel
                for sel, _ in rules
            ),
            "the closing mark is no longer shared",
        )
        self.assertTrue(
            any(
                ".tei-salute .tei-l" in sel and ".presentation h2" in sel
                for sel, _ in rules
            ),
            "the opening face is no longer shared",
        )
        self.assertEqual(
            [],
            [sel for sel, body in rules if ".presentation" in sel and "max-width" in body],
            "the foreword is capped narrower than the letters",
        )

    def test_her_signature_is_the_link_to_her_story(self):
        """The old "who am I?" sentence became a link.

        Maria's call (2026-07-29): instead of the foreword explaining her,
        the signature itself points at the Om page's section about her --
        the anchor the Om page already carries.
        """
        welcome = self.welcome()
        sign = welcome.split('class="presentation-sign"', 1)[1]
        self.assertIn('href="om/#notabene"', sign)
        self.assertIn("Maria Notabene", sign)

    def test_the_welcome_promises_no_man_behind_the_philosopher(self):
        # The one thing a Kierkegaard letter site must not say.
        self.assertNotIn("bag filosoffen", self.index)
        self.assertNotIn("mennesket bag", self.index)

    def test_the_welcome_is_the_front_pages_alone(self):
        # An editorial voice earns its place where a reader is choosing what
        # to read. On the letter's own page the letter has the word.
        for parts in (("brev", "1", "index.html"), ("personer", "index.html")):
            self.assertNotIn('class="presentation"', self.read(*parts))

    def test_a_build_without_the_curated_layer_still_has_her_welcome(self):
        """She is prose in the generator, not data: no dataset can remove her.

        The summaries can be thrown away and the site still stands; the
        welcome is part of the display layer itself.
        """
        with tempfile.TemporaryDirectory() as other:
            build_site(self.volumes, other)
            self.assertIn(
                'class="presentation"', self.read_from(other, "index.html")
            )

    # -- the Om page ------------------------------------------------------

    def test_the_om_page_is_built(self):
        self.assertTrue(
            os.path.exists(os.path.join(self.directory.name, "om", "index.html"))
        )
        self.assertIn("demonstrationsvisning", self.about)

    def test_the_om_page_states_the_architecture_note(self):
        """The thesis, in the approved text's own words (Maria, 2026-08-02).

        The old page said "Det er en pointe og ikke en spareøvelse". Maria
        ruled that out: it is both, and pretending otherwise made the page
        sound defensive about the one thing it is proudest of.
        """
        self.assertIn("tyndt og udskifteligt formidlingslag", self.about)
        self.assertIn("Det er både en pointe og en spareøvelse", self.about)
        self.assertNotIn("ikke en spareøvelse", self.about)
        self.assertIn(
            "Denne visning må gerne smides væk. Originalfilerne i SKS må ikke.",
            self.about,
        )

    def test_the_om_page_names_the_source_and_its_licence(self):
        self.assertIn("kb-dk/SKS_tei", self.about)
        self.assertIn("CC0", self.about)
        self.assertIn(FOOTER_LINKS[0], self.about)

    def test_the_om_page_points_at_the_records_instead_of_printing_the_commit(self):
        """The chain is linked to, not recited (Maria's ruling, 2026-08-03).

        The page used to print the forty-character commit hash. It now
        sends the reader to the two documents that carry it -- the
        provenance record beside the vendored files and the technical
        notes in the repo -- because a hash on a prose page is a fact
        nobody can check *here* anyway, and the page reads better without
        it. The weakening is acceptable exactly because the build still
        verifies: ``ProvenanceTest`` holds the notes' commit against
        ``PROVENANCE.md``, and the repository address the page links still
        comes from the record rather than from the links table.
        """
        recorded = self.read_from(VENDOR, "PROVENANCE.md")
        self.assertIn(self.provenance["commit"], recorded)
        self.assertNotIn(self.provenance["commit"], self.about)
        self.assertIn("proveniensdokument", self.about)
        self.assertIn("indholdstekniske noter", self.about)
        self.assertIn(
            'href="%s/blob/main/data/vendor/PROVENANCE.md"' % PROJECT_REPOSITORY,
            self.about,
        )
        self.assertIn(
            'href="%s/blob/main/docs/content-notes.md"' % PROJECT_REPOSITORY,
            self.about,
        )

    def test_the_om_page_sends_the_reader_to_the_publishers_own_edition(self):
        self.assertIn("tekster.kb.dk/sks", self.about)

    def test_the_om_page_names_the_code_licence(self):
        self.assertIn("MIT", self.about)

    def test_the_om_page_discloses_the_presenter_as_fiction(self):
        disclosure = self.about.split('id="notabene"', 1)[1]
        self.assertIn("Maria Notabene", disclosure)
        self.assertIn("opdigtet", disclosure)
        self.assertIn("pseudonym", disclosure)
        self.assertIn("Claude", disclosure)

    def test_the_presenter_is_a_descendant_and_no_longer_the_wife(self):
        """Maria's ruling (2026-08-03): "en efterkommer", not "konen".

        Nicolaus Notabene's wife is a character in a book from 1844; a
        presenter writing in 2026 cannot be her without the fiction
        reaching into the material, which is the one thing it may never
        do. "En efterkommer" keeps the inheritance and drops the claim --
        and, like the rest of her prose, it leaves the comic *Forord*
        joke felt rather than named.
        """
        disclosure = self.about.split('id="notabene"', 1)[1]
        self.assertIn("Nu har en efterkommer taget pennen", disclosure)
        self.assertNotIn("Nu har konen taget pennen", disclosure)

    def test_the_om_page_introduces_the_jargon_it_cannot_avoid(self):
        """TEI and SKS are explained, not assumed (korrektur, 2026-07-28).

        The page is read by people deciding whether to believe it, not by
        people who already know what a TEI file is. The words stay -- they
        are the honest names for the things -- but each one arrives with
        the plain Danish that says what it means. "Commit" left the page
        with the hash (2026-08-03), so it no longer needs unfolding here.
        """
        self.assertIn("Formatet hedder TEI, Text Encoding Initiative", self.about)
        self.assertIn("kodes til videnskabelig brug", self.about)
        self.assertIn("<i>Søren Kierkegaards Skrifter</i> (SKS)", self.about)

    def test_the_edition_speaks_under_its_own_name_away_from_this_page(self):
        """"Udgaven" is only unambiguous beside the page that names it.

        Maria's call (korrektur item 31): everywhere the edition makes a
        claim -- what it dates, what it marked up, whom it names as a
        sender -- it makes it as SKS, so a reader who landed on a person
        page from a search knows whose claim they are reading. The Om page
        keeps "udgaven": there the edition has just been named in full.
        """
        claims = (
            (("index.html",), "Breve, som SKS kun daterer til et år"),
            (("personer", "index.html"), "som SKS selv har mærket op"),
            (("personer", "index.html"), "skrevet ud af SKS' egen kommentar"),
            (
                ("person", "kierkegaard-peter-christian", "index.html"),
                "Breve, hvor SKS angiver",
            ),
            (
                ("person", "aabye-cicilie", "index.html"),
                "SKS' kommentar giver ingen biografisk note",
            ),
            (
                ("person", "victor-eremita", "index.html"),
                "SKS' kommentar nævner personen",
            ),
            (("tidslinje", "index.html"), "brev, som SKS daterer til dagen"),
        )
        for parts, claim in claims:
            self.assertIn(claim, self.read(*parts), "/".join(parts))
        self.assertIn("udgaven", self.about)

    def test_the_om_page_says_where_the_resumes_sit_and_is_right_about_it(self):
        """The claim about the resumés has to survive a look at a letter page.

        It read "de står med vilje ikke på brevenes egne sider" until this
        test was written, and that had stopped being true: since every row
        of "Samme brevveksling" got its resumé -- the current letter's
        included -- a letter page carries the letter's own two lines. What
        is still true, and what the page now says, is that she never sits
        *above* a transcription. So the claim is checked against a built
        letter: every resumé on it comes after the letter's own text.
        """
        disclosure = self.about.split('id="notabene"', 1)[1]
        self.assertIn("ét sted, hun aldrig sidder: oven over en brevtekst", disclosure)
        self.assertNotIn("brevenes egne sider", disclosure)

        letter = self.read("brev", "1", "index.html")
        transcription = letter.index('class="transcription"')
        positions = [
            found.start()
            for found in re.finditer(r'class="letter-summary"', letter)
        ]
        self.assertTrue(positions)          # brev 1 does carry its own
        for position in positions:
            self.assertGreater(position, transcription)

    def test_the_om_page_explains_where_the_biographies_come_from(self):
        """The filename left the page with the rest of the machinery.

        The approved text (2026-08-03) says where a biography comes from in
        words a reader can act on -- the edition's own commentary notes,
        cited under each biography -- instead of naming ``kom.xml``, which
        now lives in the technical notes the page links.
        """
        self.assertIn("biografien på udgavens kommentarnoter", self.about)
        self.assertIn("med henvisning til den note, den bygger på", self.about)

    def test_a_build_without_a_provenance_record_claims_nothing_it_cannot_show(self):
        """No record, no claim about one -- the page keeps only what is true.

        Since 2026-08-03 the page prints no commit at all; what it does
        claim is that the copy came from one particular release of the
        files and that the chain is written down in the project's
        provenance document. A build with no ``PROVENANCE.md`` beside the
        files cannot vouch for either, so both the sentence and its two
        links go, and the paragraph keeps the part that is still true: the
        copy lies unchanged in the project. The repository is still named,
        because that is the project's own prose.
        """
        with tempfile.TemporaryDirectory() as other:
            build_site(self.volumes, other, context=self.context)
            about = self.read_from(other, "om", "index.html")
            self.assertIn("kb-dk/SKS_tei", about)
            self.assertIn("Kopien ligger uændret i projektet", about)
            self.assertNotIn(self.provenance["commit"], about)
            self.assertNotIn("hentet fra én bestemt udgivelse af filerne", about)
            self.assertNotIn("proveniensdokument", about)

    def test_the_om_page_carries_its_sources_as_numbered_notes(self):
        """Every claim about the outside world is footnoted, and the notes work.

        The text makes eight statements no reader can check against the
        letters -- when the papers were given away, when the research
        centre was founded, who edited volume 28 -- and each carries a
        marker into the note list at the foot of the page. Markers and
        notes are generated from the same numbering, so a note without a
        marker (or the other way round) is a broken page, not a detail.
        """
        markers = re.findall(r'<sup><a href="#note-(\d+)">(\d+)</a></sup>', self.about)
        notes = re.findall(r'<li id="note-(\d+)">', self.about)
        self.assertEqual([str(number) for number in range(1, 9)], notes)
        self.assertEqual(set(notes), {href for href, _ in markers})
        for href, label in markers:
            self.assertEqual(href, label, "the marker shows a number it does not go to")

    def test_the_om_pages_sections_keep_the_anchors_that_are_linked_to(self):
        """Section ids are addresses other pages and readers already hold.

        ``#notabene`` is the one that must never move: the front page's
        signature links straight at it (held by
        ``test_her_signature_is_the_link_to_her_story``). The rest are the
        approved text's own sections, kept as anchors so a reader can send
        someone the paragraph rather than the page.
        """
        for anchor in (
            "forskningsprojektet",
            "originalteksterne",
            "formidlingen",
            "notabene",
            "kildekode",
            "noter",
        ):
            self.assertIn('id="%s"' % anchor, self.about)

    def test_every_number_the_om_page_claims_matches_the_built_site(self):
        """The page counts the site it belongs to; the test recounts it.

        Nine figures in the text are claims about this build -- pages,
        letters, groups, person pages, biographies, summaries and the
        timeline's four. Each sentence here is assembled from a fresh
        count of what the build actually wrote, so a corpus or a dataset
        that grows breaks the sentence loudly instead of leaving the page
        quietly wrong. It is the same standard the text sets for itself:
        the page keeps saying true things about itself.
        """
        root = self.directory.name
        timeline = self.read("tidslinje", "index.html")
        undated = timeline.split('class="tl-undated-list"', 1)[1].split("</ul>", 1)[0]
        persons = sorted(os.listdir(os.path.join(root, "person")))
        biographies = sum(
            1
            for slug in persons
            if 'class="person-bio"' in self.read("person", slug, "index.html")
        )
        pages = len(_built_pages(root))
        letters = len(os.listdir(os.path.join(root, "brev")))
        summaries = self.index.count('class="letter-summary"')
        placed = timeline.count('class="tl-letter tl-letter--') + timeline.count(
            'class="tl-vague-item"'
        )
        claims = (
            "efterlader %d færdige HTML-sider" % pages,
            "Det giver %d breve fra 1829 til 1855" % letters,
            "alle %d breve står der stadig som almindelig tekst" % letters,
            "får sin side – %d i alt" % len(persons),
            "På %d af siderne står desuden en kort biografi" % biographies,
            "de %d resuméer i brevoversigten er %d små forord" % (summaries, summaries),
            "%d breve placeret i et år, %d uden datering, %d skrifter udgivet i "
            "hans levetid og %d bopæle"
            % (
                placed,
                undated.count("<li"),
                timeline.count('class="tl-work-item'),
                timeline.count('class="tl-home-period"'),
            ),
        )
        for claim in claims:
            self.assertIn(claim, self.about)
        # The fourteen groups are spelled out in the prose, so the figure
        # is checked against the build and the word against the page.
        self.assertEqual(14, self.result["volumes"])
        self.assertIn("Fjorten grupper af korrespondancer", self.about)

    def test_the_om_page_reports_the_true_number_of_automated_tests(self):
        """The page's boast, counted rather than believed.

        "siden bliver ved med at sige de sande ting om sig selv" is the
        text's own promise, and it is made in a sentence that names a
        number of tests -- so the number comes from unittest discovery
        over this repository. Adding a test now fails this one until the
        sentence is updated, which is the cheapest way to keep a boast
        from going stale in silence.
        """
        counted = unittest.defaultTestLoader.discover(REPO_ROOT).countTestCases()
        self.assertIn("visningen har %d automatiske tests" % counted, self.about)
        # The technical notes the page links make the same claim, in the
        # same repository, and would otherwise go stale on their own.
        notes_path = os.path.join(REPO_ROOT, "docs", "content-notes.md")
        with open(notes_path, encoding="utf-8") as file:
            self.assertRegex(file.read(), r"%d\s+automated tests" % counted)
        # And the project guide, which went quietly stale once (339 while
        # the suite counted 381; noticed 2026-08-25). Same cure: count it.
        guide_path = os.path.join(REPO_ROOT, "CLAUDE.md")
        with open(guide_path, encoding="utf-8") as file:
            self.assertRegex(file.read(), r"%d\s+tests green" % counted)

    def test_the_om_page_keeps_the_sites_danish_dashes(self):
        """En dashes, like every other Danish string the site renders.

        The approved manuscript was typed with em dashes; they were
        converted on the way into the generator, because the korrektur of
        2026-07-28 settled the site's Danish punctuation and
        ``DanishEmDashesTest`` holds the datasets to it. This holds the
        longest page of prose on the site to the same rule.
        """
        self.assertNotIn("—", self.about)

    # -- the site around them ---------------------------------------------

    def test_every_page_can_reach_the_om_page(self):
        pairs = (
            (("index.html",), 'href="om/"'),
            (("brev", "1", "index.html"), 'href="../../om/"'),
            (("personer", "index.html"), 'href="../om/"'),
            (("person", "sokrates", "index.html"), 'href="../../om/"'),
            (("tidslinje", "index.html"), 'href="../om/"'),
            (("om", "index.html"), 'aria-current="page"'),
        )
        for parts, expected in pairs:
            self.assertIn(expected, self.read(*parts), "/".join(parts))

    def test_titles_name_kierkegaard_for_the_world(self):
        """Maria's SEO ruling (2026-08-03): a title must say what the page
        is without the site as context -- letters carry their own names,
        every other page carries the corpus. ❖ separates page from site in
        the browser tab only; no visible content changes.
        """
        pairs = (
            (
                ("index.html",),
                "<title>Søren Kierkegaards breve ❖ epistel</title>",
            ),
            (
                ("brev", "1", "index.html"),
                "<title>Brev 1: Søren Kierkegaard til P.C. Kierkegaard"
                " ❖ epistel</title>",
            ),
            (
                ("personer", "index.html"),
                "<title>Personer – Søren Kierkegaards breve ❖ epistel</title>",
            ),
            (
                ("tidslinje", "index.html"),
                "<title>Tidslinje – Søren Kierkegaards breve ❖ epistel</title>",
            ),
            (
                ("om", "index.html"),
                "<title>Om – Søren Kierkegaards breve ❖ epistel</title>",
            ),
            (
                ("person", "kierkegaard-peter-christian", "index.html"),
                "<title>Peter Christian Kierkegaard – Søren Kierkegaards"
                " breve ❖ epistel</title>",
            ),
        )
        for parts, expected in pairs:
            self.assertIn(expected, self.read(*parts), "/".join(parts))

    def test_a_letter_description_carries_the_details(self):
        # The title now holds the names, so the description holds the rest:
        # date first, then the resumé when this build wrote one.
        page = self.read("brev", "1", "index.html")
        self.assertIn(
            'name="description" content="Brev 1, Søren Kierkegaard til '
            "P.C. Kierkegaard, 8. marts 1829. Søren bruger den første "
            "halve side",
            page,
        )

    def test_social_metadata_is_present_and_host_agnostic(self):
        # Open Graph without og:url and og:image: both demand an absolute
        # address, and the built output stays host-agnostic on purpose.
        for parts in (("index.html",), ("brev", "1", "index.html")):
            page = self.read(*parts)
            self.assertIn('property="og:title"', page)
            self.assertIn('property="og:description"', page)
            self.assertIn('property="og:type" content="website"', page)
            self.assertIn('property="og:site_name" content="epistel"', page)
            self.assertIn('property="og:locale" content="da_DK"', page)
            self.assertIn('name="twitter:card" content="summary"', page)
            self.assertNotIn("og:url", page)
            self.assertNotIn("og:image", page)

    def test_robots_are_welcome(self):
        robots = self.read("robots.txt")
        self.assertIn("User-agent: *", robots)
        self.assertIn("Allow: /", robots)

    def test_a_letter_links_to_its_own_place_in_the_edition(self):
        """Every letter page carries one quiet deep link to the annotated
        edition (Maria's crediting decision, 2026-08-03). The address comes
        from links.json's template entry, so the self-containment allowlist
        and the pages move together; the scheme was verified against
        tekster.kb.dk 2026-08-01, sub-numbers verbatim.
        """
        page = self.read("brev", "43", "index.html")
        self.assertIn("<dt>SKS</dt>", page)
        self.assertIn(
            'href="https://tekster.kb.dk/text/sks-b43-txt-root#n43"', page
        )
        draft = self.read("brev", "159.1", "index.html")
        self.assertIn(
            'href="https://tekster.kb.dk/text/sks-b127-txt-root#n159.1"', draft
        )

    def test_a_stub_links_to_its_group_root_not_a_dead_anchor(self):
        # The three cross-reference stubs have no #n anchor at the
        # publisher's; they link to the group root instead of at nothing.
        page = self.read("brev", "b171-n171a", "index.html")
        self.assertIn(
            'href="https://tekster.kb.dk/text/sks-b171-txt-root"', page
        )
        self.assertNotIn("txt-root#n-", page)

    def test_a_publication_links_to_its_tekstredegoerelse(self):
        """Each publication on the timeline links to the SKS account of its
        own dating (Maria's crediting decision, 2026-08-03). The addresses
        travel per entry in publications.json; the timeline links only the
        ones under the declared tekster.kb.dk prefix and leaves every other
        source as text -- no address outside the table's permission.
        """
        page = self.read("tidslinje", "index.html")
        self.assertIn(
            'href="https://tekster.kb.dk/text/sks-fqa-txr-root"', page
        )

    def test_every_built_page_is_self_contained_within_its_scope(self):
        for path in _built_pages(self.directory.name):
            page = self.read_from(path)
            rel = os.path.relpath(path, self.directory.name)
            top = rel.split(os.sep)[0]
            allowed = {
                "om": ABOUT_LINKS,
                "brev": BREV_LINKS,
                "tidslinje": TIMELINE_LINKS,
            }.get(top, FOOTER_LINKS)
            with self.subTest(page=rel):
                assert_self_contained(self, page, allowed)

    def test_every_declared_link_appears_where_its_scope_says(self):
        """The table and the pages cannot drift apart, in either direction.

        A page pointing at an undeclared address fails self-containment; a
        declared link no page renders fails here. Adding a link is therefore
        always two things -- a table entry and a place on a page -- and
        removing one is one thing, caught everywhere.
        """
        for entry in _links_data()["links"]:
            # A template or prefix entry's href is the declared prefix; the
            # rendered address continues past it, so the match is open-ended.
            expected = (
                'href="%s' % entry["href"]
                if entry.get("template") or entry.get("prefix")
                else 'href="%s"' % entry["href"]
            )
            with self.subTest(link=entry["id"]):
                if entry["scope"] == "footer":
                    for parts in (
                        ("index.html",),
                        ("brev", "1", "index.html"),
                        ("om", "index.html"),
                    ):
                        self.assertIn(expected, self.read(*parts), "/".join(parts))
                elif entry["scope"] == "brev":
                    self.assertIn(expected, self.read("brev", "1", "index.html"))
                elif entry["scope"] == "tidslinje":
                    self.assertIn(expected, self.read("tidslinje", "index.html"))
                else:
                    self.assertIn(expected, self.about)

    def test_a_build_without_the_links_table_points_nowhere_but_says_the_same(self):
        """No table, no anchors -- and no words lost.

        The licence, the repository and the publisher's edition are still
        named in prose; only the addresses are gone. That keeps the table
        disposable the way every dataset here is: removing it removes
        exactly the links, never the honesty.
        """
        with tempfile.TemporaryDirectory() as other:
            build_site(
                self.volumes, other, context=self.context, provenance=self.provenance
            )
            about = self.read_from(other, "om", "index.html")
            for page in (self.read_from(other, "index.html"), about):
                self.assertNotIn("https://", page)
                self.assertNotIn("http://", page)
            for still_said in ("CC0", "kb-dk/SKS_tei", "tekster.kb.dk/sks"):
                self.assertIn(still_said, about)

    def test_the_site_never_mentions_the_name_she_was_renamed_from(self):
        """Renamed 2026-07-28. Victor Eremita, SK's own pseudonym, stays."""
        for path in _built_files(self.directory.name, (".html", ".css", ".js")):
            with open(path, encoding="utf-8") as file:
                self.assertNotIn(
                    "Victoria",
                    file.read(),
                    os.path.relpath(path, self.directory.name),
                )

    def test_the_om_page_build_is_deterministic(self):
        with tempfile.TemporaryDirectory() as other:
            build_site(
                self.volumes,
                other,
                context=self.context,
                provenance=self.provenance,
                links=self.links,
            )
            self.assertEqual(self.about, self.read_from(other, "om", "index.html"))


class SharedColumnTest(unittest.TestCase):
    """Header band, main and footer band align on one shell column.

    The shared rule near the top of site.css hands ``.site-footer > p``
    its ``margin-inline: auto``. The header's child rules are single-class
    selectors and lose to it on specificity, but any ``.site-footer p``
    rule ties with it -- so a later ``margin:`` shorthand there resets the
    inline margins and pins the footer text to the left edge, which is
    exactly how the footer shipped misaligned (caught by Maria,
    2026-07-29). Block-axis margins are fine; the shorthand is not.
    """

    @classmethod
    def setUpClass(cls):
        with open(
            os.path.join(STATIC_DIRECTORY, "site.css"), encoding="utf-8"
        ) as file:
            cls.rules = re.findall(r"([^{}]+)\{([^{}]*)\}", file.read())

    def test_the_shared_column_rule_covers_all_three_bands(self):
        shared = [
            sel
            for sel, body in self.rules
            if "margin-inline: auto" in body and "max-width: var(--shell)" in body
        ]
        self.assertTrue(
            any(
                ".site-header > p" in sel
                and ".site-footer > p" in sel
                and "main" in sel
                for sel in shared
            )
        )

    def test_no_footer_rule_clobbers_the_centering_shorthand(self):
        clobbers = [
            sel.strip()
            for sel, body in self.rules
            if ".site-footer" in sel and re.search(r"(?<![-\w])margin\s*:", body)
        ]
        self.assertEqual([], clobbers)


class LinksTableTest(unittest.TestCase):
    """data/links.json: the one list of addresses the site may point at.

    The table exists so that changing the site's external links is a data
    edit both the pages and this suite pick up. These tests hold the table
    itself to account: complete entries, no duplicates, only scopes the
    display knows, and a repository address that cannot quietly disagree
    with the provenance record beside the vendored files.
    """

    @classmethod
    def setUpClass(cls):
        cls.data = _links_data()
        cls.links = cls.data["links"]

    def test_every_link_is_fully_described(self):
        for entry in self.links:
            for field in ("id", "href", "label", "rel", "scope"):
                self.assertTrue(entry.get(field), (entry.get("id"), field))

    def test_ids_and_addresses_are_unique(self):
        ids = [entry["id"] for entry in self.links]
        hrefs = [entry["href"] for entry in self.links]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual(len(hrefs), len(set(hrefs)))

    def test_scopes_are_the_ones_the_display_knows(self):
        for entry in self.links:
            self.assertIn(
                entry["scope"],
                ("footer", "om", "brev", "tidslinje"),
                entry["id"],
            )

    def test_the_repository_link_agrees_with_the_provenance_record(self):
        recorded = load_provenance(VENDOR)
        by_id = {entry["id"]: entry for entry in self.links}
        self.assertEqual(recorded["repository"], by_id["upstream-repository"]["href"])

    def test_the_file_says_it_is_ours(self):
        self.assertTrue(self.data["_meta"]["notFromTEI"])

    def test_the_loader_hands_the_table_over_unchanged(self):
        loaded = load_links(LINKS_PATH)
        self.assertEqual(self.links, loaded["links"])
        self.assertEqual(self.data["_meta"], loaded["meta"])

    def test_a_missing_file_yields_nothing(self):
        with tempfile.TemporaryDirectory() as empty:
            self.assertIsNone(load_links(os.path.join(empty, "links.json")))

    def test_a_table_with_no_links_is_a_defect_not_a_silence(self):
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, "links.json")
            with open(path, "w", encoding="utf-8") as file:
                json.dump({"_meta": {}}, file)
            with self.assertRaises(ValueError):
                load_links(path)


class ProvenanceTest(unittest.TestCase):
    """The vendored files' record of themselves, read rather than retyped."""

    def test_the_record_names_the_repository_and_the_commit(self):
        recorded = load_provenance(VENDOR)
        self.assertEqual("https://github.com/kb-dk/SKS_tei", recorded["repository"])
        self.assertRegex(recorded["commit"], r"^[0-9a-f]{40}$")

    def test_a_directory_without_a_record_yields_nothing(self):
        with tempfile.TemporaryDirectory() as empty:
            self.assertIsNone(load_provenance(empty))

    def test_the_technical_notes_pin_the_same_commit_as_the_record(self):
        """docs/content-notes.md cannot drift from PROVENANCE.md.

        Maria's ruling (2026-08-03): the Om page no longer shows the pinned
        commit itself -- the technical notes in the repo do, and the page
        links there. The weakening is acceptable exactly because the build
        still verifies: this test holds the notes' commit to the record
        beside the files, the same guarantee the page used to carry.
        """
        recorded = load_provenance(VENDOR)
        notes_path = os.path.join(REPO_ROOT, "docs", "content-notes.md")
        with open(notes_path, encoding="utf-8") as file:
            notes = file.read()
        self.assertIn(recorded["commit"], notes)
        self.assertIn(recorded["repository"].rsplit("/", 1)[-1], notes)


def _built_pages(root):
    """Every HTML page the build wrote, in a stable order."""
    return [path for path in _built_files(root, (".html",))]


def _built_files(root, suffixes):
    found = []
    for directory, _, names in os.walk(root):
        for name in sorted(names):
            if name.endswith(suffixes):
                found.append(os.path.join(directory, name))
    return sorted(found)


def _escape(value):
    return value.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


class DanishEmDashesTest(unittest.TestCase):
    """Verify that Danish editorial text uses en dashes (–), not em dashes (—)."""

    def test_no_em_dashes_in_summaries(self):
        """summaries.json text fields must use en dashes, not em dashes."""
        with open(
            os.path.join(CONTEXT, "summaries.json"), encoding="utf-8"
        ) as file:
            data = json.load(file)
        for letter_id, summary in data.items():
            if summary and isinstance(summary, str):
                self.assertNotIn("—", summary, f"Em dash found in summaries[{letter_id}]")

    def test_no_em_dashes_in_bios(self):
        """bios.json rendered text must use en dashes, not em dashes."""
        with open(os.path.join(CONTEXT, "bios.json"), encoding="utf-8") as file:
            data = json.load(file)
        for person, bio_entry in data.items():
            if bio_entry and isinstance(bio_entry, dict):
                # Only check the 'bio' field; 'note' is dev-facing
                bio_text = bio_entry.get("bio")
                if bio_text and isinstance(bio_text, str):
                    self.assertNotIn(
                        "—", bio_text, f"Em dash found in bios[{person}][bio]"
                    )

    def test_no_em_dashes_in_publications(self):
        """publications.json rendered fields must use en dashes, not em dashes."""
        with open(
            os.path.join(CONTEXT, "publications.json"), encoding="utf-8"
        ) as file:
            data = json.load(file)
        for person, pubs in data.items():
            if pubs and isinstance(pubs, list):
                for idx, pub in enumerate(pubs):
                    if pub and isinstance(pub, dict):
                        # Only check rendered fields; 'note' is dev-facing
                        for field in ["title", "date"]:
                            value = pub.get(field)
                            if value and isinstance(value, str):
                                self.assertNotIn(
                                    "—",
                                    value,
                                    f"Em dash found in publications[{person}][{idx}][{field}]",
                                )

    def test_no_em_dashes_in_residences(self):
        """residences.json rendered fields must use en dashes, not em dashes."""
        with open(
            os.path.join(CONTEXT, "residences.json"), encoding="utf-8"
        ) as file:
            data = json.load(file)
        for person, residences in data.items():
            if residences and isinstance(residences, list):
                for idx, residence in enumerate(residences):
                    if residence and isinstance(residence, dict):
                        # Only check rendered fields; 'note' is dev-facing
                        for field in ["location", "date"]:
                            value = residence.get(field)
                            if value and isinstance(value, str):
                                self.assertNotIn(
                                    "—",
                                    value,
                                    f"Em dash found in residences[{person}][{idx}][{field}]",
                                )

    def test_no_em_dashes_in_links_labels(self):
        """data/links.json label strings must use en dashes, not em dashes."""
        links_path = os.path.join(REPO_ROOT, "data", "links.json")
        with open(links_path, encoding="utf-8") as file:
            data = json.load(file)
        for idx, link in enumerate(data.get("links", [])):
            label = link.get("label")
            if label and isinstance(label, str):
                self.assertNotIn(
                    "—", label, f"Em dash found in links[{idx}].label"
                )

    def test_no_em_dashes_in_notabene(self):
        """docs/notabene.md must use en dashes, not em dashes."""
        notabene_path = os.path.join(REPO_ROOT, "docs", "notabene.md")
        with open(notabene_path, encoding="utf-8") as file:
            content = file.read()
        self.assertNotIn("—", content, "Em dash found in docs/notabene.md")



if __name__ == "__main__":
    unittest.main()
