# The captions method

*How the image captions dataset is made. Established 2026-08-26 by a
trial round over four images; the full round (all 40 images in
`export/images.json`) ran the same day by the same playbook, verified
to zero flags with both foreign readers, doktor-runde folded in. The
audit trails live in `data/context/generated/captions-trial/` and
`data/context/generated/captions/`. The dataset itself —
`data/context/captions.json` — is assembled deterministically from the
drafts' verified end states by `scripts/assemble_captions.py` and
guarded by `tests/test_captions.py` (join integrity against the
manifest, the caption-less decisions, the duplicate-pair rules, a
draft-07 schema, source of truth `exporter/schemas/captions.schema.json`).
Since `schemaVersion` 0.3.0 the layer travels in the export too:
`context/captions.json`, verbatim, CC BY-NC-SA 4.0, its schema published
in `schema/`.*

## The product

Per image, keyed by the manifest ids in `export/images.json`:

- `alt` — neutral, descriptive Danish alt text: what one *sees*,
  no interpretation, no voice.
- `caption` — Maria Notabene's caption (`docs/notabene.md` §§2–5).
- `credit` — the edition's photo credit verbatim, where it has one.
- `sources` — one traceability line per factual claim.
- `note` — the drafter's doubts and deliberate omissions. (The notes are
  long, and that is data in itself: captions proved harder to write than
  summaries — fewer items, more time, more recorded doubt.)
- `repairs` — every verifier flag and what was done about it. Lives in
  the draft files (the audit trail) only: repairs are development
  history, and the dataset — and with it the export — does not repeat
  them (Maria, 2026-08-27; the bios' precedent, where repair logs sit in
  `generated/repairs-*.json`).

The final dataset becomes `data/context/captions.json` (editorial layer,
CC BY-NC-SA 4.0, independently disposable like every other dataset):
alt/caption/credit plus `sources` and `note`, which travel with the
product as editorial honesty.

## The flow

Grounding-only drafting with adversarial verification (the same method
as the summaries and bios — see the Om page's »modlæsningsrunde«), with
one extension: **the image itself is admissible primary grounding.**

1. **Grounding packet** per image
   (`scripts/prepare_caption_grounding.py`): the image file + the
   edition's own `<head>` captions + the letter's parsed reading text +
   the relevant commentary notes. The script writes to a gitignored
   workspace (`data/context/grounding/captions/`), and the round's
   packets are committed in the audit trail — the full round's 38 in
   `data/context/generated/captions/grounding/` (verified byte-identical
   to a fresh run), the trial's four originals in
   `data/context/generated/captions-trial/grounding/` — so every link
   of the generation chain is a readable document in the repository
   (Maria, 2026-08-27). The chain is also joined machine-readably:
   `data/context/generated/captions/timeline.json`
   (`scripts/build_caption_timeline.py`) holds each image's ordered
   stages — prompt, draft state, verdicts, repairs, doktor-runde,
   final — with every text state extracted from the verification
   prompts that embed it. Since the full round the packets are derived
   automatically from `export/images.json`: occurrence letters straight
   off the manifest, kom.xml figures via their enclosing commentary note
   and the letters referencing it, all of a letter's notes included —
   never a silent cap. Images with identical content (same source
   sha256) share one packet: shared alt text, caption per id against its
   own letter; an id with no occurrences at all stands caption-less with
   a reason, like the bio-less persons (Maria, 2026-08-26).
2. **Draft**: one multimodal Claude Opus agent per image. The rule in
   the prompt: *outside knowledge is inadmissible — admissible grounding
   is the image itself plus the packet; even a true claim is an error if
   untraceable.* The agent must record doubts and omissions (`note`) —
   that requirement is half the quality assurance.
3. **Adversarial verification, foreign model families**: OpenAI Codex
   (`codex exec -i <image> -- <prompt>`) and xAI Grok (image as ACP
   content block via `--prompt-json`), shared instruction in
   `data/context/generated/captions-trial/verifier-prompt.md`. They flag
   ungrounded claims *and* visual misdescriptions; taste and voice are
   not flagged. Run via `scripts/run_caption_verification.sh`.
4. **Arbitration** (the presenting Claude, inline): every flag is
   decided *against the image*, not against the verifier. Repairs use
   exactly what the flags point at; every decision is logged in the
   draft's `repairs`.
5. **Re-verify to zero** — surviving flags are either repaired or
   overruled with a logged reason.
6. **The language round (doktor-runden)**: after zero-verification the
   captions go to Maria for a manual voice pass. This deliberately
   breaks the automated systematics: the project's aim is to see how far
   AI-assisted humanities work reaches — not to push past the point
   where it stops working. Only captions she changes are re-verified
   (one verifier suffices when the edit adds no claims).

## What the trial round established

- **The letter is the authority; the eye is a witness.** Hard images
  (sketches, handwriting, faded stamps) cannot be described reliably by
  any single model eye — without context Grok read SK's telescope
  drawing as »The Kraken«, and ChatGPT lost the bridge entirely.
  Kierkegaard himself needed half a page to explain that drawing to
  Regine. For such images the caption carries meaning through the
  source's own words, and the alt text stays with what is robustly
  visible.
- **Single-model visual claims need consensus.** A detail only one
  reader sees — or readers see differently (stripes vs. checks, the
  telescope's direction) — is generalised or dropped. Reader
  disagreement measures the image's difficulty; it is not a verdict.
- **Grounding context disciplines the verifier too.** The same Grok that
  hallucinated a kraken on the bare image delivered the round's sharpest
  flags once it had packet + draft: the fence's true position, the
  stone's »MARTII« against the draft's paraphrase »marts«.
- **The edition's own words are safe ground**: »udskrift«, »kort«, the
  stone's capitals. Quote the source's form; paraphrase is where the
  errors crept in.
- **Voice calibration** (Maria's ruling in the trial's doktor-runde):
  keep the drafts' lyrical syntax as style, but **sharpen the
  referents** — names rather than pronouns (»både Kierkegaard og
  Regine«, not »de … begge to«), concrete places rather than directional
  adverbs (»lænet op ad stenen«, not »nedenfor«). Two-reading heaviness
  is inversion × unclear reference; remove the second factor, not the
  first. Difficulty may be dosed deliberately — on the grave-plot
  caption's heavy embedded clause: »det er den tungeste sætning i hele
  værket. Den må gerne være svær.« (Maria, 2026-08-26)
- Trial tally: round 1 raised 9 flags (all legitimate), round 2 two,
  round 3 zero from both verifiers; the doktor-runde then adjusted three
  captions, re-verified to zero.

## Practical notes

- Codex's `-i` flag is greedy — separate the prompt with `--`.
- Grok needs `--max-turns 6` (it spends a turn announcing itself), and
  images over ~600 KB must be downscaled for the call (macOS ARG_MAX);
  the audit trail notes that the verifier saw a smaller copy.
- Verifier flags are arbitrated, never obeyed: a wrong flag is overruled
  with a logged reason, and a verifier's own reading of ambiguous
  handwriting is as inadmissible as any other outside knowledge.
