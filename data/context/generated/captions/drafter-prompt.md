# Udkast-instruks — billedtekster (den store runde)

Instruks givet til hver udkastagent (Claude Opus, multimodal) sammen med
stien til grounding-pakken og billedfilen/-erne. Prøverundens instruks
blev ikke arkiveret; denne er metodens (`docs/captions-method.md`)
regler gjort ordrette, med prøverundens fire godkendte udkast i
`data/context/generated/captions-trial/drafts/` som few-shot-forbillede.

---

Du skriver, for ÉT billede fra en dansk digital udgave af Søren
Kierkegaards breve, et udkast med:

- `alt` — neutral, beskrivende dansk alt-tekst: hvad man *ser*, ingen
  tolkning, ingen stemme. Layout, hænder, farver, tekstfelter — men
  kun det, der robust kan ses.
- `caption` — Maria Notabenes billedtekst. Læs `docs/notabene.md`
  §§2–5 (stemmebiblen) FØR du skriver. Kalibrering fra prøverunden:
  lyrisk syntaks er velkommen som stil, men referenterne skal være
  skarpe — navne frem for pronominer, konkrete steder frem for
  retningsadverbier. Captionen bærer betydning gennem kildens egne ord;
  ved svært læselige billeder er brevet autoriteten, øjet et vidne.
- `credit` — udgavens fotokredit ordret (fra head, typisk »(foto: …)«),
  ellers `null`.
- `sources` — én sporbarhedslinje pr. faktuel påstand: hvor i billedet
  eller pakken den kommer fra. Citér pakkens form, parafrasér ikke.
- `note` — dine tvivl og bevidste fravalg. Dette felt er halvdelen af
  kvalitetssikringen: nedskriv alt, du så men ikke turde bruge, alt du
  udelod og hvorfor.
- `repairs` — tomt array (fyldes under arbitreringen).

REGLEN: udefrakommende viden er utilladelig. Tilladt grounding er alene
(a) selve billedfilen og (b) grounding-pakken. Selv en SAND påstand er
en fejl, hvis den ikke kan spores dertil. Utydelig håndskrift må ikke
gengives med selvsikkerhed; en detalje, du er usikker på, generaliseres
eller udelades (og noteres i `note`).

Særtilfælde (fremgår af pakken, når de gælder):

- **Én planche, to id'er** (identisk fil i to bind): skriv ÉN fælles
  `alt`, men én caption pr. id, grounded i det pågældende id's eget
  brev. JSON-formen er da `ids` (liste) og `captions` (objekt id →
  caption) i stedet for `id`/`caption`.
- **Id uden forekomster i udgaven**: captionen er `null` — billedet
  skal stå ærligt caption-løst; begrund det i `note`. Alt-teksten
  skrives stadig (billedet selv er tilladt grounding).

Skriv udkastet som JSON til
`data/context/generated/captions/drafts/<slug>.json` (slug = pakkens
filnavn uden `.md`), samme form som prøverundens udkast:

    {"id": "...", "alt": "...", "caption": "...", "credit": null,
     "sources": [...], "note": "...", "repairs": []}

Svar-teksten til den, der har kaldt dig, er blot slug + én linje om
tvivlens omfang; udkastet selv bor i filen.
