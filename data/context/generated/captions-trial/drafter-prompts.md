# The drafter prompts — the trial round

The four prompts, verbatim, that spawned the trial round's Opus drafting
agents (2026-08-26, 09:17-09:18 — all four sent within 32 seconds as one
set, never revised during the session). Recovered 2026-08-27 from the
session transcript on Maria's machine and archived here so the trial
round's chain matches the full round's (`../captions/drafter-prompt.md`).
They share one skeleton; what varies is the paths, one image-specific
"SÆRLIGT for dette billede" paragraph per special case (the photo
credit, the caption-less vignette), and small additions to the caption
instruction's list of prohibitions (grief and graves, for the grave-plot
photo). The prompts are in Danish, like the editorial process they
drove. Unlike the full round, the instruction here is embedded in each
prompt rather than read from an archived file — that indirection was
itself a lesson the full round drew from this one.

---

## b1/ill_1.jpg — udskriften

*Task-kald »Draft captions b1/ill_1«, 2026-08-26T09:17:30Z.*

```
Du er udkastagent i prøverunden for billedtekster i epistel-projektet (repo: /Users/maria/playground/epistel). Din opgave: skriv alt-tekst og Notabene-billedtekst for ÉT billede.

LÆS FØRST, i denne rækkefølge:
1. Billedet selv: /Users/maria/playground/epistel/data/vendor/b1/ill_1.jpg (brug Read — du er multimodal; billedet er tilladt primærkilde)
2. Grounding-pakken: /Users/maria/playground/epistel/data/context/grounding/captions-proeverunde/b1-ill_1.md
3. Stemmebiblen: /Users/maria/playground/epistel/docs/notabene.md (§§2–5 er godkendt kanon — captionen skal skrives i det leje)

GROUNDING-REGLEN (ufravigelig): Tilladt grounding er KUN billedet selv + pakkens indhold. Udefrakommende viden er inadmissibel — selv en sand påstand er en fejl, hvis den ikke kan spores til billedet eller pakken. En adversarial modlæser fra en fremmed modelfamilie efterprøver hver påstand bagefter.

SKRIV (på dansk):
- `alt`: neutral, beskrivende alt-tekst — hvad man SER, konkret, ingen fortolkning, ingen stemme. 1–3 sætninger. Begynd ikke med »Billede af«. Skriv til en, der ikke kan se billedet.
- `caption`: Maria Notabenes billedtekst. 1–2 sætninger, gerne under 40 ord. Hendes stemme: moderne rigsdansk, konkret, varm, let ironi kun mod hende selv/tidens afstand/udgivervanerne — aldrig mod brevskriverne. Citér gerne 2–6 ord ordret i kildens stavemåde med »danske anførselstegn«. Uvished siges ligeud. Gentag ikke udgavens caption mekanisk — men opfind intet.
- `sources`: liste af strenge, én pr. faktuel påstand i alt+caption, der sporer påstanden til grounding (fx "billedet: ...", "pakken, udgavens head: ...", "pakken, brev 2's læsetekst: ...").
- `note`: evt. tvivl, fravalg eller kant-observationer til reviewet — også hvad du IKKE kunne se tydeligt i billedet.

OUTPUT: skriv én JSON-fil (UTF-8, ensure_ascii=False-stil, dvs. æøå direkte) til /Users/maria/playground/epistel/data/context/generated/captions-proeverunde/drafts/b1-ill_1.json med objektet {"id": "b1/ill_1.jpg", "alt": ..., "caption": ..., "sources": [...], "note": ...}. Returnér derefter kort: alt + caption som tekst.
```

---

## b127/ill_14.jpg — Regine-kortet

*Task-kald »Draft captions b127/ill_14«, 2026-08-26T09:17:39Z.*

```
Du er udkastagent i prøverunden for billedtekster i epistel-projektet (repo: /Users/maria/playground/epistel). Din opgave: skriv alt-tekst og Notabene-billedtekst for ÉT billede.

LÆS FØRST, i denne rækkefølge:
1. Billedet selv: /Users/maria/playground/epistel/data/vendor/b127/ill_14.jpg (brug Read — du er multimodal; billedet er tilladt primærkilde)
2. Grounding-pakken: /Users/maria/playground/epistel/data/context/grounding/captions-proeverunde/b127-ill_14.md
3. Stemmebiblen: /Users/maria/playground/epistel/docs/notabene.md (§§2–5 er godkendt kanon — captionen skal skrives i det leje)

GROUNDING-REGLEN (ufravigelig): Tilladt grounding er KUN billedet selv + pakkens indhold. Udefrakommende viden er inadmissibel — selv en sand påstand er en fejl, hvis den ikke kan spores til billedet eller pakken. Sig fx intet om, hvem Regine Olsen var for Kierkegaard, medmindre pakken selv siger det. En adversarial modlæser fra en fremmed modelfamilie efterprøver hver påstand bagefter.

SKRIV (på dansk):
- `alt`: neutral, beskrivende alt-tekst — hvad man SER, konkret, ingen fortolkning, ingen stemme. 1–3 sætninger. Begynd ikke med »Billede af«. Skriv til en, der ikke kan se billedet.
- `caption`: Maria Notabenes billedtekst. 1–2 sætninger, gerne under 40 ord. Hendes stemme: moderne rigsdansk, konkret, varm, let ironi kun mod hende selv/tidens afstand/udgivervanerne — aldrig mod brevskriverne. Citér gerne 2–6 ord ordret i kildens stavemåde med »danske anførselstegn«. Uvished siges ligeud. Gentag ikke udgavens caption mekanisk — men opfind intet.
- `sources`: liste af strenge, én pr. faktuel påstand i alt+caption, der sporer påstanden til grounding (fx "billedet: ...", "pakken, udgavens head: ...", "pakken, brev 139's læsetekst: ...").
- `note`: evt. tvivl, fravalg eller kant-observationer til reviewet — også hvad du IKKE kunne se tydeligt i billedet.

OUTPUT: skriv én JSON-fil (UTF-8, æøå direkte) til /Users/maria/playground/epistel/data/context/generated/captions-proeverunde/drafts/b127-ill_14.json med objektet {"id": "b127/ill_14.jpg", "alt": ..., "caption": ..., "sources": [...], "note": ...}. Returnér derefter kort: alt + caption som tekst.
```

---

## b1/ill_k3.jpg — gravstedsfotoet

*Task-kald »Draft captions b1/ill_k3«, 2026-08-26T09:17:51Z.*

```
Du er udkastagent i prøverunden for billedtekster i epistel-projektet (repo: /Users/maria/playground/epistel). Din opgave: skriv alt-tekst og Notabene-billedtekst for ÉT billede.

LÆS FØRST, i denne rækkefølge:
1. Billedet selv: /Users/maria/playground/epistel/data/vendor/b1/ill_k3.jpg (brug Read — du er multimodal; billedet er tilladt primærkilde)
2. Grounding-pakken: /Users/maria/playground/epistel/data/context/grounding/captions-proeverunde/b1-ill_k3.md
3. Stemmebiblen: /Users/maria/playground/epistel/docs/notabene.md (§§2–5 er godkendt kanon — captionen skal skrives i det leje; bemærk at §5's eksempel om brev 39 findes — genbrug det IKKE, skriv billedets egen tekst)

GROUNDING-REGLEN (ufravigelig): Tilladt grounding er KUN billedet selv + pakkens indhold. Udefrakommende viden er inadmissibel — selv en sand påstand er en fejl, hvis den ikke kan spores til billedet eller pakken. En adversarial modlæser fra en fremmed modelfamilie efterprøver hver påstand bagefter.

SÆRLIGT for dette billede: udgavens egen billedtekst har en fotokredit »(foto: David Cain)« — den skal bevares ordret; læg den i et separat felt `credit`.

SKRIV (på dansk):
- `alt`: neutral, beskrivende alt-tekst — hvad man SER, konkret, ingen fortolkning, ingen stemme. 1–3 sætninger. Begynd ikke med »Billede af«. Skriv til en, der ikke kan se billedet.
- `caption`: Maria Notabenes billedtekst. 1–2 sætninger, gerne under 40 ord. Hendes stemme: moderne rigsdansk, konkret, varm, let ironi kun mod hende selv/tidens afstand/udgivervanerne — aldrig mod brevskriverne, og aldrig mod sorg eller grave. Citér gerne 2–6 ord ordret i kildens stavemåde med »danske anførselstegn«. Uvished siges ligeud. Gentag ikke udgavens caption mekanisk — men opfind intet.
- `credit`: fotokreditten ordret.
- `sources`: liste af strenge, én pr. faktuel påstand i alt+caption, der sporer påstanden til grounding (fx "billedet: ...", "pakken, udgavens head: ...", "pakken, brev 39's læsetekst: ...", "pakken, kommentarnote b-1776: ...").
- `note`: evt. tvivl, fravalg eller kant-observationer til reviewet — også hvad du IKKE kunne se tydeligt i billedet (fx om gravtekster på fotoet kan læses).

OUTPUT: skriv én JSON-fil (UTF-8, æøå direkte) til /Users/maria/playground/epistel/data/context/generated/captions-proeverunde/drafts/b1-ill_k3.json med objektet {"id": "b1/ill_k3.jpg", "alt": ..., "caption": ..., "credit": ..., "sources": [...], "note": ...}. Returnér derefter kort: alt + caption som tekst.
```

---

## vignet/vig-brev-kikkert.jpg — kikkertvignetten

*Task-kald »Draft captions kikkert-vignet«, 2026-08-26T09:18:02Z.*

```
Du er udkastagent i prøverunden for billedtekster i epistel-projektet (repo: /Users/maria/playground/epistel). Din opgave: skriv alt-tekst og Notabene-billedtekst for ÉT billede.

LÆS FØRST, i denne rækkefølge:
1. Billedet selv: /Users/maria/playground/epistel/data/vendor/vignet/vig-brev-kikkert.jpg (brug Read — du er multimodal; billedet er tilladt primærkilde)
2. Grounding-pakken: /Users/maria/playground/epistel/data/context/grounding/captions-proeverunde/vignet-kikkert.md
3. Stemmebiblen: /Users/maria/playground/epistel/docs/notabene.md (§§2–5 er godkendt kanon — captionen skal skrives i det leje)

SÆRLIGT for dette billede: udgaven har INGEN billedtekst her — figuren er en vignet i selve brev 129, dvs. tegningen er en del af brevet, og brevets første linjer taler direkte om den. Billedet + brevteksten er hele din grounding. Det gør dette til metodens skarpeste test: alt skal komme fra de to.

GROUNDING-REGLEN (ufravigelig): Tilladt grounding er KUN billedet selv + pakkens indhold. Udefrakommende viden er inadmissibel — selv en sand påstand er en fejl, hvis den ikke kan spores til billedet eller pakken. Påstå fx ikke at tegningen er lavet af Kierkegaard selv med blæk, medmindre billede/pakke bærer det. En adversarial modlæser fra en fremmed modelfamilie efterprøver hver påstand bagefter.

SKRIV (på dansk):
- `alt`: neutral, beskrivende alt-tekst — hvad man SER, konkret, ingen fortolkning, ingen stemme. 1–3 sætninger. Begynd ikke med »Billede af«. Skriv til en, der ikke kan se billedet.
- `caption`: Maria Notabenes billedtekst. 1–2 sætninger, gerne under 40 ord. Hendes stemme: moderne rigsdansk, konkret, varm, let ironi kun mod hende selv/tidens afstand/udgivervanerne — aldrig mod brevskriverne. Citér gerne 2–6 ord ordret i kildens stavemåde med »danske anførselstegn«. Uvished siges ligeud. Opfind intet.
- `sources`: liste af strenge, én pr. faktuel påstand i alt+caption, der sporer påstanden til grounding (fx "billedet: ...", "pakken, brev 129's læsetekst: ...", "pakken, kommentarnote b-1800: ...").
- `note`: evt. tvivl, fravalg eller kant-observationer til reviewet — også hvad du IKKE kunne se tydeligt i billedet.

OUTPUT: skriv én JSON-fil (UTF-8, æøå direkte) til /Users/maria/playground/epistel/data/context/generated/captions-proeverunde/drafts/vignet-kikkert.json med objektet {"id": "vignet/vig-brev-kikkert.jpg", "alt": ..., "caption": ..., "sources": [...], "note": ...}. Returnér derefter kort: alt + caption som tekst.
```
