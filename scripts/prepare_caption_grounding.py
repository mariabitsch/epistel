"""Build grounding packets for the captions round — one per distinct image.

Generalises the trial-round script (2026-08-26), which hand-picked four
images: now every image in ``export/images.json`` gets a packet, and the
context the trial curated by hand is derived automatically:

- **Letters**: every occurrence's ``letter`` (figures and page breaks in
  the manifest carry it).
- **kom.xml figures** sit in no letter division; their *enclosing*
  commentary note is located in ``kom.xml``, and every letter whose body
  references that note (``ref subtype="commentary"``, volume-local) is
  pulled in as context too.
- **Commentary notes**: all notes referenced from each included letter,
  in reading order, plus the enclosing notes — lemma and prose verbatim
  via ``pipeline.parse_kom``. Nothing is filtered: a long letter means a
  long packet, never a silent cap.
- **Duplicate content**: images with the same source sha256 share one
  packet listing both manifest ids — the alt text is shared, the caption
  is drafted per id against its own letter (Maria, 2026-08-26). Two
  pairs exist: ``b79/ill_24`` == ``b308/ill_24`` (known since the
  manifest), and — found by this grouping, 2026-08-26 —
  ``b241/ill_k10`` == ``b259/ill_k10``: the "unreferenced" b241 file is
  a byte-identical copy of b259's referenced plate.
- **Orphans**: an image referenced nowhere in the edition gets an honest
  packet stating that the image file and its provenance row are the only
  admissible grounding, and stands caption-less, like the bio-less
  persons (Maria, 2026-08-26); the packet exists for the alt text. With
  the k10 pair merged above, the only lone orphan is ``b79/ill_k4.jpg``.
  An unreferenced id *inside* a duplicate pair likewise stands
  caption-less; only the alt text is shared.

Output: ``data/context/grounding/captions/<slug>.md`` — gitignored like
the rest of ``data/context/grounding/`` (regenerable).

Run from the repo root: ``python3 scripts/prepare_caption_grounding.py``
"""

import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from pipeline.corpus import parse_corpus  # noqa: E402
from pipeline.parse_kom import parse_commentary  # noqa: E402
from pipeline.parse_tei import plain_text  # noqa: E402

VENDOR = ROOT / "data" / "vendor"
OUT = ROOT / "data" / "context" / "grounding" / "captions"

TEI = "{http://www.tei-c.org/ns/1.0}"
XML_ID = "{http://www.w3.org/XML/1998/namespace}id"


def slug_for(image_id):
    """b79/ill_24.jpg -> b79-ill_24; vignet/vig-brev-kikkert.jpg keeps its name."""
    return image_id.replace("/", "-").rsplit(".", 1)[0]


def commentary_refs(node, found):
    """Collect kom.xml note ids referenced from a parsed body, in reading order."""
    if isinstance(node, dict):
        if node.get("type") == "ref" and node.get("subtype") == "commentary":
            target = node.get("target") or ""
            if target.startswith("kom.xml#"):
                found.append(target.split("#", 1)[1])
        for value in node.values():
            commentary_refs(value, found)
    elif isinstance(node, list):
        for item in node:
            commentary_refs(item, found)


def enclosing_note(volume, figure_xml_id):
    """The xml:id of the kom.xml commentary note containing a figure, or None."""
    root = ET.parse(VENDOR / volume / "kom.xml").getroot()
    parents = {child: parent for parent in root.iter() for child in parent}
    for figure in root.iter(TEI + "figure"):
        if figure.get(XML_ID) == figure_xml_id:
            node = figure
            while node in parents:
                node = parents[node]
                if node.tag == TEI + "note" and node.get(XML_ID):
                    return node.get(XML_ID)
    return None


class Corpus:
    """Lazy per-volume access to parsed letters and commentary notes."""

    def __init__(self):
        self.volumes = {v["volume"]: v for v in parse_corpus(VENDOR)}
        self._notes = {}

    def letter(self, volume, letter_id):
        return next(l for l in self.volumes[volume]["letters"] if l["id"] == letter_id)

    def note(self, volume, note_id):
        if volume not in self._notes:
            commentary = parse_commentary(VENDOR / volume / "kom.xml")
            self._notes[volume] = {n["id"]: n for n in commentary["notes"]}
        return self._notes[volume].get(note_id)

    def letters_referencing(self, volume, note_id):
        """Letters in a volume whose bodies reference one commentary note."""
        hits = []
        for letter in self.volumes[volume]["letters"]:
            refs = []
            commentary_refs(letter["body"], refs)
            if note_id in refs:
                hits.append(letter["id"])
        return hits


def ordered_unique(items):
    seen, out = set(), []
    for item in items:
        if item not in seen:
            seen.add(item)
            out.append(item)
    return out


def group_by_content(images):
    """Group manifest entries by source sha256 (the duplicate plate merges)."""
    groups = []
    by_sha = {}
    for image in images:
        sha = image["source"]["sha256"]
        if sha in by_sha:
            by_sha[sha].append(image)
        else:
            by_sha[sha] = [image]
            groups.append(by_sha[sha])
    return groups


def packet(group, corpus):
    ids = [image["id"] for image in group]
    occurrences = [
        (image, occ, kind)
        for image in group
        for kind, occs in (("figure", image["figures"]), ("pb", image["pageBreaks"]))
        for occ in occs
    ]

    # Letters straight off the manifest occurrences.
    letters = ordered_unique(
        (occ["volume"], occ["letter"])
        for _, occ, _ in occurrences
        if occ.get("letter")
    )

    # kom.xml figures: enclosing note, plus the letters that reference it.
    enclosing = []
    for _, occ, kind in occurrences:
        if kind == "figure" and occ["file"] == "kom.xml":
            note_id = enclosing_note(occ["volume"], occ["xmlId"])
            if note_id:
                enclosing.append((occ["volume"], note_id))
    enclosing = ordered_unique(enclosing)
    for volume, note_id in enclosing:
        for letter_id in corpus.letters_referencing(volume, note_id):
            if (volume, letter_id) not in letters:
                letters.append((volume, letter_id))

    # All commentary notes each letter references, in reading order,
    # plus the enclosing notes themselves.
    notes = list(enclosing)
    for volume, letter_id in letters:
        refs = []
        commentary_refs(corpus.letter(volume, letter_id)["body"], refs)
        notes.extend((volume, note_id) for note_id in refs)
    notes = ordered_unique(notes)

    lines = ["# Grounding: %s" % " + ".join(ids), ""]
    if len(ids) > 1:
        lines.append(
            "**Én planche, to manifest-id'er** (identisk fil, samme sha256, "
            "vendoret i to bind). Alt-teksten er fælles. Captionen udkastes "
            "pr. id mod dets eget brev — men et id helt uden forekomster i "
            "udgaven skal stå caption-løst med begrundelse (kun alt-teksten "
            "deles)."
        )
        for image in group:
            if not image["figures"] and not image["pageBreaks"]:
                lines.append(
                    "Id uden forekomster: `%s` (refereres ingen steder i "
                    "udgaven)." % image["id"]
                )
        lines.append("")
    for image in group:
        lines.append("Billedfil: `data/vendor/%s` (tilladt primærkilde)." % image["id"])
    lines.append("")

    for image in group:
        lines.append("## Manifest-post: %s (export/images.json)" % image["id"])
        lines.append("```json")
        lines.append(json.dumps(image, ensure_ascii=False, indent=1))
        lines.append("```")
        lines.append("")

    heads = [h for image in group for f in image["figures"] for h in (f["head"] or [])]
    lines.append("## Udgavens egne billedtekster (head)")
    lines.extend("- %s" % h for h in ordered_unique(heads) or ["(ingen — ingen figur har en head)"])

    if not letters and not notes:
        lines.append("")
        lines.append("## Ingen forekomster i udgaven")
        lines.append(
            "Dette billede refereres ingen steder i den vendorede udgave — "
            "hverken fra en figur, et sidebrud eller en kommentarnote. "
            "Tilladt grounding er alene billedfilen selv og dens "
            "proveniensrække (manifest-posten ovenfor). Billedet skal stå "
            "caption-løst med begrundelse; kun alt-teksten udkastes."
        )

    for volume, letter_id in letters:
        letter = corpus.letter(volume, letter_id)
        lines.append("")
        lines.append("## Brev %s (%s) — overskrift og læsetekst" % (letter_id, volume))
        lines.append("Overskrift: %s" % (letter.get("heading") or "(ingen)"))
        lines.append("")
        lines.append(plain_text(letter["body"]))

    for volume, note_id in notes:
        note = corpus.note(volume, note_id)
        lines.append("")
        lines.append("## Kommentarnote %s (%s/kom.xml, ordret)" % (note_id, volume))
        if note is None:
            lines.append("(note %s not found in %s/kom.xml)" % (note_id, volume))
            continue
        if (volume, note_id) in enclosing:
            lines.append("*Denne note omslutter selve figuren i kommentarbindet.*")
        lines.append("Lemma: %s" % (note["lemma"] or "(intet)"))
        lines.append("")
        lines.append(note["text"])

    lines.append("")
    return "\n".join(lines)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    manifest = json.loads((ROOT / "export" / "images.json").read_text(encoding="utf-8"))
    corpus = Corpus()
    for group in group_by_content(manifest["images"]):
        slug = "+".join(slug_for(image["id"]) for image in group)
        path = OUT / ("%s.md" % slug)
        path.write_text(packet(group, corpus), encoding="utf-8")
        print("wrote", path)


if __name__ == "__main__":
    main()
