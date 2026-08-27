# The drafter wrapper prompts — the full round

The substance of the full round's drafting instruction lives in
`drafter-prompt.md`, written once before wave 1 and never edited (the
committed file is byte-identical to what was written — verified against
the session transcript 2026-08-27). Each drafting agent received only a
short *wrapper* prompt telling it what to read, in order: the archived
instruction, the voice bible, a trial-round exemplar, the grounding
packet, the image. This file archives those wrappers verbatim: the wave-1
skeleton every ordinary call shared (path substitutions only), and the
image-specific variants — every finding along the round entered the
process as an added line in one image's wrapper, never as an edit to the
shared instruction. Recovered from the session transcript on Maria's
machine; timestamps UTC.

---

## Bølge 1-skelettet — b1/ill_2 (repræsentativ for alle ordinære kald)

*Task-kald »Udkast caption b1/ill_2«, 2026-08-26T15:46:21Z.*

```
Du er udkastagent i billedtekst-runden for epistel. Arbejd fra repo-roden /Users/maria/playground/epistel. Læs i denne rækkefølge:
1. data/context/generated/captions/drafter-prompt.md — din instruks; følg den til punkt og prikke.
2. docs/notabene.md — stemmebiblen, §§2–5.
3. data/context/generated/captions-trial/drafts/b127-ill_14.json — godkendt forbillede for form, sources-granularitet og note-niveau.
4. Grounding-pakken: data/context/grounding/captions/b1-ill_2.md
5. Billedet: data/vendor/b1/ill_2.jpg (brug Read — det er multimodalt).
Skriv derefter udkastet som JSON til data/context/generated/captions/drafts/b1-ill_2.json. Dit svar til mig er kun slugget + én linje om tvivlens omfang.
```

---

## Genudkast efter ill_15-fundet (pakken rummer brev 136 OG 146)

*Task-kald »Genudkast caption b127/ill_15«, 2026-08-26T15:56:57Z.*

```
Du er udkastagent i billedtekst-runden for epistel. Arbejd fra repo-roden /Users/maria/playground/epistel. Læs i denne rækkefølge:
1. data/context/generated/captions/drafter-prompt.md — din instruks; følg den til punkt og prikke.
2. docs/notabene.md — stemmebiblen, §§2–5.
3. data/context/generated/captions-trial/drafts/b127-ill_14.json — godkendt forbillede for form, sources-granularitet og note-niveau.
4. Grounding-pakken: data/context/grounding/captions/b127-ill_15.md — bemærk: pakken indeholder BÅDE brev 136 (kortet øverst) og brev 146 (kortet nederst), som udgavens head selv nævner.
5. Billedet: data/vendor/b127/ill_15.jpg (brug Read — det er multimodalt).
Skriv derefter udkastet som JSON til data/context/generated/captions/drafts/b127-ill_15.json. Dit svar til mig er kun slugget + én linje om tvivlens omfang.
```

---

## Genudkast for ill_k7 (brev 189/190-forbindelsen)

*Task-kald »Genudkast caption b171/ill_k7«, 2026-08-26T15:57:00Z.*

```
Du er udkastagent i billedtekst-runden for epistel. Arbejd fra repo-roden /Users/maria/playground/epistel. Læs i denne rækkefølge:
1. data/context/generated/captions/drafter-prompt.md — din instruks; følg den til punkt og prikke.
2. docs/notabene.md — stemmebiblen, §§2–5.
3. data/context/generated/captions-trial/drafts/b127-ill_14.json — godkendt forbillede for form, sources-granularitet og note-niveau.
4. Grounding-pakken: data/context/grounding/captions/b171-ill_k7.md — bemærk: pakken indeholder både brev 189 (som udgavens head nævner: »Forsiden af Brev 189«) og brev 190; brug den forbindelse ærligt.
5. Billedet: data/vendor/b171/ill_k7.jpg (brug Read — det er multimodalt).
Skriv derefter udkastet som JSON til data/context/generated/captions/drafts/b171-ill_k7.json. Dit svar til mig er kun slugget + én linje om tvivlens omfang.
```

---

## Parret planche: k10 (b241+b259, dubletten)

*Task-kald »Udkast caption k10-parret«, 2026-08-26T16:02:04Z.*

```
Du er udkastagent i billedtekst-runden for epistel. Arbejd fra repo-roden /Users/maria/playground/epistel. Læs i denne rækkefølge:
1. data/context/generated/captions/drafter-prompt.md — din instruks; følg den til punkt og prikke, især særtilfældet »én planche, to id'er«.
2. docs/notabene.md — stemmebiblen, §§2–5.
3. data/context/generated/captions-trial/drafts/b127-ill_14.json — godkendt forbillede for form, sources-granularitet og note-niveau.
4. Grounding-pakken: data/context/grounding/captions/b241-ill_k10+b259-ill_k10.md — de to id'er er byte-identiske filer; `b241/ill_k10.jpg` refereres INGEN steder i udgaven og skal stå caption-løst (caption null + begrundelse i note), mens `b259/ill_k10.jpg` får sin caption grounded i sit brev.
5. Billedet: data/vendor/b259/ill_k10.jpg (identisk med b241-kopien; brug Read — det er multimodalt).
Skriv udkastet som ÉN JSON-fil med formen `ids` (liste) + fælles `alt` + `captions` (objekt id → caption/null) til data/context/generated/captions/drafts/b241-ill_k10+b259-ill_k10.json. Dit svar til mig er kun slugget + én linje om tvivlens omfang.
```

---

## Id uden forekomster: b79/ill_k4 (den forældreløse — alt-tekst alene)

*Task-kald »Udkast alt-tekst b79/ill_k4«, 2026-08-26T16:15:03Z.*

```
Du er udkastagent i billedtekst-runden for epistel. Arbejd fra repo-roden /Users/maria/playground/epistel. Læs i denne rækkefølge:
1. data/context/generated/captions/drafter-prompt.md — din instruks; følg den til punkt og prikke, især særtilfældet »id uden forekomster«.
2. docs/notabene.md — stemmebiblen, §§2–5.
3. data/context/generated/captions-trial/drafts/b127-ill_14.json — godkendt forbillede for form, sources-granularitet og note-niveau.
4. Grounding-pakken: data/context/grounding/captions/b79-ill_k4.md — dette billede refereres INGEN steder i udgaven: caption er null med begrundelse i note; alt-teksten skrives ud fra billedet selv (eneste tilladte grounding sammen med proveniensrækken).
5. Billedet: data/vendor/b79/ill_k4.jpg (brug Read — det er multimodalt).
Skriv derefter udkastet som JSON til data/context/generated/captions/drafts/b79-ill_k4.json. Dit svar til mig er kun slugget + én linje om tvivlens omfang.
```

---

## Parret planche: ill_24 (b308+b79, kompositplanchen — én caption pr. id)

*Task-kald »Udkast caption ill_24-parret«, 2026-08-26T16:15:17Z.*

```
Du er udkastagent i billedtekst-runden for epistel. Arbejd fra repo-roden /Users/maria/playground/epistel. Læs i denne rækkefølge:
1. data/context/generated/captions/drafter-prompt.md — din instruks; følg den til punkt og prikke, især særtilfældet »én planche, to id'er«.
2. docs/notabene.md — stemmebiblen, §§2–5.
3. data/context/generated/captions-trial/drafts/b127-ill_14.json — godkendt forbillede for form, sources-granularitet og note-niveau.
4. Grounding-pakken: data/context/grounding/captions/b308-ill_24+b79-ill_24.md — én komposit-planche, to id'er: øverst brev 317 (b308-id'ets kontekst), nederst brev 119 (b79-id'ets kontekst). Fælles alt; én caption PR. id, hver grounded i sit eget brev (Marias kald: gerne forskellige captions).
5. Billedet: data/vendor/b308/ill_24.jpg (identisk med b79-kopien; brug Read — det er multimodalt).
Skriv udkastet som ÉN JSON-fil med formen `ids` (liste) + fælles `alt` + `captions` (objekt id → caption) til 'data/context/generated/captions/drafts/b308-ill_24+b79-ill_24.json'. Dit svar til mig er kun slugget + én linje om tvivlens omfang.
```

---

## Blomster-vignetten (andet few-shot-forbillede: prøverundens kikkert)

*Task-kald »Udkast caption blomster-vignetten«, 2026-08-26T16:15:21Z.*

```
Du er udkastagent i billedtekst-runden for epistel. Arbejd fra repo-roden /Users/maria/playground/epistel. Læs i denne rækkefølge:
1. data/context/generated/captions/drafter-prompt.md — din instruks; følg den til punkt og prikke.
2. docs/notabene.md — stemmebiblen, §§2–5.
3. data/context/generated/captions-trial/drafts/vignet-kikkert.json i data/context/generated/captions-trial/drafts/ — det NÆRMESTE forbillede: prøverundens caption til den anden delte vignet (kikkerten). Læs også b127-ill_14.json for sources/note-niveau.
4. Grounding-pakken: data/context/grounding/captions/vignet-vig-brev-blomst.md
5. Billedet: data/vendor/vignet/vig-brev-blomst.jpg (brug Read — det er multimodalt).
Skriv derefter udkastet som JSON til data/context/generated/captions/drafts/vignet-vig-brev-blomst.json. Dit svar til mig er kun slugget + én linje om tvivlens omfang.
```

---

## The waves

34 drafting calls across four waves (36 manifest ids — the two pair
packets each cover two), reconstructed from the transcript's call order:

- **Wave 1**, 15:46:21-15:46:44: b1-ill_2, b1-ill_3, b1-ill_4,
  b1-ill_k1, b1-ill_k2, b120-ill_12, b120-ill_31, b120-ill_32
- **Wave 2**, 15:53:16-15:53:38: b127-ill_13, b127-ill_15, b171-ill_16,
  b171-ill_17, b171-ill_18, b171-ill_19, b171-ill_k7, b208-ill_20 —
  plus two redrafts 15:56-15:57 (ill_15 and ill_k7, after the
  two-letter packet finding)
- **Wave 3**, 16:01:57-16:02:23: b208-ill_k8, b241-ill_k10+b259-ill_k10
  (pair), b241-ill_k9, b259-ill_21, b276-ill_22, b276-ill_23, b43-ill_5,
  b43-ill_6
- **Wave 4**, 16:14:43-16:15:21: b70-ill_7, b70-ill_8, b79-ill_9,
  b79-ill_10, b79-ill_11, b79-ill_k4 (alt only, orphan),
  b79-ill_k5, b79-ill_k6, b308-ill_24+b79-ill_24 (pair),
  vignet-vig-brev-blomst

The doktor-runde's two overlap-reader calls (18:21) were not a drafting
wave; see `verification/doktor-runden/`.
