# Doktor-runden — the full round

Maria's manual review of the full round's 34 verified draft packets
(2026-08-26, 18:19–20:23), reconstructed 2026-08-27 from the session
transcript on her machine. Her words are quoted verbatim (Danish,
lowercase and typos included); the framing is the arbitrator's. The
round's re-verification files sit in `verification/doktor-runden/`; the
resulting edits are logged per draft in the `repairs` fields.

## Her review — one finding, one delegation, five favourites (18:19)

> det var en meget nem doktorrunde. nogle vidunderlige ironiske
> guldklumper undervejs:
>
> "»Ferdinand skriver formodentlig et Par Ord paa den anden Side.« Og på
> den modstående side står de — »Kiære Peter!«, skrevet med en anden
> hånd."
>
> "Molbech regner sig selv til »de procrastinerende Naturer« og skriver
> til Kierkegaard, at denne billet slet ikke er noget svar. Alligevel
> fylder den hele siden ud, ned til det enkelte »M.« nederst."
>
> "Kierkegaards signet, trykket i rød lak på brev 89 til Emil Boesen:
> »Alt bliver imellem os, Du veed jeg ynder ikke Folkesnak.« Lakken er
> brudt, og papiret omkring den er revet."
>
> "Indbydelsen, som Emil Boesen skrev den: bryllup i Frue Kirke onsdag
> den 1. maj, klokken 6 »(eller 7)«. »Jeg kommer ikke selv«, skriver
> han, for han er »blevet dygtig forkjølet«. Brevet slutter midt på
> arket."
>
> "»Blomsten selv har endda ikke taget mig saa megen Tid, men Bladet ved
> den«, skriver Søren om tegningen, der lå indlagt i brev 178 til hans
> niece Henriette Lund. Bladets streger ligger da også i lag."
>
> det eneste deciderede issue jeg er stødt på:
>
> b171/ill_k7.jpg
> "Den 31. januar vælger han »atter« papir af lignende art; det skal
> minde Michael om, at onklen er i Berlin." – har der lige sneget sig en
> reference til et fremtidigt brev ind?
>
> der er enkelte steder lidt lange resumeer af brevene som muligvis kan
> konkurrere med de egentlige resumeer. det tror jeg godt du kan sætte
> en agent eller to i gang med at undersøge. hvis overlapningen er for
> stor, vil jeg gerne have dem forkortet – ellers kan de blive.

The five "guldklumper" are quotes of the drafts' own captions — her
delight, not corrections.

## The outcomes

**ill_k7 — her finding, confirmed.** The flagged sentence had indeed
told letter 190 under letter 189's plate (the packet held both letters
on purpose; the caption crossed between them). Repaired by pure
deletion, logged in the draft's `repairs` as her find.

**The overlap question — her delegation, the arbitrator's execution.**
Two readers measured all 34 captions against the letter summaries in
`summaries.json`: 15 HIGH, 7 MODERATE, rest LOW — overlap arising
systematically where a letter is so short that image anchor and summary
cannot help meeting. Under her instruction ("hvis overlapningen er for
stor, vil jeg gerne have dem forkortet – ellers kan de blive"), 14 of
the 15 HIGH captions were shortened against the image. The readers'
prompts and full reports are archived in `overlap-readers.md`; the
pre-shortening wording is the drafts' state at commit 1f538a0, the
arbitrator's compressions (including the three slips Codex then caught:
"skrive" -> "indlevere", the "Jettes hilsen" ambiguity, the dot count)
survive inside `verification/doktor-runden/`'s prompts, and the fixed
finals are the committed drafts.

**ill_11 — spared, and by whom.** The fifteenth HIGH caption, Boesen's
wedding invitation, was one of the five captions Maria had just quoted
with delight. The *arbitrator* (Claude Fable) chose to spare it under
her delegated instruction, citing her own words, and logged the
decision in the draft's `repairs`. For the record: Maria never named
ill_11 by id, and never ruled on it line by line — the sparing is an
arbitration under delegated mandate, not a direct ruling of hers. Her
later approval of the round is general.
