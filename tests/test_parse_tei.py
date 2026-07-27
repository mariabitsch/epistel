"""Tests for the TEI -> JSON parser, run against the real vendored TEI file.

The vendored file (data/vendor/b1/txt.xml) is read-only truth: these tests read
the actual transcription out of it, so they fail loudly if the parser starts
inventing, dropping or reshaping content.

Run from the repository root:

    python3 -m unittest
"""

import json
import os
import unittest
import xml.etree.ElementTree as ET

from pipeline.parse_tei import parse_tei, parse_volume, plain_text

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
B1_PATH = os.path.join(REPO_ROOT, "data", "vendor", "b1", "txt.xml")


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
