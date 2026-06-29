# T026 — typmedvetna LLM-fel + `--timeout`

**Status:** DONE · **Fas:** 2 · **Prioritet:** P2 · **Beror på:** T011, T023

## Varför

Extern feedback (F5) från use-case-mcp-konsumenten: harnessens LLM-felmeddelande
fungerar men kan bli vassare för agent-/regressionskörning. Två konkreta brister:

1. **Feltyperna skiljs inte åt handlingsbart.** `TurnError` är idag bara
   `"LLM-anrop misslyckades: <rå exception>"` ([engine.py](../../src/mcp_harness/engine.py)).
   En timeout, en 401 och ett 5xx ser nästan likadana ut, utan vägledning
   ("kontrollera LLM_BASE_URL/last").
2. **Vi retrar fel som inte borde retras.** `urllib.error.HTTPError` ärver
   `URLError`, så `except (TimeoutError, URLError, ConnectionError)`
   ([llm.py](../../src/mcp_harness/llm.py)) fångar även **401/403/4xx** — en
   felaktig nyckel retras 3 gånger i onödan. Plus: default-timeout (120 s i CLI)
   ger lång tyst väntan innan fail, och går inte att styra.

## Omfattning

**Ingår:**
- **Klassificera felet** i `llm.py`: timeout / auth(4xx) / 5xx-server /
  connection — var och en med en kort handlingsbar rad.
- **Faila snabbt på icke-transienta fel** (4xx utom 408/429): ingen retry-loop på
  en felaktig nyckel/parameter. Retry kvar för timeout / 5xx / 408 / 429 /
  connection.
- En egen `LlmError` vars meddelande är färdig-kurerat; `run_turn` använder det
  verbatim i `TurnError` (ingen dubbel generisk prefix).
- **`--timeout <sek>`-flagga + kortare default** (60 s) så agent-/regressionskörning
  failar snabbare och tydligare.

**Ingår inte:** mer retry (vi har redan 3 försök — det efterfrågade är *snabbare/
tydligare fail*, inte mer retry). Per-tool-anrop-latens (avförd F2-rest).

## Definition of Done

- [x] 4xx-auth (401/403) failar **utan** retry, med en rad som pekar på
      `LLM_API_KEY`/behörighet.
- [x] Timeout/5xx/connection retras och failar med typspecifik, handlingsbar rad
      (timeout → `LLM_BASE_URL`/last; connection → nätverk/proxy).
- [x] `--timeout` styr per-anrops-timeouten; default kortare än tidigare (60 s).
- [x] `TurnError` bär det kurerade meddelandet verbatim.
- [x] Inga regressioner i befintlig retry-väg (5xx retras fortfarande).

## Testfall (skriv först)

1. `test_auth_4xx_fails_fast_no_retry` → kö ett 401, högt max_retries → reser
   `LlmError`, och **bara ett** request gjordes.
2. `test_auth_message_actionable` → 401-meddelandet nämner `LLM_API_KEY`.
3. `test_5xx_still_retried` → 503 ×2 + ok → lyckas (ingen regression).
4. `test_5xx_exhausted_actionable` → 503 ×N → `LlmError` med server-/försök-rad.
5. `test_timeout_message_actionable` → klassificeraren ger en timeout-rad som
   nämner `LLM_BASE_URL` (ren funktion, ingen flakig timing).
6. `test_turn_error_carries_curated_message` → en llm som reser `LlmError` →
   `TurnError.message` är det kurerade, utan generisk prefix.

## Noteringar

`except HTTPError` måste stå **före** `except URLError` (subklass). Behåll
stderr-raden per försök (T161). Testa mot `fake_llm` (riktig HTTP), hoppa över
`time.sleep` som befintliga retry-tester gör.
