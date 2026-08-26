"""Build grounding packets for the caption trial round (prøverunden).

For each trial image the packet gathers everything a drafting agent may
treat as admissible grounding *besides the image file itself*:

- the manifest entry from ``export/images.json`` (occurrences + captions),
- the edition's own ``<head>`` caption lines,
- the parsed reading text of the associated letter(s) (``plain_text``),
- the relevant commentary notes, quoted verbatim from ``kom.xml``.

Output: ``data/context/grounding/captions-trial/<slug>.md`` —
gitignored like the rest of ``data/context/grounding/`` (regenerable).

Run from the repo root: ``python3 scripts/prepare_caption_grounding.py``
"""

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from pipeline.corpus import parse_corpus  # noqa: E402
from pipeline.parse_tei import plain_text  # noqa: E402

VENDOR = ROOT / "data" / "vendor"
OUT = ROOT / "data" / "context" / "grounding" / "captions-trial"

# Trial images: (manifest id, slug, [(volume, letter id)], [(volume, kom note xml:id)])
TRIAL = [
    ("b1/ill_1.jpg", "b1-ill_1", [("b1", "2")], []),
    ("b127/ill_14.jpg", "b127-ill_14", [("b127", "139")], [("b127", "b-1878")]),
    ("b1/ill_k3.jpg", "b1-ill_k3", [("b1", "39")], [("b1", "b-1776"), ("b1", "b-1774"), ("b1", "b-1775")]),
    ("vignet/vig-brev-kikkert.jpg", "vignet-kikkert", [("b127", "129")], [("b127", "b-1800")]),
]


def kom_note(volume, xml_id):
    """Return the verbatim text of one commentary note, tags stripped."""
    xml = (VENDOR / volume / "kom.xml").read_text(encoding="utf-8")
    m = re.search(
        r'<note type="commentary" xml:id="%s".*?</note>' % re.escape(xml_id),
        xml,
        re.S,
    )
    if not m:
        return "(note %s not found in %s/kom.xml)" % (xml_id, volume)
    text = re.sub(r"<figure.*?</figure>", " [illustration her] ", m.group(0), flags=re.S)
    text = re.sub(r"<[^>]+>", "", text)
    return re.sub(r"\s+", " ", text).strip()


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    manifest = json.loads((ROOT / "export" / "images.json").read_text(encoding="utf-8"))
    by_id = {im["id"]: im for im in manifest["images"]}
    volumes = {v["volume"]: v for v in parse_corpus(VENDOR)}

    for image_id, slug, letters, notes in TRIAL:
        im = by_id[image_id]
        lines = ["# Grounding: %s" % image_id, ""]
        lines.append("Billedfilen selv: `data/vendor/%s` (tilladt primærkilde)." % image_id)
        lines.append("")
        lines.append("## Manifest-post (export/images.json)")
        lines.append("```json")
        lines.append(json.dumps(im, ensure_ascii=False, indent=1))
        lines.append("```")
        heads = [h for f in im["figures"] for h in (f["head"] or [])]
        lines.append("")
        lines.append("## Udgavens egne billedtekster (head)")
        lines.extend("- %s" % h for h in heads or ["(ingen — figuren har ingen head)"])
        for volume, letter_id in letters:
            letter = next(l for l in volumes[volume]["letters"] if l["id"] == letter_id)
            lines.append("")
            lines.append("## Brev %s — overskrift og læsetekst" % letter_id)
            lines.append("Overskrift: %s" % (letter.get("heading") or "(ingen)"))
            lines.append("")
            lines.append(plain_text(letter["body"]))
        for volume, xml_id in notes:
            lines.append("")
            lines.append("## Kommentarnote %s (%s/kom.xml, ordret, tags fjernet)" % (xml_id, volume))
            lines.append(kom_note(volume, xml_id))
        lines.append("")
        (OUT / ("%s.md" % slug)).write_text("\n".join(lines), encoding="utf-8")
        print("wrote", OUT / ("%s.md" % slug))


if __name__ == "__main__":
    main()
