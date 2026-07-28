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
- Data root: `data/v1.9/`. The letters live in the `b*` volume directories —
  `b1, b43, b70, b79, b120, b127, b161, b171, b208, b234, b241, b259, b276,
  b308` — and dedications in `ded`. **Verified 2026-07-27:** the directory
  names are the *starting global letter number* of each volume's range; the
  letter number (`<div type="letter" n="…">`) is globally unique and is our
  natural URL id. b1 contains letters 1–42.
- Each volume directory contains: `txt.xml` (the text incl. letter
  metadata), `kom.xml` (commentary), `txr.xml` (text-critical apparatus),
  `int_*.xml` (introductions), `ill_*.jpg` (illustrations). `b1/txt.xml` is
  ~480 KB; the whole letter corpus is a few MB of XML — everything fits
  comfortably in memory.
- Letter metadata uses standard TEI **`correspDesc`/`correspAction`/
  `correspContext`** — b1/txt.xml contains 42/84/42 of them (verified by
  direct count 2026-07-27; the handoff's earlier claim of 168 was wrong).
  Each letter div links its metadata: `<div type="letter" n="1" xml:id="n1"
  corresp="#correspDesc1">`. Sample:

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
- Person identification (verified 2026-07-27, b1): `<persName>` in letter
  bodies carries a `key` attribute with a normalized name ("Fenger,
  Johannes Ferdinand") — the foundation for the person index. The `<name>`
  elements inside `correspDesc` have **no** key/ref, only raw strings
  ("SK", "Kierkegaard, P.C.") — mapping those onto persName keys needs a
  small curated alias table. There is no `<listPerson>` in the header.
- Letter-internal structure (b1 counts): opener 39, closer 39, salute 38,
  signed 37, dateline 22, head 56, p 235, pb 171, hi 98, lb 13, note 1.
- **Parser (slice 2, done):** `pipeline/parse_tei.py`. Its module docstring
  IS the contract documentation — read it before consuming parser output.
  `parse_volume(path) -> dict` (groups/letters/warnings); `plain_text()` is
  the seam for the future search index. Tests: `python3 -m unittest` from
  the repo root, against the real vendored b1.
- More verified b1 quirks (2026-07-27): partial dates are **zero-padded**
  (`18370000` = 1837, `18481200` = Dec 1848 — never slice naively); 16/42
  letters lack day precision, 11 dates carry `notAfter` ranges, 23 are
  editorial/postmark-derived (`@source`). Letter headings live in `@n` of
  *empty* `<head type="letterHeader">` elements; letter 39's is broken in
  the source ("· til familien") — displays should fall back to correspDesc.
  The text-critical apparatus is inline in txt.xml (`app`/`lem`/`rdg`,
  `choice`/`abbr`/`expan`, `witDetail`) — the parser keeps variants out of
  the reading flow. Two pagination series: `pb` for manuscript leaves and
  for SKS print pages (`@edRef`), a few with `@facs` → `ill_*.jpg`. 759
  `<ref type="commentary">` targets point into `kom.xml` (not vendored
  yet). Senders are not all SK (35/42; also Else, M.P., H.P., M.A.
  Kierkegaard). No place data in `correspAction` — places only occur in
  datelines inside letter text. b1 as JSON ≈ 494 KB, so the site build
  must split output per letter rather than ship volume blobs.
- **Display layer (slice 3, done):** `build.py` → `sitegen/` (escaping,
  dates, TEI-tree renderer, pages, site assembly; templates are plain
  Python string functions). Display tests alongside the parser tests —
  `python3 -m unittest` runs all. The renderer never drops text
  silently: unmodelled elements keep their text and are warned about at
  build time (currently `milestone`, `ptr`, `formula` — deliberate).
- **Full corpus (slice 5 part 1, done):** 336 letters, 14 volumes, 85
  correspondence groups (`pipeline/corpus.py`). Numbering: whole numbers
  1–318 gapless and collision-free plus 15 sub-numbers (159.1–159.9,
  280.1, 304.1–.5); b171 has three `@n="-"` cross-reference stubs →
  slug URLs (`/brev/b171-n171a/`) and an honest "no letter text here"
  notice. `correspContext` ids repeat across volumes — anchors are
  volume-prefixed. **ded is excluded** (no correspDesc/letter model,
  book-based grouping, numbering collides with letters 1–119 — see
  corpus.py docstring). One permanent parser warning: b43 letter 50 has
  malformed `notAfter="1847000"` (7 digits), kept raw, iso=None. Known
  gap: that unreadable upper bound is not yet surfaced to the reader
  (dates.py follow-up).
- **Timeline (slice 6, done):** `/tidslinje/` — vertical rail 1813–55,
  no JS, generated by `sitegen/timeline.py` from `pipeline/context.py`
  (loads `data/context/publications.json` + `residences.json`; build
  without them still yields a complete site — the editorial layer is
  disposable). Time never compressed; imprecision gets five distinct
  honest treatments; pseudonym/signed distinguished by shape+side+words.
  Known trade-offs: letter marks are 10×11px (below WCAG 2.5.8's 24px
  target — mitigated by keyboard nav, aria-labels and the index as
  full-size alternative); publication labels drift within the five
  stretched years (leader lines carry the truth); `format_date` still
  hides b43/50's unreadable notAfter on the letter page (surfaced on
  the timeline only — one-line fix pending).
- **Persons, summaries, search (slice 7, done):** 637 pages — 336 letters,
  298 person pages, `/personer/`, `/tidslinje/` and the index.
  - `sitegen/persons.py`: the register. Built from `persName/@key` in the
    letter bodies (298 distinct keys; one `key=""` in b127/148 is skipped),
    **not** from the curated files — a person with no biography still gets a
    page. Slugs are derived (`æøå` → `ae/oe/aa`, then NFKD), collision-checked
    and numbered deterministically; the corpus currently produces zero
    collisions. Register sorted with æ/ø/å after z.
  - `data/context/aliases.json`: **curated join table**, the only bridge
    between `correspDesc`'s name strings and persName keys (the TEI joins
    them nowhere). 84 distinct correspondent forms → 71 mapped (18 exact,
    46 surname+initials expansion, 7 hand-curated incl. 3 that name two
    people), 13 deliberately unmapped with reasons. Unmapped letters appear
    on nobody's sent/received list; that is the intended outcome. Key trap
    found: "Agerskov, Chr." is *not* the body's "Agerskov, Niels" (kom.xml
    says Christian Wilhelm Hass Agerskov). The commentary's key space is not
    quite the body's — 4 known disagreements, e.g. body
    `Müller, Frederik Paludan` vs kom `Paludan-Müller, Frederik`.
  - Bios join on the persName key: 138 of 298 people have one; 152 have no
    commentary note at all and 8 are in `bios.json`'s `withoutBio`. The page
    tells the two silences apart. `withoutBio` reasons are mostly English and
    are therefore **not rendered** — a known dataset defect.
  - Summaries (`data/context/summaries.json`, 333 of 336) join on
    `volume/xml:id` and appear **only in the index**, never on a letter page
    (Maria's decision). Marked as the presenter's voice by a gilt frame-line
    plus body italic — the design's editorial register, at 333 repetitions.
  - persName links are styled to disappear while reading: `a.tei-persName`
    takes `color: inherit` and no underline at rest, keeping only the entity
    hairline the design already had; hover/focus adds the underline. Brev 1
    carries 30 of them and still reads as prose.
  - `sitegen/search.py` + `static/search.js`: three build-time facets
    (sender, recipient, year — imprecise dates filed under their earliest
    possible year, with the rule written next to the control) and an inverted
    free-text index over `plain_text()` + summaries. 13 070 words, 380 KB,
    shipped as `assets/search-index.js` (a script, not JSON: `fetch` is
    refused on `file://`) and **lazy-loaded on first search**. Folding
    (`æ→ae`, `ø→oe`, `å→aa`, NFKD) is duplicated in Python and JS and a test
    guards the pair. Progressive enhancement: the controls are in the markup
    with `hidden`; the script removes it. `[hidden] { display: none
    !important; }` is load-bearing — `.letter-entry` is a grid and an author
    `display` beats the UA's `[hidden]` rule.
- **Presenter, intro and Om page (slice 8, done):** 638 pages — the Om page
  (`/om/`) joins the site and is in the nav everywhere, unconditionally: it
  is what makes the demonstration honest, so no dataset may switch it off.
  - `sitegen/pages.py`: `_presentation()` is the front page's welcome in
    Maria Notabene's voice, placed *after* the factual lead on purpose — the
    demonstration says what it is before an invented person says anything.
    Every concrete thing in it is in a letter (b1/1 snuff box, b1/10 eighty
    rigsdaler, b1/39 grave plot, quoted in the edition's spelling). It
    mentions the timeline only when the build wrote one.
  - `about_page()` states: what the site is, the architecture note as prose,
    the source + CC0 + pinned commit, MIT for the code, `tekster.kb.dk/sks`,
    the Maria Notabene disclosure (fiction, AI, adversarial verification) and
    where the person bios come from.
  - `pipeline/provenance.py`: reads `data/vendor/PROVENANCE.md` so the commit
    on the Om page cannot drift from the record beside the files. No record →
    the page names the repository and claims no pin. `build_site` gained a
    `provenance=` keyword; it reaches exactly one page.
  - **External links:** the site points off-site in exactly three places —
    the CC0 deed in every footer, and the upstream repo + `tekster.kb.dk` on
    the Om page. `tests/test_sitegen.assert_self_contained` enforces that,
    with the Om page as the single named exception.
  - CSS: `.presentation` (paper ground, gilt top rule, display-face
    signature — not italic; 333 two-line resumés can be, a hundred words
    cannot) and `.prose` for the Om page. Contrast pairs documented in place.
- **Commentary parser (done):** `pipeline/parse_kom.py` — docstring is
  the contract. Key facts: 4376 notes corpus-wide, uniformly
  `<label>` (lemma) + `<p>` (prose); `@n="*"` on a persName marks the
  note's *biographical subject* (290 notes, 218 persons — the bio
  pipeline's primary grounding); 1096 distinct persName keys, 284 in
  >1 volume; `@sameAs` is an alias *string* (55 corpus-wide — merge
  candidates: married/maiden names, "Jette"); two `persName key=""`
  exist (b241, b43); 1864 notes cross-reference other notes; refs to
  other volumes use *uppercase* dirs (`../B1/txt.xml`) and 18 point at
  non-vendored journal volumes (would dangle as links). Bio prose uses
  dense abbreviations (`da.`, `ty.`, `prof.`, `ktl.` = SK's auction
  catalogue) worth expanding for display.
- **Design (slice 4, done): "Eckersberg"** — Maria's pick from three
  mockup directions (see `design/varianter/`, uncommitted). Museum
  formidling: plaster ground, Prussian header band, sea-green metadata
  card, gilt as frame-lines only (never text), pb markers as two-tone
  gallery chips, a visual system for editorial marks. All contrast
  pairs are measured and documented in `sitegen/static/site.css` — do
  not tweak palette values casually. Fonts: Playfair Display (display)
  + Spectral (body) self-hosted as woff2 in `sitegen/static/fonts/`
  with OFL licences (66 KB total, latin subset — ɔ/Ψ/ℳ fall back to
  system serif, accepted). Dark mode deliberately not implemented yet
  (sketch preserved as CSS comment; slice 8 owns it).
- Source-fidelity gaps found in slice 3 (all upstream, all left as-is per
  the preserve-uncertainty principle): `correspDesc` under-reports
  co-signers (letters 3, 29–32 have "og SK"-style headings but single
  `<name>` per action); the source sometimes omits whitespace between
  adjacent elements ("Cand:Theol:", "frcoHamburg"); letter 1 has a
  one-off encoding slip — "Hel&lt;pb/&gt;sing\ør," duplicated next to
  `<placeName>Helsingør</placeName>` (the file's only backslash). The
  normal convention is `<placeName key="normalized">as-written</placeName>`
  (same for persName). Letter 39's missing display-string half lives in a
  correspAction `<note>` ("· udateret [1846-47]") — shown as "Note i
  kilden".
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

## Decisions (settled with Maria, 2026-07-27)

- **Hosting:** Netlify (`netlify.toml`: `python3 build.py` → `dist/`), but
  build output stays host-agnostic (relative paths, no host-specific magic).
- **License:** MIT for code (LICENSE committed); vendored TEI stays CC0
  with provenance note in `data/vendor/PROVENANCE.md`, pinned to upstream
  commit `27a6b110c24e97b381e010595b50f3ca3d4ca8c9`.
- **Repo:** goal is a public GitHub repo. No personal information in
  commits beyond Maria's name — repo-local git email is
  `mariacodes@salonen.dk` (her public GitHub address).
- **Stack:** Python 3 stdlib only for parser + site generator
  (ElementTree, unittest); hand-written HTML/CSS + vanilla JS front-end;
  prebuilt JSON search index; self-hosted OFL serif (Didot/Walbaum
  direction — evoke the era, no fraktur body text).
- **Workflow (demo-light):** atomic commits directly to main (Maria's
  standing go for this project), no issue/PR machinery. Tests are required
  where the thesis lives — the parser — and against the real vendored TEI.
- **Design principle — preserve uncertainty (Maria, 2026-07-27):**
  presenting historical sources is largely about *keeping* their
  uncertainty. The UI shows what the edition actually knows and how it
  knows it: precision-honest dates ("december 1848", "1837", "1846–47"),
  editorial provenance visible ("dateret efter poststempel",
  "redaktionelt dateret"), source defects surfaced rather than patched
  (letter 39). Uncertainty is historical information, never a rendering
  problem to hide. All display slices inherit this.
- **Presentation:** timeline as its own narrative page (publications +
  residences from a hand-curated, source-cited `data/context/` dataset —
  editorial layer, clearly separate from TEI truth); person index; front
  page intro and the 333 index summaries by **Maria Notabene**, a fictional
  presenter in SK's own pseudonym tradition (own personality, light loving
  irony), honestly disclosed on the Om page along with AI assistance. Her
  voice bible is `docs/notabene.md` — Danish on purpose, §5 is the few-shot
  material the summaries were written from; §§2–5 are approved canon.
  **Renamed from Victoria Eremita 2026-07-28, Maria's call:** the new name
  plays on Nicolaus Notabene of *Forord* (1844), who was only allowed to
  write prefaces because his wife held book-writing to be marital
  infidelity — now the wife takes the pen and still writes only prefaces
  (the 333 summaries and the front-page intro *are* the prefaces; the
  letters are the book). It also openly carries the site builder's own first
  name, which is the Kierkegaardian joke: transparent pseudonymity, where
  all of Copenhagen knew who the publisher was.

---

*Handoff written by Claude Fable 5, July 2026. Kept up to date as the
project evolves — correct it when reality disagrees with it.*
