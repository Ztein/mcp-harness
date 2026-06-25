# T003 — CI-pipeline (ruff, mypy, pytest)

**Status:** DONE · **Fas:** 0 · **Prioritet:** P0 · **Beror på:** T001

## Varför

”Professionellt” betyder att inget odisciplinerat tar sig in i `main`. En grön
PR ska bevisa att lint, typer och hela testsviten passerar på en ren maskin —
inte bara på Joels laptop. Detta är också vad test-agenten kräver (PRD §11):
en stabil, versionerad kontraktsyta får inte drifta tyst.

## Omfattning

**Ingår:** `.github/workflows/ci.yml` som på `push` och `pull_request` kör:
installation via `uv`, `ruff check`, `ruff format --check`, `mypy`, `pytest`.
Matris över Python 3.11 + 3.12 (PRD kräver >=3.11). Branch-skydd-instruktion i
README/CONTRIBUTING (kan inte sättas via kod, dokumenteras).

**Ingår inte:** release-/publiceringsflöde (separat senare ticket vid behov).

## Definition of Done

- [ ] Workflow körs på PR och visar separata, namngivna steg (lint, format, types, tests).
- [ ] Jobbet failar högljutt om något steg failar (ingen `continue-on-error`).
- [ ] Kör på Python 3.11 och 3.12.
- [ ] Badge för CI-status i `README.md`.
- [ ] Tester som kräver riktig LLM/MCP-endpoint (ej fejk) **hoppas** rent över i
      CI via en markör, men fejk-baserade tester (T001/T002) körs alltid.

## Testfall (skriv först)

CI är infrastruktur — ”testet” är att pipelinen körs och är grön på en avsiktligt
trasig och en avsiktligt ren commit:

1. Öppna en PR med ett medvetet lint-fel → CI **röd** på lint-steget.
2. Öppna en PR med ett medvetet typfel → CI **röd** på mypy-steget.
3. Ren PR → CI **grön** på alla steg.

(Verifiera genom faktiska PR:er, inte genom att anta att YAML:en stämmer.)

## Noteringar

Cacha `uv`-miljön för fart. Pinna `actions/*` till major-version. Workflow ska
vara läsbar — inga onödiga abstraktionslager (princip 1).
