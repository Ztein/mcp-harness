# T025 — non-interaktiv verktygsdump (`--list-tools`)

**Status:** DONE · **Fas:** 2 · **Prioritet:** P3 (LÅG) · **Beror på:** T021, T030

## Varför

Extern feedback från use-case-mcp-konsumenten (se
[mcp-harness-feedback.md](../mcp-harness-feedback.md), F4). Bannern ger *antal*
verktyg och `/tools` finns interaktivt — men i en **scriptad** körning
(`printf … | mcp-harness`) går det inte att enkelt fånga hela verktygsytan till
körningsloggen. Konsumenten vill kunna **versionsstämpla "vilken yta testades"**:
exakt vilka verktyg modellen såg, med namn, beskrivning och parametrar, vid den
tidpunkt en regressionskörning gav PASS/FAIL.

JSONL-headern (T020) täcker redan delar: den listar verktygs-*namn* och ett
`tools_fingerprint` (hash av namn+beskrivning+schema). Det svarar på *"ändrades
ytan?"* men inte på *"vad bestod ytan av, i klartext?"* — fingeravtrycket går inte
att packa upp till läsbara beskrivningar/parametrar. T025 stänger den luckan.

## Omfattning

**Ingår:**
- En flagga `--list-tools` som: ansluter → skriver ut **hela verktygsschemat**
  (namn, beskrivning, input-schema/parametrar) → avslutar. Inga turer, ingen LLM.
- `--json` ger maskinläsbar dump; utan den en kort människo-läsbar lista.
- Respekterar allowlist/scoping (`--tools`) och multi-server (T030) — dumpen visar
  exakt den meny modellen *skulle* sett, inte serverns råa yta.
- Återanvänd `tools_fingerprint`-beräkningen så dump och header är samstämmiga.

**Ingår inte:** att alltid bädda in fullt schema i JSONL-headern (hålls smal —
namn + fingeravtryck räcker där; den som vill ha klartext kör `--list-tools`).

## Definition of Done

- [x] `--list-tools` ansluter, skriver schemat och avslutar rent (exit 0).
- [x] `--list-tools --json` ger en post per verktyg med namn, beskrivning och
      input-schema.
- [x] Dumpen respekterar `--tools`-scoping och multi-server.
- [x] Inget LLM-anrop sker i detta läge.

## Testfall (skriv först)

1. `test_list_tools_dumps_full_schema` → mot fejk-MCP → utdatan innehåller varje
   verktygs namn + beskrivning + parametrar.
2. `test_list_tools_json_is_parseable` → `--json` → giltig JSON, en post/verktyg.
3. `test_list_tools_respects_scoping` → med `--tools echo` → bara `echo` dumpas.
4. `test_list_tools_no_llm_call` → fejk-LLM som failar vid anrop → läget anropar
   den aldrig.
5. `test_list_tools_exit_clean` → exit 0, ingen interaktiv prompt.

## Noteringar

Verktygslistan hämtas redan i [cli.py:199](../../src/mcp_harness/cli.py) för
fingeravtrycket — bygg dumpen ovanpå samma `list_tools()`-anrop. Låg prio:
fingeravtrycket fångar redan *att* ytan ändrats; det här är klartext-bekvämlighet
för loggning, så vänta gärna tills konsumenten faktiskt behöver den.
