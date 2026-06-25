# T023 — tur-loop-broms + batch-resiliens

**Status:** DONE · **Fas:** 2 · **Prioritet:** P1 · **Beror på:** T011, T022

## Varför

Två P1 från test-agenten (PRD §11):
1. **Tur-loop-broms** — en modell som loopar (ber om verktyg i all oändlighet)
   får inte hänga en obevakad batch-körning. Det behövs ett tak på verktygsanrop
   per tur.
2. **Batch-resiliens** — i en lång piped fler-protokoll-körning får ETT slutligt
   LLM-fel inte tyst korrumpera resten av batchen; det ska loggas och hanteras
   (fortsätt nästa tur, eller avbryt rent med kod).

## Omfattning

**Ingår:**
- `--max-tool-calls-per-turn N` (rimlig default): när taket nås avbryts turen
  högljutt — händelse i JSONL, fel i sammanfattningen, påverkar exit-koden (T022).
- Definierat batch-beteende vid slutligt LLM-fel mitt i en pipe: logga felet som
  `error`-händelse, markera turen misslyckad, fortsätt med nästa tur (resten av
  batchen förblir tolkbar). Exit≠0 vid avslut om någon tur föll.

**Ingår inte:** retry-policyn inuti `chat_completion` (finns redan i llm.py).

## Definition of Done

- [x] Taket är konfigurerbart och har en default; att nå det är ett **högljutt**
      fel (ingen tyst trunkering av loopen).
- [x] Ett slutligt LLM-fel på tur k korrumperar inte tur k+1…n: efterföljande
      turer körs och loggas tolkbart.
- [x] Både broms och batch-fel reflekteras i exit-koden (T022) och sammanfattningen.

## Testfall (skriv först)

1. `test_tool_call_cap_trips_loudly` → fejk-LLM ber alltid om ett verktyg → vid
   taket: `error`-händelse + turen markeras misslyckad, ingen oändlig loop.
2. `test_cap_is_configurable` → `--max-tool-calls-per-turn 2` → exakt 2 anrop
   tillåts innan brytning.
3. `test_batch_continues_after_midstream_error` → 3 turer, tur 2 ger slutligt
   LLM-fel → tur 1 och 3 loggas korrekt; tur 3 påverkas inte.
4. `test_batch_failure_sets_exit_nonzero` → någon tur föll → exit≠0 (via T022).

## Sett i verkligheten (repro, 2026-06-25)

Batch-resiliens-delen är inte teoretisk — den **hände** under en skarp körning hos
konsumenten (use-case-mcp, T180): en 4-turs piped körning där tur 4:s LLM-anrop
**timeoutade** (read timeout, efter att `llm.py`:s retries var uttömda). Resultatet:

- Turen avbröts; transkriptet fick en `⚠️ Fel`-rad men **ingen** efterföljande
  åtgärd (tur 4 var DoD-write-back-steget, som därför aldrig kördes).
- Inget exit≠0, ingen maskinläsbar `error`-händelse → test-agenten upptäckte det
  bara genom att **manuellt** läsa transkriptet och se att kommentaren saknades, och
  fick köra om steget separat.

Exakt det T023 ska fixa: felet ska bli en `error`-händelse (T020), markera turen
misslyckad, och sätta exit≠0 (T022) — så att en obevakad batch inte tyst lämnar ett
ofullständigt resultat som ser klart ut. **Använd detta som acceptans-repro:** en
pipe där en mitt-i-tur timeoutar ska sluta tolkbart och rött, inte tyst trunkerat.

## Noteringar

Detta är backstop-disciplin för obevakade körningar — själva poängen med att
test-agenten vågar köra långa pipes. Defaulten ska vara generös men ändlig.
