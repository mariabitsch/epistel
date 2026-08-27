"""Reconstruct the caption rounds' generation timeline, per image.

The committed audit trail holds every state of every caption, but spread
across artifact types: the drafter prompts (archived instruction +
wrappers), the per-round verification files — whose *prompts* embed the
text state under review, and whose tails carry the verifier's verdict —
the repair logs, the doktor-runde documents, and the final dataset. This
script reads all of it and writes one machine-readable join:
``data/context/generated/captions/timeline.json`` — for each manifest
image id, the ordered stages of its becoming: prompt, draft state,
verification verdicts round by round, repairs, doktor-runde, final.

This is the data spine for the per-image workshop visualization (Maria's
vision, 2026-08-27): a page where the reader scrolls through the AI
process on one side while the texts update on the other. It is derived
data — deterministic from the committed audit trail plus
``data/context/captions.json``; rerun after any audit-trail change.

Extraction facts the script relies on (verified against the files):

* A codex verification file embeds the full verifier prompt, including
  the draft JSON under review (the object holding ``alt`` and
  ``caption``/``captions``), and ends with the verdict JSON (the object
  holding ``flags``), printed twice by the CLI — the last parse wins.
* A grok verification file holds only the response: an optional
  narrative line and the verdict JSON, once.
* An image appears in verification round N+1 only if round N flagged it
  (re-verify-to-zero), so the round-N+1 embedded draft IS the state
  after round N's repairs.
* The doktor-runde re-verifications (``verification/doktor-runden/``)
  embed the arbitrator's compressed texts the same way.

Run from the repo root: ``python3 scripts/build_caption_timeline.py``
"""

import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GENERATED = os.path.join(ROOT, "data", "context", "generated")
FULL = os.path.join(GENERATED, "captions")
TRIAL = os.path.join(GENERATED, "captions-trial")
DATASET = os.path.join(ROOT, "data", "context", "captions.json")
OUT = os.path.join(FULL, "timeline.json")

# The full round's wave assignment, recovered from the session transcript
# (see drafter-wrapper.md, "The waves").
WAVES = {
    "b1-ill_2": 1, "b1-ill_3": 1, "b1-ill_4": 1, "b1-ill_k1": 1,
    "b1-ill_k2": 1, "b120-ill_12": 1, "b120-ill_31": 1, "b120-ill_32": 1,
    "b127-ill_13": 2, "b127-ill_15": 2, "b171-ill_16": 2, "b171-ill_17": 2,
    "b171-ill_18": 2, "b171-ill_19": 2, "b171-ill_k7": 2, "b208-ill_20": 2,
    "b208-ill_k8": 3, "b241-ill_k10+b259-ill_k10": 3, "b241-ill_k9": 3,
    "b259-ill_21": 3, "b276-ill_22": 3, "b276-ill_23": 3, "b43-ill_5": 3,
    "b43-ill_6": 3,
    "b70-ill_7": 4, "b70-ill_8": 4, "b79-ill_9": 4, "b79-ill_10": 4,
    "b79-ill_11": 4, "b79-ill_k4": 4, "b79-ill_k5": 4, "b79-ill_k6": 4,
    "b308-ill_24+b79-ill_24": 4, "vignet-vig-brev-blomst": 4,
}


def _read(path):
    with open(path, encoding="utf-8") as file:
        return file.read()


def _read_json(path):
    with open(path, encoding="utf-8") as file:
        return json.load(file)


def _rel(path):
    return os.path.relpath(path, ROOT)


def _json_objects(text):
    """Yield every parseable top-level JSON object embedded in raw text.

    A simple brace scanner that respects string literals and escapes;
    anything that fails ``json.loads`` is skipped silently (the files are
    full of prose braces and JSON-shaped schema examples).
    """
    i, n = 0, len(text)
    while i < n:
        if text[i] != "{":
            i += 1
            continue
        depth, j, in_string, escaped = 0, i, False, False
        while j < n:
            ch = text[j]
            if in_string:
                if escaped:
                    escaped = False
                elif ch == "\\":
                    escaped = True
                elif ch == '"':
                    in_string = False
            elif ch == '"':
                in_string = True
            elif ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    break
            j += 1
        if j < n:
            try:
                yield json.loads(text[i : j + 1])
                i = j + 1
                continue
            except ValueError:
                pass
        i += 1


def _embedded_state(path):
    """The draft state a codex verification prompt carries: the object
    with ``alt`` plus ``caption`` or ``captions``. Exactly one per file."""
    states = [
        obj
        for obj in _json_objects(_read(path))
        if isinstance(obj, dict)
        and "alt" in obj
        and ("caption" in obj or "captions" in obj)
    ]
    if len(states) != 1:
        raise SystemExit("%s embeds %d draft states, expected 1" % (path, len(states)))
    return states[0]


def _verdict(path):
    """The verifier's verdict: the last embedded object holding ``flags``.

    Returns ``None`` for the one run that died without one (a grok call
    that hit its turn limit — the file records the failure and stays in
    the trail; the timeline reports it as it is, never drops it).
    """
    verdicts = [
        obj
        for obj in _json_objects(_read(path))
        if isinstance(obj, dict) and "flags" in obj
    ]
    if not verdicts:
        if "max turns reached" in _read(path).lower():
            return None
        raise SystemExit("%s holds no verdict" % path)
    return verdicts[-1]


def _text_of(state):
    """The display text of a state: alt + caption (or per-id captions)."""
    text = {"alt": state["alt"]}
    if "captions" in state:
        text["captions"] = state["captions"]
    else:
        text["caption"] = state.get("caption")
    if state.get("credit"):
        text["credit"] = state["credit"]
    return text


def _round_dirs(base):
    """The verification round directories, in order, as (label, path)."""
    verification = os.path.join(base, "verification")
    rounds = []
    for name in sorted(os.listdir(verification)):
        path = os.path.join(verification, name)
        if os.path.isdir(path) and name.startswith("round"):
            rounds.append((name, path))
    return rounds


def _verification_stage(round_label, verifier, path):
    verdict = _verdict(path)
    stage = {
        "type": "verification",
        "round": round_label,
        "verifier": verifier,
        "file": _rel(path),
        "flags": len(verdict.get("flags") or []) if verdict else None,
        "verdict": verdict,
    }
    if verdict is None:
        stage["failed"] = "max turns reached — no verdict delivered"
    return stage


def _slug_stages(base, slug, prompt_stage, doktor_stages, repairs):
    """The ordered stages for one draft slug within one round's trail."""
    stages = [prompt_stage]
    rounds = _round_dirs(base)
    first = True
    for label, rdir in rounds:
        codex = os.path.join(rdir, "codex-%s.txt" % slug)
        grok = os.path.join(rdir, "grok-%s.txt" % slug)
        if not os.path.isfile(codex) and not os.path.isfile(grok):
            continue
        if os.path.isfile(codex):
            version = 1 if first else len([s for s in stages if s["type"] == "state"]) + 1
            stages.append(
                {
                    "type": "state",
                    "version": version,
                    "source": _rel(codex),
                    "text": _text_of(_embedded_state(codex)),
                }
            )
            first = False
            stages.append(_verification_stage(label, "codex", codex))
        if os.path.isfile(grok):
            stages.append(_verification_stage(label, "grok", grok))
    stages.extend(doktor_stages)
    if repairs:
        stages.append({"type": "repairs", "entries": repairs})
    return stages


def _full_round():
    """Timelines for the full round's 34 slugs, keyed by slug."""
    drafts_dir = os.path.join(FULL, "drafts")
    doktor_dir = os.path.join(FULL, "verification", "doktor-runden")
    timelines = {}
    for name in sorted(os.listdir(drafts_dir)):
        if not name.endswith(".json"):
            continue
        slug = name[:-5]
        draft = _read_json(os.path.join(drafts_dir, name))
        prompt_stage = {
            "type": "prompt",
            "instruction": _rel(os.path.join(FULL, "drafter-prompt.md")),
            "wrapper": _rel(os.path.join(FULL, "drafter-wrapper.md")),
            "wave": WAVES[slug],
        }
        doktor_stages = []
        doktor_file = os.path.join(doktor_dir, "codex-%s.txt" % slug)
        if os.path.isfile(doktor_file):
            doktor_stages.append(
                {
                    "type": "state",
                    "version": "doktor",
                    "source": _rel(doktor_file),
                    "text": _text_of(_embedded_state(doktor_file)),
                }
            )
            doktor_stages.append(
                _verification_stage("doktor-runden", "codex", doktor_file)
            )
        doktor_stages.append(
            {
                "type": "doktor",
                "refs": [
                    _rel(os.path.join(FULL, "doktor-runden.md")),
                    _rel(os.path.join(FULL, "overlap-readers.md")),
                ],
            }
        )
        timelines[slug] = {
            "round": "full",
            "ids": draft.get("ids") or [draft["id"]],
            "packet": _rel(os.path.join(FULL, "grounding", "%s.md" % slug)),
            "draftFile": _rel(os.path.join(drafts_dir, name)),
            "stages": _slug_stages(
                FULL, slug, prompt_stage, doktor_stages, draft.get("repairs") or []
            ),
        }
    return timelines


def _trial_round():
    """Timelines for the trial round's four slugs."""
    drafts_dir = os.path.join(TRIAL, "drafts")
    timelines = {}
    for name in sorted(os.listdir(drafts_dir)):
        if not name.endswith(".json"):
            continue
        slug = name[:-5]
        draft = _read_json(os.path.join(drafts_dir, name))
        prompt_stage = {
            "type": "prompt",
            "instruction": _rel(os.path.join(TRIAL, "drafter-prompts.md")),
        }
        doktor_stages = [
            {
                "type": "language-round",
                "refs": [
                    _rel(os.path.join(TRIAL, "verified-texts-before-doktor.md")),
                    _rel(os.path.join(TRIAL, "flat-rewrites.md")),
                ],
            },
            {
                "type": "doktor",
                "refs": [_rel(os.path.join(TRIAL, "doktor-runden.md"))],
            },
        ]
        timelines[slug] = {
            "round": "trial",
            "ids": [draft["id"]],
            "packet": _rel(os.path.join(TRIAL, "grounding", "%s.md" % slug)),
            "draftFile": _rel(os.path.join(drafts_dir, name)),
            "stages": _slug_stages(
                TRIAL, slug, prompt_stage, doktor_stages, draft.get("repairs") or []
            ),
        }
    return timelines


def build():
    dataset = _read_json(DATASET)
    finals = {entry["id"]: entry for entry in dataset["captions"]}
    timelines = {}
    timelines.update(_full_round())
    timelines.update(_trial_round())

    images = {}
    for slug, timeline in timelines.items():
        for image_id in timeline["ids"]:
            final = finals[image_id]
            stages = list(timeline["stages"])
            stages.append(
                {
                    "type": "state",
                    "version": "final",
                    "source": "data/context/captions.json",
                    "text": {
                        "alt": final["alt"],
                        "caption": final["caption"],
                        **({"credit": final["credit"]} if final["credit"] else {}),
                    },
                }
            )
            images[image_id] = {
                "slug": slug,
                "round": timeline["round"],
                "sharedWith": [i for i in timeline["ids"] if i != image_id] or None,
                "packet": timeline["packet"],
                "draftFile": timeline["draftFile"],
                "stages": stages,
            }

    missing = [i for i in finals if i not in images]
    if missing:
        raise SystemExit("no timeline for %r" % missing)
    return {
        "_meta": {
            "what": (
                "Per-image generation timeline for the caption rounds: the "
                "ordered stages of each text's becoming — prompt, draft "
                "state, verification verdicts, repairs, doktor-runde, final "
                "— joined from the committed audit trail. Text states are "
                "extracted from the verification prompts that embed them; "
                "every stage cites its source file."
            ),
            "closure": (
                "A round's flags are closed by arbitration, not by the "
                "verifier: repaired against the image/packet (and "
                "re-verified in a later round where the arbitrator ordered "
                "it), or overruled with a logged reason — see each draft's "
                "repairs. Two images (b127/ill_15, b171/ill_k7) were "
                "redrafted minutes after first drafting, before any "
                "verification ran; their round 1 verifies the redraft, and "
                "the never-verified first attempt survives only in the "
                "session transcript. One grok run (round2, b70/ill_7) hit "
                "its turn limit and delivered no verdict; the stage says "
                "so."
            ),
            "generatedBy": "scripts/build_caption_timeline.py (deterministic)",
            "see": "docs/captions-method.md",
        },
        "images": {key: images[key] for key in sorted(images)},
    }


def main():
    data = build()
    with open(OUT, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=1)
        file.write("\n")
    counts = {}
    for image in data["images"].values():
        states = [s for s in image["stages"] if s["type"] == "state"]
        counts[image["slug"]] = len(states)
    print(
        "wrote %s: %d images, %d slugs, %d–%d text states per image"
        % (
            os.path.relpath(OUT, ROOT),
            len(data["images"]),
            len(set(i["slug"] for i in data["images"].values())),
            min(counts.values()),
            max(counts.values()),
        )
    )


if __name__ == "__main__":
    sys.exit(main())
