# Doktor-runden — the trial round

Maria's own editing pass over the trial round's four verified captions
(2026-08-26, 10:42–11:36), reconstructed 2026-08-27 from the session
transcript on her machine. Her words are quoted verbatim (Danish,
lowercase and typos included); the framing between quotes is the
arbitrator's. This round is where the doktor-runde was *invented* — it
began as a language question and ended as a fixed, deliberately manual
step in the method.

## The opening — a request for everyday language

After reading the four verified drafts (10:42):

> jeg er meget imponeret over teksterne. især alt-teksten er imiddelbart
> overbevisende: nøgtern, beskrivende, præcise. notabenes tekster er
> vanskeligere. sproget er poetisk, rytmisk komplekst, legende med
> almindelige ords dobbeltbetydning. de skal læses to gange, og jeg er
> ikke helt overbevist om at det fungerer i en udgave som skal gøre
> brevene mere tilgængelige, men jeg er meget åben over for det.
>
> vil du læse sprogbibelen og give dit eget bud på en let redigering af
> sproget i en mere hverdagslig retning, men uden at miste notabenes
> tænksomme ironi?

The assistant's diagnosis: the two-reading heaviness was *syntactic,
not lexical* — fronted nominals and inversions ("Udskriften på brevets
eget ark:", "Omgivelser har broen ingen af") that hold the verb back —
and it proposed flat rewrites: one thought per sentence, verb early.

## The turn — the blind spot named

Maria, reading the flat rewrites against the originals (11:27):

> der lærte jeg hele to ord: nominalkaskade og kolon-kaskade.
>
> den lyriske syntaks blev næsten usynlig for mig fordi jeg ofte bruger
> den selv ("jeg bruger ofte den lyriske syntaks selv, så derfor blev
> den usynlig for mig" er ikke så interessant for mig), men nu er den
> meget tydeligt. jeg kan også godt lide den, og nu er jeg kommet i
> tvivl.
>
> dine ændringer er meget tydelige, men rammer ikke notabenes tone så
> rent. det var jo heller ikke det primære formål. tænker at der er
> meget af opus 5s eget sproglige modus i alle teksterne, og den er
> svær at ramme.

## Her own hand — the four captions as she rewrote them (11:29)

> Skrevet på brevets eget ark: broderens adresse i Berlin, »unter Linden
> 20 drey Treppen«, og på tysk, hvad der følger med — en lille kasse med
> to bøger. Lakseglet sidder der endnu.
>
> Kortet fulgte med brev 139, hvor Kierkegaard dvæler ved blomsten i
> kvindens hånd: hvem rækker den til hvem? »Det veed ingen Trediemand.«
> Bagsiden har både Kierkegaard og Regine skrevet på.
>
> Gravstedet, som brev 39 beskriver det på forhånd: korset, gravteksten
> om faderens første kone øverst, de to tavler lænet op ad stenen.
> Pladsen, Kierkegaard bad om til sit eget navn, er fyldt ud: »DØD D. 11
> NOVEMBER 1855«.
>
> »Den Person med Kikkerten det er mig«, står der i brevet, hvor
> tegningen sidder. Omgivelser har broen ingen af — og kunstkenderne er
> ifølge brevet uenige om.

(The last sentence broke off — a typo she confirmed in the next
message. Compared with the drafts, her edits kept the lyrical syntax
and sharpened the *referents*: »i kvindens hånd« for a floating
»hendes«, »både Kierkegaard og Regine« for »de … begge to«, »lænet op
ad stenen« for »nedenfor«. That became the round's calibration: the
two-reading heaviness was inversion × unclear reference — remove the
second factor, not the first.)

## The ruling — difficulty dosed deliberately (11:35)

> korrekturen er korrekt, og ja: jeg lod den tunge sætning stå fordi det
> er den tungeste sætning i hele værket. den må gerne være svær.
>
> gør det meget gerne færdigt. hvis de ca. 40 endelige tekster også skal
> have en doktor-runde, kan vi bare tage den manuelt. det vil bryde
> systematikken, men løse den egentlige opgave: jeg vil se hvor langt
> man kan komme med ai-assisteret humanistisk arbejde, ikke krydse
> grænsen hvor det ikke virker mere.

"Den tunge sætning" is the grave-plot caption's embedded relative
clause — "Pladsen, Kierkegaard bad om til sit eget navn, er fyldt ud" —
which stands in the published dataset exactly as she left it.

## The version chain, archived

Every state of the four texts survives in this directory:

1. the first Opus drafts — embedded verbatim in `verification/round1/`'s
   verifier prompts;
2. the verified texts before the doktor-runde —
   `verified-texts-before-doktor.md` (this state never reached git as
   draft files: Maria's finals were applied before the first commit);
3. the assistant's flat rewrites — `flat-rewrites.md`;
4. Maria's own versions — quoted above;
5. the published finals — `drafts/*.json` and `captions-fragment.json`.

## What it led to

- The calibration ("behold den lyriske syntaks, men skærp
  referenterne — navne frem for pronominer, konkrete steder frem for
  retningsadverbier") was written into the method and carried into the
  full round's drafting instruction; see `docs/captions-method.md`,
  *Voice calibration*.
- The doktor-runde became step six of the method: always run, always
  manual, on purpose.
- Only edited captions were re-verified (one verifier suffices when the
  edit adds no claims); the re-verification files sit in
  `verification/`.
