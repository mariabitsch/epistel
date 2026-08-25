"""The exported editorial layers: the curated datasets, verbatim.

The editorial layer is a different kind of truth than the TEI (see
``pipeline.context``), and the export keeps the difference visible: the six
curated files are copied **byte for byte** -- their ``_meta`` blocks, source
citations and recorded disagreements are the product, and any transformation
would be drift waiting to happen. The manifest declares each one with its
entry count and its license, which is *not* CC0: this layer has an author,
and until a license is chosen the manifest says so instead of implying one.

The disposability guarantee travels too: an export without ``data/context``
is a smaller but complete, valid export -- letters, volumes, manifest --
exactly as a build without it is a complete site.
"""

import json
import os
import shutil
import tempfile
import unittest

from exporter.export import CONTEXT_FILES, export_data
from pipeline.corpus import parse_corpus
from pipeline.provenance import load_provenance

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VENDOR = os.path.join(ROOT, "data", "vendor")
CONTEXT = os.path.join(ROOT, "data", "context")


class ExportContextTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.volumes = parse_corpus(VENDOR)
        cls.provenance = load_provenance(VENDOR)
        cls.out = tempfile.mkdtemp(prefix="epistel-export-")
        cls.result = export_data(
            cls.volumes, cls.out, provenance=cls.provenance, context_dir=CONTEXT
        )

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.out)

    def _manifest(self, out=None):
        with open(os.path.join(out or self.out, "manifest.json"), encoding="utf-8") as f:
            return json.load(f)

    def test_the_curated_files_are_copied_verbatim(self):
        for name in CONTEXT_FILES:
            with open(os.path.join(CONTEXT, name + ".json"), "rb") as file:
                source = file.read()
            with open(os.path.join(self.out, "context", name + ".json"), "rb") as file:
                copied = file.read()
            self.assertEqual(copied, source, name)

    def test_the_manifest_declares_each_layer_with_its_entry_count(self):
        layers = self._manifest()["layers"]
        for name, entries_key in CONTEXT_FILES.items():
            with open(os.path.join(CONTEXT, name + ".json"), encoding="utf-8") as file:
                data = json.load(file)
            layer = layers[name]
            self.assertEqual(layer["path"], "context/%s.json" % name)
            self.assertEqual(layer["count"], len(data[entries_key]), name)

    def test_the_editorial_layers_do_not_claim_cc0(self):
        # The TEI-derived layers inherit the edition's CC0; the editorial
        # layer has an author and no chosen license yet. Saying "pending"
        # is honest; saying CC0 would be a false grant.
        layers = self._manifest()["layers"]
        for name in CONTEXT_FILES:
            self.assertIsNone(layers[name]["license"], name)
            self.assertIn("pending", layers[name]["licenseNote"], name)

    def test_an_export_without_context_is_complete_and_valid(self):
        out = tempfile.mkdtemp(prefix="epistel-export-")
        try:
            export_data(self.volumes, out, provenance=self.provenance)
            self.assertFalse(os.path.isdir(os.path.join(out, "context")))
            manifest = self._manifest(out)
            self.assertEqual(sorted(manifest["layers"]), ["letters", "volumes"])
            self.assertEqual(manifest["layers"]["letters"]["count"], 336)
        finally:
            shutil.rmtree(out)


if __name__ == "__main__":
    unittest.main()
