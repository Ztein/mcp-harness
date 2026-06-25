"""T032 — fil-uppladdning: text inline, bild multimodalt, okänd typ fail-hard.

Speglar hur harnesses låter användaren ladda upp underlag (PRD §6.4). Ingen tyst
nedgradering: en typ vi inte hanterar failar högljutt (princip 3).
"""

from __future__ import annotations

from pathlib import Path

import pytest

from mcp_harness.attachments import build_user_content, load_attachment


def test_attach_text_inlined(tmp_path: Path) -> None:
    f = tmp_path / "doc.md"
    f.write_text("# Rubrik\nInnehåll", encoding="utf-8")
    a = load_attachment(f)
    assert a.kind == "text"
    assert a.text is not None and "Innehåll" in a.text
    content = build_user_content("Vad står i filen?", [a])
    # Multimodalt/blockformat med textfrågan + filinnehållet.
    assert isinstance(content, list)
    joined = " ".join(b["text"] for b in content if b["type"] == "text")
    assert "Vad står i filen?" in joined
    assert "Innehåll" in joined


def test_attach_image_multimodal_block(tmp_path: Path) -> None:
    f = tmp_path / "bild.png"
    f.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 16)  # PNG-magi + skräp
    a = load_attachment(f)
    assert a.kind == "image"
    content = build_user_content("Vad ser du?", [a])
    assert isinstance(content, list)
    img = [b for b in content if b["type"] == "image_url"]
    assert img and img[0]["image_url"]["url"].startswith("data:image/png;base64,")


def test_attach_unsupported_type_fails_loudly(tmp_path: Path) -> None:
    f = tmp_path / "program.bin"
    f.write_bytes(b"\x00\x01\x02")
    with pytest.raises(SystemExit) as exc:
        load_attachment(f)
    assert "bin" in str(exc.value)


def test_attach_missing_file_fails_loudly(tmp_path: Path) -> None:
    with pytest.raises(SystemExit):
        load_attachment(tmp_path / "finns-ej.md")


def test_no_attachments_keeps_plain_string() -> None:
    # Ingen bilaga → enkel sträng (oförändrat beteende).
    assert build_user_content("hej", []) == "hej"


def test_attachment_metadata_recorded(tmp_path: Path) -> None:
    f = tmp_path / "data.json"
    f.write_text('{"a":1}', encoding="utf-8")
    a = load_attachment(f)
    assert a.name == "data.json"
    assert a.size == len('{"a":1}')
