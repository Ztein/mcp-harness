# T033 — observerbarhet+ (token/latens, körnings-diff)

**Status:** TODO · **Fas:** 3 · **Prioritet:** P2 · **Beror på:** T020

## Varför

PRD §6.5 / Fas 4 + test-agentens P1 ”självbeskrivande körningar för regression”:
för att kunna lägga två körningar bredvid varandra och se vad som ändrades behövs
token-/latens-mätning per tur och en självbeskrivande körlogg (prompt, modell,
params, fingeravtryck, profil) — så en matris-rad är självförklarande och två
körningar kan diffas.

## Omfattning

**Ingår:** per-tur-latens och token-`usage` (från LLM-svaret) i JSONL; stöd för
`temperature`/`seed` där modellen tillåter och **registrera** dem i headern; ett
litet `diff`-hjälpmedel eller dokumenterat sätt att jämföra två JSONL-körningar.

**Ingår inte:** ett auto-domar-/metrics-ramverk (uttryckligt icke-mål, PRD §7).

## Definition of Done

- [ ] Varje tur loggar latens (ms) och token-`usage` när endpointen ger det.
- [ ] `temperature`/`seed` kan sättas och registreras i JSONL-headern.
- [ ] Två körningar med samma input är diff-bara på ett dokumenterat sätt
      (headern gör varje körning självbeskrivande).

## Testfall (skriv först)

1. `test_turn_records_latency` → varje tur-händelse bär en latens > 0.
2. `test_usage_recorded_when_present` → fejk-LLM returnerar `usage` → det hamnar i
   JSONL.
3. `test_seed_temperature_recorded` → sätt `--seed`/`--temperature` → värdena
   syns i headern och i request-body mot endpointen.
4. `test_two_runs_diffable` → två körningar → headers gör skillnaderna explicita.

## Noteringar

Stanna vid att *mäta och registrera* — döma gör människan eller agenten (PRD §7).
Mätningen får aldrig bli ett smygande domar-lager.
