"""The people in the letters: slugs, the alias join, and the pages.

Built once against the real vendored corpus and the real curated datasets,
then read the way a visitor would read it. The numbers in here are the
corpus' own -- they are pinned so that a change in the parser, the alias
table or the biography dataset has to be noticed rather than absorbed.
"""

import json
import os
import re
import tempfile
import unittest

from pipeline.context import load_context
from pipeline.corpus import parse_corpus
from sitegen.persons import (
    assign_slugs,
    build_register,
    display_name,
    initial,
    person_keys,
    slug,
    sort_key,
)
from sitegen.site import build_site

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VENDOR = os.path.join(ROOT, "data", "vendor")
CONTEXT = os.path.join(ROOT, "data", "context")

# The corpus as it stands: every persName key in a letter body, plus whoever
# the alias table joins a sender or recipient to.
PEOPLE = 298


class SlugTest(unittest.TestCase):
    """A person's URL: derived from the key, never chosen."""

    def test_danish_letters_are_spelled_out_rather_than_stripped(self):
        self.assertEqual("kierkegaard-soeren-aabye", slug("Kierkegaard, Søren Aabye"))
        self.assertEqual("oersted-hans-christian", slug("Ørsted, Hans Christian"))
        self.assertEqual("lunde-jernstoeber", slug("Lunde, jernstøber"))

    def test_decorations_are_dropped(self):
        self.assertEqual("eiriksson-magnus", slug("Eiríksson, Magnús"))
        self.assertEqual("heloise", slug("Héloïse"))

    def test_punctuation_only_keys_still_get_an_address(self):
        # The edition prints correspondents signed "e – e" and "S: F:".
        self.assertEqual("e-e", slug("e – e"))
        self.assertEqual("s-f", slug("S: F:"))
        self.assertEqual("person", slug("—"))

    def test_the_same_key_always_gives_the_same_slug(self):
        self.assertEqual(slug("Boesen, Emil Ferdinand"), slug("Boesen, Emil Ferdinand"))

    def test_two_keys_that_transliterate_alike_get_different_pages(self):
        assigned = assign_slugs(["Moltke, O.J.", "Moltke, O. J.", "Moltke, Carl"])
        self.assertEqual(3, len(set(assigned.values())))
        # Numbered in sorted key order, so the result does not depend on the
        # order the corpus happened to hand them over in.
        self.assertEqual("moltke-o-j", assigned["Moltke, O. J."])
        self.assertEqual("moltke-o-j-2", assigned["Moltke, O.J."])

    def test_collision_numbering_is_stable_whatever_order_keys_arrive_in(self):
        keys = ["Moltke, O.J.", "Moltke, O. J."]
        self.assertEqual(assign_slugs(keys), assign_slugs(list(reversed(keys))))

    def test_the_register_sorts_the_danish_letters_last(self):
        names = ["Ørsted, A", "Aabye, B", "Zeuthen, C", "Åberg, D", "Æble, E"]
        self.assertEqual(
            ["Aabye, B", "Zeuthen, C", "Æble, E", "Ørsted, A", "Åberg, D"],
            sorted(names, key=sort_key),
        )

    def test_the_register_files_a_decorated_name_under_its_plain_letter(self):
        self.assertEqual("E", initial("Eiríksson, Magnús"))
        self.assertEqual("Ø", initial("Ørsted, Hans Christian"))
        self.assertEqual("E", initial("e – e"))


class PersonKeysTest(unittest.TestCase):
    """Which people a letter body names, read off the parser's tree."""

    def test_keys_come_out_in_reading_order_without_repeats(self):
        body = [
            {"type": "p", "content": [
                {"type": "persName", "key": "B", "content": [{"text": "B"}]},
                {"type": "persName", "key": "A", "content": [{"text": "A"}]},
                {"type": "persName", "key": "B", "content": [{"text": "B"}]},
            ]}
        ]
        self.assertEqual(["B", "A"], person_keys(body))

    def test_an_empty_key_is_not_a_person(self):
        # b127, letter 148: <persName key="">Io</persName>.
        body = [{"type": "persName", "key": "", "content": [{"text": "Io"}]}]
        self.assertEqual([], person_keys(body))


class AliasTableTest(unittest.TestCase):
    """The curated join between correspondent names and persName keys."""

    @classmethod
    def setUpClass(cls):
        with open(os.path.join(CONTEXT, "aliases.json"), encoding="utf-8") as file:
            cls.data = json.load(file)
        cls.volumes = parse_corpus(VENDOR)

    def forms_in_the_corpus(self):
        forms = set()
        for volume in self.volumes:
            for letter in volume["letters"]:
                for role in ("sender", "recipient"):
                    name = (letter.get(role) or {}).get("name")
                    if name:
                        forms.add(name)
        return forms

    def test_every_correspondent_name_is_either_mapped_or_explained(self):
        """No form may fall through: it is joined, or it is listed as not."""
        mapped = {entry["form"] for entry in self.data["aliases"]}
        unmapped = {entry["form"] for entry in self.data["unmapped"]}
        self.assertEqual(self.forms_in_the_corpus(), mapped | unmapped)
        self.assertEqual(set(), mapped & unmapped)

    def test_every_unmapped_form_says_why(self):
        for entry in self.data["unmapped"]:
            self.assertTrue(entry["reason"], entry["form"])

    def test_every_mapped_key_is_a_person_the_letters_actually_name(self):
        keys = set()
        for volume in self.volumes:
            for letter in volume["letters"]:
                keys.update(person_keys(letter["body"]))
        for entry in self.data["aliases"]:
            for key in entry["keys"]:
                self.assertIn(key, keys, entry["form"])

    def test_the_file_says_it_is_ours_and_not_the_editions(self):
        meta = self.data["_meta"]
        self.assertTrue(meta["editorialLayer"])
        self.assertTrue(meta["notFromTEI"])


class BioKeyTableTest(unittest.TestCase):
    """The curated bridge between the bodies' and the commentary's key spaces.

    bios.json is filed under kom.xml's persName keys; the person register is
    built from the letter bodies' keys. Four people fall in the gap (an
    inverted name, a rearranged surname, a missing comma), and
    ``bio_keys.json`` is our claim -- evidenced entry by entry -- that the
    two forms name the same person.
    """

    @classmethod
    def setUpClass(cls):
        with open(os.path.join(CONTEXT, "bio_keys.json"), encoding="utf-8") as file:
            cls.data = json.load(file)
        cls.context = load_context(CONTEXT)
        cls.volumes = parse_corpus(VENDOR)

    def test_every_bridge_carries_its_evidence(self):
        for entry in self.data["bridges"]:
            self.assertTrue(entry["evidence"], entry["bodyKey"])

    def test_every_body_key_is_a_person_the_letters_actually_name(self):
        keys = set()
        for volume in self.volumes:
            for letter in volume["letters"]:
                keys.update(person_keys(letter["body"]))
        for entry in self.data["bridges"]:
            self.assertIn(entry["bodyKey"], keys)

    def test_every_bio_key_holds_a_bio_and_no_bridge_shadows_one(self):
        bios = self.context["bios"]
        for entry in self.data["bridges"]:
            self.assertIn(entry["bioKey"], bios, entry["bodyKey"])

    def test_the_loader_files_the_bio_under_the_bodys_key_too(self):
        bios = self.context["bios"]
        for entry in self.data["bridges"]:
            self.assertEqual(
                bios[entry["bioKey"]], bios[entry["bodyKey"]], entry["bodyKey"]
            )

    def test_the_file_says_it_is_ours_and_not_the_editions(self):
        meta = self.data["_meta"]
        self.assertTrue(meta["editorialLayer"])
        self.assertTrue(meta["notFromTEI"])


class PersonRegisterTest(unittest.TestCase):
    """The register built from the real corpus and the real datasets."""

    @classmethod
    def setUpClass(cls):
        cls.context = load_context(CONTEXT)
        cls.volumes = parse_corpus(VENDOR)
        cls.directory = tempfile.TemporaryDirectory()
        cls.result = build_site(cls.volumes, cls.directory.name, context=cls.context)

    @classmethod
    def tearDownClass(cls):
        cls.directory.cleanup()

    def read(self, *parts):
        with open(os.path.join(self.directory.name, *parts), encoding="utf-8") as file:
            return file.read()

    def test_everyone_the_letters_name_gets_a_page(self):
        self.assertEqual(PEOPLE, self.result["people"])
        pages = os.listdir(os.path.join(self.directory.name, "person"))
        self.assertEqual(PEOPLE, len(pages))

    def test_no_two_people_share_a_page(self):
        pages = os.listdir(os.path.join(self.directory.name, "person"))
        self.assertEqual(len(pages), len(set(pages)))

    def test_the_register_links_every_person_page(self):
        index = self.read("personer", "index.html")
        linked = set(re.findall(r'href="\.\./person/([^/"]+)/"', index))
        self.assertEqual(PEOPLE, len(linked))
        for name in linked:
            self.assertTrue(
                os.path.exists(
                    os.path.join(self.directory.name, "person", name, "index.html")
                ),
                name,
            )

    def test_a_person_page_reads_end_to_end(self):
        """Emil Boesen: the biography, its citation, and both letter lists."""
        page = self.read("person", "boesen-emil-ferdinand", "index.html")
        self.assertIn("<h1>Emil Ferdinand Boesen</h1>", page)
        self.assertIn("Boesen, Emil Ferdinand", page)          # the index form
        self.assertIn("SKs nære ven Emil Ferdinand Boesen (1812-81)", page)
        self.assertIn("Efter kommentaren i SKS:", page)
        self.assertIn("b79:b-1792", page)
        sent = page.split("Breve fra Emil Ferdinand Boesen", 1)[1].split(
            "</section>", 1
        )[0]
        received = page.split("Breve til Emil Ferdinand Boesen", 1)[1].split(
            "</section>", 1
        )[0]
        self.assertIn("4 breve", sent)
        self.assertIn("37 breve", received)
        self.assertIn('href="../../brev/115/"', sent)
        self.assertIn('href="../../brev/79/"', received)

    def test_a_person_the_commentary_never_wrote_about_still_gets_their_letters(self):
        """Julie Thomsen has no biography and her letters. Both are said.

        (Henriette Lund held this role until her grounded bio landed --
        see the augmentation test below.)
        """
        page = self.read("person", "thomsen-julie-augusta", "index.html")
        self.assertIn("Kommentaren giver ingen biografisk note", page)
        self.assertNotIn("Efter kommentaren i SKS", page)
        self.assertIn("Breve til Julie Augusta Thomsen", page)
        self.assertIn('href="../../brev/40/"', page)

    def test_the_grounded_augmentation_gives_henriette_lund_her_bio(self):
        """Twenty-three letters deserved better than 'ingen biografisk note'.

        The commentary holds no subject note under her key, so her bio is
        assembled from the notes that gloss her in SK's letters to her --
        the Fenger method; see the entry's note field in bios.json for the
        verification trail.
        """
        page = self.read("person", "lund-henriette", "index.html")
        self.assertIn("Efter kommentaren i SKS:", page)
        self.assertIn("Erindringer fra Hjemmet", page)
        self.assertIn("b171:b-927", page)
        self.assertNotIn("Kommentaren giver ingen biografisk note", page)

    def test_a_bio_filed_under_another_commentary_key_still_reaches_its_page(self):
        """The four people bio_keys.json bridges each show their biography."""
        cases = [
            ("mueller-frederik-paludan", "digter"),
            ("calderon-pedro-de-la-barca", "spansk dramatiker"),
            ("collin-edvard", "Edvard Collin (1808-86)"),
            ("frederik-christian-petersen", "filolog"),
        ]
        for slug_, marker in cases:
            page = self.read("person", slug_, "index.html")
            self.assertIn("Efter kommentaren i SKS", page, slug_)
            self.assertIn(marker, page, slug_)

    def test_a_person_the_commentary_names_without_a_note_says_which_it_is(self):
        # The thirteen in bios.json's withoutBio: mentioned, but not as a
        # biographical subject. That is a different silence from having no
        # note at all, and the page distinguishes them.
        page = self.read("person", "victor-eremita", "index.html")
        self.assertIn("nævner personen, men uden biografiske oplysninger", page)

    def test_the_person_lists_wear_the_same_card_as_a_correspondence(self):
        """Maria's call (2026-07-28): one design for every letter list.

        'Breve til X', 'Breve, hvor X er nævnt' and the rest get exactly the
        letter page's 'Samme brevveksling' layout: the same head band
        over the same list, byte for byte the same structure.
        """
        person = self.read("person", "kierkegaard-peter-christian", "index.html")
        letter = self.read("brev", "1", "index.html")
        self.assertIn(
            '<div class="list-head"><h2>Breve til Peter Christian Kierkegaard</h2>',
            person,
        )
        self.assertIn('<div class="list-head"><h2>Samme brevveksling</h2>', letter)

    def test_kierkegaards_own_page_keeps_its_one_line_and_lists_his_letters(self):
        page = self.read("person", "kierkegaard-soeren-aabye", "index.html")
        self.assertIn("Søren Aabye Kierkegaard (1813-55).", page)
        self.assertIn("235 breve", page)          # sent
        self.assertIn("Breve til Søren Aabye Kierkegaard", page)

    def test_the_edition_s_abbreviation_is_spelled_out_for_the_reader(self):
        """"SK" becomes "Søren Kierkegaard" wherever a name is shown.

        Maria's call (korrektur 2026-07-28): the edition's own heading
        abbreviates the one correspondent the site is about, so a reader
        met "fra SK til ..." in 235 of 336 rows before they ever met his
        name. The source form is not thrown away -- it stays in
        ``data-name`` and it is still what the facets filter on.
        """
        self.assertEqual("Søren Kierkegaard", display_name("SK"))
        letter = self.read("brev", "1", "index.html")
        self.assertIn(">Søren Kierkegaard</a>", letter)
        self.assertIn('data-name="SK"', letter)          # the source's own word
        self.assertIn("fra Søren Kierkegaard til P.C. Kierkegaard", self.read("index.html"))

    def test_an_abbreviation_is_matched_whole_and_never_inside_a_name(self):
        """The Agerskov lesson, applied to the display side.

        "Agerskov, Chr." is a real correspondent whose surname contains the
        same two letters, upper-cased. Expanding on a substring would turn
        him into Kierkegaard; the table is looked up on the whole string.
        """
        self.assertEqual("Chr. Agerskov", display_name("Agerskov, Chr."))
        self.assertEqual("SKS", display_name("SKS"))
        self.assertEqual("Peter Skram", display_name("Skram, Peter"))
        self.assertIn("Chr. Agerskov", self.read("index.html"))

    def test_the_alias_table_is_what_puts_a_letter_on_a_persons_page(self):
        """"SK" is not a persName key; the curated table makes it one."""
        letter = self.read("brev", "1", "index.html")
        self.assertIn('href="../../person/kierkegaard-soeren-aabye/"', letter)
        self.assertIn('href="../../person/kierkegaard-peter-christian/"', letter)
        page = self.read("person", "kierkegaard-peter-christian", "index.html")
        self.assertIn('href="../../brev/1/"', page)

    def test_a_letter_addressed_to_nobody_in_particular_links_to_nobody(self):
        """Letter 39 is addressed to "familien" -- a group, left unmapped."""
        letter = self.read("brev", "39", "index.html")
        recipient = letter.split("<dt>Til</dt>", 1)[1].split("</div>", 1)[0]
        self.assertIn('data-name="Kierkegaard, familien"', recipient)
        self.assertNotIn("<a", recipient)

    def test_a_letter_to_two_people_names_both(self):
        letter = self.read("brev", "159", "index.html")
        recipient = letter.split("<dt>Til</dt>", 1)[1].split("</div>", 1)[0]
        self.assertIn('href="../../person/schlegel-johan-frederik/"', recipient)
        self.assertIn('href="../../person/olsen-regine/"', recipient)

    def test_named_people_in_a_transcription_link_to_their_pages(self):
        letter = self.read("brev", "40", "index.html")
        transcription = letter.split('class="transcription"', 1)[1]
        self.assertIn('<a class="tei-persName" href="../../person/', transcription)
        for href in re.findall(
            r'<a class="tei-persName[^"]*" href="([^"]+)"', transcription
        ):
            self.assertTrue(href.startswith("../../person/"))

    def test_a_named_person_is_never_left_as_a_dead_span(self):
        """Every persName with a key is a link; only the keyless one is not."""
        spans = 0
        for entry in sorted(os.listdir(os.path.join(self.directory.name, "brev"))):
            page = self.read("brev", entry, "index.html")
            spans += len(re.findall(r'<span class="tei-persName', page))
        self.assertEqual(1, spans)               # b127, letter 148: key=""

    def test_the_navigation_reaches_the_register_from_every_page(self):
        for parts, href in (
            (("index.html",), 'href="personer/"'),
            (("brev", "1", "index.html"), 'href="../../personer/"'),
            (("personer", "index.html"), 'href="../personer/"'),
            (("person", "olsen-regine", "index.html"), 'href="../../personer/"'),
        ):
            self.assertIn(href, self.read(*parts))

    def test_person_pages_are_self_contained(self):
        for name in ("boesen-emil-ferdinand", "lund-henriette", "e-e"):
            page = self.read("person", name, "index.html")
            stripped = page.replace("https://creativecommons.org", "")
            self.assertNotIn("http://", stripped)
            self.assertNotIn("https://", stripped)
            self.assertNotIn('href="/', page)
            self.assertNotIn("None", page)

    def test_the_register_is_built_from_the_tei_and_not_from_the_biographies(self):
        """No curated data at all: the people are still there, unannotated."""
        with tempfile.TemporaryDirectory() as other:
            result = build_site(self.volumes, other)
            self.assertEqual(PEOPLE, result["people"])
            self.assertEqual(0, result["biographies"])
            page = os.path.join(other, "person", "boesen-emil-ferdinand", "index.html")
            self.assertTrue(os.path.exists(page))
            with open(page, encoding="utf-8") as file:
                self.assertIn("Kommentaren giver ingen biografisk note", file.read())

    def test_the_register_only_counts_people_the_alias_table_could_place(self):
        register = build_register(
            [
                _view("1", sender="SK", sender_keys=["Kierkegaard, Søren Aabye"]),
                _view("2", sender="ukendt", sender_keys=[]),
            ]
        )
        self.assertEqual(["Kierkegaard, Søren Aabye"], [p["key"] for p in register])
        self.assertEqual(1, len(register[0]["sent"]))


def _view(slug_value, sender="", sender_keys=(), person_keys_=()):
    return {
        "slug": slug_value,
        "person_keys": list(person_keys_),
        "sender_keys": list(sender_keys),
        "recipient_keys": [],
    }


if __name__ == "__main__":
    unittest.main()
