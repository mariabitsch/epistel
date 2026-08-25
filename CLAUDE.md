# epistel — project guide

## What this is

A demonstration: a polished, Danish-language reading experience for Søren
Kierkegaard's letters, built as a **thin, serverless, disposable display
layer** over public standard-format data (the CC0 TEI of *Søren Kierkegaards
Skrifter*). The demo doubles as an architectural argument: the lasting value
of a text collection lives in its raw-data layer; displays on top should be
cheap to build, cheap to run, and safe to throw away.

**State:** live at <https://epistel-demo.netlify.app/> (public repo
mariabitsch/epistel; every push to main deploys). 638 static pages — 336
letter pages, 298 person pages (143 with bios), index with facets +
client-side search, `/tidslinje/`, `/personer/`, `/om/`. 391 tests green
(that number is machine-guarded; see Working here). The front page opens
with a factual lead (Maria's own text) and Maria Notabene's foreword, set
in the letters' frame. Since 2026-08-25 the corpus is also published as
**data**: a typed JSON export in `export/`, released via git tags
(first release `v0.1.0`); `docs/export-format.md` is its contract.

## Working here

- Build: `python3 build.py` → `dist/` (deterministic, ~0.5 s). Serve with
  `python3 -m http.server 8123 -d dist`; rebuild after changes or the
  served pages are stale.
- Export: `python3 export.py` → `export/` (deterministic, committed on
  purpose — the diff is the review artifact, and a drift test holds the
  committed copy to a fresh run). Regenerate after any pipeline or
  exporter change; tag a release when `schemaVersion` earns it.
- Tests: `python3 -m unittest` from the repo root — they run against the
  real vendored TEI, on purpose. The suite counts itself: adding tests
  means bumping `AUTOMATED_TESTS` in `sitegen/pages.py`,
  `docs/content-notes.md` and the "tests green" number in this guide —
  all three are guard-enforced.
- **Stack is Python 3 stdlib only** (ElementTree, unittest) + hand-written
  HTML/CSS + one vanilla-JS file. No pip, no CDNs, no frameworks. Keep it
  defensibly boring.
- Workflow (public-repo, Maria 2026-08-03; supersedes the demo-light
  direct-to-main rule from before the site went public): atomic commits on
  a feature branch → PR → Netlify deploy preview → Maria reviews the built
  site → merge to main, which deploys. Change and verification notes belong
  in the PR body, in the repo — never on the website. Still no issue
  machinery. Tests required where the thesis lives — the pipeline — and for
  display behavior that encodes a decision. New TEI elements are modelled
  test-first; text is never dropped silently. **A PR that changes what this
  guide states — products, commands, counts, guarantees — updates the
  guide in the same PR**: it is part of the change, not an afterthought
  (rule added 2026-08-25, after the guide had quietly gone stale).
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
exporter/       data → typed JSON + semantic HTML            ← the data product
build.py        orchestrates the site; dist/ is the site
export.py       orchestrates the export; export/ is committed and released
```

Guarantees the next team inherits (all tested):

- The display can be rewritten without touching `pipeline/` — that
  separation is the thesis. Since 2026-08-25 `exporter/` proves it from
  the other side: a second pipeline consumer whose product is the corpus
  itself as data — envelopes + semantic HTML bodies in a closed,
  TEI-named vocabulary (`docs/export-format.md` is the contract). Its
  guarantees are tested too: nothing repaired, nothing lost (a fragment's
  visible text equals the parsed reading text), deterministic output, the
  committed `export/` cannot drift from a fresh run, and the editorial
  layers travel verbatim under their own license (CC BY-NC-SA 4.0),
  distinct from the vendor layers' CC0.
- **Every editorial dataset is independently disposable**: a build with no
  `data/context/` files still yields a complete, honest site (no timeline,
  no bios, no summaries — but 336 letters, 298 person pages, search).
- **Module docstrings are the contract documentation.** Read them before
  consuming a module: `pipeline/parse_tei.py` (letters; `plain_text()` is
  the search seam), `pipeline/parse_kom.py` (commentary notes),
  `pipeline/corpus.py` (what "the corpus" is; why ded is excluded),
  `pipeline/context.py` (editorial loaders), `pipeline/provenance.py`
  (pinned SHA + the per-file record; neither the Om page nor the export
  can drift from PROVENANCE.md), `exporter/export.py` +
  `exporter/body.py` (the export's layout and vocabulary),
  `sitegen/persons.py` (register + slugs), `sitegen/search.py` (facets +
  inverted index; å/ø/æ folding duplicated in JS, test-guarded).

## Data layers

**`data/vendor/`** — 15 directories (14 `b*` letter volumes + `ded`), each
with `txt.xml` + `kom.xml`, plus the corpus volumes' 38 `ill_*.jpg`
illustrations and the two shared `vignet/` files the letters reference
(vendored 2026-08-25; upstream has no full-page letter scans — this is
everything). All fetched pinned to upstream commit
`27a6b110c24e97b381e010595b50f3ca3d4ca8c9`, sha256 per file in
`PROVENANCE.md`. Never edit; never fetch from `master`; do not clone the
upstream repo (~190 MB). `ded` is vendored but excluded from the corpus
(no correspDesc model at all — see `corpus.py` docstring).

**`data/context/`** — the editorial layer, each file with `_meta` stating
what it is and where it came from:

- `publications.json` (38) + `residences.json` (9): hand-curated, dates
  verbatim from the edition's tekstredegørelser, source-cited per entry,
  disagreements recorded in notes, `approx` flags where sources conflict.
- `summaries.json` (336): Maria Notabene's index summaries, grounded solely
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
datasets the same way; the method is what matters.

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
  use uppercase dirs, 18 pointing at non-vendored journal volumes — and
  two `graphic` urls with the same uppercase quirk (`../B120/ill_31.jpg`,
  `ill_32`): preserved verbatim, resolved case-insensitively. One image
  reference is dangling upstream: b241/249's `facs="../b241/ill_k15.jpg"`
  (404 at the pin; the file exists as `ded/ill_k15.jpg`) — preserved
  verbatim, pinned as the only one by the export's tests.

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
  2026-07-28 (apparatus, not reading matter) — their two-tone design
  survives inert in the CSS. The text-critical marks stay and are
  explained by the per-letter Tegnforklaring, whose legend lines wear
  their own marks. **Every contrast pair is measured and documented in
  the CSS — do not tweak palette values casually.** Fonts: Playfair
  Display + Spectral, self-hosted woff2 + OFL licences (66 KB; ɔ/Ψ/ℳ
  fall back to system serif, accepted). The three candidate directions
  live in `design/varianter/` as project record. Meaning is never
  encoded by color alone.
- **Maria Notabene** (`docs/notabene.md` — the voice bible; §§2–5 are
  approved canon, §5 is the summaries' few-shot material): the fictional
  presenter, after Nicolaus Notabene of *Forord* (1844) who could only
  write prefaces — now the wife takes the pen and still writes only
  prefaces; the 336 summaries and the front page's foreword *are* the
  prefaces, the letters are the book. In her own prose the comic *Forord*
  inheritance is **felt, never named** (Maria, 2026-07-29). Openly
  carries the builder's first name — transparent pseudonymity in SK's own
  tradition, disclosed on `/om/` along with AI assistance. Summaries
  appear under **every letter list**; every row carries its resumé, one
  clickable block each. The one place she never sits is *above* a
  transcription — there the letter has the word.
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
host-agnostic) · MIT for code, CC0 data with provenance, the export's
editorial layers CC BY-NC-SA 4.0 (Maria, 2026-08-25) · public GitHub
repo; no personal info in commits beyond Maria's name (repo-local email
`mariacodes@salonen.dk`) · demo-light workflow · neutral identity: an
independent demonstration, no institution lookalike · UI must work with
JS off (search/facets are progressive enhancement) · timeline option A
(2026-07-29): one layout at every width, 24 px targets, vend-telefonen
below 40rem; the `CELL_HIT_PX`/`--tl-hit` px/rem coupling is held by a
stylesheet-reading test · front page (2026-07-29): Maria's factual lead
introduces the pseudonym before her foreword speaks; the foreword shares
the letter transcriptions' frame via shared CSS selector lists, also
test-held.

## Known gaps & v2 backlog

- **Crediting links** — the mechanism is live (`data/links.json`: add an
  entry *and* a render spot; the tests catch drift both ways). Which links
  to add for generous crediting of kb-dk/SKS_tei is Maria's open decision;
  the lead's publisher reference waits with it. The no-lookalike rule
  stands regardless.
- **Brevlisterne skal have luft** (endorsed 2026-07-29, deliberately
  parked): more distance between rows, the sender emphasized. Not yet
  designed — discuss before building.
- Korrektur leftovers: the presentation signature's decorative em dash
  (`content: "— "` in site.css — design, not sentence: keep, or make
  Danish?), and three »udgaven« phrasings that fell outside the SKS
  ruling's scope (»Udgaven trykker ingen brevtekst her«, »Udgaven daterer
  ikke disse 10 breve«, »lagt oven på udgaven«) — extend »SKS« there too,
  or leave them. (The front page's fourth resolved 2026-07-29 by
  disappearing with the old lead.)
- Dark mode: deliberately absent; the Eckersberg dark sketch survives as
  a CSS comment (so does the retired pb-chip design).
- Commentary display: 759 `<ref type="commentary">` targets and the
  parsed apparatus variants are preserved but have no UI yet.
- `ded` (120 dedications) excluded — needs its own metadata/grouping/URL
  model if ever included.
- (Export foundations complete as of schemaVersion 0.1.1: JSON Schemas
  in `export/schema/` — draft-07, validated by the suite when the
  optional `fastjsonschema` is importable, e.g. from a local `.venv`
  created with `python3 -m venv .venv && .venv/bin/pip install
  fastjsonschema` — and the editorial layers licensed.)
- Småting: more TEI-annotation finds may come.

## Explicitly out of scope

CMS, user accounts, editing, annotations, analytics, server components,
runtime API calls, facsimile viewing on the *site* (the source's
`ill_*.jpg` illustrations are vendored and travel with the export, where
their TEI references resolve — but the site still displays none of them).

---

*Original brief by Claude Fable 5, July 2026; rewritten as an onboarding
guide 2026-07-28 after v1 shipped; slimmed for the public repo 2026-07-29
(process notes live in the local, uncommitted memory). Kept up to date as
the project evolves — correct it when reality disagrees with it.*
