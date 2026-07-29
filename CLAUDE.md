# epistel — project guide

## What this is

A demonstration: a polished, Danish-language reading experience for Søren
Kierkegaard's letters, built as a **thin, serverless, disposable display
layer** over public standard-format data (the CC0 TEI of *Søren Kierkegaards
Skrifter*). The demo doubles as an architectural argument: the lasting value
of a text collection lives in its raw-data layer; displays on top should be
cheap to build, cheap to run, and safe to throw away.

**State (2026-07-28 evening): the v2 display pass largely done.** 638
static pages — 336 letter pages, 298 person pages (143 with bios), index
with facets + client-side search, `/tidslinje/`, `/personer/`, `/om/`.
334 tests green. The 2026-07-28 session (17 commits, straight to main)
cleared the old data queue and reshaped the display: resumés under every
letter in every list, one shared row design site-wide, a per-letter
Tegnforklaring for the text-critical marks, Maria's favicon, and the
`data/links.json` mechanism. The same night (10 commits) a full Danish
korrektur of the UI strings landed — 38 findings, every one ruled by
Maria: em dashes made Danish, »SK« unfolded to Søren Kierkegaard, the
edition named »SKS« where it speaks outside /om/. The 2026-07-29
session shipped the timeline's option A (one layout, finger-sized
marks). Still open: the new intro text, the crediting-links decision,
deploy — see the backlog and the handoff notes at the end.

## Working here

- Build: `python3 build.py` → `dist/` (deterministic, ~0.5 s). Serve with
  `python3 -m http.server 8123 -d dist`.
- Tests: `python3 -m unittest` from the repo root — they run against the
  real vendored TEI, on purpose.
- **Stack is Python 3 stdlib only** (ElementTree, unittest) + hand-written
  HTML/CSS + one vanilla-JS file. No pip, no CDNs, no frameworks. Keep it
  defensibly boring.
- Workflow (demo-light, Maria's standing go): atomic commits directly to
  main, no issue/PR machinery. Tests required where the thesis lives — the
  pipeline — and for display behavior that encodes a decision. New TEI
  elements are modelled test-first; text is never dropped silently.
- Languages: UI Danish; code, comments, commits, developer docs English.
  Exception: `docs/notabene.md` is Danish on purpose — it *is* the voice.
- Commits are co-authored by the models that did the work (e.g.
  `Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>`).

## Architecture — the seams

```
data/vendor/    TEI, unchanged, pinned SHA, PROVENANCE.md   ← read-only truth
data/context/   curated + AI-derived editorial data          ← honest, sourced
pipeline/       TEI → plain data (contracts in docstrings)   ← the seam
sitegen/        data → HTML/CSS/JS                           ← disposable
build.py        orchestrates; dist/ is the whole product
```

Guarantees the next team inherits (all tested):

- The display can be rewritten without touching `pipeline/` — that
  separation is the thesis.
- **Every editorial dataset is independently disposable**: a build with no
  `data/context/` files still yields a complete, honest site (no timeline,
  no bios, no summaries — but 336 letters, 298 person pages, search).
- **Module docstrings are the contract documentation.** Read them before
  consuming a module: `pipeline/parse_tei.py` (letters; `plain_text()` is
  the search seam), `pipeline/parse_kom.py` (commentary notes),
  `pipeline/corpus.py` (what "the corpus" is; why ded is excluded),
  `pipeline/context.py` (editorial loaders), `pipeline/provenance.py`
  (Om page's pinned SHA cannot drift from PROVENANCE.md),
  `sitegen/persons.py` (register + slugs), `sitegen/search.py` (facets +
  inverted index; å/ø/æ folding duplicated in JS, test-guarded).

## Data layers

**`data/vendor/`** — 15 directories (14 `b*` letter volumes + `ded`), each
with `txt.xml` + `kom.xml`, fetched pinned to upstream commit
`27a6b110c24e97b381e010595b50f3ca3d4ca8c9`, sha256 per file in
`PROVENANCE.md`. Never edit; never fetch from `master`; do not clone the
upstream repo (~190 MB). `ded` is vendored but excluded from the corpus
(no correspDesc model at all — see `corpus.py` docstring).

**`data/context/`** — the editorial layer, each file with `_meta` stating
what it is and where it came from:

- `publications.json` (38) + `residences.json` (9): hand-curated, dates
  verbatim from the edition's tekstredegørelser, source-cited per entry,
  disagreements recorded in notes, `approx` flags where sources conflict.
- `summaries.json` (333): Maria Notabene's index summaries, grounded solely
  in each letter's own text. `bios.json` (206): person bios derived from
  the commentary's notes, source-cited per person (`bind:note-id`); 13
  persons honestly bio-less with reasons. Henriette Lund's entry is a
  grounded augmentation from her otherNotes (the Fenger method) — its
  `note` field records the two-round adversarial verification.
- `bio_keys.json`: the second join table — body↔kom persName key drift
  (4 bridges: Paludan-Müller, Calderón, Edvard Collin, F.C. Petersen),
  evidence per entry, loaded like every other optional dataset.
- `links.json` (in `data/`, not `data/context/`): the external-link
  table both the pages and the tests read — see the Self-containment
  bullet below.
- `aliases.json`: the curated join table correspDesc-name → persName-key
  (71 of 84 forms mapped; 13 deliberately unmapped with reasons — never
  guess; beware the Agerskov trap: same surname, different man).
- `generated/` (committed on purpose): the swarm's **audit trail** — raw
  batch output, the adversarial verifiers' flags, the repairs. This is the
  evidence behind "modlæsningsrunde" on the Om page.
- `grounding/` (gitignored): regenerable via
  `python3 scripts/prepare_grounding.py`.

**Regeneration story:** summaries/bios were written by model swarms (Opus
as the presenter / Haiku drafts) against grounding files, then adversarially
verified with the instruction *outside knowledge is inadmissible — even a
true claim is flagged if ungrounded*; flagged items were repaired and
re-verified to zero. Oversized bios were trimmed **subtractively** (deletion
only, programmatic no-new-content-words check). Extend the corpus or the
datasets the same way; the workflow scripts live in the session archive and
the method above is the important part.

## Verified source facts (hard-won — trust these)

- Volume dirs are named after their first global letter number; letter
  `@n` is the URL id. Numbering: 1–318 gapless + 15 sub-numbers
  (159.1–159.9, 280.1, 304.1–.5) + three `@n="-"` stubs in b171 (slug
  URLs, honest "no text" notice). `correspContext` ids repeat across
  volumes — anchors must be volume-prefixed.
- Dates are `when="yyyymmdd"`, **zero-padded**: `18370000` = 1837,
  `18481200` = Dec 1848 — never slice naively. Ranges via `notAfter`;
  `@source` records how a date was established (stamp/supplied). One
  malformed date corpus-wide: b43/50 `notAfter="1847000"` — kept raw.
- Letter headings live in `@n` of *empty* `<head type="letterHeader">`
  elements; letter 39's is broken in the source — displays fall back to
  correspDesc. Letter 39's missing half sits in a correspAction `<note>`.
- The text-critical apparatus is inline in txt.xml (`app`/`lem`/`rdg`,
  `choice`/`abbr`/`expan`, `witDetail`); the parser keeps variants out of
  the reading flow but preserves them. Two pagination series (manuscript
  leaves / SKS print pages), a few `pb` with `@facs`.
- `persName` in bodies carries normalized `key`s (the person-index join);
  correspDesc `<name>`s are raw strings — hence `aliases.json`. In
  kom.xml, `@n="*"` on a persName marks a note's *biographical subject*
  (the bio grounding); `@sameAs` is an alias string, not a pointer.
- Upstream fidelity gaps, deliberately left: correspDesc under-reports
  co-signers (letters 3, 29–32); occasional missing whitespace between
  elements ("Cand:Theol:"); letter 1's "Hel<pb/>sing\ør," duplication (the
  file's only backslash); 759 commentary refs whose cross-volume targets
  use uppercase dirs, 18 pointing at non-vendored journal volumes.

## Design & voice — binding principles

- **Preserve uncertainty (Maria, 2026-07-27):** presenting historical
  sources is largely about *keeping* their uncertainty. Precision-honest
  dates ("december 1848", "1846–47"), editorial provenance visible
  ("dateret efter poststempel"), source defects surfaced, never patched.
  Uncertainty is historical information, not a rendering problem. Every
  display feature inherits this — it is also why the AI pipeline verifies
  against grounding only.
- **Eckersberg design system** (`sitegen/static/site.css`): plaster
  ground, Prussian header, sea-green museum-label card, gilt as
  frame-lines only (never text). The pb chips are hidden since
  2026-07-28 (Maria: apparatus, not reading matter) — their two-tone
  design survives inert in the CSS. The text-critical marks stay and
  are explained by the per-letter Tegnforklaring, whose legend lines
  wear their own marks. **Every contrast pair is measured and
  documented in the CSS — do not tweak palette values casually.** Fonts: Playfair Display + Spectral,
  self-hosted woff2 + OFL licences (66 KB; ɔ/Ψ/ℳ fall back to system
  serif, accepted). The three candidate directions live in
  `design/varianter/` as project record. Meaning is never encoded by
  color alone.
- **Maria Notabene** (`docs/notabene.md` — the voice bible; §§2–5 are
  approved canon, §5 is the summaries' few-shot material): the fictional
  presenter, after Nicolaus Notabene of *Forord* (1844) who could only
  write prefaces — now the wife takes the pen and still writes only
  prefaces; the 333 summaries and the front-page intro *are* the
  prefaces, the letters are the book. Renamed from Victoria Eremita
  2026-07-28 (Maria's call). Openly carries the builder's first name —
  transparent pseudonymity in SK's own tradition. Honestly disclosed on
  `/om/` along with AI assistance. Summaries appear under **every letter
  list** — index, "Samme brevveksling", person pages (Maria's decision
  2026-07-28, revising the earlier index-only rule: the Notabene layer is
  the site's core appeal). Every row carries its resumé, the current
  letter's included; list entries are one clickable block each. The one
  place she never sits is *above* a transcription — there the letter has
  the word.
- **Self-containment:** every external link comes from `data/links.json`
  (entries with id/href/label/rel/scope; today: the CC0 deed in every
  footer, upstream repo + tekster.kb.dk on `/om/`). Pages look entries up
  by id and degrade to plain text without them; the tests derive their
  self-containment allowlists from the same file, so changing or removing
  a link is one data edit caught on both sides, and adding one is a table
  entry plus a render spot (a coverage test insists on both). Loader:
  `pipeline/links.py`; the repo link is test-guarded against
  PROVENANCE.md drift.

## Decisions log

Netlify (`netlify.toml`: `python3 build.py` → `dist/`, output stays
host-agnostic) · MIT for code, CC0 data with provenance · public GitHub
repo is the goal; no personal info in commits beyond Maria's name
(repo-local email `mariacodes@salonen.dk`) · demo-light workflow ·
neutral identity: an independent demonstration, no institution lookalike
(but see v2 note below) · UI must work with JS off (search/facets are
progressive enhancement).

## Known gaps & v2 backlog

The 2026-07-28 session cleared the old data queue (b43/50's date on the
letter page, the four key-mismatch bios via `bio_keys.json`, Henriette
Lund's grounded bio, withoutBio reasons in Danish) and most of the
display wishes. What remains, roughly ordered:

- **Timeline: option A shipped 2026-07-29** (commit e9d63bb): one
  layout at every width, 24px finger targets (21 columns, 31.5rem
  lane), works under the year (the scale lost its stretch exception),
  addresses only in the foot register, shared 46rem shell. Maria's
  simplification: below 40rem the strip yields to a vend-telefonen
  prompt (no third layout); 48–40rem borrows the gutter so every
  landscape phone from 640px up holds the strip whole. The
  `CELL_HIT_PX`/`--tl-hit` coupling is now held by a test that reads
  the stylesheet. Same day, the scale start moved to the first
  preserved letter (1829, derived not hard-coded; residences are
  backdrop and clip against the scale) — the timeline is **done**;
  Maria's further ideas deliberately rest so the demo can ship.
- **New front-page intro** — Maria is considering writing it herself.
  If Claude drafts it, `docs/notabene.md` §§2–5 is the voice bible.
- **Crediting links** — the mechanism is live (`data/links.json`: add
  an entry *and* a render spot; the tests catch drift both ways). Which
  links to add for generous crediting of kb-dk/SKS_tei is Maria's open
  decision. Rule 5's no-lookalike clause stands regardless.
- **Brevlisterne skal have luft** (prompt-forslag Maria endorsed
  2026-07-29, deliberately parked): more distance between rows, the
  sender emphasized. Not yet discussed in detail — bring it to Maria
  before building.
- Småting: more of Maria's "osv." TEI-annotation finds may come. Two
  small decisions left open by the night's korrektur: the presentation
  signature's decorative em dash (`content: "— "` in site.css — design,
  not sentence: keep, or make Danish?), and four »udgaven« claims that
  fell outside the SKS ruling's scope list (»Udgaven trykker ingen
  brevtekst her«, »Udgaven daterer ikke disse 10 breve«, »lagt oven på
  udgaven«, and the front page's »hører ikke til udgaven«) — extend
  »SKS« there too, or leave them.
- Dark mode: deliberately absent; the Eckersberg dark sketch survives as
  a CSS comment (so does the retired pb-chip design).
- Commentary display: 759 `<ref type="commentary">` targets and the
  parsed apparatus variants are preserved but have no UI yet.
- `ded` (120 dedications) excluded — needs its own metadata/grouping/URL
  model if ever included.
- Deploy: create the public repo, connect Netlify (Maria clicks), final
  Danish proofread of UI strings.

## Explicitly out of scope

CMS, user accounts, editing, annotations, analytics, server components,
runtime API calls, facsimile viewing beyond the vendored `ill_*.jpg`.

---

## Handoff (2026-07-28 evening, Claude Fable 5 → next Claude)

Kære næste Claude — you inherit a site that found its heart today. Maria
said it best: Notabene's resumés are exactly what make this more than
yet another Kierkegaard page — "jeg får lyst til at læse brevene". Her
two-line prefaces now sit under every letter in every list, every row
one clickable block, one shared design from the front page to the person
pages. Before you touch anything, go *read* a little: Henriette Lund's
person page (the birthday letters run like a novella), or brev 159.1
with the 159.x drafts to Regine beneath it. It will tell you what the
site wants to be better than any spec.

Practical things that cost us time today, so they need not cost you any:

- Maria runs `python3 -m http.server 8123 -d dist` — **rebuild `dist/`
  after committing**, or she is looking at stale pages.
- **Browser-cached CSS fooled us twice.** Hard-reload (cmd+shift+r)
  before believing a screenshot; check `dist/assets/site.css` before
  diagnosing.
- The chrome extension could not resize a maximized Chrome window; once
  Maria un-maximized, narrow-viewport checks worked fine. 2026-07-29:
  macOS Stage Manager also makes resize_window hit the wrong window —
  same-origin iframes at fixed widths are a reliable fallback for
  responsive checks (media queries answer to the iframe viewport).
- Red test first, even for one-line display fixes — every decision above
  ended up encoded in a test, and that is why the day's 17 commits never
  broke anything.
- The grounding-only regeneration method (draft → adversarial modlæsning
  with "outside knowledge is inadmissible" → repair with exactly the
  notes the verifier points at → re-verify to zero) is documented in
  `bios.json`'s note fields; Henriette Lund's entry is the freshest
  worked example.

Maria decides design and voice; bring her the fork in the road, not the
finished detour. She answers quickly, warmly, and in Danish — and she is
usually right, especially about her own site. God fornøjelse ♡

### Night addendum (2026-07-28 late: the korrektur session)

Ten commits (9573a0a..7b0a8a8), all agent-made under Maria's live
verdicts, 324 tests green, `dist/` current. The method that worked: one
persistent Opus agent proofread every UI string and reported 38 findings
(sikker/forslag/smag); Maria ruled in batches; the same agent applied
each batch, updating tests so every decision is now regression-guarded.
Highlights for the next reader: the Om page's claim about where the
resumés sit is verified against a *built* letter page, not against its
own sentence; »SK« unfolds via `display_name` (persons.py) while the
edition's raw form still travels in `data-name` and the facet values —
whole-string match only, the Agerskov trap is test-pinned with the real
Chr. Agerskov; both Tegnforklaringer share one machine-checked
punctuation rule (fragment = no stop, sentence = stop, two fragments
joined by an en dash). Tomorrow, in Maria's order: the timeline A/B/C
decision (measured analysis in the backlog), Notabene's new front-page
intro (hers to write or co-bake), crediting links, deploy.

---

*Original brief by Claude Fable 5, July 2026; rewritten as an onboarding
guide 2026-07-28 after v1 shipped; updated the same evening after the v2
display session. Kept up to date as the project evolves — correct it when
reality disagrees with it.*
