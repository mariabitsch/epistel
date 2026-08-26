"""The export's JSON Schemas: the contract, machine-checkable.

``docs/export-format.md`` says what the export looks like; the schemas in
``export/schema/`` say it formally (JSON Schema draft-07, the draft the
validation ecosystem supports universally). They are published *with* the
export and declared in the manifest, so a consumer holds data and contract
in the same download.

Two levels of guarding, on purpose:

* **Always on** (standard library): the schemas exist, parse, declare
  draft-07 and are exactly what the manifest points at. The repository's
  no-dependency rule stays intact.
* **When available**: if ``fastjsonschema`` is importable (a deliberately
  optional, pure-Python dev dependency — e.g. in a local ``.venv``), the
  committed export is validated against its own schemas: the manifest, the
  volume index, the image manifest and all 336 envelopes. Where it is not
  installed the test skips, visibly.
"""

import json
import os
import unittest

try:
    import fastjsonschema
except ImportError:  # The optional validator; the suite says so, loudly.
    fastjsonschema = None

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXPORT = os.path.join(ROOT, "export")

SCHEMAS = ("manifest", "volumes", "letter", "images")


def _read_json(*parts):
    with open(os.path.join(*parts), encoding="utf-8") as file:
        return json.load(file)


class SchemaPublicationTest(unittest.TestCase):
    """Always-on: the contract ships with the data and is declared."""

    def test_schemas_are_published_and_declared_in_the_manifest(self):
        manifest = _read_json(EXPORT, "manifest.json")
        self.assertEqual(sorted(manifest["schemas"]), sorted(SCHEMAS))
        for name in SCHEMAS:
            path = manifest["schemas"][name]
            self.assertEqual(path, "schema/%s.schema.json" % name)
            schema = _read_json(EXPORT, path)
            self.assertEqual(
                schema["$schema"], "http://json-schema.org/draft-07/schema#"
            )
            self.assertEqual(schema["type"], "object")
            self.assertIn("title", schema)

    def test_the_letter_schema_admits_no_undeclared_fields(self):
        # additionalProperties: false is the schema's whole bite -- an
        # envelope field added without a schema update must fail validation,
        # not slip through.
        schema = _read_json(EXPORT, "schema", "letter.schema.json")
        self.assertIs(schema["additionalProperties"], False)


@unittest.skipUnless(fastjsonschema, "fastjsonschema not installed (optional)")
class SchemaValidationTest(unittest.TestCase):
    """Optional: the committed export validates against its own contract."""

    @classmethod
    def setUpClass(cls):
        cls.validators = {
            name: fastjsonschema.compile(
                _read_json(EXPORT, "schema", "%s.schema.json" % name)
            )
            for name in SCHEMAS
        }

    def test_the_manifest_validates(self):
        self.validators["manifest"](_read_json(EXPORT, "manifest.json"))

    def test_the_volume_index_validates(self):
        self.validators["volumes"](_read_json(EXPORT, "volumes.json"))

    def test_the_image_manifest_validates(self):
        self.validators["images"](_read_json(EXPORT, "images.json"))

    def test_every_envelope_validates(self):
        validated = 0
        letters_dir = os.path.join(EXPORT, "letters")
        for volume in sorted(os.listdir(letters_dir)):
            volume_dir = os.path.join(letters_dir, volume)
            for name in sorted(os.listdir(volume_dir)):
                if not name.endswith(".json"):
                    continue
                envelope = _read_json(volume_dir, name)
                try:
                    self.validators["letter"](envelope)
                except fastjsonschema.JsonSchemaException as error:
                    self.fail("%s/%s: %s" % (volume, name, error))
                validated += 1
        self.assertEqual(validated, 336)


if __name__ == "__main__":
    unittest.main()
