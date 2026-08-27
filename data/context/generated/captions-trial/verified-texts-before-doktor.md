<!--
Archived 2026-08-27 from the trial-round session transcript: the glosh
document shown to Maria 2026-08-26T10:16Z, verbatim. These are the four
texts as they stood after three verification rounds (zero flags) and
BEFORE the doktor-runde — a state that never reached git, because
Maria's final versions were applied to the draft files prior to the
round's first commit. Part of the language round's version chain; see
doktor-runden.md.
-->

# Prøverunden er i mål — 4 billedtekster, 3 runder, 0 flag

## Teksterne (din dom over stemmen, tak — især fork #2!)

### 1. b1/ill_1 — Brev 2, udskriften (standardtilfældet)

**alt:** Foldet, gulnet brevark, set fra den side der bærer adressen. I
midterfeltet står med håndskrift »Cand: Theol: P. C. Kierkegaard« og
»unter Linden 20 drey Treppen«, med stor skrift »Berlin« og til venstre
nogle linjer på tysk om det medfølgende; til højre et ovalt stempel med
teksten »HAMBURG 6/4«. Spredt over arket ligger røde og sorte tal og
påtegninger, nederst i midten en rund, orangerød laksegl, og papiret har
tydelige foldespor, brune pletter og skrift fra arkets anden side, der
skinner igennem.

**caption:** Udskriften på brevets eget ark: broderens adresse i Berlin,
»unter Linden 20 drey Treppen«, og på tysk, hvad der følger med — en
lille kasse med to bøger. Lakseglet sidder der endnu.

### 2. b127/ill_14 — det kolorerede kort til Regine

**alt:** Et koloreret kort: en ung mand med mønstret turban, rød jakke
over en lyseblå vest og mønstrede vinrøde bukser sidder på en stenbænk
med et lutlignende strengeinstrument i skødet og strækker den ene hånd
op mod en ung kvinde, der læner sig ud af et vindue ovenover og holder
en lille buket ned mod hans hånd; et grønt klæde hænger ud af vinduet,
et andet ligger på bænken, og bagved ses et landskab med et højt smalt
tårn, bygninger og bjerge under en gylden himmel. Nedenunder ses kortets
bagside med fem håndskrevne verselinjer på tysk — under dem står »des
Knaben Wunderhorn« — og derunder nogle linjer på dansk skrevet med en
anden hånd i brunligt blæk. I bagsidens fire hjørner sidder runde orange
mærker.

**caption:** Kortet fulgte med brev 139, hvor Kierkegaard bliver ved
blomsten i hendes hånd: hvem rækker den til hvem? »Det veed ingen
Trediemand.« Bagsiden har de skrevet på begge to.

### 3. b1/ill_k3 — familiegravstedet (kom-foto)

**alt:** Et familiegravsted fotograferet i sort-hvid, med et gitter og
træer bagved. Øverst rejser sig en sten med et kors på toppen og en
indskriftstavle for Kirstine Nielsdatter Kierkegaard, født Royen, »DØDE
DEN 23 MARTII 1796«. Foran stenen står på en lavere sokkel to tavler
lænet op ad den: den venstre med Søren Michael, Maren Kirstine og Søren
Aabye Kierkegaards navne og et vers, den højre med Anne Kierkegaard født
Lund og Michael Pedersen Kierkegaard; omkring gravstedet græs med
nedfaldne blade.

**caption:** Gravstedet, som brev 39 beskriver det på forhånd: korset,
gravteksten om faderens første kone øverst, de to tavler lænet op
nedenfor. Pladsen, Kierkegaard bad om til sit eget navn, er fyldt ud:
»DØD D. 11 NOVEMBER 1855«.

**credit:** (foto: David Cain)

### 4. vignet/vig-brev-kikkert — SK's tegning i brev 129

**alt:** Enkel stregtegning i sort på hvid bund: to lange, svagt
opadbuede vandrette streger løber mellem to lodrette streger uden helt
at nå dem. På den nederste streg står en lille figur i profil med høj
hat og lang frakke og holder en lang kikkert for øjet, rettet mod højre;
ellers er fladen mellem stregerne tom. Øverst til højre, uden for den
højre lodrette streg, står et par ord skrevet i hånden med skråskrift.

**caption:** »Den Person med Kikkerten det er mig«, står der i brevet,
hvor tegningen sidder. Omgivelser har broen ingen af — og kunstkenderne
er ifølge brevet uenige om hvorfor.

## Forløbet i tal

| runde | codex | grok |
|---|---|---|
| 1 (udkast) | 6 flag | 3 flag (+1 hallucineret kraken, uden kontekst) |
| 2 (repareret) | 0 | 2 tvivl |
| 3 (mikrorepareret) | **0** | **0** |

Alle 11 flag var berettigede. Bedste fangster: grok så gitterets
placering rigtigt, hvor både udkast og codex tog fejl/tav; stenens
»MARTII« vs. parafrasens »marts«; »underskrevet des Knaben Wunderhorn«
→ kildeangivelse. Udkastagenterne var selv metodetro: forstørrede
billeder, holdt »Tre Kroner«-læsningen ude som usikker, afviste
halstørklæde-koblingen som ubelagt.

## Læringer → den store runde (i METODE.md)

1. **Brevet er autoriteten, øjet er vidne** — svære billeder bæres af
   kildens ord i captionen; alt-teksten holder sig til det robust synlige.
2. **Enkeltmodel-syn kræver konsensus** — striber/tern-uenighed →
   »mønstret«; retninger, materialer, antal demoveres ved uenighed.
3. **Grounding-kontekst disciplinerer modlæseren** — kraken-grok blev
   rundens skarpeste flagger, da den fik pakke + udkast med.
4. **Udgavens egne ord er sikker grund** — »udskrift«, »kort«, »MARTII«.

## Filer (alt utracket — intet committet)

```
scripts/prepare_caption_grounding.py      pakke-generator (genbrugelig)
scripts/run_caption_verification.sh       modlæser-runner (codex + grok)
data/context/grounding/captions-proeverunde/   4 pakker (gitignored)
data/context/generated/captions-proeverunde/
  METODE.md                               drejebog + læringer + facit
  modlaeser-prompt.md                     den fælles modlæser-instruks
  drafts/*.json                           4 udkast m. sources/note/repairs
  modlaesning/runde1|runde2|*.txt         alle rå domme
  captions-fragment.json                  leverancen i captions.json-form
```

## Dine kald herfra

1. **Stemmen** — holder Notabene ved faksimilerne? (fork #2: »Lakseglet
   sidder der endnu« / »Det veed ingen Trediemand« er hendes prøvesvar)
2. **Godkend/juster teksterne** — alt+caption er dine at redigere
3. **Commit af prøverunden som audit trail?** (generated/ er committed
   praksis, men du bestemmer om/hvornår — evt. først med den store runde)
4. **Den store runde**: 36 billeder tilbage, frisk session, samme
   pipeline — pakke-generatoren skal generaliseres fra TRIAL-listen først
