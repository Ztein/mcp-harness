# T011 — bryt ut agent-loopen till en testbar motor

**Status:** TODO · **Fas:** 1 · **Prioritet:** P0 · **Beror på:** T010

## Varför

Hjärtat i harnessen är loopen: skicka meddelanden → modellen ber om verktyg →
kör verktyg → mata tillbaka → upprepa tills textsvar. Idag är den inflätad i
`main()` med `input()`/`print()` och kan inte testas. Vi bryter ut den till en
motor som tar in injicerbara beroenden (en ”LLM-callable” och en `ClientSession`)
och returnerar/strömmar strukturerade händelser. Detta är förutsättningen för
ALLT i Fas 2 (JSONL-logg, exit-kod, loop-broms bygger på denna motor).

## Omfattning

**Ingår:** en `run_turn(session, llm, messages, oai_tools) -> TurnResult`-motor
(eller motsvarande) som:
- anropar `llm`, hanterar `tool_calls`, kör `session.call_tool`, matar tillbaka,
  loopar tills textsvar;
- yield:ar/samlar strukturerade händelser (user_turn, tool_call, tool_result,
  assistant_text, error) — inte print-strängar;
- är fri från `input()`/`print()` (I/O ligger kvar i `cli()`).

**Ingår inte:** JSONL-serialisering (T020), broms/tak (T023) — men motorn ska
vara formad så de kan hängas på utan omskrivning.

## Definition of Done

- [ ] Motorn testas helt med fejk-LLM (T001) + fejk-MCP (T002), utan TTY.
- [ ] Den producerar strukturerade händelser med **fullständiga** args och svar
      (ingen trunkering i datamodellen — trunkering är enbart en vy-angelägenhet).
- [ ] Ett verktygsfel blir en `tool_result`-händelse med felet, loopen fortsätter
      som idag (inte en krasch).
- [ ] `main()`/`cli()` bygger sin människo-utskrift ovanpå motorns händelser.

## Testfall (skriv först)

1. `test_plain_text_turn` → LLM svarar utan tool_calls → en `assistant_text`-
   händelse, inga verktygsanrop.
2. `test_single_tool_call_then_text` → LLM ber om `echo`, sedan text → händelse-
   sekvens: tool_call(echo) → tool_result("hej") → assistant_text.
3. `test_chained_tool_calls` → LLM ber om verktyg två turer i rad innan text →
   båda körs i ordning.
4. `test_tool_error_is_event_not_crash` → LLM ber om `boom` → `tool_result` bär
   felet; loopen avslutas rent med modellens efterföljande text.
5. `test_full_args_preserved` → tool_call-händelsen innehåller exakt de args LLM
   skickade (ingen förlust).

## Noteringar

Designa returtypen som datat T020 (JSONL) och T022 (sammanfattning) behöver —
tänk på kontraktsytan redan här, men serialisera inte ännu.
