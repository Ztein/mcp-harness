# PRD — mcp-harness

**Status:** utkast v0.1 · **Ägare:** Joel · **Senast ändrad:** 2026-06-25

## 1. Sammanfattning

`mcp-harness` är ett **terminalfönster för att testköra MCP-servrar**. Det kör en
MCP genom en riktig LLM med en systemprompt och en CLI-konversation — och låter
användaren **approximera olika värd-harnesses** (Intric, Claude Desktop, Cursor,
ChatGPT:s verktygsläge, en egen agent) så att man kan se hur en MCP faktiskt
uppför sig *i den miljö där den ska leva*, utan att behöva den riktiga harnessen.

Det är **inte** en gör-allt-agent och **inte** ett tungt ramverk. Det är ett litet,
ärligt observerbart testfönster: prompt in, verktygsanrop ut, svar tillbaka,
loggat så att en människa (eller en agent) kan döma resultatet.

## 2. Problem

En MCP-server beter sig aldrig isolerat — den beter sig **genom sin harness**. Samma
server ger olika resultat beroende på:

- **Systemprompten** värden injicerar (varje seriöst system — Intric, Claude
  Desktop, Cursor — har en sådan; den styr ton, regler, verktygsdisciplin).
- **Hur verktygsschemat presenteras** för modellen (namn, beskrivningar,
  parameter-schema, ev. omskrivning/trunkering).
- **Vilka servrar** som är inkopplade samtidigt (verktygs-antal påverkar
  modellens val — en stor meny gör rätt val svårare, särskilt för små modeller).
- **Modell + parametrar** (temperatur, max tokens).
- **Hur verktygssvar matas tillbaka** (full text? trunkerad? sammanfattad?).

Idag finns inget lätt sätt att **återskapa den miljön** för att testa en MCP. Man
tvingas antingen klicka i den riktiga harnessen (långsamt, ej skriptbart, svårt
att jämföra körningar) eller skriva engångs-skript. Resultatet: MCP-beteende
upptäcks sent, i produktion, i fel harness.

## 3. Vision

> Ett terminalfönster där jag kan säga *"kör min MCP som om den satt i Intric"*
> (eller Claude Desktop, eller …), prata med den som en användare, ladda upp en
> fil, och få en exakt, skriptbar, loggad bild av hur den beter sig — innan jag
> rör den riktiga harnessen.

## 4. Användare

- **MCP-utvecklaren** — bygger en MCP och vill se hur den uppför sig under en
  riktig modell + systemprompt, inte bara via unit-tester.
- **Prompt-/skill-författaren** — itererar på systemprompten och vill se effekten
  på verktygsval och ton.
- **Test-/QA-agenten (människa eller Claude)** — kör protokoll-scenarier som en
  människa skulle och dömer PASS/FAIL semantiskt (det här verktygets ursprung).
- **Den som utvärderar en främmande MCP** — vill snabbt förstå vad en MCP gör och
  hur robust den är under press, utan att koppla in den i sin riktiga miljö.

## 5. Kärnkoncept: harness-emulering

Produktens särdrag är **harness-profilen**: en namngiven beskrivning av hur en
specifik värd-harness presenterar MCP:er för sin modell. En körning = en
**harness-profil** + ett **scenario**.

En **harness-profil** fångar (alla värden kända/approximerade):

| Aspekt | Vad profilen sätter |
|---|---|
| Systemprompt-konvention | bas-systemprompt/ramning harness alltid lägger till |
| Verktygspresentation | hur tool-schemat skickas (oförändrat, omskrivet, namn-prefix) |
| Server-uppsättning | vilka MCP-servrar som kopplas in (en eller flera) |
| Modell + parametrar | modellsträng, temperatur, max tokens |
| Verktygssvar tillbaka | full text / trunkerad till N / sammanfattad |
| Verktygs-scoping | allowlist per "assistent"/roll |

Exempel-profiler att leverera: `intric`, `claude-desktop`, `cursor`, `generic-openai`,
`raw` (ingen extra ramning). Profiler är **data** (en fil), inte kod — användaren
kan skriva egna och dela dem.

Ett **scenario** = systemprompt (skill/persona) + ev. förvalt indata (turer att
mata) + ev. bifogade filer. Scenarier är skriptbara (piped stdin idag).

> Notera: "approximera" — inte "vara identisk med". Målet är *troget nog* för att
> fånga beteende-skillnader (verktygsval, fält-mappning, vägran, hallucination),
> med ärliga noter om var approximationen skiljer sig från den riktiga harnessen.

## 6. Kärnfunktioner

Markeringar: **[finns]** i MVP-koden · **[mål]** roadmap.

### 6.1 Systemprompt (skill/persona)
- **[finns]** Ladda en systemprompt från `.md`-fil (`--system`) eller env; inbyggd
  default annars. Detta är "skillen" som alla värdsystem har.
- **[mål]** Bas-ramning per harness-profil läggs *runt* användarens skill (så man
  ser skillens beteende under olika harness-konventioner).

### 6.2 MCP-servrar — flera, via config
- **[finns]** En server via `MCP_URL`/`MCP_KEY` (Streamable HTTP, bearer).
- **[mål]** En **config-fil** som listar flera servrar (likt Claude Desktops
  `mcpServers`): namn, transport (Streamable HTTP / stdio / SSE), auth, ev.
  scoping. Verktygen aggregeras till en meny (med namn-krock-hantering), precis
  som en riktig multi-server-harness.

### 6.3 CLI-interaktion
- **[finns]** Interaktiv REPL (`> `), och **piped stdin** (en rad = en tur, EOF
  avslutar) → skriptbara körningar.
- **[finns]** `/tools`, `/reset`, `/quit`.
- **[mål]** Fler kommandon: `/attach <fil>`, `/profile <namn>`, `/save`, `/system <fil>`,
  `/model <namn>`; och en icke-interaktiv `run`-subkommando för scenariefiler.

### 6.4 Fil-uppladdning / kontext
- **[mål]** Bifoga filer till konversationen (`/attach` eller `--attach`): text
  inline som kontext; bilder/PDF som multimodalt innehåll där modellen stödjer
  det. Spegla hur harnesses låter användaren ladda upp underlag.

### 6.5 Observerbarhet
- **[finns]** Läsbart Markdown-transkript (`👤/🤖/⚙`), flushas löpande; visar
  varje verktygsanrop med argument och (klippt) svar.
- **[mål]** Strukturerad körlogg (JSONL) för diff mellan körningar; token-/
  latens-mätning per tur; verktygslista + fingeravtryck vid anslutning (så man
  ser exakt vilken serverversion man talar med — en stale server ska aldrig kunna
  maskera sig).

### 6.6 Verktygs-scoping
- **[finns]** `--tools a,b,c` allowlist (fail-hard på okänt namn) — approximerar
  per-assistent-scoping (visa bara en delmängd av verktygen för modellen).

## 7. Icke-mål

- **Inte en produktions-agent/orkestrerare.** Det approximerar harnesses för
  *test*, det ersätter dem inte.
- **Inte en MCP-server.** Det är en *klient/värd*.
- **Inte ett GUI.** Terminal-först, skriptbart. (Ev. TUI senare, lågt prio.)
- **Inte leverantörslåst.** LLM-config är OpenAI-kompatibel och agnostisk; ingen
  leverantör/URL/modell hårdkodas.
- **Inte ett auto-domar-ramverk.** Det *kör* och *loggar*; dömningen görs av en
  människa eller en agent (ev. dedikerat lager senare).

## 8. Principer (ärvda, medvetna)

1. **Litet och CLI-först** — inget manager-/plugin-/config-imperium. Lägg
   funktioner bara när ett konkret behov visat sig.
2. **Agnostisk LLM-config** — `LLM_BASE_URL/_API_KEY/_MODEL` (+ valfri proxy/
   params). Fungerar mot on-prem/air-gapped OpenAI-kompatibla endpoints.
3. **Fail-hard, aldrig tyst** — saknad config eller okänt verktyg failar
   högljutt; approximationer som skiljer sig från en riktig harness *noteras*.
4. **Observerbart** — varje verktygsanrop och svar syns och loggas; man ska kunna
   lägga två körningar bredvid varandra och se vad som ändrades.

## 9. Nuläge → faser

**Nuläge (v0.1, denna commit):** MVP-kärnan kopierad från `use-case-mcp/scripts/
mcp_chat.py` + `llm_client.py`. En MCP via env, en systemprompt, allowlist,
transkript, piped-körning. Bevisat dugligt: hela protokoll-sviter har körts genom
det mot en riktig MCP + modell.

- **Fas 1 — flera servrar + config.** Config-fil med `mcpServers` (Streamable HTTP
  först, sedan stdio). Verktygs-aggregering + namn-krock-hantering.
- **Fas 2 — harness-profiler.** Profil-filer (`intric`, `claude-desktop`, …);
  bas-ramning runt skillen; svars-trunkerings-/presentations-strategi per profil.
- **Fas 3 — fil-uppladdning.** `/attach` + `--attach`; text inline, bild/PDF
  multimodalt.
- **Fas 4 — observerbarhet+.** JSONL-körlogg, token/latens, server-fingeravtryck,
  körnings-diff.
- **Fas 5 (ev.) — scenariefiler + dömnings-stöd.** Deklarativa scenarier; valfritt
  domar-lager (metrics/LLM-domare), aldrig som ersättning för mänsklig dom.

## 10. Öppna frågor

- Namn — `mcp-harness` är arbetsnamn (alt: `mcp-probe`, `harness-emu`, `mcp-bench`).
- Hur långt ska "approximera Intric" gå innan det blir falsk trygghet? (Profiler
  ska bära ärliga "skiljer sig här"-noter.)
- stdio-transport-prioritet (många MCP:er är stdio, inte HTTP) — sannolikt Fas 1.
- Behövs ett litet test-/CI-lager för själva harnessen (mot en fejk-MCP)?
