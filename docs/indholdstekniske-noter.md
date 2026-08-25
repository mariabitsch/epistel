# Indholdstekniske noter

*Om-sidens tekniske bagside, på dansk med vilje ligesom siden selv.
Om-siden linker hertil; ændringshistorik og verifikationsnoter bor i
repoets pull requests.*

## Kæden fra kilde til side

- **Pinned commit.** Alle vendorerede filer er hentet fra ét bestemt commit i
  `kb-dk/SKS_tei`, `27a6b110c24e97b381e010595b50f3ca3d4ca8c9` (lagt op hos
  udgiveren 2023-03-09), hentet 2026-07-27. Aldrig fra `master`.
  Hentemønsteret står i klartekst i
  [`data/vendor/PROVENANCE.md`](../data/vendor/PROVENANCE.md).
- **sha256 pr. fil.** Samme fil optegner lokal sti, sti hos udgiveren og
  sha256-sum for hver af de 30 hentede filer (15 mapper à `txt.xml` +
  `kom.xml`).
- **Uændret kopi.** Filerne under `data/vendor/` rettes aldrig. Alt, hvad
  visningen gør ved teksten, sker i den automatiserede byggeproces, som læser
  dem og aldrig skriver til dem.
- **Ingen drift mellem tekst og optegnelse.** Commit-angivelsen her og
  Om-sidens henvisninger efterprøves mod `PROVENANCE.md` i byggeprocessen —
  en angivelse, bygningen ikke kan efterprøve mod optegnelsen ved siden af
  filerne, ville være værre end ingen.
- **Deterministisk og offline.** Byggeprocessen henter intet fra nettet. Samme
  filer ind giver samme sider ud, på enhver maskine, hver gang. 365
  automatiske test kører mod de rigtige vendorerede filer — ikke mod testdata.
- **Afgrænsning.** Af de 15 vendorerede mapper indgår 14 i korpus — én for
  hver af bind 28's grupper. Mappen `ded` med dedikationerne er hentet og
  ligger i projektet, men er holdt uden for visningen: dens TEI har hverken
  `correspDesc`, afsender eller modtager og bruger sit eget nummereringsrum.
  Det er en udeladelse, ikke en tilsnigelse.

## Kildens defekter, bevaret

- Ét brev har en øvre datogrænse, ingen kan læse maskinelt (`notAfter`
  angivet som `1847000`). Værdien beholdes rå, og brevsiden oplyser det åbent.
- Brev 39's overskrift står ufuldstændig i kilden; siden falder tilbage på
  brevhovedets oplysninger i stedet for at digte en overskrift.
- Tre poster i gruppen med familien Lund er krydshenvisninger uden egen
  brevtekst (`n="-"`); deres sider siger det, og deres resuméer peger på de
  breve, hvor SKS trykker teksten.
- Manglende mellemrum og en enkelt dublering fra kildens opmærkning gengives,
  som de står. Der rettes ikke stiltiende i teksten.
- Brevhovedernes rå navneformer og brevteksternes normaliserede
  personnøgler er to registre, som TEI-filerne ingen steder forbinder. Vores
  sammenkoblingstabel er redaktionel og siger det: 71 former er koblet, 13 er
  bevidst ladt ukoblede med en begrundelse hver.

## Tal

Tal om *epistel* selv (638 sider, 336 breve i 14 grupper, 298 personsider
heraf 143 med biografi, 336 resuméer, 326 placerede og 10 udaterede breve på
tidslinjen, 38 skrifter, 9 bopæle, 341 grønne tests, byggetid ca. et halvt
sekund) er talt op ved at bygge sitet, ikke hentet fra hukommelsen. Det
fastholdte commit læses af `data/vendor/PROVENANCE.md`; »en lille uges tid«
er spændet mellem første og sidste commit i `git log`. »Cirka 100 agenter«
er transkript-tællingen: 84 subagent-transkripter frem til 29. juli plus den
afsluttende rundes hold. Begge efterprøves igen ved offentliggørelse.
