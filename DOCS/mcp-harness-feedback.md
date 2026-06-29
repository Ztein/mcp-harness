# Feedback till mcp-harness-teamet

**Från:** use-case-mcp-projektet (en konsument av `mcp-harness`)
**Datum:** 2026-06-26
**Sammanhang:** Vi använder `mcp-harness` som testfordon för **ADR-004 lager-2**
— en Claude-agent kör .md-testprotokoll *som en mänsklig testare* genom
`mcp-harness` (LLM + systemprompt + MCP-verktyg) mot vår domän-MCP, och dömer
PASS/FAIL semantiskt. Den här sessionen körde vi en full regressionssvit
(~25 protokoll-körningar: registreringsassistent + ledningsassistent) efter att
ha lagt till ett nytt MCP-verktyg.

> **Syfte med dokumentet:** ge er underlag, inte färdiga tickets. Vi beskriver
> observationer + förslag på *riktning*; ni prioriterar och designar era egna
> aktiviteter. Allt nedan är från faktisk användning den här sessionen.

---

## TL;DR

`mcp-harness` är ett utmärkt fordon för det här arbetssättet — det enda som
över huvud taget gör semantisk lager-2-bedömning praktiskt möjlig. Den största
hävstången framåt ligger i **observability för agent-driven körning**:
maskinläsbar utdata, per-tur-timing, och en körnings-summering. Det är inte ett
prestanda-problem (se "Icke-problem" — vi mätte).

Topp-3 önskemål, i prioordning:
1. **Maskinläsbar transkript** (`--jsonl`) — störst värde.
2. **Per-tur-latens/tidsstämplar** i utdatan.
3. **Körnings-summering + meningsfulla exit-koder.**

---

## Det som fungerar bra (behåll/skydda)

1. **`⚙ namn(args)`-transkriptet + auto-exekvering av tool-anrop.** Detta är
   kärnvärdet. Vi dömde ~25 protokoll nästan uteslutande från de raderna:
   "anropade assistenten `aggregate` eller räknade den själv ur en lista?",
   "rätt enum-värde?", "rätt `action`-parameter på ett konsoliderat verktyg?",
   "rörde den ett borttaget verktyg?". Det speglar Intrics "godkänn"-flöde
   troget och gör beteendet inspekterbart.
2. **Connect-bannern** (`Ansluten: <url> — N verktyg, modell <id>`). Vi använde
   den som *deploy-verifiering*: bekräftade direkt att ett nytt verktyg gått
   live genom en Cloudflare-tunnel (27→28 verktyg). Omedelbar
   "är rätt sak uppe?"-signal.
3. **`--system` + `--tools`.** Reproducerar per-assistent-scoping troget (vi
   kör två olika assistent-prompter mot samma server).
4. **stdin = en rad per tur, ren EOF-exit.** Det är det som gör batch-körning
   möjlig (`printf '%s\n' tur1 tur2 … | mcp-harness`). Vi bekräftade att den
   **avslutar rent** vid EOF (~0,5 s connect+exit utan turer).

---

## Förbättringsförslag (observationer + riktning — ni designar tickets)

### F1 — Maskinläsbar transkript (`--jsonl`)  · prio: HÖG
- **Observation:** tool-anrop finns bara i markdown-transkriptet, formaterade
  som `` - ⚙ `namn({...json...})` ``. För programmatisk bedömning parsar vi med
  regex över markdown — och vår *första* regex missade för att vi inte räknade
  med back-ticken efter `⚙`.
- **Impact:** all automatiserad/agent-driven bedömning blir regex-skör och
  formatberoende. Ett litet renderingsbyte i transkriptet bryter tysta nedströms.
- **Förslag på riktning:** en `--jsonl`-utdata (en post per tur) med strukturerat
  innehåll, t.ex. `{turn, role, text, tool_calls:[{name, args, result, error,
  latency_ms}]}`. Markdown kvar för människor; JSONL för maskiner.

### F2 — Per-tur-latens / tidsstämplar  · prio: MEDEL
- **Observation:** transkriptet har ingen tid. Vår RUN-mall ber om per-tur-latens
  men vi kan inte fylla fältet. När en körning kändes långsam fick vi mäta utifrån
  (process-`etime`, fil-mtimes) i stället för att läsa det ur utdatan.
- **Impact:** svårt att upptäcka/diagnostisera latens-regressions, och svårt att
  veta om långsamhet kommer från LLM:en, MCP-servern eller harnessen. (I vårt fall
  visade mätning att ~14 s/tur var ren LLM-latens — men det fick vi räkna ut själva.)
- **Förslag på riktning:** tidsstämpel per tur, och gärna per tool-anrop
  (`latency_ms`). Ev. en `--timing`-flagga eller alltid i `--jsonl`.

### F3 — Körnings-summering + meningsfulla exit-koder  · prio: MEDEL
- **Observation:** exit-koden säger inte om alla turer kördes eller om något
  tool-anrop felade. Vi fick räkna användar-tur-rubriker i transkriptet för att
  verifiera att en körning var komplett, och leta efter inline-fel manuellt.
- **Impact:** i batch/CI går det inte att grinda på "gick körningen igenom?" utan
  att parsa transkriptet.
- **Förslag på riktning:** en slutrad/summering (antal turer, antal tool-anrop,
  antal tool-fel) och en exit-kod som blir non-zero vid tool-fel eller avbruten
  körning.

### F4 — Dumpbar verktygslista non-interaktivt  · prio: LÅG
- **Observation:** bannern ger *antal* verktyg; `/tools` finns interaktivt. I en
  scriptad körning kan vi inte enkelt fånga hela verktygsytan (namn + beskrivning
  + parametrar) till körnings-loggen.
- **Förslag på riktning:** en `--list-tools`(`--json`) som ansluter, skriver ut
  schemat och avslutar. Bra för att versionsstämpla "vilken yta testades".

---

## Icke-problem (mätt — så ni slipper jaga spöken)

- **Ingen EOF-hang.** En enstaka tur tar ~14,5 s *wall*, och harnessen avslutar
  rent direkt efter. Vi trodde först att vi sett en hang i batch-körning, men
  mätning visade att det var **kumulativ LLM-latens** över många turer × flera
  sessioner — inte harnessen.
- **Försumbar startup-overhead.** Connect+exit utan turer ≈ 0,45–0,51 s.
  `uv run mcp-harness` vs `.venv/bin/mcp-harness` skiljde ~0,06 s (lockfilen är
  cachead). Harness-overhead är alltså inte flaskhalsen — LLM-anropet är det.

---

## Mätningar (denna session, för referens)

| Mätning | Värde | Metod |
|---|---|---|
| Connect + exit (0 turer) | ~0,45–0,51 s | `/usr/bin/time -p`, tom stdin |
| 1 användartur (assistent-svar) | ~14,5 s wall | `/usr/bin/time -p`, 1 rad stdin |
| `uv run` vs direkt binär | +~0,06 s | samma, jämförelse |
| Per-tur-latens, dominerande källa | LLM (gemma via extern endpoint) | uträknat |

Modell: `google/gemma-4-31B-it` via extern OpenAI-kompatibel endpoint. Servern
var en MCP (Streamable HTTP) bakom Cloudflare-tunnel. Mätningarna gjordes med
LLM-endpointen i övrigt obelastad.

---

## En not om vårt eget angränsande behov (inte ett mcp-harness-krav)

Vår multi-case-körning (en separat harness i vårt repo, `roleplay.py`) körde
först **seriellt** — 7 case × multi-tur × LLM-latens blev 10–30 min. Vi
parallelliserade den på vår sida (7 samtidiga processer → ~2,5 min totalt).
Det här ligger hos *oss*, men det reser en fråga som kan vara relevant för er
roadmap: **om `mcp-harness` någon gång ska driva flera sessioner/case, är någon
form av samtidighet (eller en återanvändbar uppkoppling över sessioner) värd att
överväga** — i dag är varje körning en egen process/uppkoppling. Lågt prio, men
värt att ha med i bilden.

---

*Sammanställt av Claude (Opus 4.8) utifrån en faktisk regressionssession
2026-06-26. Frågor/komplettering: hör av er till use-case-mcp-projektet.*
