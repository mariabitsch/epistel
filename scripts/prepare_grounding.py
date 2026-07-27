"""Prepare grounding batches for the bio/summary swarm.

One-shot generator, run before the generation workflow. It derives two sets
of batch files under ``data/context/grounding/`` (gitignored -- regenerable
from the vendored TEI at any time):

* ``letters-NN.json`` -- every letter that prints text, with its reading
  text (``plain_text``), for the summary writers. Join key back to the site
  is ``(volume, xmlId)``.
* ``persons-NN.json`` -- every person the commentary marks as a note's
  biographical subject (``persName/@n="*"``), with all notes that mention
  them across all volumes (including ded's commentary), for the bio writers.

Batches are deterministic: sorted input, fixed batch size, stable file
names. A ``manifest.json`` records counts and batch lists for the workflow.
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pipeline import corpus
from pipeline.parse_kom import parse_commentary
from pipeline.parse_tei import plain_text

VENDOR = "data/vendor"
OUT = "data/context/grounding"
BATCH = 20


def letter_batches():
    letters = []
    for volume in corpus.parse_corpus(VENDOR):
        for letter in volume["letters"]:
            text = plain_text(letter["body"]).strip()
            if not text:
                continue  # the b171 stubs print no letter text
            letters.append(
                {
                    "volume": volume["volume"],
                    "volumeTitle": volume["title"],
                    "xmlId": letter["xmlId"],
                    "id": letter["id"],
                    "heading": letter["heading"],
                    "sender": (letter["sender"] or {}).get("name"),
                    "recipient": (letter["recipient"] or {}).get("name"),
                    "senderNote": (letter["sender"] or {}).get("note"),
                    "text": text,
                }
            )
    return _chunk(letters)


def person_batches():
    persons = {}
    for name in sorted(os.listdir(VENDOR)):
        path = os.path.join(VENDOR, name, "kom.xml")
        if not os.path.isfile(path):
            continue
        commentary = parse_commentary(path)
        for note in commentary["notes"]:
            mention = {
                "volume": commentary["volume"],
                "noteId": note["id"],
                "n": note["n"],
                "lemma": note["lemma"],
                "text": note["text"],
            }
            for person in note["persNames"]:
                key = person["key"]
                if not key:
                    continue  # two empty keys exist upstream; nothing to join on
                entry = persons.setdefault(
                    key, {"key": key, "sameAs": [], "subjectNotes": [], "otherNotes": []}
                )
                if person["sameAs"] and person["sameAs"] not in entry["sameAs"]:
                    entry["sameAs"].append(person["sameAs"])
                bucket = "subjectNotes" if person["isSubject"] else "otherNotes"
                if not any(
                    m["noteId"] == mention["noteId"] and m["volume"] == mention["volume"]
                    for m in entry[bucket]
                ):
                    entry[bucket].append(mention)
    subjects = [p for key, p in sorted(persons.items()) if p["subjectNotes"]]
    return _chunk(subjects), len(persons)


def _chunk(items):
    return [items[i : i + BATCH] for i in range(0, len(items), BATCH)]


def main():
    os.makedirs(OUT, exist_ok=True)
    letters = letter_batches()
    persons, total_keys = person_batches()
    manifest = {"letterBatches": [], "personBatches": []}
    for index, batch in enumerate(letters, 1):
        name = "letters-%02d.json" % index
        _write(name, batch)
        manifest["letterBatches"].append({"file": name, "count": len(batch)})
    for index, batch in enumerate(persons, 1):
        name = "persons-%02d.json" % index
        _write(name, batch)
        manifest["personBatches"].append({"file": name, "count": len(batch)})
    _write("manifest.json", manifest)
    print(
        "letters: %d in %d batches | subjects: %d in %d batches (of %d keys total)"
        % (
            sum(b["count"] for b in manifest["letterBatches"]),
            len(letters),
            sum(b["count"] for b in manifest["personBatches"]),
            len(persons),
            total_keys,
        )
    )


def _write(name, data):
    with open(os.path.join(OUT, name), "w") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
