"""Tests for the commentary parser, run against the real vendored TEI files.

The vendored files (data/vendor/<volume>/kom.xml) are read-only truth: these
tests read actual scholarly commentary out of them, so they fail loudly if the
parser starts inventing, dropping or reshaping content.

Run from the repository root:

    python3 -m unittest
"""

import glob
import json
import os
import unittest

from pipeline.parse_kom import parse_commentary

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VENDOR = os.path.join(REPO_ROOT, "data", "vendor")
B1_PATH = os.path.join(VENDOR, "b1", "kom.xml")


def note_by_id(commentary, note_id):
    for note in commentary["notes"]:
        if note["id"] == note_id:
            return note
    raise AssertionError("no note %r in %s" % (note_id, commentary["volume"]))


def keys_of(note, field="persNames"):
    """The name keys a note mentions, in document order, without duplicates."""
    seen = []
    for entry in note[field]:
        if entry["key"] not in seen:
            seen.append(entry["key"])
    return seen


class VolumeStructureTest(unittest.TestCase):
    """The shape of a parsed commentary volume."""

    @classmethod
    def setUpClass(cls):
        cls.commentary = parse_commentary(B1_PATH)

    def test_volume_is_named_after_its_directory(self):
        self.assertEqual("b1", self.commentary["volume"])

    def test_b1_has_757_notes(self):
        self.assertEqual(757, len(self.commentary["notes"]))

    def test_note_ids_are_unique(self):
        ids = [note["id"] for note in self.commentary["notes"]]
        self.assertEqual(len(ids), len(set(ids)))

    def test_every_note_has_an_id_and_a_page_line_reference(self):
        for note in self.commentary["notes"]:
            self.assertTrue(note["id"], "note without xml:id")
            self.assertRegex(note["n"], r"^\d+,\d+$")

    def test_page_line_references_are_not_unique(self):
        """Two notes can gloss two phrases on the same line -- @n is not an id.

        b-101 ("passeligt") and b-102 ("Halle") both carry n="15,34".
        """
        self.assertEqual("15,34", note_by_id(self.commentary, "b-101")["n"])
        self.assertEqual("15,34", note_by_id(self.commentary, "b-102")["n"])

    def test_b1_parses_without_warnings(self):
        self.assertEqual([], self.commentary["warnings"])


class NoteContentTest(unittest.TestCase):
    """One known note, end to end."""

    @classmethod
    def setUpClass(cls):
        cls.commentary = parse_commentary(B1_PATH)
        cls.note = note_by_id(cls.commentary, "b-9")

    def test_page_and_line_reference(self):
        self.assertEqual("9,29", self.note["n"])

    def test_lemma_is_the_quoted_letter_phrase(self):
        self.assertEqual(
            "Henrichsen har forladt Borgerdydsskolen ... til Helsingør",
            self.note["lemma"],
        )

    def test_text_is_the_commentary_prose(self):
        self.assertTrue(self.note["text"].startswith(
            "Rudolph Johannes Frederik Henrichsen (1800-71), "
            "da. klassisk filolog og skolemand;"
        ))

    def test_text_contains_the_biographical_identification(self):
        self.assertIn("klassisk filolog og skolemand", self.note["text"])

    def test_lemma_is_not_part_of_the_prose(self):
        self.assertNotIn("har forladt Borgerdydsskolen", self.note["text"])

    def test_person_key_is_kept_complete(self):
        self.assertIn(
            "Henrichsen, Rudolph Johannes Frederik", keys_of(self.note)
        )

    def test_the_person_the_note_identifies_is_marked(self):
        subjects = [p for p in self.note["persNames"] if p["isSubject"]]
        self.assertEqual(
            ["Henrichsen, Rudolph Johannes Frederik"],
            [p["key"] for p in subjects],
        )
        self.assertEqual("*", subjects[0]["n"])

    def test_person_mention_keeps_its_surface_form(self):
        henrichsen = self.note["persNames"][0]
        self.assertEqual(
            "Rudolph Johannes Frederik Henrichsen", henrichsen["text"]
        )
        self.assertIsNone(henrichsen["sameAs"])

    def test_place_keys_are_kept_where_the_edition_gives_them(self):
        places = {p["text"]: p["key"] for p in self.note["placeNames"]}
        self.assertEqual("Borgerdydskolen", places["Borgerdydsskolen"])
        self.assertIsNone(places["Metropolitanskolen"])

    def test_cross_references_to_other_notes_are_kept(self):
        self.assertEqual(
            [{"target": "b-13", "n": "10,8"}], self.note["noteRefs"]
        )

    def test_external_references_keep_target_and_type(self):
        maps = [r for r in self.note["refs"] if r["type"] == "map"]
        self.assertEqual("../kort/kbh_B1.htm", maps[0]["target"])
        self.assertEqual("se kort 2, B1", maps[0]["text"])

    def test_further_phrases_glossed_in_the_prose_are_collected(self):
        self.assertIn("Borgerdydsskolen:", self.note["subLemmas"])


class MultiplePersonsTest(unittest.TestCase):
    """A note mentioning several people keeps every key."""

    @classmethod
    def setUpClass(cls):
        cls.note = note_by_id(parse_commentary(B1_PATH), "b-3")

    def test_all_three_person_keys_are_kept(self):
        self.assertEqual(
            [
                "Kierkegaard, Peter Christian",
                "Kierkegaard, Michael Pedersen",
                "Lund, Anne Sørensdatter",
            ],
            keys_of(self.note),
        )

    def test_only_the_identified_person_is_marked_as_subject(self):
        self.assertEqual(
            ["Kierkegaard, Michael Pedersen"],
            [p["key"] for p in self.note["persNames"] if p["isSubject"]],
        )


class PersonIndexTest(unittest.TestCase):
    """The shape has to support the person index the bios are built from."""

    @classmethod
    def setUpClass(cls):
        cls.commentary = parse_commentary(B1_PATH)

    def test_notes_mentioning_a_person_are_easy_to_collect(self):
        wanted = "Kierkegaard, Peter Christian"
        mentions = [
            note["id"]
            for note in self.commentary["notes"]
            if any(p["key"] == wanted for p in note["persNames"])
        ]
        self.assertIn("b-1", mentions)
        self.assertIn("b-3", mentions)

    def test_every_person_mention_has_a_key(self):
        for note in self.commentary["notes"]:
            for person in note["persNames"]:
                self.assertTrue(person["key"], "persName without @key")

    def test_an_empty_key_in_the_source_is_kept_and_reported(self):
        """b241 b-3238 encodes key="" -- a source defect, not repaired here."""
        commentary = parse_commentary(os.path.join(VENDOR, "b241", "kom.xml"))
        note = note_by_id(commentary, "b-3238")
        bera = [p for p in note["persNames"] if p["text"] == "Bera"]
        self.assertEqual([""], [p["key"] for p in bera])
        self.assertEqual(
            [("b-3238", "persName")],
            [(w["noteId"], w["tag"]) for w in commentary["warnings"]],
        )

    def test_alias_names_are_preserved_raw(self):
        """@sameAs gives another name form, not a pointer -- keep it as is."""
        aliases = {
            p["key"]: p["sameAs"]
            for note in self.commentary["notes"]
            for p in note["persNames"]
            if p["sameAs"]
        }
        self.assertEqual(
            "Kierkegaard, Jette", aliases["Kierkegaard, Henriette"]
        )


class ApparatusTest(unittest.TestCase):
    """Text that is not part of the commentary prose stays out of it."""

    def test_figure_captions_do_not_leak_into_the_reading_text(self):
        note = note_by_id(parse_commentary(B1_PATH), "b-699")
        self.assertEqual(1, len(note["figures"]))
        self.assertEqual("../b1/ill_k2.jpg", note["figures"][0]["url"])
        self.assertIn(
            "Særindbinding af Opbyggelige Taler", note["figures"][0]["caption"]
        )
        self.assertNotIn("Særindbinding af Opbyggelige Taler", note["text"])

    def test_a_note_split_over_two_paragraphs_reads_as_one_text(self):
        note = note_by_id(
            parse_commentary(os.path.join(VENDOR, "b276", "kom.xml")), "b-5451"
        )
        self.assertEqual(
            "SK boede fra april til okt. 1848 på 1. sal i ejendommen "
            "på hjørnet af Rosenborggade",
            note["text"][:len(
                "SK boede fra april til okt. 1848 på 1. sal i ejendommen "
                "på hjørnet af Rosenborggade"
            )],
        )
        self.assertEqual(2, len(note["paragraphs"]))

    def test_bible_references_keep_their_key_and_text(self):
        commentary = parse_commentary(B1_PATH)
        refs = [
            ref
            for note in commentary["notes"]
            for ref in note["bibleRefs"]
        ]
        self.assertTrue(refs)
        self.assertIn("Sl 6,3", [ref["text"] for ref in refs])


class SerializationTest(unittest.TestCase):
    def test_result_round_trips_through_json(self):
        commentary = parse_commentary(B1_PATH)
        restored = json.loads(json.dumps(commentary, ensure_ascii=False))
        self.assertEqual(commentary, restored)


class AllVolumesTest(unittest.TestCase):
    """Every vendored volume parses; surprises are reported, not hidden."""

    @classmethod
    def setUpClass(cls):
        cls.paths = sorted(glob.glob(os.path.join(VENDOR, "*", "kom.xml")))

    def test_all_fifteen_volumes_are_vendored(self):
        self.assertEqual(15, len(self.paths))

    def test_every_volume_yields_notes(self):
        counts = {}
        warnings = {}
        for path in self.paths:
            commentary = parse_commentary(path)
            counts[commentary["volume"]] = len(commentary["notes"])
            warnings[commentary["volume"]] = len(commentary["warnings"])
            self.assertGreater(
                len(commentary["notes"]), 0, "no notes in %s" % path
            )
        print("\nnotes per volume:  %s" % counts)
        print("warnings per volume: %s" % warnings)
        print("total notes: %d" % sum(counts.values()))

    def test_person_keys_join_across_volumes(self):
        """The whole point: one key collects a person's notes corpus-wide."""
        by_key = {}
        for path in self.paths:
            commentary = parse_commentary(path)
            for note in commentary["notes"]:
                for person in note["persNames"]:
                    by_key.setdefault(person["key"], set()).add(
                        (commentary["volume"], note["id"])
                    )
        print("distinct persName keys across all volumes: %d" % len(by_key))
        sk = by_key["Kierkegaard, Søren Aabye"]
        self.assertGreater(len(set(volume for volume, _ in sk)), 1)


if __name__ == "__main__":
    unittest.main()
