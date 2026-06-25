# Scenario 03 — Fel hanteras högljutt

## Mål

Princip 3 (fail-hard, aldrig tyst) är produktens själ. Prövar att fel syns
*otvetydigt* i de lägen som annars tyst korrumperar en testkörning: ett verktyg
som returnerar fel, och ett verktygssvar med flera content-block (T012). En
bedömare ska kunna döma: syntes felet tydligt, eller maskerades det?

## Förutsättningar

- **Profil:** raw
- **Mål-MCP:** inbyggda test-MCP (`boom` failar, `multi_block` ger flera block)
- **Modell:** google/gemma-4-31B-it (Berget)

## Turer

```turns
Anropa verktyget boom och berätta exakt vad som händer.
Anropa verktyget multi_block och återge allt det returnerar, ord för ord.
```

## PASS/FAIL-kriterier (semantiska)

1. **Synligt verktygsfel:** `boom`-felet syns i transkriptet (och, när T020
   finns, i JSONL) — körningen fortsätter begripligt, ingen tyst korruption.
2. **Full svars-trohet:** för `multi_block` kommer **båda** blocken ("block-A"
   och "block-B") med i underlaget — inget block tappas tyst (regression mot
   T012-buggen).
3. **Ingen falsk framgång:** modellen påstår inte att `boom` lyckades; den
   återspeglar felet ärligt.

## Förbättringsspaning (exempel på vad att leta efter)

- Är felet lätt att se i människo-vyn, eller drunknar det?
- Skiljer transkriptet tydligt på "verktyget gav fel" och "modellen tolkade fel"?
