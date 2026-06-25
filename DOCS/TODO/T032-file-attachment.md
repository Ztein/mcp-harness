# T032 — fil-uppladdning / kontext

**Status:** TODO · **Fas:** 3 · **Prioritet:** P2 · **Beror på:** T011, T012

## Varför

PRD §6.4 / Fas 3 (uttryckligt användar-önskemål): kunna bifoga filer till
konversationen och se hur MCP+modell hanterar dem — text inline som kontext,
bild/PDF som multimodalt innehåll där modellen stödjer det. Speglar hur riktiga
harnesses låter användaren ladda upp underlag.

## Omfattning

**Ingår:** `--attach <fil>` och `/attach <fil>` i REPL; text-filer inline:as som
kontext; bild/PDF skickas som multimodalt innehåll mot modeller som stödjer det
(fail-hard med tydligt meddelande mot modeller som inte gör det). Bilagan loggas
i JSONL (namn, typ, storlek — inte nödvändigtvis hela innehållet).

**Ingår inte:** OCR eller dokument-förbehandling — råinnehåll skickas som det är.

## Definition of Done

- [ ] `--attach`/`/attach` läser fil och fogar in den i nästa tur.
- [ ] Textfil → inline-kontext; modellen ser innehållet.
- [ ] Bild/PDF → multimodalt block mot stödjande modell; mot icke-stödjande →
      **fail-hard** med tydligt fel (ingen tyst nedgradering).
- [ ] Bilaga registreras i JSONL (metadata).

## Testfall (skriv först)

1. `test_attach_text_inlined` → bifoga `.md` → fejk-LLM ser innehållet i nästa
   request-body.
2. `test_attach_image_multimodal_block` → bifoga bild → request bär ett
   multimodalt content-block.
3. `test_attach_unsupported_model_fails_loudly` → multimodalt mot modell utan
   stöd (markerat) → tydligt fel, ingen tyst släng.
4. `test_attach_recorded_in_jsonl` → bilagans metadata finns i loggen.

## Noteringar

Lås exakt multimodalt format mot den faktiska OpenAI-kompatibla endpointens
kontrakt när ticketen tas — bekräfta via doc-verktyget.
