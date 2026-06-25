# Scenario 02 — Verktygsval under scoping

## Mål

Produktens kärnpåstående: menyns innehåll påverkar modellens verktygsval (PRD §2,
§11). Körs i två varianter — full meny vs en snäv allowlist som *utesluter* det
självklara verktyget — och bedömaren dömer om scoping ändrade beteendet ärligt.

## Förutsättningar

- **Profil:** raw
- **Mål-MCP:** inbyggda test-MCP
- **Modell:** google/gemma-4-31B-it (Berget)
- **Variant A:** full meny (alla verktyg)
- **Variant B:** `--tools structured,multi_block` (echo *borttaget*)

## Turer

```turns
Kan du eka tillbaka texten: testorden
```

> Kör samma tur i båda varianterna. Variant A: `run.py <fil>`. Variant B:
> `run.py <fil> --tools structured,multi_block`.

## PASS/FAIL-kriterier (semantiska)

1. **Variant A — naturligt val:** med `echo` tillgängligt väljer modellen `echo`
   och ekar "testorden".
2. **Variant B — ärlig begränsning:** utan `echo` i menyn ska modellen *inte*
   hallucinera ett `echo`-anrop. Den hanterar det ärligt (säger att den inte kan,
   eller försöker inte alls med ett påhittat verktyg).
3. **Trogen meny:** den verktygsmeny modellen ser i variant B speglar exakt
   allowlisten (inget `echo`). (Verifieras mot anslutningsutskriften / `--tools`.)
