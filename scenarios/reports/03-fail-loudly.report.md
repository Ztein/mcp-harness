# Protokoll — 03 Fel hanteras högljutt (2026-06-25, google/gemma-4-31B-it)

## Sammanfattning

**PASS.** Verktygsfelet syntes och rapporterades ärligt, och flerblockssvaret kom
med i sin helhet — T012-fixen bevisad end-to-end genom riktig CLI + riktig modell.
Men en konkret fail-loudly-brist hittades i människo-vyn (se förbättringar).

## Utfall per kriterium

| # | Kriterium | Utfall | Motivering (från körningen) |
|---|-----------|--------|------------------------------|
| 1 | Synligt verktygsfel | **PASS** | `⚙ boom({})` → `→ Error executing tool boom: avsiktligt fel`; modellen sa ärligt att det "resulterade i ett felmeddelande". Körningen fortsatte. |
| 2 | Full svars-trohet | **PASS** | `multi_block` gav **både** "block-A" och "block-B" i underlaget. content[0]-buggen vore bara "block-A". |
| 3 | Ingen falsk framgång | **PASS** | Modellen påstod aldrig att `boom` lyckades; den återgav felet. |

## Förbättringsspaning

- **🔴 Verktygsfel är inte visuellt utmärkta i transkriptet (ny ticket T015).**
  `boom`-felet renderas som ett vanligt `→ Error executing tool boom: …` — samma
  prefix som ett lyckat svar. `ToolResult.is_error=True` finns i datat men
  människo-vyn skiljer inte på fel och framgång. För en princip-3-produkt ska ett
  fel *se ut* som ett fel (t.ex. `→ ⚠️`). Hög: detta är kärnan i fail-loudly.
- **Flerradiga verktygssvar bryter indenteringen.** `multi_block` renderas som
  `→ block-A` följt av `block-B` på en rad utan `→`/indent. Kosmetiskt, men en
  parser eller läsare kan missuppfatta var svaret slutar. Lågt.
- **Deprecation i shippad kod (ny ticket T016).** mcp varnar:
  `streamablehttp_client` → `streamable_http_client`. Gäller `cli.py` och testerna.
- **JSONL (T020) skulle bära `is_error` maskinläsbart** — i dag måste en agent
  gissa felstatus ur prosan. Bekräftar T020 som P0.

## Uppföljning

- **T015 LANDAD.** Verktygsfel renderas nu distinkt: transkriptet visar
  `→ ⚠️ Error executing tool boom: avsiktligt fel` (verifierat i omkörning). Den
  enda fail-loudly-bristen detta scenario hittade är åtgärdad.

## Körbevis

- Transkript: `03-fail-loudly.transcript.md` · Rådata: `03-fail-loudly.raw.txt` · exit=0
- **Approximation-not:** `raw`-profil + inbyggd test-MCP — *inte* verifierat i en riktig harness.
