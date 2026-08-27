"""Assemble ``data/context/captions.json`` from the caption rounds' drafts.

The captions were written in two rounds (2026-08-26, see
``docs/captions-method.md``): a trial of four images and a full round of
the remaining 36 manifest ids. Their verified end states live in the
committed audit trail:

* ``data/context/generated/captions/drafts/*.json`` -- the full round's
  34 draft files, doktor-runde folded in. Two are *pair* files (the
  byte-identical duplicates), holding ``ids`` and a per-id ``captions``
  map over one shared alt/credit/sources/note/repairs.
* ``data/context/generated/captions-trial/captions-fragment.json`` -- the
  trial's four approved texts (alt/caption/credit, post doktor-runde);
  their sources/note/repairs sit in the trial's own ``drafts/*.json``.

This script flattens all of that to one entry per manifest id, ordered by
``export/images.json``, and writes the dataset with its ``_meta``. It is
deterministic: same inputs, same file. Rerun it after touching a draft;
the diff is the review artifact, as everywhere else in this repository.

The dataset carries what the bios' precedent carries: the texts, their
``sources`` lines and the drafter's recorded doubts (``note``) -- editorial
honesty that belongs with the product. The repair logs (verifier flags and
what was done about them) are development history and stay in the drafts;
the dataset -- and with it the export -- does not repeat them (Maria,
2026-08-27).
"""

import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONTEXT = os.path.join(ROOT, "data", "context")
FULL_DRAFTS = os.path.join(CONTEXT, "generated", "captions", "drafts")
TRIAL = os.path.join(CONTEXT, "generated", "captions-trial")
MANIFEST = os.path.join(ROOT, "export", "images.json")
OUT = os.path.join(CONTEXT, "captions.json")

META = {
    "description": (
        "Alt-tekster og billedtekster til udgavens illustrationer: en "
        "alt-tekst pr. billede og, hvor udgaven selv giver billedet et "
        "sted at tale fra, en billedtekst af Maria Notabene (fiktiv "
        "formidler, se docs/notabene.md og Om-siden). Nøglen er "
        "billed-id'et fra export/images.json; de to filer, udgaven ikke "
        "henviser til nogen steder, står bevidst uden billedtekst "
        "(caption: null, begrundet i entry'ens note)."
    ),
    "editorialLayer": True,
    "notFromTEI": True,
    "license": "CC BY-NC-SA 4.0",
    "method": (
        "docs/captions-method.md — grounding-only udkast (billedet selv + "
        "grounding-pakke er eneste tilladte belæg), adversarial modlæsning "
        "med to fremmede modelfamilier (OpenAI Codex, xAI Grok) til nul "
        "flag, arbitrering mod billedet, og Marias egen doktor-runde. "
        "Hele revisionssporet — udkast, flag, reparationer — er committet "
        "i data/context/generated/captions/ og captions-trial/."
    ),
    "generator": (
        "Claude Opus 5 (udkast), OpenAI Codex + xAI Grok (adversarial "
        "modlæsning), Claude Fable 5 (arbitrering og samling), "
        "Maria Bitsch (doktor-runden)"
    ),
    "generated": "2026-08-26",
    "assembledBy": "scripts/assemble_captions.py (deterministisk, fra udkastfilerne)",
}

# The dataset's field order, kept stable for readable diffs.
FIELDS = ("id", "alt", "caption", "credit", "sources", "note")


def _read_json(path):
    with open(path, encoding="utf-8") as file:
        return json.load(file)


def _entry(image_id, alt, caption, credit, sources, note):
    return {
        "id": image_id,
        "alt": alt,
        "caption": caption,
        "credit": credit,
        "sources": sources,
        "note": note,
    }


def _full_round_entries():
    """One entry per id from the full round's drafts; pair files flatten
    to one entry per id over the shared fields."""
    entries = {}
    for name in sorted(os.listdir(FULL_DRAFTS)):
        if not name.endswith(".json"):
            continue
        draft = _read_json(os.path.join(FULL_DRAFTS, name))
        if "ids" in draft:  # a pair file: shared everything but the caption
            for image_id in draft["ids"]:
                entries[image_id] = _entry(
                    image_id,
                    draft["alt"],
                    draft["captions"][image_id],
                    draft["credit"],
                    draft["sources"],
                    draft["note"],
                )
        else:
            entries[draft["id"]] = _entry(
                draft["id"],
                draft["alt"],
                draft["caption"],
                draft["credit"],
                draft["sources"],
                draft["note"],
            )
    return entries


def _trial_entries():
    """The trial's four: approved texts from the fragment (the doktor-runde
    happened there), audit fields from the trial's own drafts."""
    fragment = _read_json(os.path.join(TRIAL, "captions-fragment.json"))
    drafts = {}
    trial_drafts = os.path.join(TRIAL, "drafts")
    for name in sorted(os.listdir(trial_drafts)):
        if name.endswith(".json"):
            draft = _read_json(os.path.join(trial_drafts, name))
            drafts[draft["id"]] = draft
    entries = {}
    for image_id, text in fragment["captions"].items():
        draft = drafts[image_id]
        entries[image_id] = _entry(
            image_id,
            text["alt"],
            text["caption"],
            text.get("credit"),
            draft["sources"],
            draft["note"],
        )
    return entries


def assemble():
    manifest_ids = [image["id"] for image in _read_json(MANIFEST)["images"]]
    entries = _full_round_entries()
    for image_id, entry in _trial_entries().items():
        if image_id in entries:
            raise SystemExit("%s drafted in both rounds" % image_id)
        entries[image_id] = entry
    missing = [i for i in manifest_ids if i not in entries]
    extra = sorted(set(entries) - set(manifest_ids))
    if missing or extra:
        raise SystemExit(
            "drafts and manifest disagree: missing %r, extra %r"
            % (missing, extra)
        )
    return {
        "_meta": META,
        "captions": [entries[image_id] for image_id in manifest_ids],
    }


def main():
    data = assemble()
    with open(OUT, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)
        file.write("\n")
    print("wrote %s (%d entries)" % (os.path.relpath(OUT, ROOT), len(data["captions"])))


if __name__ == "__main__":
    sys.exit(main())
