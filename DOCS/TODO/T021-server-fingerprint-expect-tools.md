# T021 — server-fingeravtryck + `--expect-tools` (fail-hard)

**Status:** TODO · **Fas:** 2 · **Prioritet:** P0 · **Beror på:** T010

## Varför

Test-agentens dyraste incident (PRD §11): en **stale server** (rätt antal verktyg,
gammal kod) maskerade sig och kostade en hel felsökningsrunda. Harnessen ska göra
det omöjligt att tro att man testar ny kod när man testar gammal. Lösning: skriv
ut verktygs-**namnen** (inte bara antal) + en hash av verktygsschemat vid
anslutning, och låt en förväntan **faila högljutt** vid avvikelse.

## Omfattning

**Ingår:**
- Vid anslutning: skriv verktygsnamn (sorterade) + en stabil hash av det
  aggregerade verktygsschemat (namn + beskrivning + inputSchema) till stdout och
  till JSONL-headern (T020).
- `--expect-tools a,b,c`: failar med exit≠0 om den faktiska verktygsmängden
  avviker (saknade och oväntade listas).
- Valfri `--expect-tools-count N` som enklare räknare.

**Ingår inte:** profil-medveten meny (T031) — men hashen ska beräknas på den
faktiska menyn modellen ser (efter allowlist/scoping), inte råservern.

## Definition of Done

- [ ] Verktygs-fingeravtryck (sorterade namn + schemahash) skrivs vid anslutning
      och i JSONL-headern.
- [ ] Hashen är **stabil** mellan körningar för samma schema och **ändras** när
      ett verktygs schema ändras.
- [ ] `--expect-tools` failar högljutt (exit≠0, tydligt meddelande med saknade +
      oväntade namn) vid avvikelse; matchar → tyst grönt.
- [ ] Fingeravtrycket beräknas på menyn **efter** allowlist/scoping.

## Testfall (skriv först)

1. `test_fingerprint_stable_across_runs` → samma fejk-MCP → identisk hash två ggr.
2. `test_fingerprint_changes_on_schema_change` → ändra ett verktygs inputSchema →
   hashen ändras.
3. `test_expect_tools_match_passes` → `--expect-tools echo,boom,...` lika med
   faktiska → ingen exit.
4. `test_expect_tools_mismatch_fails_loudly` → förvänta ett verktyg som saknas →
   `SystemExit`/exit≠0 som listar det saknade.
5. `test_fingerprint_reflects_allowlist` → med allowlist `{echo}` → hash/namn
   speglar bara `echo`.

## Noteringar

Detta är kärnan i ”fail-hard, aldrig tyst” (princip 3). En grön körning mot fel
serverversion är det värsta utfallet — denna ticket gör det omöjligt.
