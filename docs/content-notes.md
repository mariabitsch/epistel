# Content notes

*The Om page's technical backside. The page links here; change history and
verification notes live in the repository's pull requests. The site itself
is Danish; the repository's developer documents, this one included, are
English.*

## The chain from source to page

- **Pinned commit.** Every vendored file was fetched from one specific
  commit of `kb-dk/SKS_tei`, `27a6b110c24e97b381e010595b50f3ca3d4ca8c9`
  (published upstream 2023-03-09), fetched 2026-07-27. Never from `master`.
  The fetch pattern is spelled out in
  [`data/vendor/PROVENANCE.md`](../data/vendor/PROVENANCE.md).
- **sha256 per file.** The same record lists the local path, the upstream
  path and the sha256 of each of the 30 fetched files (15 directories of
  `txt.xml` + `kom.xml`).
- **Unmodified copy.** The files under `data/vendor/` are never edited.
  Everything the display does to the text happens in the automated build,
  which reads them and never writes to them.
- **No drift between prose and record.** The commit stated here and the Om
  page's references are verified against `PROVENANCE.md` by the build — a
  claim the build cannot check against the record beside the files would be
  worse than none.
- **Deterministic and offline.** The build fetches nothing from the
  network. Same files in, same pages out, on any machine, every time. 396
  automated tests run against the real vendored files — not against
  fixtures.
- **Scope.** Of the 15 vendored directories, 14 form the corpus — one for
  each of volume 28's groups. The `ded` directory holding the dedications
  is fetched and kept in the project but excluded from the display: its TEI
  has no `correspDesc`, no sender, no recipient, and numbers from 1 again.
  An omission, not a sleight of hand.

## The source's defects, preserved

- One letter has an upper date bound no machine can read (`notAfter` given
  as `1847000`). The value is kept raw, and the letter's page says so
  openly.
- Letter 39's heading stands incomplete in the source; the page falls back
  on the correspondence metadata instead of inventing a heading.
- Three entries in the Lund family group are cross-references with no
  letter text of their own (`n="-"`); their pages say so, and their
  summaries point to the letters where SKS prints the text.
- Missing whitespace and a single duplication in the source's markup are
  reproduced as they stand. Nothing is corrected silently.
- The letter headers' raw name forms and the letter bodies' normalized
  person keys are two registers the TEI files nowhere join. Our join table
  is editorial and says so: 71 forms mapped, 13 deliberately left unmapped,
  each with a reason.

## Numbers

Numbers about *epistel* itself (638 pages, 336 letters in 14 groups, 298
person pages of which 143 with a biography, 336 summaries, 326 placed and
10 undated letters on the timeline, 38 publications, 9 residences, a build
time of about half a second) are counted by building the site, not recalled
from memory. The pinned commit is read from `data/vendor/PROVENANCE.md`;
»en lille uges tid« (about a week) is the span between the first and last
commit in `git log`. »Cirka 100 agenter« (about 100 agents) is the
transcript count: 84 subagent transcripts up to 29 July plus the closing
round's team. Both were verified again at publication.
