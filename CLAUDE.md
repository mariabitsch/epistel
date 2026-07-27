# epistel — build brief

## What this is

A demonstration: a polished, Danish-language reading experience for a
TEI-encoded letter collection, built as a **thin, serverless, disposable
display layer** over public standard-format data.

The demo doubles as an architectural argument: the lasting value of a text
collection lives in its standard-format raw-data layer (public TEI files);
displays on top should be cheap to build, cheap to run, and safe to throw
away. Everything about this project should embody that argument.

The collection: Søren Kierkegaard's letters (and dedications) from the
scholarly edition *Søren Kierkegaards Skrifter* (SKS), whose TEI source is
public and CC0-licensed.

## Data source (public, CC0)

- Upstream repo: `github.com/kb-dk/SKS_tei` — license **CC0-1.0** (verified
  2026-07-27). TEI P5, "allPlus" ODD pinned to TEI Guidelines 3.2.0 (2017);
  generated schema files (`tei_allPlus.rnc` etc.) sit at the repo root.
- Data root: `data/v1.9/`. The letters appear to live in the `b*` volume
  directories — `b1, b43, b70, b79, b120, b127, b161, b171, b208, b234,
  b241, b259, b276, b308` (ranges of letter numbers) — and dedications in
  `ded`. **Verify this mapping against the TEI headers before relying on
  it**; it is inferred from directory names.
- Each volume directory contains: `txt.xml` (the text incl. letter
  metadata), `kom.xml` (commentary), `txr.xml` (text-critical apparatus),
  `int_*.xml` (introductions), `ill_*.jpg` (illustrations). `b1/txt.xml` is
  ~480 KB; the whole letter corpus is a few MB of XML — everything fits
  comfortably in memory.
- Letter metadata uses standard TEI **`correspDesc`/`correspAction`/
  `correspContext`** (b1/txt.xml contains 168/168/134 of them, verified by
  direct count). Sample from a prior inspection — re-verify against the
  actual file:

  ```xml
  <correspDesc xml:id="correspDesc1">
    <correspAction type="sent"><name>SK</name><date when="18290308"/></correspAction>
    <correspAction type="received"><name>Kierkegaard, P.C.</name></correspAction>
    <correspContext><p><name>Peter Christian Kierkegaard</name></p></correspContext>
  </correspDesc>
  ```

- Known quirks: dates are `when="yyyymmdd"` (no separators — not
  dash-formatted ISO); sender names may be abbreviated (`SK` = Søren
  Kierkegaard); person names come in "Efternavn, Fornavn" form. Expect
  inconsistencies and partial data (undated letters, unnamed recipients) —
  surface them honestly in the UI; never silently "fix" the source.
- **Do not clone the upstream repo** (~190 MB, mostly images across all
  volumes). Fetch only the files you need via
  `https://raw.githubusercontent.com/kb-dk/SKS_tei/master/data/v1.9/...`.
- The edition is also published at `tekster.kb.dk/sks` — useful for
  cross-checking that transcriptions render sensibly. Do **not** copy that
  site's design or assets.

## Rules of the game

1. **The TEI is read-only truth.** Vendor the needed XML files unchanged
   into `data/vendor/`, and record source URL + upstream commit SHA in a
   provenance file. Never edit vendored files. All processing happens in a
   build step.
2. **Static output only.** No server-side runtime, no database, no external
   services at runtime. The built site must work from any static file host,
   with fully self-contained assets (no CDNs, no external fonts).
3. **Boring technology, minimal dependencies.** A small, deterministic
   build pipeline (TEI XML → JSON → static site). Choose tools you can
   defend as boring; no heavy SPA framework unless genuinely needed.
4. **The display is disposable; the pipeline contract is the seam.**
   Parsing (TEI → structured JSON) and display are strictly separated. It
   must be plausible to rewrite the display entirely without touching the
   parser — that separation *is* the thesis.
5. **Neutral identity.** The site presents itself as a demonstration
   ("demonstrationsvisning"). No institution's branding, logos, or
   lookalike design — this must look like what it is: an independent
   demonstration built on public data. An "Om" page states what the site
   is, the data source and CC0 license (with link), and that the site was
   built with AI assistance (Claude).
6. **Languages.** UI: Danish. Code, comments, commits, developer docs:
   English.

## What to build

Target experience — polished *formidling*, not a developer tool:

- **Letter index**: filterable list with facets for sender, recipient and
  year/period, plus client-side free-text search over a prebuilt index.
- **Letter view**: the transcription rendered from TEI (headings,
  paragraphs, page breaks, editorial marks — as sensibly as the encoding
  allows), a metadata panel (sender, recipient, date, place), and
  prev/next navigation. Where `correspContext` connects related letters,
  link them.
- **Dedications** (`ded`): secondary — include if cheap, skip if they
  complicate the model.
- **"Om" page**: provenance, license, and a one-paragraph architecture
  note ("visningen læser fra offentligt TEI; visningslaget er bevidst
  tyndt og udskifteligt").
- Typography and layout matter: this must feel cared-for. Responsive;
  accessibility basics (semantic HTML, contrast, keyboard navigation).
- Performance: everything is pregenerated and small — aim for instant.

## Suggested milestones (adapt as needed)

1. Vendor `b1`; write the TEI→JSON parser with tests against the real file
   (letter count, correspDesc fields, one known letter's content end-to-end).
2. Index page with facets + search over b1.
3. Letter view with TEI rendering.
4. Extend to all `b*` volumes (+ `ded` if cheap); polish pass; Om page.

Ship in small vertical slices — a working b1-only site early beats a
perfect parser with no display. Follow the repo owner's global workflow
conventions (failing test first, atomic commits, etc.).

## Explicitly out of scope

CMS, user accounts, editing, annotations, analytics, server components,
runtime API calls, and facsimile viewing beyond the `ill_*.jpg` files
already in the volumes (include those only if trivially easy).

## Open decisions (ask Maria only if blocking)

- Hosting: undecided; the repo is private for now. Build output must not
  assume a particular host.
- Code license: MIT suggested (vendored TEI stays CC0 with provenance
  note); add the LICENSE file once confirmed.

---

*Handoff written by Claude Fable 5, July 2026.*
