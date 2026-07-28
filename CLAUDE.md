# epistel — project guide

## What this is

A demonstration: a polished, Danish-language reading experience for Søren
Kierkegaard's letters, built as a **thin, serverless, disposable display
layer** over public standard-format data (the CC0 TEI of *Søren Kierkegaards
Skrifter*). The demo doubles as an architectural argument: the lasting value
of a text collection lives in its raw-data layer; displays on top should be
cheap to build, cheap to run, and safe to throw away.

**State (2026-07-28): v1 feature-complete, unpolished.** 638 static pages —
336 letter pages, 298 person pages, letter index with Maria Notabene's
summaries + facets + client-side search, `/tidslinje/`, `/personer/`,
`/om/`. 278 tests green. Not yet done: the polish pass (slice 8 below),
public GitHub repo, Netlify hookup. Maria has v2 ideas coming; expect
change requests in a fresh session.

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
  in each letter's own text. `bios.json` (205): person bios derived from
  the commentary's notes, source-cited per person (`bind:note-id`); 13
  persons honestly bio-less with reasons.
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
  frame-lines only (never text), pb markers as two-tone chips. **Every
  contrast pair is measured and documented in the CSS — do not tweak
  palette values casually.** Fonts: Playfair Display + Spectral,
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
  `/om/` along with AI assistance. Summaries appear in the index only,
  never on letter pages (Maria's decision).
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

Slice 8 (polish) never ran as a unit. Known items, roughly ordered:

- **Maria's v2 pass is coming** (fresh session): change requests to the
  presentation, and a **reconsideration of external links / crediting** —
  if the demo is to persuade KB decision-makers, generous crediting of
  kb-dk/SKS_tei may serve better than strict link-minimalism. Rule 5's
  no-lookalike clause stands regardless. (The mechanism landed
  2026-07-28: `data/links.json` — which links to *add* is still Maria's
  open decision.)
- b43/50's unreadable `notAfter` is surfaced on the timeline but still
  hidden on the letter page (`dates.py`, one-line fix + test).
- Henriette Lund: 23 letters, no bio (no subject note under her key);
  candidate for a grounded augmentation from her otherNotes, like the
  J.F. Fenger repair. Four body↔kom key mismatches each cost a bio
  (Müller/Paludan-Müller, Calderón, Collin Edvard, F.C. Petersen) — needs
  a second small join table.
- `bios.json` `_meta.withoutBio` reasons are English on a Danish site
  (not rendered, but a data defect).
- Dark mode: deliberately absent; the Eckersberg dark sketch survives as
  a CSS comment.
- Timeline letter marks are 10×11px (below WCAG 2.5.8's 24px target;
  mitigations exist — revisit in polish). Publication labels drift within
  the five stretched years (leader lines carry the truth).
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

*Original brief by Claude Fable 5, July 2026; rewritten as an onboarding
guide 2026-07-28 after v1 shipped. Kept up to date as the project evolves —
correct it when reality disagrees with it.*
