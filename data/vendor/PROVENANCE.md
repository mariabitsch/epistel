# Provenance of vendored TEI files

The files under `data/vendor/` are unmodified copies from the public TEI
source of *Søren Kierkegaards Skrifter* (SKS). They are read-only truth for
this project: never edit them; all processing happens in the build step.

- **Upstream repository:** https://github.com/kb-dk/SKS_tei
- **License:** CC0-1.0 (public domain dedication) —
  https://creativecommons.org/publicdomain/zero/1.0/
- **Pinned upstream commit:** `27a6b110c24e97b381e010595b50f3ca3d4ca8c9`
  (committed upstream 2023-03-09)
- **Fetched:** 2026-07-27

## Files

| Local path | Upstream path | SHA-256 |
|---|---|---|
| `b1/txt.xml` | `data/v1.9/b1/txt.xml` | `28b8cb1234f972e288459b1e76fab66f996edf9a322bf220d3a151a77a4703a5` |

Fetch pattern (pinned to the commit above, never `master`):

```
https://raw.githubusercontent.com/kb-dk/SKS_tei/27a6b110c24e97b381e010595b50f3ca3d4ca8c9/data/v1.9/<path>
```

When vendoring additional volumes, extend the table above.
