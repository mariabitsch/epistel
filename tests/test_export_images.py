"""The exported images: the source's own illustrations, travelling with
the letters.

The pinned upstream commit holds 38 ``ill_*.jpg``/``ill_k*.jpg`` files
across the 14 corpus volumes (no full-page scans exist upstream — this is
everything). They are vendored with sha256 rows in ``PROVENANCE.md`` and
copied into ``export/letters/<volume>/``, which makes the TEI's own
relative references (``facs="../b1/ill_1.jpg"``) resolve as they stand
from the sidecar fragments. ``ill_k*`` files are referenced from the
commentary, which the export does not include; they still travel, because
they are part of the volume's recorded material.

Since schemaVersion 0.2.0 they also travel as a *dataset*:
``export/images.json`` describes every one of the 40 files -- where it
came from (upstream path + sha256), where it sits in the export, and
every place the edition refers to it, in the edition's own words. It is
the vendor layer alone; captions of our own would be an editorial layer
and are not in it.
"""

import hashlib
import json
import os
import re
import shutil
import tempfile
import unittest

from exporter.export import export_data
from pipeline.corpus import parse_corpus
from pipeline.provenance import load_file_record, load_provenance

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VENDOR = os.path.join(ROOT, "data", "vendor")
CONTEXT = os.path.join(ROOT, "data", "context")

_REFERENCE = re.compile(r'data-(?:facs|url)="([^"]+)"')

# One upstream reference is dangling at its written path: b241's letter 249
# points at ../b241/ill_k15.jpg, which the source repository does not hold
# (HTTP 404 at the pinned commit) — the file exists as ded/ill_k15.jpg,
# referenced correctly from ded's commentary. The reference is preserved
# verbatim, never repaired, and this set pins the defect: a new dangling
# reference (or this one healing upstream) must fail loudly.
KNOWN_DANGLING = {"../b241/ill_k15.jpg"}


def _read_json(*parts):
    with open(os.path.join(*parts), encoding="utf-8") as file:
        return json.load(file)


class ExportImagesTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.volumes = parse_corpus(VENDOR)
        cls.record = load_file_record(VENDOR)
        cls.images = {
            local: entry
            for local, entry in cls.record.items()
            if local.lower().endswith((".jpg", ".jpeg"))
        }
        cls.out = tempfile.mkdtemp(prefix="epistel-export-")
        cls.result = export_data(
            cls.volumes,
            cls.out,
            provenance=load_provenance(VENDOR),
            context_dir=CONTEXT,
            files=cls.record,
            vendor_dir=VENDOR,
        )

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.out)

    def test_every_vendored_image_is_exported_byte_identical(self):
        # 38 volume illustrations + the two shared vignet files.
        self.assertEqual(len(self.images), 40)
        for local in self.images:
            with open(os.path.join(VENDOR, local), "rb") as file:
                vendored = file.read()
            with open(os.path.join(self.out, "letters", local), "rb") as file:
                exported = file.read()
            self.assertEqual(exported, vendored, local)

    def test_vendored_images_match_their_recorded_checksums(self):
        # The chain guard, extended to the images: the provenance table
        # vouches for bytes that are actually on disk.
        for local, entry in self.images.items():
            with open(os.path.join(VENDOR, local), "rb") as file:
                digest = hashlib.sha256(file.read()).hexdigest()
            self.assertEqual(digest, entry["sha256"], local)

    def test_every_image_reference_in_a_fragment_resolves(self):
        # The TEI writes relative paths from inside the volume directory
        # (facs="../b1/ill_1.jpg"); with the images beside the fragments,
        # those paths must resolve exactly as the source wrote them.
        resolved = 0
        dangling = set()
        letters_dir = os.path.join(self.out, "letters")
        for volume in os.listdir(letters_dir):
            volume_dir = os.path.join(letters_dir, volume)
            for name in os.listdir(volume_dir):
                if not name.endswith(".html"):
                    continue
                with open(os.path.join(volume_dir, name), encoding="utf-8") as file:
                    fragment = file.read()
                for reference in _REFERENCE.findall(fragment):
                    target = os.path.normpath(os.path.join(volume_dir, reference))
                    if not os.path.isfile(target):
                        # Two upstream graphic urls write the volume dir in
                        # uppercase ("../B120/ill_31.jpg") — the same quirk
                        # as the commentary's uppercase cross-volume refs.
                        # The reference is preserved verbatim (never
                        # repaired); consumers resolve case-insensitively,
                        # and so does this test.
                        head, tail = os.path.split(target)
                        target = os.path.join(
                            os.path.dirname(head),
                            os.path.basename(head).lower(),
                            tail,
                        )
                    if not os.path.isfile(target):
                        dangling.add(reference)
                        continue
                    resolved += 1
        self.assertEqual(
            dangling, KNOWN_DANGLING, "the set of dangling image references changed"
        )
        self.assertGreater(resolved, 0)

    def test_the_manifest_declares_the_images_layer(self):
        manifest = _read_json(self.out, "manifest.json")
        images = manifest["layers"]["images"]
        # The layer's entry point is its manifest, the way the volumes
        # layer's is volumes.json; the image files themselves sit where
        # each entry's "path" says.
        self.assertEqual(images["path"], "images.json")
        self.assertEqual(images["count"], 40)
        self.assertEqual(images["license"], "CC0-1.0")

    # -- the image manifest ------------------------------------------------

    def test_the_image_manifest_describes_every_vendored_image(self):
        manifest = _read_json(self.out, "images.json")
        entries = manifest["images"]
        self.assertEqual(len(entries), 40)
        self.assertEqual([entry["id"] for entry in entries], sorted(self.images))
        for entry in entries:
            recorded = self.images[entry["id"]]
            self.assertEqual(entry["source"], recorded)
            # The id is the vendor-relative path; "path" says where the
            # file actually landed, so a consumer needs no convention.
            self.assertEqual(entry["path"], "letters/%s" % entry["id"])
            self.assertTrue(
                os.path.isfile(os.path.join(self.out, entry["path"])), entry["id"]
            )

    def test_an_entry_records_the_editions_own_figure(self):
        entry = self._entry("b1/ill_1.jpg")
        self.assertEqual(
            entry["figures"],
            [
                {
                    "volume": "b1",
                    "file": "txt.xml",
                    "xmlId": "ill_1",
                    "type": None,
                    "rend": "verso",
                    "url": "../b1/ill_1.jpg",
                    "head": ["1. Brev 2, bl. [2v], udskrift"],
                    "figDesc": None,
                    "letter": "2",
                    "letterXmlId": "n2",
                }
            ],
        )
        # The same plate reproduces a leaf of the manuscript, which is a
        # second, different reference: the page break says which leaf.
        self.assertEqual(
            [(pb["n"], pb["letter"], pb["facs"]) for pb in entry["pageBreaks"]],
            [("2v", "2", "../b1/ill_1.jpg")],
        )

    def test_a_commentary_plate_belongs_to_no_letter(self):
        # kom.xml gathers its plates in a division of its own. The figure
        # travels; the letter field says null rather than guessing.
        entry = self._entry("b1/ill_k2.jpg")
        figure = entry["figures"][0]
        self.assertEqual(figure["file"], "kom.xml")
        self.assertIsNone(figure["letter"])
        self.assertIsNone(figure["letterXmlId"])
        self.assertEqual(len(figure["head"]), 2)

    def test_the_uppercase_volume_quirk_is_recorded_not_repaired(self):
        # ../B120/ill_31.jpg is what the source wrote; the file lives in
        # b120. The url stays as written, the id names the real file, and
        # a consumer that matches case-insensitively joins the two.
        entry = self._entry("b120/ill_31.jpg")
        self.assertEqual(entry["figures"][0]["url"], "../B120/ill_31.jpg")
        self.assertEqual(entry["path"], "letters/b120/ill_31.jpg")

    def test_the_vignettes_carry_no_caption_and_say_so(self):
        # The two shared vignettes are the only typed figures and the only
        # uncaptioned ones: an empty figDesc, no head. A future captions
        # dataset keys off these ids; it does not belong in this layer.
        for image_id, letter in (
            ("vignet/vig-brev-kikkert.jpg", "129"),
            ("vignet/vig-brev-blomst.jpg", "178"),
        ):
            figure = self._entry(image_id)["figures"][0]
            self.assertEqual(figure["type"], "vignet")
            self.assertEqual(figure["head"], [])
            self.assertIsNone(figure["figDesc"])
            self.assertEqual(figure["letter"], letter)

    def test_images_the_edition_never_refers_to_say_nothing(self):
        # Two vendored files are referenced nowhere in the vendored TEI:
        # b241's commentary prints no plates at all, and b79/ill_k4.jpg is
        # likewise unreferenced. They are recorded material, so they ship
        # -- with both occurrence lists honestly empty.
        silent = {
            entry["id"]
            for entry in _read_json(self.out, "images.json")["images"]
            if not entry["figures"] and not entry["pageBreaks"]
        }
        self.assertEqual(silent, {"b241/ill_k10.jpg", "b79/ill_k4.jpg"})

    def test_a_plate_may_be_reproduced_from_another_volume(self):
        # b79's letter 119 points its leaf at ../b79/ill_24.jpg, a copy of
        # the plate b308 prints as figure ill_24 (its caption names both
        # letters). Two files, two ids, no merging.
        entry = self._entry("b79/ill_24.jpg")
        self.assertEqual(entry["figures"], [])
        self.assertEqual(
            [(pb["volume"], pb["letter"]) for pb in entry["pageBreaks"]],
            [("b79", "119")],
        )
        self.assertEqual(self._entry("b308/ill_24.jpg")["figures"][0]["xmlId"], "ill_24")

    def test_references_no_file_answers_are_listed_rather_than_dropped(self):
        # Two causes, one list: b241's letter 249 points at a file the
        # source repository does not hold (dangling upstream), and ded's
        # own plates are not vendored (ded is outside the corpus). Either
        # way the export ships no file, and says so.
        unshipped = _read_json(self.out, "images.json")["unshippedReferences"]
        self.assertEqual(
            sorted((ref["volume"], ref["element"], ref["url"]) for ref in unshipped),
            [
                ("b241", "pb", "../b241/ill_k15.jpg"),
                ("ded", "figure", "../ded/ill_25.jpg"),
                ("ded", "figure", "../ded/ill_26.jpg"),
                ("ded", "figure", "../ded/ill_27.jpg"),
                ("ded", "figure", "../ded/ill_28.jpg"),
                ("ded", "figure", "../ded/ill_29.jpg"),
                ("ded", "figure", "../ded/ill_k15.jpg"),
                ("ded", "pb", "../ded/ill_k11.jpg"),
            ],
        )
        dangling = next(ref for ref in unshipped if ref["volume"] == "b241")
        self.assertEqual(dangling["letter"], "249")
        self.assertEqual(dangling["file"], "txt.xml")

    def test_the_image_manifest_holds_the_vendor_layer_only(self):
        entry = self._entry("b1/ill_1.jpg")
        self.assertEqual(sorted(entry), ["figures", "id", "pageBreaks", "path", "source"])
        self.assertEqual(
            sorted(_read_json(self.out, "images.json")),
            ["images", "unshippedReferences"],
        )

    def _entry(self, image_id):
        entries = _read_json(self.out, "images.json")["images"]
        return next(entry for entry in entries if entry["id"] == image_id)


if __name__ == "__main__":
    unittest.main()
