"""Tests for the TEI -> JSON parser, run against the real vendored TEI files.

The vendored files (data/vendor/<volume>/txt.xml) are read-only truth: these
tests read the actual transcription out of them, so they fail loudly if the
parser starts inventing, dropping or reshaping content. b1 is covered in
depth; ``CorpusTest`` and the spot checks below hold the parser to the other
thirteen volumes as well.

Run from the repository root:

    python3 -m unittest
"""

import json
import os
import re
import unittest
import xml.etree.ElementTree as ET

from pipeline.corpus import parse_corpus, volume_names
from pipeline.parse_tei import parse_tei, parse_volume, plain_text

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VENDOR = os.path.join(REPO_ROOT, "data", "vendor")
B1_PATH = os.path.join(VENDOR, "b1", "txt.xml")

# The whole corpus parses in a fraction of a second, but it is still parsed
# once for all the tests that need it rather than once per test class.
_CORPUS = []


def corpus():
    if not _CORPUS:
        _CORPUS.extend(parse_corpus(VENDOR))
    return _CORPUS


def nodes_of_type(nodes, wanted):
    """Collect every node of a given type from a body tree, depth first.

    Body content is a tree (a letter holds an opener, which holds a salute,
    which holds lines), so tests cannot assume a flat list of blocks.
    """
    found = []
    for node in nodes:
        if node.get("type") == wanted:
            found.append(node)
        found.extend(nodes_of_type(node.get("content", []), wanted))
        found.extend(nodes_of_type(node.get("variants", []), wanted))
        found.extend(nodes_of_type(node.get("alternatives", []), wanted))
    return found


def all_strings(value):
    """Yield every string found anywhere in a JSON-shaped structure."""
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for key, item in value.items():
            yield key
            yield from all_strings(item)
    elif isinstance(value, list):
        for item in value:
            yield from all_strings(item)


class VolumeStructureTest(unittest.TestCase):
    """The shape of the volume as a whole."""

    @classmethod
    def setUpClass(cls):
        cls.volume = parse_volume(B1_PATH)

    def test_volume_is_named_after_its_directory(self):
        self.assertEqual("b1", self.volume["volume"])

    def test_volume_contains_42_letters(self):
        self.assertEqual(42, len(self.volume["letters"]))

    def test_letter_ids_are_the_sequence_from_the_n_attribute(self):
        ids = [letter["id"] for letter in self.volume["letters"]]
        self.assertEqual([str(n) for n in range(1, 43)], ids)

    def test_letters_keep_their_xml_ids(self):
        first = self.volume["letters"][0]
        self.assertEqual("n1", first["xmlId"])
        self.assertEqual("n42", self.volume["letters"][-1]["xmlId"])

    def test_every_tei_element_in_b1_is_handled(self):
        # Warnings name TEI elements the parser does not model. b1 should be
        # fully covered; a non-empty list here means content is only surviving
        # through the generic fallback.
        self.assertEqual([], self.volume["warnings"])

    def test_letters_are_grouped_by_correspondence_context(self):
        groups = self.volume["groups"]
        self.assertEqual(8, len(groups))
        first = groups[0]
        self.assertEqual("correspContext1", first["id"])
        self.assertEqual("P.C. Kierkegaard", first["heading"])
        self.assertEqual([str(n) for n in range(1, 23)], first["letterIds"])
        self.assertIn("Peter Christian Kierkegaard", first["notes"])

    def test_every_letter_points_at_the_group_it_belongs_to(self):
        by_id = {group["id"]: group for group in self.volume["groups"]}
        for letter in self.volume["letters"]:
            group_id = letter["context"]["groupId"]
            self.assertIn(group_id, by_id, "letter %s" % letter["id"])
            self.assertIn(letter["id"], by_id[group_id]["letterIds"])


class LetterMetadataTest(unittest.TestCase):
    """correspDesc -> sender / recipient / date, end to end for letter 1."""

    @classmethod
    def setUpClass(cls):
        cls.volume = parse_volume(B1_PATH)
        cls.letters = {letter["id"]: letter for letter in cls.volume["letters"]}

    def test_letter_1_sender_recipient_and_date(self):
        letter = self.letters["1"]
        self.assertEqual("SK", letter["sender"]["name"])
        self.assertEqual("Kierkegaard, P.C.", letter["recipient"]["name"])
        self.assertEqual("18290308", letter["sender"]["date"]["raw"])
        self.assertEqual("1829-03-08", letter["sender"]["date"]["iso"])
        self.assertEqual("day", letter["sender"]["date"]["precision"])

    def test_letter_1_heading_comes_from_the_letter_header(self):
        self.assertEqual(
            "Fra SK · 8. marts 1829 · til P.C. Kierkegaard",
            self.letters["1"]["heading"],
        )

    def test_recipient_has_no_date_in_this_volume(self):
        # Only the "sent" action carries a date in b1; the parser must not
        # borrow the sender's date for the recipient.
        self.assertIsNone(self.letters["1"]["recipient"]["date"])

    def test_no_place_is_recorded_in_correspaction(self):
        # b1 encodes no place of sending/receipt. The slot exists (other
        # volumes may fill it) but must stay null rather than be guessed at
        # from the dateline inside the letter.
        self.assertIsNone(self.letters["1"]["sender"]["place"])
        self.assertIsNone(self.letters["1"]["recipient"]["place"])

    def test_year_only_date_is_kept_as_a_year(self):
        # Letter 24: <date when="18370000" notAfter="18390000" source="supplied"/>
        date = self.letters["24"]["sender"]["date"]
        self.assertEqual("18370000", date["raw"])
        self.assertEqual("1837", date["iso"])
        self.assertEqual("year", date["precision"])
        self.assertEqual(1837, date["year"])
        self.assertIsNone(date["month"])
        self.assertIsNone(date["day"])
        self.assertEqual("supplied", date["source"])
        self.assertEqual("18390000", date["notAfter"]["raw"])
        self.assertEqual("1839", date["notAfter"]["iso"])

    def test_month_only_date_is_kept_as_a_month(self):
        # Letter 19: <date when="18481200" source="supplied"/>
        date = self.letters["19"]["sender"]["date"]
        self.assertEqual("18481200", date["raw"])
        self.assertEqual("1848-12", date["iso"])
        self.assertEqual("month", date["precision"])
        self.assertEqual(12, date["month"])
        self.assertIsNone(date["day"])

    def test_stamped_date_keeps_its_source(self):
        # Letter 4 is dated from the postmark, not by Kierkegaard.
        self.assertEqual("stamp", self.letters["4"]["sender"]["date"]["source"])

    def test_undated_letter_39_keeps_its_editorial_note(self):
        # Letter 39 is the one letter whose correspAction carries a note, and
        # whose generated header is incomplete in the source. Both are kept as
        # they are; nothing is reconstructed.
        letter = self.letters["39"]
        self.assertEqual("· udateret [1846-47]", letter["sender"]["note"])
        self.assertEqual("· til familien", letter["heading"])
        self.assertEqual("18460000", letter["sender"]["date"]["raw"])
        self.assertEqual("year", letter["sender"]["date"]["precision"])

    def test_every_letter_in_b1_has_a_named_sender_and_recipient(self):
        for letter in self.volume["letters"]:
            self.assertTrue(letter["sender"]["name"], "letter %s" % letter["id"])
            self.assertTrue(letter["recipient"]["name"], "letter %s" % letter["id"])


class LetterBodyTest(unittest.TestCase):
    """Letter 1's transcription, checked against the text in the XML."""

    @classmethod
    def setUpClass(cls):
        cls.volume = parse_volume(B1_PATH)
        cls.letters = {letter["id"]: letter for letter in cls.volume["letters"]}
        cls.letter = cls.letters["1"]
        cls.body = cls.letter["body"]

    def test_body_blocks_are_typed_and_have_content(self):
        for block in self.body:
            self.assertIn("type", block)
            self.assertIn("content", block)

    def test_letter_header_is_not_repeated_inside_the_body(self):
        self.assertEqual([], nodes_of_type(self.body, "head"))

    def test_opener_holds_the_salutation(self):
        openers = nodes_of_type(self.body, "opener")
        self.assertEqual(1, len(openers))
        self.assertEqual("Kjære Broder!", plain_text(openers[0]).strip())

    def test_first_paragraph_reads_as_transcribed(self):
        paragraphs = nodes_of_type(self.body, "p")
        self.assertEqual(5, len(paragraphs))
        self.assertTrue(
            plain_text(paragraphs[0]).startswith(
                "Dersom Du skulde slutte Dig til af hvad jeg skrev, "
                "hvorledes jeg levede, kunde Du gjerne falde paa at jeg var "
                "død og borte"
            ),
            plain_text(paragraphs[0])[:200],
        )

    def test_signature_and_dateline_are_kept_as_blocks(self):
        signed = nodes_of_type(self.body, "signed")
        self.assertEqual(1, len(signed))
        signature = plain_text(signed[0])
        self.assertIn("Din hengivne Broder,", signature)
        self.assertIn("Søren.", signature)

        datelines = nodes_of_type(self.body, "dateline")
        self.assertEqual(1, len(datelines))
        dateline = plain_text(datelines[0])
        self.assertIn("Kbh:", dateline)
        self.assertIn("Martz. 1829", dateline)

    def test_closer_wraps_signature_and_dateline(self):
        closers = nodes_of_type(self.body, "closer")
        self.assertEqual(1, len(closers))
        self.assertEqual(1, len(nodes_of_type(closers[0]["content"], "signed")))
        self.assertEqual(1, len(nodes_of_type(closers[0]["content"], "dateline")))

    def test_page_breaks_survive_with_their_numbers(self):
        page_breaks = nodes_of_type(self.body, "pb")
        first = page_breaks[0]
        self.assertEqual("1r", first["n"])
        self.assertEqual("supplied", first["rend"])
        # The printed SKS edition's pagination is a second, independent series.
        sks_pages = [pb["n"] for pb in page_breaks if pb.get("edRef") == "#SKS"]
        self.assertIn("9", sks_pages)
        self.assertIn("10", sks_pages)

    def test_envelope_address_is_kept(self):
        trailers = nodes_of_type(self.body, "trailer")
        self.assertEqual(1, len(trailers))
        self.assertEqual("addrOnEnvelope", trailers[0]["subtype"])
        self.assertIn("P.C. Kierkegaard", plain_text(trailers[0]))

    def test_person_name_keys_survive_into_the_body(self):
        names = nodes_of_type(self.body, "persName")
        keys = [name["key"] for name in names]
        self.assertIn("Fenger, Johannes Ferdinand", keys)
        self.assertIn("Kierkegaard, Søren Aabye", keys)
        fenger = [n for n in names if n["key"] == "Fenger, Johannes Ferdinand"][0]
        self.assertEqual("Fenger", plain_text(fenger))

    def test_place_name_keys_survive_into_the_body(self):
        places = nodes_of_type(self.body, "placeName")
        keys = [place["key"] for place in places]
        self.assertIn("København", keys)

    def test_commentary_references_keep_their_targets(self):
        refs = nodes_of_type(self.body, "ref")
        self.assertTrue(refs)
        first = refs[0]
        self.assertEqual("commentary", first["subtype"])
        self.assertEqual("kom.xml#b-1", first["target"])
        self.assertEqual("Broder", plain_text(first))

    def test_apparatus_variants_stay_out_of_the_reading_text(self):
        # <app><lem>Du</lem><rdg><del>d</del></rdg></app> -- the established
        # reading belongs in the flow, the deleted variant does not.
        text = plain_text(self.body)
        self.assertIn("besluttede Du, at", text)
        self.assertNotIn("besluttede Dud", text)

        apps = nodes_of_type(self.body, "app")
        with_variants = [app for app in apps if app["variants"]]
        self.assertTrue(with_variants)
        variant_text = plain_text(with_variants[0]["variants"])
        self.assertTrue(variant_text)

    def test_witness_details_are_notes_not_reading_text(self):
        # "Kun<unclear>d</unclear><witDetail>ms. beskadiget</witDetail>skaber"
        text = plain_text(self.body)
        self.assertIn("Kundskaber", text)
        self.assertNotIn("ms. beskadiget", text)
        details = nodes_of_type(self.body, "witDetail")
        self.assertIn("ms. beskadiget", [d["note"] for d in details])

    def test_abbreviations_read_as_written_and_keep_their_expansion(self):
        # <choice><abbr>Cand:</abbr><expan>Candidat</expan></choice>
        choices = nodes_of_type(self.body, "choice")
        self.assertTrue(choices)
        abbreviated = [plain_text(choice) for choice in choices]
        self.assertIn("Cand:", abbreviated)
        expansions = [plain_text(choice["alternatives"]) for choice in choices]
        self.assertIn("Candidat", expansions)
        self.assertNotIn("Cand:Candidat", plain_text(self.body))

    def test_editorially_supplied_letters_are_marked_but_readable(self):
        # "en<supplied>d</supplied>" -> reads "end", flagged as supplied.
        self.assertIn("ei andet end Fritagelse", plain_text(self.body))
        supplied = nodes_of_type(self.body, "supplied")
        self.assertIn("d", [plain_text(node) for node in supplied])


class OutputContractTest(unittest.TestCase):
    """Invariants that keep parsing and display separable."""

    @classmethod
    def setUpClass(cls):
        cls.volume = parse_volume(B1_PATH)

    def test_result_round_trips_through_json(self):
        encoded = json.dumps(self.volume, ensure_ascii=False)
        self.assertEqual(self.volume, json.loads(encoded))

    def test_output_contains_no_markup(self):
        for text in all_strings(self.volume):
            self.assertNotIn("<", text)
            self.assertNotIn(">", text)

    def test_every_letter_has_a_non_empty_body(self):
        for letter in self.volume["letters"]:
            self.assertTrue(letter["body"], "letter %s" % letter["id"])


class CorpusTest(unittest.TestCase):
    """All fourteen letter volumes, and the assumptions that tie them together."""

    # The edition's own volume order; a directory is named after the first
    # letter number it holds, so numeric order of the names is edition order.
    EXPECTED_VOLUMES = [
        "b1", "b43", "b70", "b79", "b120", "b127", "b161", "b171",
        "b208", "b234", "b241", "b259", "b276", "b308",
    ]

    # Verified by direct count against the vendored files (2026-07-27).
    EXPECTED_COUNTS = {
        "b1": 42, "b43": 27, "b70": 9, "b79": 41, "b120": 7, "b127": 43,
        "b161": 10, "b171": 40, "b208": 26, "b234": 7, "b241": 18,
        "b259": 17, "b276": 38, "b308": 11,
    }

    @classmethod
    def setUpClass(cls):
        cls.volumes = corpus()
        cls.letters = [
            (volume["volume"], letter)
            for volume in cls.volumes
            for letter in volume["letters"]
        ]

    def test_every_vendored_letter_volume_is_parsed_in_edition_order(self):
        self.assertEqual(self.EXPECTED_VOLUMES, volume_names(VENDOR))
        self.assertEqual(
            self.EXPECTED_VOLUMES, [volume["volume"] for volume in self.volumes]
        )

    def test_the_dedications_are_not_a_letter_volume(self):
        # data/vendor/ded holds <div type="dedication"> inside <div
        # type="work">, with no correspDesc at all: a different model, kept
        # out of the corpus rather than bent into shape. See the build brief.
        self.assertNotIn("ded", volume_names(VENDOR))

    def test_each_volume_holds_the_letters_the_edition_prints_in_it(self):
        counted = {volume["volume"]: len(volume["letters"]) for volume in self.volumes}
        self.assertEqual(self.EXPECTED_COUNTS, counted)
        self.assertEqual(336, len(self.letters))

    def test_every_volume_names_itself_in_its_tei_header(self):
        for volume in self.volumes:
            self.assertTrue(volume["title"], volume["volume"])
            self.assertTrue(volume["shortTitle"], volume["volume"])
        titles = {volume["volume"]: volume["title"] for volume in self.volumes}
        self.assertEqual("Familien Kierkegaard", titles["b1"])
        self.assertEqual("Emil Boesen", titles["b79"])
        self.assertEqual("Regine Olsen, gift Schlegel", titles["b127"])

    def test_letter_numbers_are_unique_across_the_whole_corpus(self):
        """The global-numbering assumption, checked rather than trusted."""
        numbered = [
            letter["id"]
            for _, letter in self.letters
            if re.match(r"^\d+(\.\d+)*$", letter["id"] or "")
        ]
        self.assertEqual(333, len(numbered))
        duplicates = sorted(
            {n for n in numbered if numbered.count(n) > 1}
        )
        self.assertEqual([], duplicates)

    def test_whole_letter_numbers_run_from_1_to_318_without_gaps(self):
        whole = sorted(
            int(letter["id"])
            for _, letter in self.letters
            if (letter["id"] or "").isdigit()
        )
        self.assertEqual(list(range(1, 319)), whole)

    def test_each_volume_starts_at_the_number_its_directory_is_named_after(self):
        for volume in self.volumes:
            first = int(volume["volume"][1:])
            numbers = [
                int(letter["id"])
                for letter in volume["letters"]
                if (letter["id"] or "").isdigit()
            ]
            self.assertEqual(first, min(numbers), volume["volume"])

    def test_sub_numbered_drafts_keep_the_editions_own_number(self):
        # b127 prints nine drafts of letter 159 as 159.1-159.9 and b276 six
        # more; they are letters in their own right, numbered by the edition.
        by_id = {
            "%s/%s" % (volume, letter["id"]) for volume, letter in self.letters
        }
        self.assertIn("b127/159.1", by_id)
        self.assertIn("b127/159.9", by_id)
        self.assertIn("b276/280.1", by_id)
        self.assertIn("b276/304.5", by_id)

    def test_three_letters_carry_no_number_at_all(self):
        """b171 prints three cross-reference stubs with @n="-".

        Their text is printed elsewhere (letters 193 and 194); here they are
        entries pointing at it. The parser keeps the source's "-" rather than
        inventing a number, so they collide with each other -- the display is
        what has to keep their URLs apart.
        """
        unnumbered = [
            (volume, letter)
            for volume, letter in self.letters
            if letter["id"] == "-"
        ]
        self.assertEqual(3, len(unnumbered))
        self.assertEqual({"b171"}, {volume for volume, _ in unnumbered})
        self.assertEqual(
            ["n171a", "n176a", "na"],
            sorted(letter["xmlId"] for _, letter in unnumbered),
        )
        # Each one points the reader at the letter that does carry the text.
        for _, letter in unnumbered:
            self.assertRegex(letter["sender"]["note"], r"^, se Brev 19[34]$")

    def test_every_letter_in_the_corpus_has_an_xml_id(self):
        # The display builds collision-free URLs out of these, so a missing
        # one would be a silent ambiguity.
        for volume, letter in self.letters:
            self.assertTrue(letter["xmlId"], "%s/%s" % (volume, letter["id"]))

    def test_every_letter_belongs_to_a_correspondence_group(self):
        for volume in self.volumes:
            grouped = {
                identifier
                for group in volume["groups"]
                for identifier in group["letterIds"]
            }
            for letter in volume["letters"]:
                self.assertIn(
                    letter["id"], grouped, "%s/%s" % (volume["volume"], letter["id"])
                )

    def test_correspondence_group_ids_repeat_across_volumes(self):
        """Group ids are file-local, not global: every volume starts over.

        Recorded as a test because the index has to prefix them; if the
        edition ever made them unique this test fails and the prefix can go.
        """
        seen = [group["id"] for volume in self.volumes for group in volume["groups"]]
        self.assertEqual(14, seen.count("correspContext1"))

    def test_no_tei_element_in_the_corpus_is_left_unmodelled(self):
        unmodelled = [
            "%s: %s" % (volume["volume"], warning["tag"])
            for volume in self.volumes
            for warning in volume["warnings"]
            if warning["message"].startswith("unhandled TEI element")
        ]
        self.assertEqual([], unmodelled)

    def test_the_only_remaining_warning_is_the_editions_malformed_date(self):
        """One date in b43 is written with seven digits instead of eight.

        <date when="18460000" notAfter="1847000"> in correspDesc50. The parser
        keeps the source's string and says it could not read it; it does not
        quietly pad it out to 18470000.
        """
        warnings = [
            (volume["volume"], warning)
            for volume in self.volumes
            for warning in volume["warnings"]
        ]
        self.assertEqual(1, len(warnings), warnings)
        volume, warning = warnings[0]
        self.assertEqual("b43", volume)
        self.assertEqual("50", warning["letterId"])
        self.assertEqual("date", warning["tag"])
        self.assertIn("1847000", warning["message"])

        b43 = [v for v in self.volumes if v["volume"] == "b43"][0]
        letter = [l for l in b43["letters"] if l["id"] == "50"][0]
        not_after = letter["sender"]["date"]["notAfter"]
        self.assertEqual("1847000", not_after["raw"])
        self.assertIsNone(not_after["iso"])
        self.assertIsNone(not_after["precision"])

    def test_the_whole_corpus_round_trips_through_json(self):
        for volume in self.volumes:
            encoded = json.dumps(volume, ensure_ascii=False)
            self.assertEqual(volume, json.loads(encoded))

    def test_no_letter_in_the_corpus_loses_its_body(self):
        for volume, letter in self.letters:
            self.assertIsInstance(letter["body"], list)


class NewlyCoveredElementsTest(unittest.TestCase):
    """TEI that b1 does not use and the other thirteen volumes do."""

    @classmethod
    def setUpClass(cls):
        cls.by_volume = {volume["volume"]: volume for volume in corpus()}

    def letter(self, volume, identifier):
        return [
            letter
            for letter in self.by_volume[volume]["letters"]
            if letter["id"] == identifier
        ][0]

    def test_an_authors_footnote_is_modelled_as_a_note(self):
        # b43 letter 65 carries Kierkegaard's own footnote, encoded as
        # <note type="author" place="bottom"> with a reference marker and a
        # paragraph. It is reading text and must survive as structure.
        notes = nodes_of_type(self.letter("b43", "65")["body"], "note")
        self.assertEqual(1, len(notes))
        note = notes[0]
        self.assertEqual("author", note["subtype"])
        self.assertEqual("bottom", note["place"])
        self.assertIn(
            "medens det er uhøfligt betræffende Noget", plain_text(note)
        )
        # The reference marker and the note's prose are separate children,
        # not one run of text.
        markers = [
            segment
            for segment in nodes_of_type(note["content"], "seg")
            if segment["subtype"] == "refMarker"
        ]
        self.assertEqual(["1"], [plain_text(marker) for marker in markers])
        self.assertEqual(1, len(nodes_of_type(note["content"], "p")))

    def test_a_footnote_may_say_it_is_not_anchored_in_the_text(self):
        note = nodes_of_type(self.letter("b234", "234")["body"], "note")
        self.assertEqual(["false"], [n["anchored"] for n in note])

    def test_every_authors_footnote_in_the_corpus_is_a_note_node(self):
        found = [
            (volume["volume"], letter["id"])
            for volume in corpus()
            for letter in volume["letters"]
            for _ in nodes_of_type(letter["body"], "note")
        ]
        self.assertEqual(7, len(found))

    def test_a_figure_description_is_modelled(self):
        # b127 letter 129 sets a vignette as <figure type="vignet"> holding an
        # (empty) <figDesc> and a <graphic>. figDesc is the only TEI element
        # in the corpus that b1 never uses.
        figures = nodes_of_type(self.letter("b127", "129")["body"], "figure")
        vignettes = [f for f in figures if f["subtype"] == "vignet"]
        self.assertEqual(1, len(vignettes))
        self.assertEqual(
            ["figDesc", "graphic"],
            [child["type"] for child in vignettes[0]["content"]],
        )

    def test_a_formula_keeps_the_digits_the_edition_printed(self):
        # <date when="18440516"><formula notation="mathml">165</formula> 44</date>
        # -- the edition writes the day over the month as a fraction, and the
        # TEI keeps only the digits. Nothing is reconstructed from them.
        formulas = nodes_of_type(self.letter("b1", "11")["body"], "formula")
        self.assertEqual(["mathml"], [f["notation"] for f in formulas])
        self.assertEqual(["165"], [plain_text(f) for f in formulas])


class NonB1SpotCheckTest(unittest.TestCase):
    """Two letters from two other volumes, read against the raw XML."""

    @classmethod
    def setUpClass(cls):
        cls.by_volume = {volume["volume"]: volume for volume in corpus()}

    def letter(self, volume, identifier):
        return [
            letter
            for letter in self.by_volume[volume]["letters"]
            if letter["id"] == identifier
        ][0]

    def test_b79_letter_82_to_emil_boesen(self):
        letter = self.letter("b79", "82")
        self.assertEqual("n82", letter["xmlId"])
        self.assertEqual("SK", letter["sender"]["name"])
        self.assertEqual("Boesen, Emil", letter["recipient"]["name"])
        date = letter["sender"]["date"]
        self.assertEqual("18411214", date["raw"])
        self.assertEqual("1841-12-14", date["iso"])
        # The edition supplied the year but not the day: it says so on @source.
        self.assertEqual("suppliedYear", date["source"])
        self.assertEqual(
            "Fra SK · 14. dec. [1841] · til Emil Boesen", letter["heading"]
        )
        text = plain_text(letter["body"])
        self.assertIn("Min kjære Emil!", text)
        self.assertIn(
            "Tak skal Du have for Dit Brev, og Skam skal Du faae, fordi Du "
            "har ladet mig vente saa længe.",
            text,
        )

    def test_b259_letter_262_to_kolderup_rosenvinge(self):
        letter = self.letter("b259", "262")
        self.assertEqual("n262", letter["xmlId"])
        self.assertEqual("SK", letter["sender"]["name"])
        self.assertEqual(
            "Kolderup-Rosenvinge, J.L.A.", letter["recipient"]["name"]
        )
        date = letter["sender"]["date"]
        self.assertEqual("18480700", date["raw"])
        self.assertEqual("month", date["precision"])
        self.assertEqual("supplied", date["source"])
        text = plain_text(letter["body"])
        self.assertIn("Kiære Hr Conferentsraad!", text)
        self.assertIn(
            "hvis man syede Munden til paa ham, saa lærte han sig til at "
            "snakke med Næseborene",
            text,
        )

    def test_a_draft_has_no_named_correspondents_and_says_so(self):
        # b127 prints nine drafts of letter 159. Their correspAction carries a
        # note and a date but no <name>, and there is no "received" action at
        # all. Nothing is borrowed from letter 159 to fill the gaps.
        letter = self.letter("b127", "159.1")
        self.assertIsNone(letter["sender"]["name"])
        self.assertIsNone(letter["recipient"])
        self.assertEqual("Udkast til Brev 159", letter["sender"]["note"])
        self.assertEqual("Udkast til Brev 159", letter["heading"])
        self.assertEqual("18491100", letter["sender"]["date"]["raw"])

    def test_a_cross_reference_stub_has_metadata_but_no_reading_text(self):
        letter = [
            l
            for l in self.by_volume["b171"]["letters"]
            if l["xmlId"] == "n171a"
        ][0]
        self.assertEqual("-", letter["id"])
        self.assertEqual("Lund, Carl", letter["recipient"]["name"])
        self.assertEqual(", se Brev 193", letter["sender"]["note"])
        self.assertEqual("", plain_text(letter["body"]).strip())


class FallbackTest(unittest.TestCase):
    """Unknown TEI keeps its text and is reported, never silently dropped."""

    MINIMAL = """
    <TEI xmlns="http://www.tei-c.org/ns/1.0">
      <teiHeader>
        <fileDesc><titleStmt><title>Test</title></titleStmt></fileDesc>
      </teiHeader>
      <text>
        <body>
          <div type="correspondance" corresp="#correspContext1">
            <head type="topText" n="Test group"/>
            <div type="letter" n="99" xml:id="n99" corresp="#correspDesc99">
              <head type="letterHeader" n="Test letter"/>
              <div type="mainText">
                <p>before <weirdElement>kept text</weirdElement> after</p>
              </div>
            </div>
          </div>
        </body>
      </text>
    </TEI>
    """

    @classmethod
    def setUpClass(cls):
        cls.volume = parse_tei(ET.fromstring(cls.MINIMAL), volume="test")

    def test_unknown_element_keeps_its_text(self):
        letter = self.volume["letters"][0]
        self.assertIn("before kept text after", plain_text(letter["body"]))

    def test_unknown_element_is_reported(self):
        tags = [warning["tag"] for warning in self.volume["warnings"]]
        self.assertIn("weirdElement", tags)

    def test_missing_correspdesc_is_reported_not_invented(self):
        letter = self.volume["letters"][0]
        self.assertIsNone(letter["sender"])
        self.assertIsNone(letter["recipient"])
        messages = [warning["message"] for warning in self.volume["warnings"]]
        self.assertTrue(
            any("correspDesc99" in message for message in messages), messages
        )


if __name__ == "__main__":
    unittest.main()
