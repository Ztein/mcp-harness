# T020 — JSONL-körlogg, versionerat schema, otrunkerat

**Status:** DONE · **Fas:** 2 · **Prioritet:** P0 · **Beror på:** T011

## Varför

Test-agentens **första** P0 (PRD §11): den regex-skrapar idag människo-
transkriptet för att dra ut verktygsanrop och döma — sprött och förlustfullt.
Den behöver en maskinläsbar JSONL-logg parallellt med transkriptet: en rad per
händelse, med **fullständiga** args och **otrunkerade** svar. Detta är produktens
verkliga kontraktsyta — den måste vara versionerad och stabil.

## Omfattning

**Ingår:** en JSONL-sink (konsument av T011:s händelser) som skriver en rad per
händelse: `user_turn`, `tool_call` (namn + fulla args), `tool_result`
(otrunkerat), `assistant_text`, `usage`/latens, `error`. Varje rad har ett
`schema_version`-fält. En körnings-header-rad med modell, params, MCP-URL,
server-fingeravtryck (fylls av T021), profil (av T031). `--jsonl <fil>`-flagga.

**Ingår inte:** server-fingeravtryck-beräkningen (T021), profil-fältet (T031) —
men fälten reserveras i schemat nu.

## Definition of Done

- [x] `--jsonl <fil>` skriver giltig JSONL (en JSON per rad, går att `json.loads`
      rad-för-rad).
- [x] Varje rad bär `schema_version` och `type`.
- [x] `tool_call`-rader bär **fullständiga** args; `tool_result`-rader bär
      **otrunkerat** svar — verifierat med ett svar längre än människo-vyns klipp.
- [x] Loggen flushas löpande (en avbruten körning lämnar läsbara rader).
- [x] Schemat dokumenteras i `DOCS/` eller `docs/jsonl-schema.md` och versioneras.

## Testfall (skriv först)

1. `test_jsonl_one_object_per_line` → kör en flertur mot fejk-LLM+MCP → varje rad
   parsar som JSON.
2. `test_jsonl_tool_result_untruncated` → verktygssvar > klipp-gränsen → JSONL-
   raden innehåller HELA svaret medan transkriptet (T013) klipper.
3. `test_jsonl_tool_call_full_args` → stort args-objekt → JSONL bär det oavkortat.
4. `test_jsonl_has_schema_version` → varje rad har `schema_version`.
5. `test_jsonl_flushed_incrementally` → läs filen mitt i en körning → tidigare
   rader finns redan på disk.

## Noteringar

Detta är den **versionerade kontraktsytan** test-agenten bygger sin loop på —
ändra aldrig fältbetydelse utan att bumpa `schema_version`. Skriv schema-doc:en
som en del av ticketen, inte efteråt.
