# T012 — full verktygssvars-trohet: konkatenera ALLA content-block

**Status:** TODO · **Fas:** 1 · **Prioritet:** P0 (buggfix) · **Beror på:** T011

## Varför

[cli.py:162](../../src/mcp_harness/cli.py) läser bara `result.content[0].text`.
Ett MCP-verktygssvar kan bestå av **flera** content-block; allt utom det första
tappas tyst. Det bryter direkt mot test-agentens P1 ”Full verktygssvars-trohet”
(PRD §11): dömning sker ofta på fält (`id`, `status`, `missing`) som kan ligga i
ett senare block. Detta är en tyst förlust — exakt det fail-loudly förbjuder.

## Omfattning

**Ingår:** konkatenera text ur **alla** content-block; hantera icke-text-block
(t.ex. bild/resurs) på ett ärligt, icke-tappande sätt (representera dem, släng
dem inte tyst); bevara strukturerat/JSON-innehåll så det går att assert:a på fält.

**Ingår inte:** multimodal vidaresändning till modellen (det är T032).

## Definition of Done

- [ ] Alla text-block i ett verktygssvar når både motor-händelsen och det som
      matas tillbaka till modellen.
- [ ] Tomt svar hanteras explicit (t.ex. `"(tomt)"`) — ingen `IndexError`.
- [ ] Icke-text-block tappas inte tyst; de representeras (åtminstone som en not).
- [ ] Befintligt enkel-block-beteende oförändrat (regression täckt).

## Testfall (skriv först)

1. `test_multi_block_concatenated` → mot fejk-MCP `multi_block()` (T002): svaret
   som motorn ger innehåller text från **alla** block, i ordning.
2. `test_single_block_unchanged` → `echo` ger exakt sin text (ingen regression).
3. `test_empty_content_safe` → verktyg med tomt content → ingen krasch, explicit
   markör.
4. `test_structured_result_fields_accessible` → `structured()` → JSON-fält går
   att läsa ut ur svaret (PRD §11 fält-assertion).

## Noteringar

Skriv test 1 FÖRST och se det faila mot nuvarande `content[0]`-kod — det bevisar
att buggen finns innan den fixas. Det är poängen med ticketen.
