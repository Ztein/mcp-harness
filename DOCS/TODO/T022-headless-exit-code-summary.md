# T022 — headless exit-kod + enrads-sammanfattning

**Status:** TODO · **Fas:** 2 · **Prioritet:** P0 · **Beror på:** T011

## Varför

Test-agenten driver harnessen från Bash, ibland i bakgrund/SSH (PRD §11). Den
måste kunna **greena/röda en körning programmatiskt**: exit≠0 om en tur slutligen
misslyckades, plus en enrads-sammanfattning (turer, verktygsanrop, fel). Idag är
exit alltid 0 och det finns inga TTY-fria garantier.

## Omfattning

**Ingår:**
- Ren exit-kod: `0` om alla turer gav ett textsvar; `≠0` om någon tur slutligen
  misslyckades (LLM-fel som inte återhämtades, eller broms-tak T023 slog till).
- En enrads-sammanfattning till stderr/stdout vid avslut: antal turer,
  verktygsanrop, fel.
- Helt headless: inga `input()`-antaganden i piped läge; EOF avslutar rent.

**Ingår inte:** broms/tak-logiken (T023), men exit-koden ska reflektera den.

## Definition of Done

- [ ] Piped körning utan TTY fungerar och avslutar rent vid EOF.
- [ ] Exit `0` när alla turer lyckades; exit `≠0` när minst en slutligen
      misslyckades.
- [ ] Enrads-sammanfattning skrivs vid avslut, oavsett utfall.
- [ ] Sammanfattningen och exit-koden är samstämmiga (inte exit 0 + ”1 fel”).

## Testfall (skriv först)

1. `test_all_turns_succeed_exit_zero` → piped lyckad flertur → exit 0.
2. `test_final_failure_exit_nonzero` → fejk-LLM failar slutligt på en tur → exit≠0.
3. `test_summary_line_counts` → kör N turer med M verktygsanrop → sammanfattningen
   rapporterar N och M korrekt.
4. `test_eof_exits_cleanly` → stäng stdin → ren avslutning, ingen traceback.
5. `test_no_tty_no_input_prompt` → i piped läge skrivs ingen interaktiv `> `-prompt
   som blockerar.

## Noteringar

Testa exit-koden via subprocess mot CLI:t (riktig process, riktig pipe) — det är
exakt så test-agenten kör det. Mocka inte `sys.exit`; observera den faktiska koden.
