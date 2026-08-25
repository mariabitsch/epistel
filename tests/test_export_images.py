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
"""

import hashlib
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
        import json

        with open(os.path.join(self.out, "manifest.json"), encoding="utf-8") as file:
            manifest = json.load(file)
        images = manifest["layers"]["images"]
        self.assertEqual(images["path"], "letters/")
        self.assertEqual(images["count"], 40)
        self.assertEqual(images["license"], "CC0-1.0")


if __name__ == "__main__":
    unittest.main()
