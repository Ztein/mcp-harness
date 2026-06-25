# T013 — transkript-skrivare som injicerbar sink

**Status:** TODO · **Fas:** 1 · **Prioritet:** P2 · **Beror på:** T011

## Varför

Människo-transkriptet skrivs idag via fria `_w(tr, ...)`-anrop inflätade i loopen.
När motorn (T011) producerar strukturerade händelser bör transkriptet bli en
**konsument** av de händelserna — en sink — i stället för en parallell kodväg.
Då kan vi testa transkript-formatet isolerat och garantera att det stabila,
parsbara `⚙ namn(args-json)`-formatet bevaras (PRD §11 P2).

## Omfattning

**Ingår:** en transkript-sink som tar motorns händelser och skriver människo-
läsbar Markdown; bevara `👤/🤖/⚙`-formatet och `⚙ namn(args-json)`-raden som
äldre parsers kan förlita sig på. Trunkering (`…`) är tillåten **endast** i denna
människo-vy — aldrig i datat (det är T020:s domän).

**Ingår inte:** JSONL-loggen (T020).

## Definition of Done

- [ ] Transkript-sinken matas av motorns händelser, inte av egna inline-anrop.
- [ ] `⚙ namn(args-json)`-formatet bevaras tecken-för-tecken (parsbart).
- [ ] Trunkering i människo-vyn är synlig (`…`) och dokumenterad som vy-only.
- [ ] Sinken är testbar utan att starta en riktig körning.

## Testfall (skriv först)

1. `test_transcript_renders_tool_call_format` → en tool_call-händelse →
   `⚙ namn(args-json)`-raden matchar exakt.
2. `test_transcript_truncates_long_result_with_ellipsis` → långt svar → vyn
   klipper med `…`, och det är enda stället trunkering sker.
3. `test_transcript_roles_rendered` → user/assistant-händelser → `👤`/`🤖`-rubriker.

## Noteringar

Detta är polering, inte kontraktsyta — därför P2. Den riktiga kontraktsytan för
maskiner är JSONL (T020). Gör inte transkriptet ”smart”; håll det dumt och stabilt.
