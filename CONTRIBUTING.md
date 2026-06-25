# Bidra till mcp-harness

Tack för att du tittar in. Projektet hålls **litet, CLI-först och ärligt
observerbart** (se [PRD.md](PRD.md) §8). Två principer styr allt arbete:

1. **Strikt TDD** — testen skrivs först. Inget produktionsbeteende utan ett test
   som var rött innan koden fanns.
2. **Testa på riktigt, fail loudly** — inga mockar som döljer verkligheten. Vi
   kör mot en riktig in-process fejk-MCP-server och en riktig HTTP-fejk-LLM. Ett
   tyst halvresultat är värre än ett högljutt fel.

## Arbetsflöde

Arbetet styrs av tickets på en enkel tavla i [`DOCS/`](DOCS/README.md):
`TODO/` → `DOING/` → `DONE/`. En ticket = en markdown-fil med tydlig
**Definition of Done** och **testfall som skrivs först**.

1. Plocka en ticket från `DOCS/TODO/`. `git mv` den till `DOCS/DOING/` och sätt
   statusraden till `DOING`. Håll helst bara en i `DOING`.
2. Skapa en branch: `git switch -c t0xx-kort-slug`.
3. **Skriv testet först.** Se det faila. Skriv minsta kod som gör det grönt.
   Refaktorera under grönt.
4. Innan PR — kör hela grinden lokalt (samma som CI):
   ```bash
   uv run --group dev ruff check .
   uv run --group dev ruff format --check .
   uv run --group dev mypy
   uv run --group dev pytest
   ```
   Eller installera grinden: `uv run --group dev pre-commit install`.
5. När ticketens DoD (och den globala i [`DOCS/README.md`](DOCS/README.md)) är
   uppfylld: `git mv` ticketen till `DOCS/DONE/`, sätt `DONE`, öppna en PR.
6. **En PR per ticket.** PR:n ska vara grön i CI innan den slås ihop.

## Commit-stil

`typ(Txxx): kort sammanfattning` — t.ex. `test(T012): konkatenera alla content-block`.
Beskriv *varför* i kroppen när det inte är självklart.

## Setup

```bash
uv venv && uv sync --group dev
cp .env.example .env   # fyll i LLM_* + MCP_URL/MCP_KEY för skarp körning
```

Tester som kräver en riktig LLM/MCP-endpoint (inte fejkarna) markeras och hoppas
över i CI — fejk-baserade tester körs alltid.
