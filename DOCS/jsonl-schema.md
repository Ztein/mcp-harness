# JSONL-körlogg — schema

Den maskinläsbara kontraktsytan för agent-/regressionstestning (PRD §11). Skrivs
med `--jsonl <fil>`. **En JSON per rad**, UTF-8, flushad löpande. Varje rad bär
`schema_version` och `type`. Svar och args är **otrunkerade** (trunkering hör bara
hemma i människo-transkriptet).

**Aktuell version: `schema_version = 1`.** Fältbetydelse ändras aldrig utan att
versionen bumpas.

## Radtyper

### `run_header` (en gång, först)
| Fält | Typ | Beskrivning |
|------|-----|-------------|
| `schema_version` | int | Schemaversion. |
| `type` | `"run_header"` | |
| `model` | str | Modellsträng. |
| `params` | obj \| null | Extra LLM-params (LLM_PARAMS), t.ex. `{"temperature":0}`. |
| `mcp_url` | str | Ansluten MCP-server (komma-separerad om flera). |
| `servers` | str[] | Namn på alla anslutna servrar (T030). |
| `tools` | str[] | Verktygsmenyn modellen ser (efter allowlist/scoping). |
| `tools_fingerprint` | str | Stabil hash av menyn (namn+beskrivning+schema) — fångar stale server. |
| `profile` | str | Harness-profilens namn (T031). |
| `approximation_note` | str | Ärlig 'skiljer sig här'-not — en grön körning är inte 'verifierad i den riktiga harnessen'. |
| `system_chars` | int | (Ramad) systemprompts längd i tecken. |

### `user_turn`
| `type` `"user_turn"` · `text` str | En användartur. |

### `tool_call`
| Fält | Typ | Beskrivning |
|------|-----|-------------|
| `type` | `"tool_call"` | |
| `name` | str | Verktygsnamn. |
| `arguments` | obj | **Fullständiga** args (ingen förlust). |
| `call_id` | str | Korrelations-id mot `tool_result`. |

### `tool_result`
| Fält | Typ | Beskrivning |
|------|-----|-------------|
| `type` | `"tool_result"` | |
| `call_id` | str | Matchar `tool_call`. |
| `name` | str | Verktygsnamn. |
| `text` | str | **Otrunkerad** konkatenering av alla text-block. |
| `is_error` | bool | Verktyget returnerade fel. |
| `block_count` | int | Antal content-block i svaret. |
| `non_text_blocks` | int | Antal icke-text-block (bild/resurs). |
| `structured` | obj \| null | Strukturerat svar (`structuredContent`) om sådant finns. |

### `assistant_text`
| `type` `"assistant_text"` · `text` str | Modellens textsvar som avslutar turen. |

### `attachment`
| `type` `"attachment"` · `name` str · `kind` `"text"`\|`"image"` · `size` int | En bilaga lades till (T032; metadata, ej innehåll). |

### `turn_meta` (efter varje tur)
| Fält | Typ | Beskrivning |
|------|-----|-------------|
| `type` | `"turn_meta"` | |
| `latency_ms` | float | Turens totala väggklocka (LLM + verktyg). |
| `llm_calls` | int \| null | Antal LLM-anrop i turen. |
| `usage` | obj \| null | Summerad token-`usage` (och ev. leverantörs-extra som co2/energi). |

### `error`
| `type` `"error"` · `message` str | LLM-fel eller tak-överskridande (turen misslyckades). |

## Diffa två körningar (T033)

Headern gör varje körning självbeskrivande (modell, params inkl. `seed`/
`temperature`, servrar, fingeravtryck, profil). För att jämföra två körningar:
diffa headern för att se vad som ändrades i uppsättningen, och jämför `tool_call`/
`tool_result`/`assistant_text`-raderna för beteendeskillnader. Eftersom args och
svar är otrunkerade är diffen trogen. `turn_meta` ger latens/token-trend.

## Exempel

```json
{"schema_version":1,"type":"run_header","model":"google/gemma-4-31B-it","params":{"temperature":0},"mcp_url":"http://127.0.0.1:8765/mcp","tools":["echo","boom"],"system_chars":436}
{"schema_version":1,"type":"user_turn","text":"Eka tillbaka: hej"}
{"schema_version":1,"type":"tool_call","name":"echo","arguments":{"text":"hej"},"call_id":"c1"}
{"schema_version":1,"type":"tool_result","call_id":"c1","name":"echo","text":"hej","is_error":false,"block_count":1,"non_text_blocks":0,"structured":null}
{"schema_version":1,"type":"assistant_text","text":"hej"}
```
