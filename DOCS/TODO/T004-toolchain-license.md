# T004 — verktygskedja + LICENSE (ruff format, mypy, pre-commit)

**Status:** TODO · **Fas:** 0 · **Prioritet:** P1 · **Beror på:** T001

## Varför

Repot är publikt utan licens (= all rights reserved), vilket motsäger PRD:ns
idé att profiler ”kan delas”. Och för att hålla koden professionell behöver vi
deterministisk formattering, typkontroll och en lokal grind som fångar fel innan
CI. Allt detta är engångsuppsättning som betalar sig varje commit.

## Omfattning

**Ingår:**
- `LICENSE` (MIT, om inget annat beslutas) + `license`-fält i `pyproject.toml`.
- `mypy`-konfiguration i `pyproject.toml` (strict där rimligt; börja pragmatiskt).
- `ruff format`-konvention (line-length finns redan: 100).
- `.pre-commit-config.yaml`: ruff, ruff-format, mypy, slut-radslut/whitespace.
- `CONTRIBUTING.md` med arbetssättet (TDD, DOCS-tavlan, branch→PR).

**Ingår inte:** CHANGELOG/semver-release (lägg till när första taggen är nära).

## Definition of Done

- [ ] `LICENSE` finns och `pyproject.toml` deklarerar den.
- [ ] `pre-commit run --all-files` är grönt på ren kod.
- [ ] `mypy src/` rent.
- [ ] `CONTRIBUTING.md` beskriver: skriv test först, flytta ticket TODO→DOING→DONE,
      en PR per ticket, grön CI krävs.
- [ ] README länkar till `DOCS/README.md` och `CONTRIBUTING.md`.

## Testfall (skriv först)

Mest konfiguration, men verifiera mekaniskt:

1. Kör `pre-commit run --all-files` på en avsiktligt formatfel-commit → **fångas**.
2. Kör `mypy` på en avsiktlig typfelsrad → **fångas**.
3. Ren kod → båda gröna.

## Noteringar

Bekräfta licensval med Joel innan commit om något annat än MIT är aktuellt.
Håll pre-commit och CI samstämmiga — samma verktyg, samma flaggor, så lokalt och
CI aldrig divergerar.
