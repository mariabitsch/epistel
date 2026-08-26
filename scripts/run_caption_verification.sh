#!/bin/bash
# Adversarial verification of one caption draft (the captions rounds).
# Usage: run_caption_verification.sh <slug> <image-path> <verifier: codex|grok>
# Round dirs default to the full round; override for the trial round:
#   CAPTIONS_ROUND=captions-trial run_caption_verification.sh ...
# Composes: shared instruction + grounding packet + draft JSON into one
# prompt, attaches the image, captures raw output to the audit dir.
set -euo pipefail
cd "$(dirname "$0")/.."

SLUG="$1"; IMG="$2"; WHO="$3"
ROUND="${CAPTIONS_ROUND:-captions}"
GEN="data/context/generated/$ROUND"
PROMPT="$(sed -n '/^You are an adversarial verifier/,$p' "$GEN/verifier-prompt.md")

The grounding packet (contents inline):
---
$(cat "data/context/grounding/$ROUND/$SLUG.md")
---
The draft JSON under verification (contents inline):
---
$(cat "$GEN/drafts/$SLUG.json")
---
Both documents are quoted above in full; do not try to read files. Respond with ONLY the JSON object."

mkdir -p "$GEN/verification"
OUT="$GEN/verification/$WHO-$SLUG.txt"

if [ "$WHO" = codex ]; then
  codex exec -i "$IMG" -- "$PROMPT" > "$OUT" 2>&1
else
  # macOS ARG_MAX is 1MB; downscale large images for the grok call and
  # note it — the verifier then saw a smaller copy, not the vendored file.
  if [ "$(stat -f%z "$IMG")" -gt 600000 ]; then
    SMALL="$(mktemp -t capver).jpg"
    sips -Z 1400 -s formatOptions 70 "$IMG" --out "$SMALL" >/dev/null
    IMG="$SMALL"
  fi
  B64=$(base64 -i "$IMG")
  grok --prompt-json "$(python3 -c '
import json, sys
prompt = sys.argv[1]; b64 = sys.argv[2]
print(json.dumps([{"type": "text", "text": prompt},
                  {"type": "image", "data": b64, "mimeType": "image/jpeg"}]))
' "$PROMPT" "$B64")" --max-turns 10 > "$OUT" 2>&1
fi
echo "wrote $OUT"
