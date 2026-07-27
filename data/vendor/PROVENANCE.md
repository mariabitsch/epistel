# Provenance of vendored TEI files

The files under `data/vendor/` are unmodified copies from the public TEI
source of *Søren Kierkegaards Skrifter* (SKS). They are read-only truth for
this project: never edit them; all processing happens in the build step.

- **Upstream repository:** https://github.com/kb-dk/SKS_tei
- **License:** CC0-1.0 (public domain dedication) —
  https://creativecommons.org/publicdomain/zero/1.0/
- **Pinned upstream commit:** `27a6b110c24e97b381e010595b50f3ca3d4ca8c9`
  (committed upstream 2023-03-09)
- **Fetched:** b1/txt.xml 2026-07-27; all remaining files 2026-07-27
- Volumes b1–b308 hold the letters (directory name = first global letter
  number in the volume); `ded` holds the dedications. `txt.xml` is the
  text, `kom.xml` the scholarly commentary (used for person biographies).

## Files

| Local path | Upstream path | SHA-256 |
|---|---|---|
| `b1/kom.xml` | `data/v1.9/b1/kom.xml` | `68936f65fb91dfc8e03ed546b31aedc3f8c05ddda92f12b13516d94f2b9ef9be` |
| `b1/txt.xml` | `data/v1.9/b1/txt.xml` | `28b8cb1234f972e288459b1e76fab66f996edf9a322bf220d3a151a77a4703a5` |
| `b120/kom.xml` | `data/v1.9/b120/kom.xml` | `f55b64ae09ef84f76f7becb2d443a1b82fb76cfb88beadb8d14cfae56511e359` |
| `b120/txt.xml` | `data/v1.9/b120/txt.xml` | `bfa25a002e7f45e83fcb1558356a0d8cc2fab0d9ffba62f8401b39a05f4a0db5` |
| `b127/kom.xml` | `data/v1.9/b127/kom.xml` | `8447e31801674231b820d493797df40348ce7a70f5cbe06034d9c78d9c6ceb55` |
| `b127/txt.xml` | `data/v1.9/b127/txt.xml` | `af2c84d84a11a95f3727c436ad88bab902dc8a38a581d7e28725d9486412b5da` |
| `b161/kom.xml` | `data/v1.9/b161/kom.xml` | `6a0d313e6f89973115327ec037513fe128a990a54b254b99ea6681bbe634ee18` |
| `b161/txt.xml` | `data/v1.9/b161/txt.xml` | `d7542dc81457214009f3bd616e18b5af34d823b95397dc15a8fc2c1eafe75d61` |
| `b171/kom.xml` | `data/v1.9/b171/kom.xml` | `7c2d879ab2cc76a963f1f551e995da0d997b6c594c2d04609be5b336de30d9ce` |
| `b171/txt.xml` | `data/v1.9/b171/txt.xml` | `64a97b352956d3daa69082c83529f0fb75c952d4bfd4098d6b8ceb0ff39afe27` |
| `b208/kom.xml` | `data/v1.9/b208/kom.xml` | `ea4406a0ca1cf937edd297cc2e8d379b0e5c4865b76eefa105ca82c650e667bf` |
| `b208/txt.xml` | `data/v1.9/b208/txt.xml` | `c7846610a34fd9f9f20b4d5b51773226e498cf82d8aae0832910f158f33c9b18` |
| `b234/kom.xml` | `data/v1.9/b234/kom.xml` | `828eeb9c941577556081c6a28408b1a6ae81ae584bb7b93dc6ce529e57753c42` |
| `b234/txt.xml` | `data/v1.9/b234/txt.xml` | `91c4cd88574c88f8a0a4606c5f71228f0115ea9602acda2ede7b3841f304d6cf` |
| `b241/kom.xml` | `data/v1.9/b241/kom.xml` | `180997784f0bcdf15cde627b61c5254219debc4970f73640a4269d4bf6463551` |
| `b241/txt.xml` | `data/v1.9/b241/txt.xml` | `76c0fd38b1e92f6cce513a1638b50ca5c7c81e46c909c00912eb04b26326da0b` |
| `b259/kom.xml` | `data/v1.9/b259/kom.xml` | `f6401a91f902e84b1e31178cdf7c8598af4c2cc420f64b901524f4de2367d80d` |
| `b259/txt.xml` | `data/v1.9/b259/txt.xml` | `535e2d2bd34263c268c2e7f44271be57405bcbe07b41a2e22e18d8ac7e3a5b68` |
| `b276/kom.xml` | `data/v1.9/b276/kom.xml` | `a27b0954761f4f988f135fdb44371d92b25c55d4f5b10442007fec01c07c305e` |
| `b276/txt.xml` | `data/v1.9/b276/txt.xml` | `119499fd64ab148886f9944cef39c427c953b186ab986c527504d66dcdb84da4` |
| `b308/kom.xml` | `data/v1.9/b308/kom.xml` | `7e269ab0567ae3b4a50a7f18d59209c57739ad9abbbc9deead7c5b49daf69bae` |
| `b308/txt.xml` | `data/v1.9/b308/txt.xml` | `27f180e0b5894d910b2ed3bc8cd62f1d9367bc42de32d761cc291105d8c36e48` |
| `b43/kom.xml` | `data/v1.9/b43/kom.xml` | `5103c427cdbabbedef80ad0afd75ba48b4e8fcc6efe892371fae1a249aeae63d` |
| `b43/txt.xml` | `data/v1.9/b43/txt.xml` | `cbdfe1c3c27724ad0cb17da1f66cf0c4ea44972f6a68e43d4d1da5ef30e6d225` |
| `b70/kom.xml` | `data/v1.9/b70/kom.xml` | `629e56f371374464cd97dc3a2386bc91990db909fe6edac41b9a6249573172a8` |
| `b70/txt.xml` | `data/v1.9/b70/txt.xml` | `425be1201be792cc932cc1cd42f5acd001874ff3fed941f1b3a9fb92d72b8088` |
| `b79/kom.xml` | `data/v1.9/b79/kom.xml` | `cca29cf51661da99673781a7c2b17893ba6521676a92fd6362b4d3aa25e0e0b9` |
| `b79/txt.xml` | `data/v1.9/b79/txt.xml` | `f5c8b505e4d05db50c641cbd92889320269bec63fc16edfcbced257d67c2f3a8` |
| `ded/kom.xml` | `data/v1.9/ded/kom.xml` | `8a6396ffba244c9d0710ca642f472966a320c72a339b451eec867bc60635dae9` |
| `ded/txt.xml` | `data/v1.9/ded/txt.xml` | `433385a77b240e0141ee38b397e5feb00cdb8611935ebee85cc14582b17f7952` |

Fetch pattern (pinned to the commit above, never `master`):

```
https://raw.githubusercontent.com/kb-dk/SKS_tei/27a6b110c24e97b381e010595b50f3ca3d4ca8c9/data/v1.9/<path>
```
