"""The captions dataset: our own words about the edition's illustrations.

``export/images.json`` is the vendor layer -- every illustration file with
its provenance and every place the edition points at it, verbatim.
``data/context/captions.json`` is the *editorial* layer on top: an alt text
and (where the edition gives the image a place to speak from) a Maria
Notabene caption per image, keyed by the manifest's image ids and licensed
CC BY-NC-SA 4.0 like the other editorial layers.

The dataset was written by the two caption rounds of 2026-08-26 (trial +
full round): grounding-only drafting against the image and a grounding
packet, adversarial counter-reading by two foreign model families to zero
flags, arbitration against the image, and Maria's own doktor-runde. The
audit trail -- drafts, flags, repairs -- is committed under
``data/context/generated/captions*/``; ``docs/captions-method.md`` is the
playbook. These tests pin the *decisions* the round ended on:

* every manifest image has an entry, in manifest order;
* only the two files the edition never refers to stand caption-less
  (Maria, 2026-08-26: orphans get no caption -- there is no letter for
  Notabene to speak from), each with a note saying why;
* byte-identical duplicates share their alt text but never a caption
  (two ids, two places in the edition, two captions -- or one and none).
"""

import json
import os
import shutil
import tempfile
import unittest

try:
    import fastjsonschema
except ImportError:  # The optional validator; the suite says so, loudly.
    fastjsonschema = None

from pipeline.context import load_context

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONTEXT = os.path.join(ROOT, "data", "context")
CAPTIONS = os.path.join(CONTEXT, "captions.json")
SCHEMA = os.path.join(ROOT, "exporter", "schemas", "captions.schema.json")
MANIFEST = os.path.join(ROOT, "export", "images.json")

# The two files the edition refers to nowhere (see CLAUDE.md's source
# facts): b241/ill_k10.jpg is a byte-identical copy of b259's referenced
# plate, b79/ill_k4.jpg is the one true orphan. Both carry an alt text --
# the file is real and a reader may meet it -- but no caption.
CAPTIONLESS = {"b241/ill_k10.jpg", "b79/ill_k4.jpg"}

# The only images whose grounding packets name a photographer to credit.
CREDITED = {
    "b1/ill_k2.jpg": "(foto: Josiah Thompson)",
    "b1/ill_k3.jpg": "(foto: David Cain)",
    "b79/ill_10.jpg": "(foto: © Fondation Martin Bodmer, Cologny (Genève))",
}

# The two byte-identical pairs (sha256 match, pinned in CLAUDE.md).
DUPLICATE_PAIRS = [
    ("b79/ill_24.jpg", "b308/ill_24.jpg"),
    ("b241/ill_k10.jpg", "b259/ill_k10.jpg"),
]


def _read_json(path):
    with open(path, encoding="utf-8") as file:
        return json.load(file)


class CaptionsDatasetTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = _read_json(CAPTIONS)
        cls.entries = {entry["id"]: entry for entry in cls.data["captions"]}
        cls.manifest_ids = [
            image["id"] for image in _read_json(MANIFEST)["images"]
        ]

    def test_every_manifest_image_has_an_entry_in_manifest_order(self):
        self.assertEqual(
            [entry["id"] for entry in self.data["captions"]],
            self.manifest_ids,
        )

    def test_meta_declares_the_editorial_layer(self):
        meta = self.data["_meta"]
        self.assertTrue(meta["editorialLayer"])
        self.assertTrue(meta["notFromTEI"])
        self.assertEqual(meta["license"], "CC BY-NC-SA 4.0")
        self.assertIn("docs/captions-method.md", meta["method"])

    def test_every_entry_carries_exactly_the_published_fields(self):
        # sources and note travel with the dataset -- grounding and recorded
        # doubt are editorial honesty, the bios' precedent. The repair logs
        # (verifier flags and what was done) are development history and
        # stay in the committed audit trail, never in the dataset (Maria,
        # 2026-08-27).
        fields = ["alt", "caption", "credit", "id", "note", "sources"]
        for entry in self.data["captions"]:
            with self.subTest(id=entry["id"]):
                self.assertEqual(sorted(entry), fields)
                self.assertTrue(entry["alt"].strip())
                self.assertTrue(entry["sources"])
                for source in entry["sources"]:
                    self.assertTrue(source.strip())

    def test_only_the_unreferenced_files_stand_captionless(self):
        captionless = {
            entry["id"]
            for entry in self.data["captions"]
            if entry["caption"] is None
        }
        self.assertEqual(captionless, CAPTIONLESS)
        for image_id in CAPTIONLESS:
            # A missing caption is a decision, not a gap: the note says why.
            self.assertTrue(self.entries[image_id]["note"])

    def test_duplicates_share_their_alt_but_never_a_caption(self):
        for first_id, second_id in DUPLICATE_PAIRS:
            with self.subTest(pair=(first_id, second_id)):
                first, second = self.entries[first_id], self.entries[second_id]
                self.assertEqual(first["alt"], second["alt"])
                captions = {first["caption"], second["caption"]}
                self.assertEqual(len(captions), 2)  # never merged

    def test_credits_travel_only_where_a_photographer_is_named(self):
        credits = {
            entry["id"]: entry["credit"]
            for entry in self.data["captions"]
            if entry["credit"] is not None
        }
        self.assertEqual(credits, CREDITED)


class CaptionsSchemaTest(unittest.TestCase):
    """The dataset's schema (draft-07, closed), guarded at its source.

    The schema's source of truth is ``exporter/schemas/`` like every export
    schema -- since schemaVersion 0.3.0 the captions travel in the export,
    and ``test_export_schema`` holds the published copy. Here the *source*
    dataset is validated against it, so a hand edit in ``data/context``
    cannot drift from the contract before the next export run. Same
    two-level pattern: structure always, validation when the optional
    ``fastjsonschema`` is importable.
    """

    @classmethod
    def setUpClass(cls):
        cls.schema = _read_json(SCHEMA)

    def test_schema_is_draft_07_titled_and_closed(self):
        self.assertEqual(
            self.schema["$schema"], "http://json-schema.org/draft-07/schema#"
        )
        self.assertIn("title", self.schema)
        self.assertEqual(self.schema["type"], "object")
        self.assertIs(self.schema["additionalProperties"], False)
        entry = self.schema["properties"]["captions"]["items"]
        self.assertIs(entry["additionalProperties"], False)

    @unittest.skipUnless(fastjsonschema, "fastjsonschema not installed")
    def test_the_dataset_validates(self):
        fastjsonschema.validate(self.schema, _read_json(CAPTIONS))

    @unittest.skipUnless(fastjsonschema, "fastjsonschema not installed")
    def test_an_undeclared_field_fails_validation(self):
        # additionalProperties: false is the schema's whole bite -- a field
        # added without a schema update must fail, not slip through.
        data = _read_json(CAPTIONS)
        data["captions"][0]["surprise"] = "x"
        with self.assertRaises(fastjsonschema.JsonSchemaException):
            fastjsonschema.validate(self.schema, data)


class CaptionsLoaderTest(unittest.TestCase):
    """The dataset arrives through the same seam as every editorial layer:
    ``pipeline.context.load_context``, optional on its own."""

    @classmethod
    def setUpClass(cls):
        cls.context = load_context(CONTEXT)

    def test_load_context_serves_captions_by_manifest_id(self):
        captions = self.context["captions"]
        entry = captions["b1/ill_2.jpg"]
        self.assertTrue(entry["alt"].strip())
        self.assertTrue(entry["caption"].strip())
        self.assertIsNone(entry["credit"])
        self.assertIn("captions", self.context["meta"])

    def test_captionless_entries_still_carry_their_alt(self):
        entry = self.context["captions"]["b79/ill_k4.jpg"]
        self.assertTrue(entry["alt"].strip())
        self.assertIsNone(entry["caption"])

    def test_captions_are_disposable_on_their_own(self):
        with tempfile.TemporaryDirectory() as tmp:
            shutil.copy(
                os.path.join(CONTEXT, "summaries.json"),
                os.path.join(tmp, "summaries.json"),
            )
            without = load_context(tmp)
            self.assertNotIn("captions", without)
            self.assertIn("summaries", without)

            shutil.copy(CAPTIONS, os.path.join(tmp, "captions.json"))
            with_captions = load_context(tmp)
            self.assertIn("captions", with_captions)


if __name__ == "__main__":
    unittest.main()
