"""Where the edition points at its own illustration files.

``pipeline.images`` is the second reading of the vendored TEI: not the
letters, but the *references* to image files -- ``<figure>``'s ``graphic``
url and ``<pb>``'s ``@facs``, in ``txt.xml`` and ``kom.xml`` alike, for
every vendored directory including ``ded`` (which the corpus excludes).
It is the vendor-layer source of the export's image manifest.

The rules are the project's usual ones: nothing repaired, nothing guessed.
A url the edition wrote with an uppercase volume directory stays uppercase;
a figure with an empty ``figDesc`` and no caption says so rather than
inventing one.
"""

import unittest

from pipeline.images import find_image_references, resolve_reference

import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VENDOR = os.path.join(ROOT, "data", "vendor")


class ImageReferenceTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.references = find_image_references(VENDOR)

    def _one(self, **fields):
        found = [
            reference
            for reference in self.references
            if all(reference[key] == value for key, value in fields.items())
        ]
        self.assertEqual(len(found), 1, "%r matched %d references" % (fields, len(found)))
        return found[0]

    def test_every_image_reference_in_the_vendored_tei_is_found(self):
        # 40 illustrated figures (34 in the corpus volumes, 6 in ded) and 35
        # page breaks carrying a facsimile reference. The numbers are the
        # source's, counted at the pinned commit: a reference appearing or
        # disappearing upstream must fail here rather than pass unnoticed.
        by_element = {}
        for reference in self.references:
            by_element.setdefault(reference["element"], []).append(reference)
        self.assertEqual(len(by_element["figure"]), 40)
        self.assertEqual(len(by_element["pb"]), 35)
        self.assertEqual(len(self.references), 75)

    def test_a_figure_reference_carries_the_editions_own_words(self):
        figure = self._one(element="figure", url="../b1/ill_1.jpg")
        self.assertEqual(figure["volume"], "b1")
        self.assertEqual(figure["file"], "txt.xml")
        self.assertEqual(figure["xmlId"], "ill_1")
        self.assertIsNone(figure["type"])
        self.assertEqual(figure["rend"], "verso")
        self.assertEqual(figure["head"], ["1. Brev 2, bl. [2v], udskrift"])
        self.assertIsNone(figure["figDesc"])
        self.assertEqual(
            figure["division"], {"type": "letter", "n": "2", "xmlId": "n2"}
        )

    def test_a_figure_keeps_all_of_its_captions(self):
        # Several plates carry a second <head> holding the photo credit; a
        # display may set it apart, but the export may not drop it.
        figure = self._one(element="figure", url="../b79/ill_10.jpg")
        self.assertEqual(
            figure["head"],
            [
                "10. SKs signet af mandehoved i profil i rød lak på Brev 89",
                "(foto: © Fondation Martin Bodmer, Cologny (Genève))",
            ],
        )

    def test_the_uppercase_volume_directory_travels_verbatim(self):
        # Two graphic urls in b120 write their own directory in uppercase.
        # The reference is data, not a path to be tidied: it stays as
        # written, and so does what it resolves to. Consumers match
        # case-insensitively (see the export's image manifest).
        figure = self._one(element="figure", url="../B120/ill_31.jpg")
        self.assertEqual(figure["volume"], "b120")
        self.assertEqual(
            resolve_reference("b120", "../B120/ill_31.jpg"), "B120/ill_31.jpg"
        )
        self.assertEqual(resolve_reference("b1", "../b1/ill_1.jpg"), "b1/ill_1.jpg")

    def test_the_two_vignettes_are_typed_figures_without_a_caption(self):
        # The shared vignettes are the only figures with a @type and the
        # only ones the edition leaves uncaptioned: an empty <figDesc> and
        # no <head> at all. Empty is recorded as empty.
        for url, letter in (
            ("../vignet/vig-brev-kikkert.jpg", "129"),
            ("../vignet/vig-brev-blomst.jpg", "178"),
        ):
            figure = self._one(element="figure", url=url)
            self.assertEqual(figure["type"], "vignet")
            self.assertIsNone(figure["rend"])
            self.assertEqual(figure["head"], [])
            self.assertIsNone(figure["figDesc"])
            self.assertEqual(figure["division"]["n"], letter)

    def test_a_page_break_facsimile_is_a_reference_too(self):
        # b241's letter 249 points a manuscript leaf at ../b241/ill_k15.jpg
        # -- the reference the source repository does not answer. It is
        # found and recorded like any other; the export does not repair it.
        page_break = self._one(element="pb", url="../b241/ill_k15.jpg")
        self.assertEqual(page_break["volume"], "b241")
        self.assertEqual(page_break["file"], "txt.xml")
        self.assertEqual(page_break["n"], "1r")
        self.assertEqual(page_break["rend"], "supplied")
        self.assertIsNone(page_break["edRef"])
        self.assertEqual(
            page_break["division"], {"type": "letter", "n": "249", "xmlId": "n249"}
        )
        # Page breaks carry no caption of their own.
        self.assertEqual(page_break["head"], [])

    def test_a_reference_outside_a_letter_says_so(self):
        # The commentary volumes gather their plates in a division of their
        # own, and ded numbers dedications rather than letters. Neither is
        # a letter, and neither is turned into one.
        commentary = self._one(element="figure", url="../b1/ill_k2.jpg")
        self.assertEqual(commentary["file"], "kom.xml")
        self.assertIsNone(commentary["division"])
        dedication = self._one(element="figure", url="../ded/ill_25.jpg")
        self.assertEqual(
            dedication["division"], {"type": "dedication", "n": "15", "xmlId": "n15"}
        )


if __name__ == "__main__":
    unittest.main()
