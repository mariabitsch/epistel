# The JSON export format

`export/` is the corpus offered as data: the same letters this repository
renders as a website, in a form any other display can consume. It is written
by `python3 export.py`, deterministic (same input, byte-identical output),
and committed, so every change to it is a reviewable diff. The format's
motto: **TEI semantics, web ergonomics** — the edition's own concepts and
names, in files a web stack (or a browser, or a person) can open directly.

This document is the contract. The test suite holds the export to it:
`tests/test_export.py` (envelopes, manifest, determinism, drift) and
`tests/test_export_body.py` (the body vocabulary below, including the rule
that every class used must be named in this file).

## Layout

```
export/
  manifest.json                 schemaVersion, provenance, license per layer
  volumes.json                  volume titles, groups, document order, warnings
  images.json                   every illustration file and its references
  schema/*.schema.json          JSON Schemas (draft-07) for the above
  letters/<volume>/<xmlId>.json one envelope per letter (metadata)
  letters/<volume>/<xmlId>.html the letter's transcription (see Vocabulary)
  letters/<volume>/ill_*.jpg    the source's illustrations (see Images)
  letters/vignet/*.jpg          shared vignettes two letters reference
```

Each volume in `volumes.json` carries a `source` object naming its TEI
files by basename — `txt.xml` (the letters) and `kom.xml` (the edition's
commentary, which this export does not otherwise use) — each with the
upstream repository path and the sha256 the provenance record vouches for.
With the manifest's pinned commit, that is a stable, checkable address for
the exact bytes (e.g. `https://raw.githubusercontent.com/<repository>/
<commit>/<path>`); no folder needs listing to learn what exists. Without a
provenance record, `source` is honestly `null`.

Letters are filed by volume directory plus TEI `xml:id` — the only
identifier every letter has (three b171 stubs carry no letter number). The
edition's public letter number travels inside the envelope as `number`,
`"-"` included. Reading order is recorded in `volumes.json`; the files on
disk carry no order of their own.

## Guarantees

* **Nothing is repaired.** Whatever the edition encodes is what comes out:
  the malformed date in b43 travels raw, letter 39's broken heading stays
  broken, uncertainty is data (see Dates).
* **Nothing is lost, nothing is added.** The visible text of every body
  fragment is exactly the reading text of the parsed TEI; apparatus that is
  not part of the reading text is present in the markup with `hidden`.
* **The vendor layer stands alone.** Envelopes and bodies derive from the
  CC0 TEI only — no editorial joins mixed in. Curated datasets arrive as
  separate collections, each with its own `_meta` and license, and each one
  is disposable on its own.
* **Deterministic, offline, no timestamps.** Provenance is the pinned
  upstream commit recorded in the manifest, not a build date.

## The manifest

```json
{
  "schemaVersion": "0.2.0",
  "language": "da",
  "source": {"repository": "...", "commit": "..."},
  "layers": {
    "letters": {"path": "letters/", "count": 336, "license": "CC0-1.0"},
    "volumes": {"path": "volumes.json", "count": 14, "license": "CC0-1.0"},
    "images": {"path": "images.json", "count": 40, "license": "CC0-1.0"}
  },
  "schemas": {
    "images": "schema/images.schema.json",
    "letter": "schema/letter.schema.json",
    "manifest": "schema/manifest.schema.json",
    "volumes": "schema/volumes.schema.json"
  }
}
```

A layer's `path` is its entry point: the directory the letters live in, or
the file that describes the layer. The image *files* sit beside the
letters; `images.json` is where each one says so.

The schemas (JSON Schema **draft-07** — the draft the validation ecosystem
supports universally) formally describe the manifest, the volume index, the
image manifest and the letter envelope, with `additionalProperties: false`
throughout: a field
this document does not know cannot validate. The prose vocabulary table
below remains the contract for the HTML *bodies*, which JSON Schema cannot
describe. Validation is optional by design — the repository stays
dependency-free; the test suite validates the committed export against the
schemas when the pure-Python `fastjsonschema` package is available and
skips visibly when it is not.

`schemaVersion` is what a release tag promises; it changes when the shape of
the export does. Licenses are SPDX identifiers, one per layer, because the
layers have different authors: the TEI-derived layers inherit the edition's
CC0.

## Envelopes

One JSON object per letter: `volume`, `xmlId`, `number`, `heading` (the
edition's own, `null` where the source lost it), `sender` and `recipient`
(raw name strings as the edition wrote them, no resolution), `context` (the
correspondence group), `body` (the sidecar fragment's filename).

### Dates

Dates keep the source string and add a derived reading, never a guess:

```json
{"raw": "18481200", "iso": "1848-12", "precision": "month",
 "year": 1848, "month": 12, "day": null,
 "notBefore": null, "notAfter": null, "source": "supplied", "text": null}
```

The edition zero-pads what it does not know (`18370000` = the year 1837);
`precision` says how much of the date is real. A date the source wrote
unreadably keeps its `raw` value with `iso: null`. A missing date is `null`.

## The body vocabulary

A body file is an HTML *fragment* (no doctype, no head): open it in a
browser and it reads as the letter reads. The rules:

* **HTML elements where HTML has the concept**, a neutral `span`/`div`
  everywhere else.
* **TEI names carry the semantics**: every element wears
  `class="tei-<element>"` — the TEI element's own name, honouring its TEI
  meaning — and its TEI attributes as `data-*` attributes (lower-cased:
  `@edRef` → `data-edref`), values verbatim. TEI's `@type` is `data-type`.
* **Apparatus is present but `hidden`**: rejected readings, editorial
  expansions and witness remarks are in the markup with HTML's `hidden`
  attribute, so a bare browser shows the reading text while a consumer has
  everything. Un-hide them and the apparatus is on screen.
* No scripts, no styles, no links, no external references of any kind.

The vocabulary is **closed**: only what is listed here may appear, and the
conformance test fails on anything else, so growth is deliberate. A new
element would be added to this table, the test, and the renderer together.

| Markup | TEI | Meaning |
|---|---|---|
| `<div class="tei-div">` | div | a division of the letter (`data-type`: mainText, ...) |
| `<p class="tei-p">` | p | paragraph |
| `<p class="tei-head">` | head | a heading in the body (`figcaption` inside figures) |
| `<div class="tei-opener">` / `tei-closer` | opener/closer | a letter's opening/closing block |
| `<div class="tei-salute">` / `tei-signed` / `tei-dateline` / `tei-postscript` / `tei-trailer` | salute … | greeting, signature, dateline, postscript, trailer |
| `<div class="tei-lg">`, `<span class="tei-l">` | lg/l | verse: line group and line |
| `<br>` | lb | line break in the source |
| `<table class="tei-table">`, `tr.tei-row`, `td.tei-cell` | table/row/cell | layout tables (envelope addresses); `colspan`/`rowspan` are real |
| `<aside class="tei-note">` | note | the letter-writer's own footnote (`data-anchored="false"`: the edition found no marker for it) |
| `<figure class="tei-figure">` | figure | an illustration in the letter; caption as `figcaption` |
| `<span class="tei-figDesc">` | figDesc | description of an illustration |
| `<span class="tei-graphic" data-url>` | graphic | the illustration file the edition references (not shipped here) |
| `<i>`/`<sup>`/`<span>` `class="tei-hi"` | hi | source emphasis; `#ita`/`#sup` renditions map to HTML typography, the raw value stays in `data-rendition` |
| `<span class="tei-seg">` | seg | a typed span of text |
| `<span class="tei-persName" data-key>` | persName | a person, with the edition's normalized register key |
| `<span class="tei-placeName" data-key>` / `tei-name` / `tei-rs` | placeName/name/rs | places, other names, referring strings |
| `<span class="tei-ref" data-target>` / `tei-ptr` | ref/ptr | references (`data-type="commentary"`: into the edition's commentary volumes) |
| `<span class="tei-date" data-when>` | date | a date in the text |
| `<span class="tei-formula" data-notation>` | formula | a number the edition sets as a formula (dates written as fractions) |
| `<span class="tei-supplied">` | supplied | text supplied by the editors |
| `<span class="tei-unclear">` | unclear | uncertain reading (`data-reason`, `data-cert`) |
| `<span class="tei-corr">` / `tei-sic` | corr/sic | editorial correction / the source as it stands |
| `<span class="tei-add">` / `tei-del` | add/del | added / deleted in the source |
| `<span class="tei-choice">` | choice | abbreviation as written (`tei-abbr`) + the editors' expansion (`tei-expan`, hidden) |
| `<span class="tei-app">` | app | text-critical apparatus: the established reading (`tei-lem`) + rejected readings (`tei-rdg`, `tei-rdgGrp`, hidden) |
| `<span class="tei-witDetail" hidden>` | witDetail | the editors' remark about the manuscript ("ms. beskadiget") |
| `<span class="tei-witStart">` / `tei-witEnd` | witStart/witEnd | where a witness's coverage begins/ends |
| `<span class="tei-pb">` | pb | page/leaf boundary: `data-n` the number, `data-edref` present = the printed SKS pagination, absent = the manuscript's leaves, `data-facs` a facsimile reference |
| `<span class="tei-milestone">` | milestone | a boundary in another edition's numbering (`data-edref`, `data-unit`) |

## Images

The upstream repository holds no full-page scans of the letters; what it
holds — and what this export carries, completely — is the source's **40
illustrations** (`ill_*.jpg` in the letter volumes, plus two shared
`vignet/` files): drawings in the letters, seals, commentary portraits.
Several are tagged as manuscript facsimiles via `pb/@facs` in the TEI.
Each file is recorded in the provenance table (upstream path + sha256)
like every other vendored file, inherits the edition's CC0, and is copied
under `letters/<its directory>/` — **beside the fragments, so the TEI's
own relative references** (`data-facs="../b1/ill_1.jpg"`,
`data-url="../vignet/vig-brev-blomst.jpg"`) **resolve exactly as
written**. `ill_k*` files are referenced from the edition's commentary
(not part of this export's fragments) and still travel as volume
material.

### The image manifest

`images.json` is the same 40 files as *data*, so a consumer never has to
open an XML file to know what an image is:

```json
{
  "id": "b1/ill_1.jpg",
  "path": "letters/b1/ill_1.jpg",
  "source": {"path": "data/v1.9/b1/ill_1.jpg", "sha256": "5bf8f7bb…"},
  "figures": [
    {"volume": "b1", "file": "txt.xml", "xmlId": "ill_1",
     "type": null, "rend": "verso", "url": "../b1/ill_1.jpg",
     "head": ["1. Brev 2, bl. [2v], udskrift"], "figDesc": null,
     "letter": "2", "letterXmlId": "n2"}
  ],
  "pageBreaks": [
    {"volume": "b1", "file": "txt.xml", "xmlId": "id767b1df6…",
     "n": "2v", "rend": "supplied", "edRef": null,
     "facs": "../b1/ill_1.jpg", "letter": "2", "letterXmlId": "n2"}
  ]
}
```

`id` is the file's vendor-relative path and the **join key**: a captions
dataset, or any other editorial layer about the images, keys off it.
`path` says where the file sits in this export; `source` is the provenance
record's row for it, so the bytes stay checkable against the pinned commit.

The edition points at an image in exactly two ways, and each gets its own
list, in reading order:

* **`figures`** — a plate the edition prints (`<figure>`), with its `type`
  (only the two shared vignettes carry one: `vignet`), its `rend`
  (`recto`/`verso`/`opening`), the `<graphic>` url **as written**, and its
  `<head>` caption lines complete (a second line usually holds the photo
  credit). `figDesc` is the figure's description, `null` where the edition
  writes none or leaves it empty — which is the case for both vignettes.
* **`pageBreaks`** — a `<pb facs="…">`, i.e. this file reproduces that
  manuscript leaf; `n` is the leaf in the manuscript's own numbering.

`letter` and `letterXmlId` name the letter a reference sits in and join
straight to `letters/<volume>/<xmlId>.json`; they are `null` where it sits
in no letter (the commentary volumes gather their plates in a division of
their own; `ded` numbers dedications, not letters). Both lists may be
empty: `b241/ill_k10.jpg` and `b79/ill_k4.jpg` are vendored but referenced
nowhere in the vendored TEI, and several files are referenced only from a
page break. Everything in this file is the vendor layer — the edition's own
words or the provenance record's; nothing was written for it here.

`unshippedReferences` is the honest remainder: image references in the TEI
that this export ships no file for, listed rather than dropped. Eight of
them, from two causes the file deliberately does not label, because a third
cause would go unnoticed if it did: `ded`'s own plates are not vendored
(`ded` is outside the corpus), and one reference is dangling upstream.

### Source quirks, preserved rather than repaired

* Two `graphic` urls write their volume directory in uppercase
  (`../B120/ill_31.jpg`). The files are exported under the lowercase
  directory the repository actually uses, and the manifest's `id` names
  that file while `url` keeps the uppercase; resolve image references
  case-insensitively (or lowercase the directory component) and both
  resolve.
* One reference is dangling at its written path: b241's letter 249 has
  `facs="../b241/ill_k15.jpg"`, and the source repository holds no such
  file — it exists as `ded/ill_k15.jpg`, referenced correctly from the
  dedications' commentary. The reference travels verbatim, and appears in
  `unshippedReferences`; the export does not guess on the source's behalf.
  The test suite pins this as the only dangling reference.
* `b79/ill_24.jpg` and `b308/ill_24.jpg` are two copies of one plate,
  filed in two volumes. They stay two entries with two ids; the export
  merges nothing.

## The editorial layers

`export/context/` holds the curated datasets, copied **byte for byte** from
`data/context/` — their `_meta` blocks state what each file is, where it
came from and how it was verified, and that record is part of the product.
Six files, each declared in the manifest with its entry count and each
disposable on its own: `publications` and `residences` (the timeline's
hand-curated data), `summaries` (Maria Notabene's letter summaries),
`bios` (person biographies drawn from the edition's commentary),
`bio_keys` and `aliases` (the two curated join tables; see each file's
`_meta` for the join keys). An export without any of them — or without the
whole directory — is a smaller but complete export.

**License**: unlike the TEI-derived layers, this layer has an author, and
it is licensed [CC BY-NC-SA
4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/) — reuse with
attribution, non-commercially, under the same license. The manifest
declares it per layer (`"license": "CC-BY-NC-SA-4.0"`). Do not assume CC0
here; only the TEI-derived layers carry that.

## Versioning and consumption

The export is consumed by pinning: clone at a commit, or fetch a tagged
release. `schemaVersion` in the manifest is the compatibility promise. To
regenerate from source: clone this repository and run `python3 export.py` —
standard library Python only, no network, ~1 second.
