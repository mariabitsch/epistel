# Provenance of vendored TEI files

The files under `data/vendor/` are unmodified copies from the public TEI
source of *Søren Kierkegaards Skrifter* (SKS). They are read-only truth for
this project: never edit them; all processing happens in the build step.

- **Upstream repository:** https://github.com/kb-dk/SKS_tei
- **License:** CC0-1.0 (public domain dedication) —
  https://creativecommons.org/publicdomain/zero/1.0/
- **Pinned upstream commit:** `27a6b110c24e97b381e010595b50f3ca3d4ca8c9`
  (committed upstream 2023-03-09)
- **Fetched:** b1/txt.xml 2026-07-27; all remaining files 2026-07-27;
  the 38 letter-volume `ill_*.jpg`/`ill_k*.jpg` illustrations and the two
  shared `vignet/` files the letters reference 2026-08-25
  (the TEI tags several of them as manuscript facsimiles via `pb/@facs`;
  `ill_k*` are referenced from the commentary files)
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
| `b1/ill_1.jpg` | `data/v1.9/b1/ill_1.jpg` | `5bf8f7bbbc9bf3520a88b49ad73991cac28c172c7ee521ee5decb6bda8cc3b49` |
| `b1/ill_2.jpg` | `data/v1.9/b1/ill_2.jpg` | `d0ae3bab1db015993090b948c925c9793e3d49c07e0bc339cc6b9366083e0930` |
| `b1/ill_3.jpg` | `data/v1.9/b1/ill_3.jpg` | `078e4b5d4d5216cbd6d88cdd35cc448091875ced380a75326d865129018e226f` |
| `b1/ill_4.jpg` | `data/v1.9/b1/ill_4.jpg` | `2ae6a961bf747cf5816f2c0701bd25319c12b33f98234ed044ae11c7e969f86f` |
| `b1/ill_k1.jpg` | `data/v1.9/b1/ill_k1.jpg` | `bca39018d18f8df2784e6cbccc12e2471093ab7d0f9f4647caf7075f5662c7e1` |
| `b1/ill_k2.jpg` | `data/v1.9/b1/ill_k2.jpg` | `7effd32d0a2e1fe490455ba676095509c96436d809d5fc038e1e8492a42027b2` |
| `b1/ill_k3.jpg` | `data/v1.9/b1/ill_k3.jpg` | `0d7042917e1c2faceb8f19f9a9be8a7193a8cb854d7aee257c532c0e6e5fa27d` |
| `b43/ill_5.jpg` | `data/v1.9/b43/ill_5.jpg` | `cdb07e6b4947bdcef4dc2b4c730e5dbf0349cbd20493e9b761c72a1afb2327dd` |
| `b43/ill_6.jpg` | `data/v1.9/b43/ill_6.jpg` | `567600921ef8f83b54923718368eabd3562dc3ce32e0b800928baab1d0a2f291` |
| `b70/ill_7.jpg` | `data/v1.9/b70/ill_7.jpg` | `38d896e935d26f401918dfa7a8814c45910f4e9516fef154ab0308e11541e9fb` |
| `b70/ill_8.jpg` | `data/v1.9/b70/ill_8.jpg` | `0f4412b20cb6eec5cda5bf73ed41a56850b876b6ce41d5a1825a919bd9c7a54a` |
| `b79/ill_10.jpg` | `data/v1.9/b79/ill_10.jpg` | `0cd239044f701ebdf771ea53ca80b6a0b635b6ba72698200f795f190cbfd24bb` |
| `b79/ill_11.jpg` | `data/v1.9/b79/ill_11.jpg` | `653d4665568ca8ab187b3c12a1c25e356f6195c84b65e88ae515d0c35ee7c55a` |
| `b79/ill_24.jpg` | `data/v1.9/b79/ill_24.jpg` | `f3999ec2861d951669f7b2738c7787a9bef4cee38fce93ac0f5c413370c07dea` |
| `b79/ill_9.jpg` | `data/v1.9/b79/ill_9.jpg` | `8f76e184c1b52739e20058ecad4e74eca1dcf805a860804a860c831844e05ca2` |
| `b79/ill_k4.jpg` | `data/v1.9/b79/ill_k4.jpg` | `b5297364812538f9620ac2783d815b9756fbf5871d3b2bb781a0f63ae646456b` |
| `b79/ill_k5.jpg` | `data/v1.9/b79/ill_k5.jpg` | `6752f81fce825de0882217dab5cf53cfa11df59179c126e88c7a8004f5aa2539` |
| `b79/ill_k6.jpg` | `data/v1.9/b79/ill_k6.jpg` | `7bcc31689c30a5e3b4c10dad26e8a7fadb2b1237eb3070903fa459d40ca44e57` |
| `b120/ill_12.jpg` | `data/v1.9/b120/ill_12.jpg` | `9f318d8d46f5c6dcb2030d02085a3681d23a0ef154a76dfe0ddd570e2d48e200` |
| `b120/ill_31.jpg` | `data/v1.9/b120/ill_31.jpg` | `30f9f44dba08cc9d8561c898f2f3f1eb2fad9a5966832774f566a4e5b276e28c` |
| `b120/ill_32.jpg` | `data/v1.9/b120/ill_32.jpg` | `e87118bc5f3f9e51f3b66d3421eb04b931bc71ea610d7a9a2a796e3831894b9e` |
| `b127/ill_13.jpg` | `data/v1.9/b127/ill_13.jpg` | `981bd8870cf44b0280d808b2557a5b10fb44ec5466a64e71b7c11af5c7da13f0` |
| `b127/ill_14.jpg` | `data/v1.9/b127/ill_14.jpg` | `00297f64539b8834a02d7772712dbc90de722298dafe433663fbf7e3a59c2ff7` |
| `b127/ill_15.jpg` | `data/v1.9/b127/ill_15.jpg` | `e7dca9b557d96d6242cf40c74f32be3b68aa3286141c33245af819d204f35718` |
| `b171/ill_16.jpg` | `data/v1.9/b171/ill_16.jpg` | `80d1aaf8e0c06a07ab8a7c32bfad33725e4c89f074243e5c01816ede099362ab` |
| `b171/ill_17.jpg` | `data/v1.9/b171/ill_17.jpg` | `2f14467312ef18cd6f4fa2608d6bdb50e2cccd023b75890df6a7f5cf6d8d3453` |
| `b171/ill_18.jpg` | `data/v1.9/b171/ill_18.jpg` | `a43fa15e168a1264c7017220b2e03b6fd3d2ef4875f29d82fc72f74c4e9ad723` |
| `b171/ill_19.jpg` | `data/v1.9/b171/ill_19.jpg` | `0565b915ee7b49af14e2560dfb5c60fdd2b8db9bca70bb1bddaa942fbf1b30ab` |
| `b171/ill_k7.jpg` | `data/v1.9/b171/ill_k7.jpg` | `7275e2d6662783d1b035dbbc33c68d06f64a43bdcbd1918562d96e0a85aa3997` |
| `b208/ill_20.jpg` | `data/v1.9/b208/ill_20.jpg` | `310e3fe7ae566dabcb3b408d9ea9b3366b5c014b7360e9e1d627ff26368abcdb` |
| `b208/ill_k8.jpg` | `data/v1.9/b208/ill_k8.jpg` | `3a19d89c6005d194e596930b7ac301b5080517c7b98338243d184b1ef524bdff` |
| `b241/ill_k10.jpg` | `data/v1.9/b241/ill_k10.jpg` | `d88f1f3f7d69b4788737c08e1809de19dd5688b19d9633b8d36967305972bad3` |
| `b241/ill_k9.jpg` | `data/v1.9/b241/ill_k9.jpg` | `10e5310d6801dd6cca7565347302eb1fe6a86725ed9eb339a41520a2031a71b2` |
| `b259/ill_21.jpg` | `data/v1.9/b259/ill_21.jpg` | `b44d9e826c7e817ebad715cc130ad45dd2e53a73fad6570b38e016477355c19e` |
| `b259/ill_k10.jpg` | `data/v1.9/b259/ill_k10.jpg` | `d88f1f3f7d69b4788737c08e1809de19dd5688b19d9633b8d36967305972bad3` |
| `b276/ill_22.jpg` | `data/v1.9/b276/ill_22.jpg` | `7d96d5649d292e734bc3de98370f771ce16a1a69674e7c077421e6bce51a8cff` |
| `b276/ill_23.jpg` | `data/v1.9/b276/ill_23.jpg` | `191927c2b90a3dc827333f0137dbb3cdbbca7cd2cdc5adcccab7d0ad9910682c` |
| `b308/ill_24.jpg` | `data/v1.9/b308/ill_24.jpg` | `f3999ec2861d951669f7b2738c7787a9bef4cee38fce93ac0f5c413370c07dea` |
| `vignet/vig-brev-blomst.jpg` | `data/v1.9/vignet/vig-brev-blomst.jpg` | `69f13c313cb60e9c3955557bed61dcb87a8c3e03c9db0cc1a911d562978f2443` |
| `vignet/vig-brev-kikkert.jpg` | `data/v1.9/vignet/vig-brev-kikkert.jpg` | `e0acce4a608a1d33521aefac053587fab573568c6649549df95cd632957846b3` |

Fetch pattern (pinned to the commit above, never `master`):

```
https://raw.githubusercontent.com/kb-dk/SKS_tei/27a6b110c24e97b381e010595b50f3ca3d4ca8c9/data/v1.9/<path>
```
