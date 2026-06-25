# Scenarier — agent-driven E2E-testning

Här bor **scenarier** skrivna som en mänsklig testare skulle köra dem i CLI:t, och
**protokoll** (rapporter) från körningar. Den primära testaren är en agent (Claude)
som kör scenarierna genom CLI:t, dömer PASS/FAIL **semantiskt**, och spanar efter
förbättringar (PRD §4, §11). Verktyget *kör och loggar troget* — domen görs av
agenten/människan, inte av ett auto-domar-lager (PRD §7 icke-mål).

## Scenarioformat

En `.md`-fil med:

- **Mål** — vad scenariot prövar.
- **Förutsättningar** — profil, mål-MCP, modell.
- **Turer** — ett `turns`-kodblock; en rad = en användartur som matas till CLI:t
  (piped stdin). Skrivet i naturligt språk, som en människa skriver.
- **PASS/FAIL-kriterier** — semantiska, bedömbara av människa eller LLM.

Exempel på turblock:

````
```turns
Vad kan du hjälpa mig med?
Kan du eka tillbaka "hej världen"?
```
````

## Köra (agenten gör detta)

```bash
# 1. Fyll i .env (LLM_BASE_URL/_API_KEY/_MODEL + MCP_URL/MCP_KEY). Se .env.example.
# 2. Starta test-MCP:n (T044) i en egen terminal:
uv run python -m tests.support.fake_mcp --port 8765 --key test-key
# 3. Kör ett scenario:
uv run python scenarios/run.py scenarios/01-explore-unknown-mcp.md
```

`run.py` matar scenariots turer till CLI:t, sparar transkript +
rådata under `reports/<scenario>.*`, och skriver ut exit-kod. Agenten läser
underlaget och skriver sedan ett **protokoll** (se mall nedan) till
`reports/<scenario>.report.md`.

## Protokoll-mall

```markdown
# Protokoll — <scenario> (<datum>, <modell>)

## Sammanfattning
PASS / FAIL / DELVIS — en mening.

## Utfall per kriterium
| # | Kriterium | Utfall | Motivering (från körningen) |
|---|-----------|--------|------------------------------|

## Förbättringsspaning
- Konkreta, observerade förslag (verktyg, prompt, harness, UX).

## Körbevis
- Transkript: reports/<scenario>.transcript.md
- Rådata: reports/<scenario>.raw.txt · exit-kod: <n>
- Approximation-not: körd mot `raw`-profil + inbyggd test-MCP — inte verifierad i
  en riktig harness.
```

> Ärlighet: ett grönt scenario mot test-MCP:n + `raw`-profil betyder *inte*
> "verifierad i Intric". Protokollet ska alltid bära den noten.
