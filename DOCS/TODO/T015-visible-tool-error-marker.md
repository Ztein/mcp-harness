# T015 — markera verktygsfel synligt i transkriptet (is_error)

**Status:** TODO · **Fas:** 1 · **Prioritet:** P1 · **Beror på:** T013

## Varför

Upptäckt i E2E-körning av scenario 03 (`scenarios/reports/03-fail-loudly.report.md`).
Ett verktygsfel renderas i människo-transkriptet som ett vanligt
`→ Error executing tool boom: …` — **samma prefix som ett lyckat svar**.
`ToolResult.is_error=True` finns i datat men vyn skiljer inte fel från framgång.
För en princip-3-produkt (fail-hard, aldrig tyst) ska ett fel *se ut* som ett fel.

## Omfattning

**Ingår:** `render_event` (och stdout-vyn i `cli.py`) markerar `ToolResult` med
`is_error=True` distinkt, t.ex. `→ ⚠️ <text>`. Endast presentation — datat
(events/JSONL) är oförändrat.

**Ingår inte:** ändrad felhantering i motorn (felet fångas redan korrekt).

## Definition of Done

- [ ] Ett verktygsfel renderas visuellt distinkt från ett lyckat svar i transkriptet.
- [ ] Samma distinktion i stdout-vyn.
- [ ] Lyckade svar oförändrade (regression täckt).

## Testfall (skriv först)

1. `test_transcript_marks_tool_error` → `ToolResult(is_error=True)` → renderingen
   innehåller felmarkören (t.ex. ⚠️); `is_error=False` gör det inte.

## Noteringar

Liten men viktig — det var den enda konkreta fail-loudly-bristen agent-testningen
hittade i Fas 1-koden.
