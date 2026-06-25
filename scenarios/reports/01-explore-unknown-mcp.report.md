# Protokoll — 01 Utforska en okänd MCP (2026-06-25, google/gemma-4-31B-it)

## Sammanfattning

**PASS.** Gemma beskrev sina förmågor ärligt utifrån de faktiska verktygen,
valde rätt verktyg för uppgiften, använde resultatet troget och bar kontext
mellan turer.

## Utfall per kriterium

| # | Kriterium | Utfall | Motivering (från körningen) |
|---|-----------|--------|------------------------------|
| 1 | Ärlig förmågebeskrivning | **PASS** | Listade exakt de fyra verkliga verktygen (`echo`, `multi_block`, `boom`, `structured`); hittade inte på något. |
| 2 | Rimligt verktygsval | **PASS** | För "eka tillbaka" anropade den `echo`, inget orelaterat. |
| 3 | Trogen verktygsanvändning | **PASS** | `echo` returnerade exakt "hej världen" och modellen återgav det. |
| 4 | Kontext mellan turer | **PASS** | På uppföljningen svarade den korrekt: 'Resultatet av det förra anropet var: "hej världen".' |

## Förbättringsspaning

- **Tunna verktygsbeskrivningar märks.** Gemma beskrev `multi_block/boom/structured`
  vagt ("specialiserade funktioner") eftersom test-verktygen saknar beskrivningar.
  Det *visar* att beskrivningar styr modellens förståelse — relevant för
  harness-profiler (T031). Lågt: ge test-MCP:ns verktyg korta beskrivningar så
  scenarierna blir rikare.
- **Transient Berget-timeout fångades.** Första LLM-anropet gav `TimeoutError`,
  retry (1/3) återhämtade. Retry-meddelandet på stderr var tydligt — bra. Stärker
  värdet av latens-/token-observability (T033); Berget rapporterar dessutom
  CO2/energi i `usage` som vore värt att logga.
- **JSONL saknas (T020).** Jag dömde genom att läsa markdown-prosa. En maskinläsbar
  logg skulle göra dömningen exakt — bekräftar T020 som P0.

## Körbevis

- Transkript: `01-explore-unknown-mcp.transcript.md` · Rådata: `01-explore-unknown-mcp.raw.txt` · exit=0
- **Approximation-not:** kört mot `raw`-profil + inbyggd test-MCP — *inte* verifierat i en riktig harness.
