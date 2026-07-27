# Vendored webfonts

Two OFL families, self-hosted. The built site must fetch nothing at runtime
(build brief, rule 2), so the woff2 files and their licences are copied
verbatim into `dist/assets/fonts/` by `sitegen.site._copy_static` — this
README is a developer note and stays here — and are referenced from
`site.css` with relative `url(fonts/…)` paths, which resolve the same way
from `/` and from `/brev/<n>/`, because a stylesheet's URLs are relative to
the stylesheet.

Fetched **2026-07-27**. Nothing here is edited; to refresh a file, re-fetch it
from the URL below and update the checksum.

## Playfair Display — the display face

Didone; stands in for Didot / Bodoni 72 in the design's font stack.
Version 40 (`v40` in the URL), subset `latin`.

| file | style | weight | bytes |
| --- | --- | --- | --- |
| `playfair-display-latin-400-normal.woff2` | normal | 400 | 21 880 |

- Requested via the Google Fonts CSS API (a browser `User-Agent` is required
  to be served woff2):
  `https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400&display=swap`
- Font file:
  `https://fonts.gstatic.com/s/playfairdisplay/v40/nuFvD-vYSZviVYUb_rj3ij__anPXJzDwcbmjWBN2PKdFvXDXbtPK-F2qC0s.woff2`
- Licence: SIL Open Font License 1.1 — `OFL-PlayfairDisplay.txt`, from
  `https://raw.githubusercontent.com/google/fonts/main/ofl/playfairdisplay/OFL.txt`

## Spectral — the reading face

Warm transitional with a generous x-height; stands in for Palatino / Hoefler
Text. Version 15 (`v15`), subset `latin`.

| file | style | weight | bytes |
| --- | --- | --- | --- |
| `spectral-latin-400-normal.woff2` | normal | 400 | 14 028 |
| `spectral-latin-400-italic.woff2` | italic | 400 | 14 988 |
| `spectral-latin-600-normal.woff2` | normal | 600 | 15 164 |

- Requested via:
  `https://fonts.googleapis.com/css2?family=Spectral:ital,wght@0,400;0,600;1,400&display=swap`
- Font files:
  - `https://fonts.gstatic.com/s/spectral/v15/rnCr-xNNww_2s0amA9M5knjsS_ul.woff2` (400)
  - `https://fonts.gstatic.com/s/spectral/v15/rnCt-xNNww_2s0amA9M8onrmTNmnUHo.woff2` (400 italic)
  - `https://fonts.gstatic.com/s/spectral/v15/rnCs-xNNww_2s0amA9vmtm3BafaPWnII.woff2` (600)
- Licence: SIL Open Font License 1.1 — `OFL-Spectral.txt`, from
  `https://raw.githubusercontent.com/google/fonts/main/ofl/spectral/OFL.txt`

## Why exactly these four faces

`site.css` was audited for what it asks for, and nothing more is vendored:

- **Playfair 400** — every rule that sets `--display` also sets
  `font-weight: 400` (site title, `h1`, group and section headings, index
  entry headings, salutation, signature, dateline, `.r-lat`). The display
  face is never asked for in italic or bold.
- **Spectral 400** — body text.
- **Spectral 400 italic** — group notes, date provenance, `<i>` in the lead
  and footer, and `<em>` (the source's own `hi rendition="#ita"`).
- **Spectral 600** — `.lead strong` and the current entry in a
  correspondence list. Both are upright; there is no bold italic on the site.

The label micro-type (`--label`: small caps-ish sans for `dt`, page-break
chips, nav buttons) deliberately stays on the reader's system sans. The
design mockup listed Public Sans as optional there; at the sizes it is used,
a third webfont would cost more bytes than it would add.

Total payload: **66 060 bytes** of woff2. Per page a browser fetches at most
these four files, and only the faces a page actually uses.

## Coverage

The `latin` subset covers Danish (æ ø å Æ Ø Å) and all punctuation in the
corpus. Exactly three characters in b1 fall outside it — `ɔ` (U+0254), `Ψ`
(U+03A8) and `ℳ` (U+2133), eight occurrences, all in one letter. They are
drawn by the reader's fallback serif. Adding whole `latin-ext` and `greek`
subsets for eight glyphs is not a trade the reader benefits from; the
`unicode-range` declarations in `site.css` make the boundary explicit.

The arrows in the navigation (`←`, `→`) are also outside the subset, but they
are set in the label font, which is the system sans — no webfont involved.

## Checksums (SHA-256)

```
57edb864a5b79ea8143aa35b89212f99ef63d150052bb6dbb912827e67fa61ba  playfair-display-latin-400-normal.woff2
bcb83e9c56d40c5111a2bdbc3d8bdabf66bd31337e968f1c223b61879b8d3cad  spectral-latin-400-normal.woff2
7cfafd3583aecfe216f860d7a1c5689e86f7f92681946ca582d042c1c96b37d7  spectral-latin-400-italic.woff2
1fb6ca29fc243e8bfdfce12d8d6806f322bcc62d38036986812be28fb1f41f0a  spectral-latin-600-normal.woff2
566be814f8e96e93dfa16101331557eb6b5467e9e03f627c0910fe93ca12300e  OFL-PlayfairDisplay.txt
501d6ceca8e552630fe3aa9442b9a818565680a1a2f79f3fb8c13d6f309a9e98  OFL-Spectral.txt
```
