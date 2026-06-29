# T024 — verktygsfel i sammanfattning + grindbart utfall

**Status:** DONE · **Fas:** 2 · **Prioritet:** P1 · **Beror på:** T022

## Varför

Extern feedback från use-case-mcp-konsumenten (se
[mcp-harness-feedback.md](../mcp-harness-feedback.md), F3) bad om att kunna grinda
på "gick körningen igenom?" i batch/CI — inklusive **verktygsfel**. Idag räknar
`RunSummary` bara `failed_turns` (en tur vars *sista* händelse är `TurnError`).
Ett hanterat verktygsfel (`tool_result.is_error == true`) räknas **inte** alls:
det syns varken i sammanfattningsraden eller i exit-koden. En körning där varje
tool-anrop felade men modellen ändå svarade i text blir alltså grön — vilket
direkt motsäger vad konsumenten bad om ("antal tool-fel" i summeringen och
"exit-kod som blir non-zero vid tool-fel").

## Omfattning

**Ingår:**
- Räkna **tool-fel** (`ToolResult.is_error`) i `RunSummary` (nytt fält, t.ex.
  `tool_errors`).
- Visa antalet i enrads-sammanfattningen ([engine.py:48](../../src/mcp_harness/engine.py)).
- Exit-kod blir `≠0` även när tool-fel förekom — men **separerbart** från
  slutligt misslyckade turer, så CI kan välja policy.

**Designval att bestämma (öppen fråga från F3):** ska tool-fel *alltid* grinda
körningen rött, eller bara via en opt-in-flagga (t.ex. `--fail-on-tool-error`)?
Default-förslag: tool-fel **rapporteras alltid** i summeringen, men grindar
exit-koden bara med flaggan satt — så att dagens beteende (modellen får hantera
ett verktygsfel och gå vidare) inte tyst bryts för befintliga användare.

**Ingår inte:** per-tool-anrop-latens (egen ticket), ändring av JSONL-schemat
utöver att `is_error` redan finns där.

## Definition of Done

- [x] `RunSummary` har ett `tool_errors`-fält som räknar `is_error`-resultat.
- [x] Enrads-sammanfattningen rapporterar antal tool-fel.
- [x] `--fail-on-tool-error` (eller motsv.) gör exit-koden `≠0` vid ≥1 tool-fel;
      utan flaggan är dagens exit-beteende oförändrat.
- [x] Sammanfattning och exit-kod är samstämmiga.

## Testfall (skriv först)

1. `test_tool_error_counted_in_summary` → tur med ett `is_error`-resultat →
   summeringen rapporterar 1 tool-fel.
2. `test_tool_error_does_not_gate_by_default` → tool-fel men textsvar →
   utan flaggan exit 0.
3. `test_fail_on_tool_error_flag_gates` → samma körning med
   `--fail-on-tool-error` → exit ≠0.
4. `test_summary_and_exit_consistent` → ingen "exit 0 + 1 tool-fel grindat".

## Noteringar

`is_error` finns redan på `ToolResult` (T012) och i JSONL (T020) — det här
handlar om att *aggregera och exponera* det, inte om ny instrumentering. Testa
exit-koden via subprocess mot CLI:t, som i T022.
