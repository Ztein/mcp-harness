# mcp-harness

Ett **terminalfönster för att testköra MCP-servrar** genom en riktig LLM och en
systemprompt — precis som en värd-harness (Intric, Claude Desktop, Cursor, en
egen agent) skulle göra, fast i terminalen och under din fulla kontroll.

> **Varför:** en MCP beter sig inte i ett vakuum — den beter sig *genom* den
> harness som kör den (systemprompt, hur verktygsschemat presenteras, vilka
> servrar som är inkopplade, modell + parametrar, hur verktygssvar matas
> tillbaka). `mcp-harness` låter dig återskapa den miljön och se hur din MCP
> faktiskt uppför sig — utan att behöva den riktiga harnessen.

Se **[PRD.md](PRD.md)** för vad produkten ska bli. Koden här är startpunkten
(härstammar från `use-case-mcp`:s `mcp_chat.py`).

## Snabbstart (MVP)

```bash
uv venv && uv pip install -e .
cp .env.example .env            # fyll i LLM_* + MCP_URL/MCP_KEY

# interaktivt
mcp-harness --system prompts/min-skill.md

# skriptat (en rad = en tur, avslutar vid EOF) — det som gör protokoll-körning möjlig
printf '%s\n' "Hej, vad kan du?" "Lista mina ärenden." \
  | mcp-harness --system prompts/min-skill.md --transcript transcripts/run.md
```

Kommandon i chatten: `/tools` (lista verktyg), `/reset` (nollställ historik), `/quit`.

Flaggor: `--system <fil>` (systemprompt/skill), `--transcript <fil>`,
`--tools a,b,c` (visa bara en delmängd av verktygen — approximerar per-assistent-scoping).

## Status

MVP (kopierad kärna): **en** MCP-server via `MCP_URL`/`MCP_KEY`, en systemprompt,
verktygs-allowlist, läsbart transkript. Roadmap mot flera servrar, harness-profiler
och fil-uppladdning i [PRD.md](PRD.md).

## Utveckling

Arbetet drivs av tickets med strikt TDD. Se **[DOCS/README.md](DOCS/README.md)**
för arbetstavlan (TODO/DOING/DONE) och **[CONTRIBUTING.md](CONTRIBUTING.md)** för
arbetssättet. Kör grinden lokalt:

```bash
uv sync --group dev
uv run --group dev ruff check . && uv run --group dev mypy && uv run --group dev pytest
```

## Licens

[MIT](LICENSE).
