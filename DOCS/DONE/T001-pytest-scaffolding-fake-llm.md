# T001 — pytest-scaffolding + fejk-LLM över riktig HTTP

**Status:** DONE · **Fas:** 0 · **Prioritet:** P0 · **Beror på:** —

## Varför

Det finns inga tester. Innan en enda funktion läggs till måste vi kunna köra
strikt TDD. Det första vi behöver är ett sätt att testa `llm.py` **på riktigt** —
inte genom att mocka bort `urllib`, utan genom att starta en faktisk HTTP-server
som svarar med canned OpenAI-kompatibel JSON. Då exekveras hela kodvägen
(request-bygge, headers, proxy-hantering, retry, JSON-parse) — precis enligt
PRD §8.3 (fail-hard) och §11 (testa på riktigt).

## Omfattning

**Ingår:** `pytest` + `pytest-asyncio` i en `[dependency-groups]`/`dev`-grupp i
`pyproject.toml`; en `tests/`-mapp; en återanvändbar fejk-LLM-fixtur som startar
en riktig `http.server` på en ledig port och returnerar köade svar; tester för
`chat_completion` och `_require`.

**Ingår inte:** fejk-MCP-servern (T002), CI (T003).

## Definition of Done

- [ ] `uv run pytest` kör grönt lokalt.
- [ ] Dev-beroenden deklarerade i `pyproject.toml` (ingen global pip-install krävs).
- [ ] Fejk-LLM-fixturen startar en **riktig** socket-lyssnande server, köar svar
      och returnerar URL:en som sätts i `LLM_BASE_URL` — ingen `unittest.mock` av
      `urllib` förekommer i `llm`-testerna.
- [ ] Fixturen registrerar varje inkommen request (body + headers) så testen kan
      assert:a på vad som faktiskt skickades.

## Testfall (skriv först)

1. `test_chat_completion_returns_full_response` → fejk-LLM svarar med `usage` +
   `choices`; `chat_completion` returnerar HELA dicten inkl. `usage`.
2. `test_chat_completion_sends_bearer_and_model` → assert:a på att servern fick
   `Authorization: Bearer <key>` och rätt `model` i body.
3. `test_tools_set_tool_choice_auto` → när `tools=[...]` skickas ska body
   innehålla `tool_choice: "auto"`.
4. `test_require_missing_env_exits_loudly` → utan `LLM_MODEL` → `SystemExit` med
   ett meddelande som nämner variabeln (fail-hard, princip 2).
5. `test_retry_then_success` → servern failar 2 ggr (connection reset), lyckas på
   3:e; `chat_completion(max_retries=3)` returnerar svaret; stderr nämner försöken.
6. `test_retry_exhausted_raises` → servern failar alltid → sista exception
   propageras (sväljs inte).

## Noteringar

Använd `monkeypatch.setenv` för `LLM_*`. Lediga porten: bind `("127.0.0.1", 0)`
och läs ut tilldelad port. Kör servern i en daemon-tråd; stäng i fixturens teardown.
