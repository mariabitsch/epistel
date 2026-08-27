# The overlap readers — the doktor-runde's delegated check

Maria's doktor-runde instruction (2026-08-26, 18:19) delegated one
question: do the captions overlap the letter summaries in
`summaries.json` too much? ("hvis overlapningen er for stor, vil jeg
gerne have dem forkortet – ellers kan de blive.") Two Claude Sonnet
readers measured all 34 drafts independently — A took the early waves,
B the late ones. This file archives their prompts and their full
reports verbatim, recovered 2026-08-27 from the session transcript.
Verdict: 15 HIGH, 7 MODERATE, rest LOW; the pattern being that overlap
arises where a letter is so short that image anchor and summary cannot
help meeting.

What followed, and where each state lives:

- 14 of the 15 HIGH captions were shortened against the image
  (subtractive/rearranged, no new claims); the fifteenth, ill_11, was
  spared as one of Maria's quoted favourites — an arbitration under her
  delegated mandate, logged in that draft's `repairs`. Every
  shortening is logged per draft in `repairs`; the pre-shortening
  wording is the drafts' state at commit 1f538a0 (diff to 5901340
  shows every edit).
- The shortened captions were re-verified by Codex —
  `verification/doktor-runden/`, 14 raw outputs whose prompts embed the
  compressed texts verbatim. Codex caught three slips in the
  arbitrator's own compressions ("skrive" -> "indlevere", the "Jettes
  hilsen" ambiguity, the dot count) — even the arbitrator gets
  counter-read. The fixes are in the drafts' final state; the flawed
  intermediates survive inside the verification files.

---

## Reader A — prompt

*Task-kald "Overlap captions vs resuméer A", 2026-08-26T18:21:05Z.*

```
Arbejd fra repo-roden /Users/maria/playground/epistel. Undersøgelse (kun læsning, INGEN filændringer):

Spørgsmål: konkurrerer billedtekst-udkastenes captions med Maria Notabenes egentlige brev-resuméer? En caption må gerne citere og pege ind i brevet, men den skal være en *billedtekst* — hvis den reelt genfortæller brevets indhold, overlapper den resuméets funktion.

For hver af disse 17 udkast i data/context/generated/captions/drafts/ (felterne `caption` eller `captions`):
b1-ill_2, b1-ill_3, b1-ill_4, b1-ill_k1, b1-ill_k2, b120-ill_12, b120-ill_31, b120-ill_32, b127-ill_13, b127-ill_15, b171-ill_16, b171-ill_17, b171-ill_18, b171-ill_19, b171-ill_k7, b208-ill_20, b208-ill_k8

1. Find det/de tilhørende breve: grounding-pakken data/context/grounding/captions/<slug>.md har »## Brev N (bX)«-overskrifter.
2. Slå brevets resumé op i data/context/summaries.json (nøglet på brev-id).
3. Bedøm overlappet: LAV (captionen bliver ved billedet, citater er punktnedslag), MODERAT (genfortæller en del af brevets ærinde, men med billedet som anker) eller HØJ (fungerer reelt som et andet resumé af brevet).
Returnér som rådata (dit svar ER resultatet): pr. udkast én linje »slug | brev(e) | LAV/MODERAT/HØJ | begrundelse i én sætning«, og for alle MODERAT/HØJ desuden captionen og resuméet citeret, så en arbitrering kan afgøre forkortelse.
```

## Reader A — report (verbatim)

## Metode

For hvert udkast: fundet brevnummer(-numre) i grounding-pakken, slået resumé op i `data/context/summaries.json`, sammenlignet caption mod resumé.

## Resultat

```
b1-ill_2   | brev 3 (b1)          | MODERAT | samme nøglecitat (»for tillige at gjendrive Fader«) og samme handling (faderens klage + Sørens tilføjelse) som resuméet, blot afgrænset til denne side
b1-ill_3   | brev 20+22 (b1)      | HØJ     | gengiver stort set ordret begge breves pointe (arv/forlovelse »lige så forpligtende som et ægteskab«; den unævnte hvem forfatterskabet er tilegnet)
b1-ill_4   | brev 28 (b1)         | MODERAT | deler et næsten enslydende faktum (»vognen har han ikke til rådighed«) og brevets ærinde (tak for bogen), men udelader resuméets pointe (floskel-kritikken)
b1-ill_k1  | brev 2 (b1)          | LAV     | captionen bliver ved sidens fysiske afslutning (dato, Ferdinands note); intet af brevets indhold (Cicero, Asp, engelsk) berøres
b1-ill_k2  | brev 36 (b1)         | LAV     | captionen anker i det specifikke, indbundne eksemplar; resuméets egentlige pointe (rådet om at gå) er slet ikke med
b120-ill_12| brev 122 (b120)      | HØJ     | hovedsætningen er næsten identisk med resuméet ord for ord
b120-ill_31| brev 121 (b120)      | LAV     | beskriver bevidst kun sidens fysiske træk og udskyder selve pointen (»må bagsiden fortælle«) til ill_32
b120-ill_32| brev 121 (b120)      | HØJ     | gentager resuméets kernesætning med samme latinske citat næsten ordret
b127-ill_13| brev 139 (b127)      | MODERAT | genfortæller brevets grundlæggende ærinde (billedet er hendes, han længes), men uden resuméets særlige detaljer (blomst-tvetydighed, halstørklæde)
b127-ill_15| brev 136+146 (b127)  | HØJ     | brev 146-delen er en næsten fuldstændig gengivelse af resuméet; brev 136-delen overlapper delvist
b171-ill_16| brev 176 (b171)      | HØJ     | gengiver hele brevets ærinde (opgivet gave, brev med bygningsramme, »foran museet«) parallelt med resuméet
b171-ill_17| brev 193 (b171)      | LAV     | captionen holder sig til rammens dekoration og den fysiske indretning; intet af indholdet (bal-drilleri, stokke-historien) nævnes
b171-ill_18| brev 193 (b171)      | HØJ     | gengiver stokke-historien næsten identisk med resuméet
b171-ill_19| brev 202 (b171)      | MODERAT | deler den centrale sætning (»bad om en oversigt over trækfuglenes ankomsttider«) ordret, men vælger andre konkrete fugle/detaljer end resuméet
b171-ill_k7| brev 189+190 (b171)  | HØJ     | gengiver brev 189's kernesætning (Schelling-citat, Michael skal vise Peter) næsten ordret
b208-ill_20| brev 224 (b208)      | HØJ     | samme handling og opstilling (»gør ... op«, boglade-pris vs. forlangende) som resuméet, blot med andre konkrete tal
b208-ill_k8| brev 211 (b208)      | HØJ     | samme kerneplot (afbryder ugedagen pga. dom om »Fædrelandet«) som resuméet, kun med et andet citat
```

## Citater til arbitrering (MODERAT/HØJ)

**b1-ill_2** (MODERAT)
- caption: »Bagsiden af brev 3's første blad. M.P. Kierkegaard beklager sig over, at han ikke kan få Søren til at skrive til broderen P.C. Kierkegaard, og spørger, om det er »Aands Fattigdom«. Nederst på samme side, med mindre skrift, føjer Søren selv sit eget til: han skriver snart, »for tillige at gjendrive Fader«.«
- resumé: »Faderen sender Peter et kreditiv på 60 Fr. d'or til Göttingen og en nøje anvisning på det høflige følgebrev, der skal med. Han kan ikke få Søren til at skrive – og nederst lover Søren at gøre det snart, »for tillige at gjendrive Fader«.«

**b1-ill_3** (HØJ)
- caption: »To udskrifter til den samme mand, Kierkegaards bror, og uden på begge den samme besked: »At aabne efter min Død.« Øverst brev 20, det med den sorte lak, som gør Regine Schlegel til arving efter en forlovelse, Kierkegaard regner for lige så forpligtende som et ægteskab; nederst brev 22, det med den røde, hvor hun er »Den Ubenævnte, hvis Navn engang vil nævnes,« som hele forfattervirksomheden er tilegnet.«
- resumé (20): »Brevet skal åbnes efter hans død: fru Regine Schlegel arver ubetinget »al den Smule«, han kan efterlade sig, og vil hun ikke modtage det, kan hun give det til de fattige. En forlovelse var ham lige så forpligtende som et ægteskab.«
- resumé (22): »Et par linjer i en konvolut med påskriften »At aabne efter min Død«. Indeni siger Kierkegaard rent ud, hvem den unævnte er, som hele forfattervirksomheden er tilegnet: hans forlovede engang, fru Regine Schlegel.«

**b1-ill_4** (MODERAT)
- caption: »Brev 28 udenpå: arket bærer foldelinjerne endnu, det lille guldfarvede mærke sidder der endnu, med et trekantet lyst felt i papiret under sig, og adressen står på skrå »Til Hr Magister Kierkegaard. – hersteds.« Indeni takker H.P. Kierkegaard for »den tilsendte Bog« og håber at komme selv om nogle dage — vognen har han ikke til sin rådighed i de første.«
- resumé: »Tak for bogen – men ikke med floskelen »hvor det har glædet mig«: Peter Kierkegaard vil hellere sige, at gaven netop blev givet, fordi den ville glæde. Vognen har han ikke til rådighed i de første dage, så takken må være skriftlig.«

**b120-ill_12** (HØJ)
- caption: »»Til Kongen!« står der øverst, med sving: Kierkegaard beder Christian VIII om lov til at indlevere sin magisterafhandling »om Begrebet Ironi med stadigt Hensyn til Socrates« »i Modersmaalet«. Ærindet står to gange på det stemplede ark — kort i venstre spalte, udførligt i højre, og den udførlige når ikke at blive færdig på bladet.«
- resumé: »Kierkegaard beder kongen om lov til at indlevere sin magisterafhandling »om Begrebet Ironi med stadigt Hensyn til Socrates« på modersmålet i stedet for latin, og vedlægger en attest fra sin gamle rektor på, hvor godt han kan latin.«

**b120-ill_32** (HØJ)
- caption: »Brevets anden side begynder midt i sætningen: Kierkegaard fortæller Københavns Universitet, at han sagde teologien helt farvel — »omnino theologiæ valedixi« — og at han aldrig havde taget de forladte studier op igen, hvis ikke faderens død havde bundet ham ved et slags løfte. Under datoen står listen over, hvad han har læst af Det Gamle Testamente.«
- resumé: »På latin fortæller Kierkegaard fakultetet om sine studier og indrømmer lige ud, at han engang sagde teologien helt farvel – »omnino theologiæ valedixi« – og kun tog den op igen, fordi faderens død bandt ham til et løfte.«

**b127-ill_13** (MODERAT)
- caption: »Brev 139, første blad: Kierkegaard sender Regine billedet, som er hendes, men »længes utaalmodigt« efter at komme hen til hende. Nederst, lige over »Din S. K.«, er de sidste par linjer streget ud, til der ikke er mere at læse.«
- resumé: »Et billede, hun ejer, er havnet hos ham og længes hjem igen: kvinden på det holder en blomst – rækker hun den, eller har hun fået den? »Det veed ingen Trediemand« – og med brevet følger et halstørklæde, som kun hun skal vide, hun ejer.«

**b127-ill_15** (HØJ)
- caption: »Øverst det billede, Kierkegaard sender Regine i brev 136, fordi han ikke selv kommer den lørdag: »Det er en gammel Kone, der læser«. Hun læser højt — ikke for en tilhører, men fordi mennesket vil høre det bedste og ikke blot se det. Nederst det fra brev 146, hvor han kun beder om, at det ikke må hænge »upaaagtet paa et ubeboet Værelse«.«
- resumé (136): »Det er lørdag, og han kommer ikke. I stedet et lille billede af en gammel kone, der læser højt – og en tilståelse: han har beholdt hendes strikketøj, det ligger ved siden af ham i sofaen, mens han selv læser højt.«
- resumé (146): »Et billede følger med; han ønsker ikke, det skal hænge upåagtet på et ubeboet værelse. Under hilsenen står et lille tysk vers: »Ich dein Du mein«.«

**b171-ill_16** (HØJ)
- caption: »Jettes fødselsdag faldt, mens Kierkegaard var i Berlin, og planen om en foræring fra Königstraße opgav han. Hun fik i stedet sin gratulation på dette papir, hvis ramme »forestiller 3 store Bygninger i Berlin« — og foran museet står de træer, brevet beder hende se efter på tegningen.«
- resumé: »I stedet for en gave fra Königstraße – pakker overlever sjældent posten – får Jette et brev på papir med tre berlinske bygninger i rammen. Så kan hun rejse i Berlin hjemme i dagligstuen og se den uhyre stenkumme foran museet.«

**b171-ill_18** (HØJ)
- caption: »Bagsiden af brev 193, halvdelen til nevøen Carl. Kierkegaard havde længe betragtet »en tynd Stok« i vinduet hos en kunstdrejer; da han endelig trådte ind i butikken, slog han en stor rude i stykker, betalte ruden og lod stokken stå.«
- resumé: »Ét ark, to breve: Sophie drilles for at have skrevet lige før et bal, og Carl får historien om stokken hos kunstdrejeren – da onklen endelig trådte ind, slog han en rude i stykker og betalte den i stedet for at købe stokken.«

**b171-ill_19** (MODERAT)
- caption: »Adressesiden til venstre, brevets første side til højre: den røde lak og adressen til »Hr Mag. art. S. Kierkegaard« i København — og så Henrik Lunds undskyldning for sin lange tavshed. Onklen havde bedt om en oversigt over trækfuglenes ankomsttider, og listen begynder nederst på siden med understregede fuglenavne, hvor Sanglærken og Guulspurven deler klamme og ankomsttid.«
- resumé: »Onklen bad om en oversigt over trækfuglenes ankomsttider, og Henrik Lund har gået i skovene selv og spurgt landmænd og zoologer: storken sidst i marts, svalen sidst i april, nattergalen 10.-12. maj. Skovskaden findes virkelig – udstoppet i et vindue på Østergade.«

**b171-ill_k7** (HØJ)
- caption: »Forsiden af brevet til nevøen Michael Lund er optaget af guld: ranker, dusker og to vingede fabeldyr om et felt, hvor der ikke står et ord. Kierkegaard begynder derfor sit svar inde i arket, »da en Kunstner har ladet das unvordenkliche Seyn, das allem Denken zuvorkommt, gaae iforveien« — Schellings yndlingsudtryk, som Michael skal vise videre til onkel Peter.«
- resumé (189): »Svaret begynder på anden side, fordi en kunstner har ladet »das unvordenkliche Seyn« gå i forvejen – og Michael skal vise stedet til onkel Peter og hilse, at det er Schellings yndlingsudtryk. Ellers er det blevet smukt vintervejr.«

**b208-ill_20** (HØJ)
- caption: »Kierkegaard gør sit eget forfatterskab op i to kolonner, »Boglade Priis« og »Mit Forlangende«: hvor mange »Stadier paa Livets Vei« og »Philosophiske Smuler« der ligger tilbage hos C.A. Reitzel og hos Luno — af Begrebet »Angest« kun restoplaget hos Reitzel — og hvad Kierkegaard vil have for dem. Nederst på venstre side har Reitzel siden skrevet sine egne tal ind, med blæk og blyant.«
- resumé: »Kierkegaard gør restoplagene op titel for titel, otte bøger og 970 rigsdaler i forlangende. Bogladeprisen på det ene punkt viser sig at være en anden, men nu »gider jeg ikke regne om igjen«.«

**b208-ill_k8** (HØJ)
- caption: »Brevets første side: Kierkegaard afbryder den faste ugedag hos vennen Giødwad, redaktør af »Fædrelandet«, fordi bladet efter Kierkegaards dom har handlet uforsvarligt med hans forfattervirksomhed. Dér står sætningen: »Jeg ønsker blot min Frihed, og saa veed Gud vil jeg gjerne see Dem.« Brevet blev aldrig sendt.«
- resumé: »Kierkegaard opsiger den faste ugedag hos Giødwad: to så offentlige og så uenige personer kan vanskeligt have et privat forhold, og sin dom om »Fædrelandet« kan han ikke holde tilbage. Hengivenheden beholder han – »enten De tillader det eller ikke tillader det«.«

## Kort sammenfatning

9 af 17 udkast ligger på HØJ, 5 på MODERAT, kun 3 på LAV (b1-ill_k1, b1-ill_k2, b120-ill_31, b171-ill_17 — faktisk 4). Mønsteret: hver gang billedets synlige tekst *er* brevets kerne-ærinde (afhandlingsansøgningen, ophævelsen af ugedagen, opgørelsen over restoplag, Schelling-citatet, stokke-historien), gengiver draft-agenten næsten den samme sætning som resuméet, ofte med samme eller et næsten enslydende citat. De tre-fire LAV-eksempler er dem, hvor billedet viser noget andet end brevets pointe (en ramme-dekoration, en lukkedato, et indbundet eksemplars fysiske kendetegn, sidens tomme halvdel) — der bliver captionen reelt ved billedet.

---

## Reader B — prompt

*Task-kald "Overlap captions vs resuméer B", 2026-08-26T18:21:12Z.*

```
Arbejd fra repo-roden /Users/maria/playground/epistel. Undersøgelse (kun læsning, INGEN filændringer):

Spørgsmål: konkurrerer billedtekst-udkastenes captions med Maria Notabenes egentlige brev-resuméer? En caption må gerne citere og pege ind i brevet, men den skal være en *billedtekst* — hvis den reelt genfortæller brevets indhold, overlapper den resuméets funktion.

For hver af disse 17 udkast i data/context/generated/captions/drafts/ (felterne `caption` eller `captions`; parrede udkast har `captions` som objekt id → caption, bedøm hver caption for sig; caption null = spring over):
b241-ill_k10+b259-ill_k10, b241-ill_k9, b259-ill_21, b276-ill_22, b276-ill_23, b308-ill_24+b79-ill_24, b43-ill_5, b43-ill_6, b70-ill_7, b70-ill_8, b79-ill_10, b79-ill_11, b79-ill_9, b79-ill_k4, b79-ill_k5, b79-ill_k6, vignet-vig-brev-blomst

1. Find det/de tilhørende breve: grounding-pakken data/context/grounding/captions/<slug>.md har »## Brev N (bX)«-overskrifter.
2. Slå brevets resumé op i data/context/summaries.json (nøglet på brev-id).
3. Bedøm overlappet: LAV (captionen bliver ved billedet, citater er punktnedslag), MODERAT (genfortæller en del af brevets ærinde, men med billedet som anker) eller HØJ (fungerer reelt som et andet resumé af brevet).
Returnér som rådata (dit svar ER resultatet): pr. udkast én linje »slug | brev(e) | LAV/MODERAT/HØJ | begrundelse i én sætning«, og for alle MODERAT/HØJ desuden captionen og resuméet citeret, så en arbitrering kan afgøre forkortelse.
```

## Reader B — report (verbatim)

# Overlapsanalyse: billedtekst-udkast vs. brev-resuméer

Metode: for hvert udkast er brevets nummer fundet i grounding-pakken (`data/context/grounding/captions/&lt;slug&gt;.md`, »## Brev N«), resuméet slået op i `data/context/summaries.json`, og captionen sammenlignet med resuméet på indhold og citater — ikke kun tema.

## Resultatlinjer

```
b241-ill_k10+b259-ill_k10 (b241/ill_k10) | – | SPRINGES OVER | caption = null (ingen forekomst i udgaven)
b241-ill_k10+b259-ill_k10 (b259/ill_k10) | brev 271 (b259) | MODERAT | genfortæller annonce-delen af brevet med to citater, men rører aldrig resuméets "egentlige" pointe (sorgen over datterdatteren)
b241-ill_k9                              | brev 256 (b241) | HØJ | brevet er otte linjer, og captionen dækker det samme forløb med samme nøglecitat som resuméet
b259-ill_21                              | brev 267 (b259) | LAV | captionen holder sig til bladets fysiske "tomme rum"/spadseretur-konceit; resuméets indhold (regnvejr, Cavaignac, bryllup, digtet) berøres slet ikke
b276-ill_22                              | brev 283 (b276) | HØJ | captionens hovedsætning gengiver hele brevets ærinde med samme citat som resuméet; kun billeddetaljen (dyr, signatur) er ny
b276-ill_23                              | brev 285 (b276) | HØJ | brevet er én sætning, og captionens første sætning er stort set resuméet ordret; anden sætning er billedspecifik tilføjelse
b308-ill_24+b79-ill_24 (b308/ill_24)     | brev 317 (b308) | LAV | anden gloss og andre citater end resuméets (bøgernes titler, "34-årig"-pointen); tyngden ligger på konvolutten
b308-ill_24+b79-ill_24 (b79/ill_24)      | brev 119 (b79)  | LAV | deler kun den ene faktuelle sætning ("takker for tre bøger"); resuméets øvrige indhold (Johannes, Louise, "som om Du sagde Farvel") mangler helt
b43-ill_5                                | brev 53 (b43)   | HØJ | samme hændelsesforløb og samme nøglecitat ("jeg har aldrig noget færdigt") som resuméet
b43-ill_6                                | brev 59 (b43)   | MODERAT | åbningssætningen ("prokrastinerende naturer"/"intet svar") er næsten identisk med resuméets, men caption mangler resuméets pointe (læste Enten–Eller to gange) og pivoterer til et billeddetalje
b70-ill_7                                | brev 72 (b70)   | HØJ | samme to-eksemplar-handling og samme citat ("kært at gøre... ikke blive mig en Vane") som resuméet
b70-ill_8                                | brev 78 (b70)   | MODERAT | gengiver brevets kernepointe (hun skal kun læse artiklen om hende) parallelt med resuméet, men tilføjer konvolut/dedikations-detaljer resuméet ikke har
b79-ill_10                               | brev 89 (b79)   | LAV | citat og fokus (seglet, "Folkesnak") er helt forskelligt fra resuméets indhold (arbejde, biblioteket, restaurationsturen)
b79-ill_11                               | brev 117 (b79)  | HØJ | brevet er en kort indbydelse, og captionen gengiver samme detaljer og citater som resuméet næsten ord for ord
b79-ill_9                                | brev 81 (b79)   | LAV | ren beskrivelse af konvolut/segl plus et citat ("Dig skal jeg ikke tabe"), der ikke findes i resuméet; ingen berøring af resuméets indhold (foredraget om støvlerne, den unge pige)
b79-ill_k4                               | – | SPRINGES OVER | caption = null
b79-ill_k5                               | brev 79 (b79)   | LAV | andet citat og andet fokus (stikket/"Dands af Gnomer") end resuméets (arken, "afsat fyrste", underskriftens parentes)
b79-ill_k6                               | brev 115 (b79), kontekst brev 83 | LAV | captionen handler kun om håndskriften/illustrationens formål og et citat fra det ældre brev 83; berører intet af brev 115's eget resumé (søndag i præstekjole, hospitalskirken, hestemarked, de tre bønner)
vignet-vig-brev-blomst                   | brev 178 (b171) | LAV | andet citat og anden vinkel (blomst/blad-bemærkningen) end resuméets (byttehandel med Jettes frugtstykke, natten oppe, "saa flaut")
```

## Citater til arbitrering (alle MODERAT/HØJ)

**b259-ill_10 (brev 271) — MODERAT**
- Caption: »Brev 271 til Kolderup-Rosenvinge standser ved netop denne annonce: Adressecomptoiret ejer formodentlig kun én vignet med en hest, »en høi, lang, tynd Rad, det bare Skind og Been«, og under den udsælger hesteslagter Koblauch kødet af to særdeles meget fede heste. Det er, siger Kierkegaard, at oplyse teksten ved hjælp af illustrationer.«
- Resumé: »Først hesteslagterens annonce, hvor vignetten viser en radmager fuldblodshest over tilbuddet om »særdeles meget fedt Kjød«. Til sidst, langsomt, det egentlige: conferensrådens tab af den lille datterdatter, og hvorfor en bedstefar sørger anderledes og længere end den unge mor.«

**b241-ill_k9 (brev 256) — HØJ**
- Caption: »Otte linjer og en underskrift: Kierkegaard anbefaler »paa det Varmeste« en ansøger, han har kendt gennem en række år. Hvor almindelig anbefalingen end lyder — »Ansøgerens Værdighed er ualmindelig«. Hvem ansøgeren var, ved vi ikke.«
- Resumé: »Anbefalingen nævner ikke ansøgeren ved navn og lyder ganske almindelig, men »Ansøgerens Værdighed er ualmindelig«: Kierkegaard kender ikke ét menneske til, som han på samme måde ville føle sig forpligtet til at anbefale.«

**b276-ill_22 (brev 283) — HØJ**
- Caption: »Rasmus Nielsen vil ikke have sit anliggende afhandlet på en spadseretur, og før Kierkegaard igen kalder på ham, mødes de næppe: »jeg har Tid at vente.« Øverst i hjørnet står et lille sort dyr med korsfane, nederst signaturen »R. N.««
- Resumé: »Det, der ligger Nielsen på sinde, vil han for ingen pris have afhandlet på en spadseretur. Derfor mødes de næppe igen, før Kierkegaard atter kalder på ham: »jeg har Tid at vente«.«

**b276-ill_23 (brev 285) — HØJ**
- Caption: »»Systemet« er kommet, melder Rasmus Nielsen; beskeden fylder én sætning. Ved den store lakklat øverst står linjen — vendt på hovedet i forhold til adressen — »Et sort Forsøg paa at forbedre en slet Forsegling«.«
- Resumé: »»Systemet« er kommet, det ankom i forgårs med omnibussen. Mere står der ikke.«

**b43-ill_5 (brev 53) — HØJ**
- Caption: »Brevets første blad bærer to underskrifter. Øverst melder Giødwad med sit eget navn, at et forseglet brev til Victor Eremita er blevet afleveret på Kierkegaards bopæl; nedenunder står afskriften af svaret, »jeg har aldrig noget færdigt«, underskrevet Victor Eremita.«
- Resumé: »Et forseglet brev til Victor Eremita var afleveret på Kierkegaards bopæl; han sendte det til Giødwad, der »tilstillede strax Adressatus Brevet«. Kopien af svaret, Giødwad her sender P.L. Møller, er kort: pseudonymet har aldrig noget færdigt og binder sig aldrig ved noget løfte.«

**b43-ill_6 (brev 59) — MODERAT**
- Caption: »Molbech regner sig selv til »de procrastinerende Naturer« og skriver til Kierkegaard, at denne billet slet ikke er noget svar. Alligevel fylder den hele siden ud, ned til det enkelte »M.« nederst.«
- Resumé: »Molbech hører til de prokrastinerende naturer – nogle breve venter halvandet år på svar – og erklærer derfor, at dette ikke er noget svar. Men han, der »aldrig læser danske Bøger«, har alligevel læst i Enten – Eller to gange på to dage.«

**b70-ill_7 (brev 72) — HØJ**
- Caption: »Brev 72, første blad: Kierkegaard beder professor Heiberg give et eksemplar af »en lille Bog« videre til Hverdags-Historiens forfatter og beholde et selv. I sætningen om eksemplaret er der skudt ord ind over linjen. At sende Heiberg et sådant eksemplar »er mig kjært at gjøre, og kan derfor ikke blive mig en Vane.««
- Resumé: »En pakke med to eksemplarer: det ene skal videre til Hverdags-Historiens forfatter, som udgiveren er vejen til, det andet er til professoren selv. At sende ham bøger er kært at gøre og kan derfor »ikke blive mig en Vane«.«

**b70-ill_8 (brev 78) — MODERAT**
- Caption: »Kierkegaard forsikrer Johanne Luise Heiberg om, at det ikke er meningen at få hende til at læse en hel lille bog — kun den ene lille artikel, som »forholder sig særligt til Dem«. Nedenunder ligger konvolutten med dedikationen til »Den lykkelige Kunstnerinde«, »med Beundring fra Forfatteren«.«
- Resumé: »Bogen behøver hun ikke at læse; den ville kun kede. Men i den nævnes en lille artikel af Inter et Inter om en skuespillerindes krise, og bliver den ikke læst af hende, er den efter forfatterens mening ikke kommet til sin bestemmelse.«

**b79-ill_11 (brev 117) — HØJ**
- Caption: »Indbydelsen, som Emil Boesen skrev den: bryllup i Frue Kirke onsdag den 1. maj, klokken 6 »(eller 7)«. »Jeg kommer ikke selv«, skriver han, for han er »blevet dygtig forkjølet«. Brevet slutter midt på arket.«
- Resumé: »Emil Boesen indbyder til sit eget bryllup, onsdag den 1. maj kl. 6 (eller 7) i Frue Kirke. Han kommer ikke selv med indbydelsen, for han er blevet »dygtig forkjølet« og må se at blive den kvit igen – svar udbedes.«

## Kort konklusion

7 af de 15 vurderbare captions (de to null-udkast er sprunget over) lander på HØJ eller MODERAT: b241-ill_k9, b276-ill_22, b276-ill_23, b43-ill_5, b70-ill_7 er reelt dubletter af resuméet (samme centrale citat, samme hændelsesforløb, ofte fordi brevet selv er meget kort); b259-ill_10, b43-ill_6, b70-ill_8 er delvise genfortællinger, der låner resuméets hovedpointe men tilføjer ægte billedankre. De øvrige 8 (b259-ill_21, b308/b79-ill_24-parret, b79-ill_10, b79-ill_9, b79-ill_k5, b79-ill_k6, vignet-blomst) citerer konsekvent andre steder i brevet end resuméet og holder sig til det, billedet selv viser — mønstret her er, at overlap opstår systematisk ved de korteste breve (256, 283, 285, 117), hvor der reelt er for lidt brevtekst til, at en billedanker og et resumé kan undgå at sige det samme.
