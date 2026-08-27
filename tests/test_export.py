"""The JSON export: the raw-data layer offered as a product of its own.

``export.py`` writes ``export/`` -- letter envelopes, a volume index and a
manifest -- for consumers other than this repository's own site generator.
These tests hold the export to the same standards as the display:

* nothing is repaired on the way out (the malformed b43 date travels raw),
* every letter is present, including the three unnumbered b171 stubs,
* the envelopes are the *vendor layer only* -- no editorial data mixed in,
  so the letters collection stays buildable without ``data/context``,
* the output is deterministic, and the committed ``export/`` never drifts
  from what the pipeline would generate today.
"""

import json
import os
import shutil
import tempfile
import unittest

from exporter.export import export_data
from pipeline.corpus import parse_corpus
from pipeline.provenance import load_file_record, load_provenance

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VENDOR = os.path.join(ROOT, "data", "vendor")
CONTEXT = os.path.join(ROOT, "data", "context")
COMMITTED_EXPORT = os.path.join(ROOT, "export")


def _read_json(*parts):
    with open(os.path.join(*parts), encoding="utf-8") as file:
        return json.load(file)


def _tree(root):
    """Relative path -> file bytes, for whole-tree comparisons."""
    files = {}
    for dirpath, _, filenames in os.walk(root):
        for name in filenames:
            path = os.path.join(dirpath, name)
            with open(path, "rb") as file:
                files[os.path.relpath(path, root)] = file.read()
    return files


class ExportTest(unittest.TestCase):
    """One export run, shared by every test; the corpus is the real corpus."""

    @classmethod
    def setUpClass(cls):
        cls.volumes = parse_corpus(VENDOR)
        cls.provenance = load_provenance(VENDOR)
        cls.out = tempfile.mkdtemp(prefix="epistel-export-")
        cls.result = export_data(
            cls.volumes,
            cls.out,
            provenance=cls.provenance,
            context_dir=CONTEXT,
            files=load_file_record(VENDOR),
            vendor_dir=VENDOR,
        )

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.out)

    # -- completeness ------------------------------------------------------

    def test_every_parsed_letter_has_an_envelope(self):
        expected = sum(len(volume["letters"]) for volume in self.volumes)
        written = [
            name
            for volume in self.volumes
            for name in os.listdir(os.path.join(self.out, "letters", volume["volume"]))
            if name.endswith(".json")
        ]
        self.assertEqual(len(written), expected)
        self.assertEqual(self.result["letters"], expected)
        # The corpus: 318 numbered letters, 15 sub-numbers, 3 stubs.
        self.assertEqual(expected, 336)

    def test_the_three_unnumbered_stubs_are_exported(self):
        b171 = next(v for v in self.volumes if v["volume"] == "b171")
        stubs = [letter for letter in b171["letters"] if letter["id"] == "-"]
        self.assertEqual(len(stubs), 3)
        for stub in stubs:
            envelope = _read_json(self.out, "letters", "b171", stub["xmlId"] + ".json")
            self.assertEqual(envelope["number"], "-")
            self.assertEqual(envelope["xmlId"], stub["xmlId"])

    # -- fidelity ----------------------------------------------------------

    def test_envelopes_carry_the_parser_data_unchanged(self):
        for volume in self.volumes:
            for letter in volume["letters"]:
                envelope = _read_json(
                    self.out, "letters", volume["volume"], letter["xmlId"] + ".json"
                )
                self.assertEqual(envelope["volume"], volume["volume"])
                self.assertEqual(envelope["xmlId"], letter["xmlId"])
                self.assertEqual(envelope["number"], letter["id"])
                self.assertEqual(envelope["heading"], letter["heading"])
                self.assertEqual(envelope["sender"], letter["sender"])
                self.assertEqual(envelope["recipient"], letter["recipient"])
                self.assertEqual(envelope["context"], letter["context"])

    def test_the_malformed_b43_date_travels_raw(self):
        # b43 letter 50: notAfter="1847000" -- unreadable, kept raw, never
        # repaired. The export inherits the honesty verbatim.
        b43 = next(v for v in self.volumes if v["volume"] == "b43")
        letter = next(l for l in b43["letters"] if l["id"] == "50")
        envelope = _read_json(self.out, "letters", "b43", letter["xmlId"] + ".json")
        dates = [
            correspondent["date"]
            for correspondent in (envelope["sender"], envelope["recipient"])
            if correspondent and correspondent["date"]
        ]
        malformed = [
            date["notAfter"]
            for date in dates
            if date["notAfter"] and date["notAfter"]["raw"] == "1847000"
        ]
        self.assertTrue(malformed, "the malformed notAfter is missing")
        self.assertIsNone(malformed[0]["iso"])

    def test_envelopes_hold_the_vendor_layer_only(self):
        # No editorial fields: resolved person keys, summaries and the like
        # arrive as their own collections, so this one stays buildable
        # without data/context.
        envelope = _read_json(
            self.out, "letters", "b1", self.volumes[0]["letters"][0]["xmlId"] + ".json"
        )
        self.assertEqual(
            sorted(envelope),
            [
                "body",
                "context",
                "heading",
                "number",
                "recipient",
                "sender",
                "volume",
                "xmlId",
            ],
        )

    # -- the volume index --------------------------------------------------

    def test_volume_index_keeps_document_order_and_warnings(self):
        index = _read_json(self.out, "volumes.json")
        self.assertEqual(len(index["volumes"]), len(self.volumes))
        b127 = next(v for v in index["volumes"] if v["volume"] == "b127")
        numbers = [ref["number"] for ref in b127["letters"]]
        drafts = ["159.%d" % n for n in range(1, 10)]
        start = numbers.index("159")
        self.assertEqual(numbers[start : start + 11], ["159"] + drafts + ["160"])
        for volume, parsed in zip(index["volumes"], self.volumes):
            self.assertEqual(volume["title"], parsed["title"])
            self.assertEqual(volume["groups"], parsed["groups"])
            self.assertEqual(volume["warnings"], parsed["warnings"])

    def test_volumes_name_their_source_files_with_upstream_path_and_checksum(self):
        # The way back to the TEI should not require looking in a folder:
        # each volume names its source files, with the upstream path (which,
        # with the manifest's pinned commit, is a stable raw URL) and the
        # sha256 the provenance record vouches for.
        record = load_file_record(VENDOR)
        index = _read_json(self.out, "volumes.json")
        for volume in index["volumes"]:
            source = volume["source"]
            # Every volume has its two TEI files; most also record images.
            self.assertLessEqual({"kom.xml", "txt.xml"}, set(source), volume["volume"])
            for filename, entry in source.items():
                recorded = record["%s/%s" % (volume["volume"], filename)]
                self.assertEqual(entry["path"], recorded["path"])
                self.assertEqual(entry["sha256"], recorded["sha256"])
                self.assertTrue(entry["path"].endswith(filename))

    def test_the_recorded_checksum_matches_the_vendored_bytes(self):
        # The chain is only as honest as its weakest link: spot-verify that
        # the provenance table describes the files actually on disk.
        import hashlib

        record = load_file_record(VENDOR)
        for local in ("b1/txt.xml", "b1/kom.xml"):
            with open(os.path.join(VENDOR, local), "rb") as file:
                digest = hashlib.sha256(file.read()).hexdigest()
            self.assertEqual(digest, record[local]["sha256"], local)

    # -- the manifest ------------------------------------------------------

    def test_manifest_records_provenance_and_a_license_per_layer(self):
        manifest = _read_json(self.out, "manifest.json")
        self.assertEqual(manifest["source"], self.provenance)
        self.assertEqual(manifest["schemaVersion"], "0.3.0")
        letters = manifest["layers"]["letters"]
        self.assertEqual(letters["license"], "CC0-1.0")
        self.assertEqual(letters["count"], self.result["letters"])
        self.assertEqual(manifest["layers"]["volumes"]["license"], "CC0-1.0")

    # -- determinism and drift ---------------------------------------------

    def test_the_export_is_deterministic(self):
        again = tempfile.mkdtemp(prefix="epistel-export-")
        try:
            export_data(
                self.volumes,
                again,
                provenance=self.provenance,
                context_dir=CONTEXT,
                files=load_file_record(VENDOR),
                vendor_dir=VENDOR,
            )
            self.assertEqual(_tree(self.out), _tree(again))
        finally:
            shutil.rmtree(again)

    def test_the_committed_export_has_not_drifted(self):
        # export/ is committed so PR diffs are the review artifact; this test
        # is what makes the committed copy trustworthy. Regenerate after
        # changing the pipeline or the exporter: python3 export.py
        self.assertTrue(
            os.path.isdir(COMMITTED_EXPORT),
            "export/ is not committed; run python3 export.py",
        )
        self.assertEqual(_tree(COMMITTED_EXPORT), _tree(self.out))


if __name__ == "__main__":
    unittest.main()
