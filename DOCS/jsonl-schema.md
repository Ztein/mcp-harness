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
| `mcp_url` | str | Ansluten MCP-server. |
| `tools` | str[] | Verktygsmenyn modellen ser (efter allowlist/scoping). |
| `tools_fingerprint` | str | Stabil hash av menyn (namn+beskrivning+schema) — fångar stale server. |
| `system_chars` | int | Systempromptens längd i tecken. |

> Reserverat för senare faser: `profile` + approximation-not (T031).

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

### `error`
| `type` `"error"` · `message` str | LLM-fel eller tak-överskridande (turen misslyckades). |

## Exempel

```json
{"schema_version":1,"type":"run_header","model":"google/gemma-4-31B-it","params":{"temperature":0},"mcp_url":"http://127.0.0.1:8765/mcp","tools":["echo","boom"],"system_chars":436}
{"schema_version":1,"type":"user_turn","text":"Eka tillbaka: hej"}
{"schema_version":1,"type":"tool_call","name":"echo","arguments":{"text":"hej"},"call_id":"c1"}
{"schema_version":1,"type":"tool_result","call_id":"c1","name":"echo","text":"hej","is_error":false,"block_count":1,"non_text_blocks":0,"structured":null}
{"schema_version":1,"type":"assistant_text","text":"hej"}
```
