# epistel

Demonstrationsvisning af en TEI-kodet brevsamling: Søren Kierkegaards breve
fra *Søren Kierkegaards Skrifter* (kilde: [kb-dk/SKS_tei](https://github.com/kb-dk/SKS_tei),
CC0).

Pointen med demonstrationen: bevaringsværdien bor i standardformatet (TEI,
offentligt tilgængeligt) — visningen ovenpå er et tyndt, statisk og
udskifteligt lag. Poleret formidling uden server, database eller
driftsmiljø.

**Status: demoen er hel.** 638 statiske sider — 336 breve med
transskription og tekstkritiske markeringer, 298 personsider, indeks med
søgning, tidslinje — bygget deterministisk med `python3 build.py`
(Python 3-stdlib, ingen afhængigheder) og serveret som ren statik.
Byggebriefen ligger i `CLAUDE.md`.

**Samlingen udgives også som data.** `python3 export.py` bygger
`export/` (committet i repoet): typede JSON-konvolutter og semantiske
HTML-transskriptioner for alle 336 breve, udgavens 40 illustrationer med
et manifest over hver eneste henvisning til dem, de redaktionelle datasæt
verbatim, JSON-skemaer og proveniens med sha256-kæde tilbage til kilden.
Formatet er beskrevet i [`docs/export-format.md`](docs/export-format.md);
versionerede udgivelser med tarball ligger under
[releases](https://github.com/mariabitsch/epistel/releases).

**Licenser — én pr. lag:** kildekoden er MIT ([`LICENSE`](LICENSE)) ·
TEI-kopien er CC0 som kilden ([`data/vendor/PROVENANCE.md`](data/vendor/PROVENANCE.md)) ·
de redaktionelle tekster (resuméer, biografier og kuraterede datasæt i
`data/context/` og i eksportens `context/`-lag) er
[CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/)
([`data/context/LICENSE`](data/context/LICENSE)). GitHubs licens-badge
viser kun rodens MIT; dette afsnit og eksportens manifest er de
autoritative kort.

---

*Bygget med AI-assistance (Claude).*
