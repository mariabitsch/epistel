# The grounding packets — the full caption round

The 38 grounding packets the caption round's drafting and verification
worked against: per image (or per byte-identical pair, the two `+` file
names), the manifest entry from `export/images.json`, the edition's own
`<head>` captions, the reading text of every letter the image occurs in
or is named by, and the relevant commentary notes. Together with the
image file itself, a packet is the *complete admissible grounding* for
that image's alt text and caption — the method's central constraint
(see `docs/captions-method.md`).

Provenance and reproducibility:

- Produced by `scripts/prepare_caption_grounding.py`. The committed
  copies were verified **byte-identical to a fresh run** of the script
  at the round's final state (checked 2026-08-27) — like `export/`, the
  files are deterministic derivations, committed so every link of the
  round's chain is a readable document in the repository.
- The script was repaired mid-round: the `ill_15` finding (commit
  `7969903`) added the letters an edition `<head>` caption *names* to
  the packets. Drafts made before that repair saw pre-fix packets for
  their images; the difference is visible in the script's git history,
  and the affected drafts went through re-verification like everything
  else.
- The four trial-round image ids (`b1-ill_1`, `b1-ill_k3`,
  `b127-ill_14`, `vignet-vig-brev-kikkert`) appear here as the
  generalised script's *regenerated* packets. The packets the trial's
  drafter agents actually received are preserved separately in
  `../../captions-trial/grounding/`.

38 packets cover all 40 manifest ids: the two byte-identical pairs
(`b241/ill_k10`+`b259/ill_k10`, `b308/ill_24`+`b79/ill_24`) share one
packet each. The packet content is almost entirely the edition's own
CC0 text; the framing is ours.
