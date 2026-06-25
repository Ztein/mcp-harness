# Scenario 01 — Utforska en okänd MCP

## Mål

Den vanligaste mänskliga testsituationen: en testare möter en server hen inte
känner och försöker förstå den genom samtal. Prövar att modell+MCP beter sig
begripligt: förklarar förmågor utan att hitta på, väljer rimligt verktyg, och
använder ett tidigare resultat i en uppföljning.

## Förutsättningar

- **Profil:** raw (ingen extra ramning)
- **Mål-MCP:** inbyggda test-MCP (echo, multi_block, boom, structured)
- **Modell:** google/gemma-4-31B-it (Berget)

## Turer

```turns
Hej! Vad kan du hjälpa mig med? Vilka verktyg har du?
Kan du eka tillbaka exakt texten: hej världen
Vad blev resultatet av det förra anropet?
```

## PASS/FAIL-kriterier (semantiska)

1. **Ärlig förmågebeskrivning** — assistenten beskriver vad den kan utifrån sina
   faktiska verktyg, utan att hitta på verktyg som inte finns.
2. **Rimligt verktygsval** — för "eka tillbaka"-uppgiften väljer den `echo`
   (inte ett orelaterat verktyg, och inte inget alls).
3. **Trogen verktygsanvändning** — det `echo` returnerar är exakt "hej världen".
4. **Kontext mellan turer** — i uppföljningen refererar den korrekt till
   resultatet från föregående tur i stället för att börja om.
