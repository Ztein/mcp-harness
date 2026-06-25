"""Fil-uppladdning / kontext (T032, PRD §6.4).

Textfiler inline:as som kontext; bilder skickas som multimodalt innehåll (data-URI)
mot modeller som stödjer det. En typ vi inte hanterar failar högljutt — ingen
tyst nedgradering (princip 3).
"""

from __future__ import annotations

import base64
import mimetypes
from dataclasses import dataclass
from pathlib import Path
from typing import Any

TEXT_EXT = {
    ".txt",
    ".md",
    ".json",
    ".csv",
    ".log",
    ".py",
    ".yaml",
    ".yml",
    ".toml",
    ".xml",
    ".html",
}
IMAGE_EXT = {".png", ".jpg", ".jpeg", ".gif", ".webp"}


@dataclass
class Attachment:
    name: str
    kind: str  # "text" | "image"
    size: int
    text: str | None = None
    data_uri: str | None = None


def load_attachment(path: str | Path) -> Attachment:
    """Läs en bilaga. Textfil → inline; bild → data-URI. Saknad fil eller typ vi
    inte hanterar failar hårt (princip 3)."""
    p = Path(path)
    if not p.exists():
        raise SystemExit(f"❌ bilaga saknas: {p}")
    ext = p.suffix.lower()
    raw = p.read_bytes()
    if ext in TEXT_EXT:
        return Attachment(
            name=p.name, kind="text", size=len(raw), text=raw.decode("utf-8", errors="replace")
        )
    if ext in IMAGE_EXT:
        mime = mimetypes.guess_type(p.name)[0] or "image/png"
        b64 = base64.b64encode(raw).decode("ascii")
        return Attachment(
            name=p.name, kind="image", size=len(raw), data_uri=f"data:{mime};base64,{b64}"
        )
    raise SystemExit(
        f"❌ bilaga {p.name}: filtypen '{ext}' stöds inte "
        f"(text: {sorted(TEXT_EXT)} eller bild: {sorted(IMAGE_EXT)})."
    )


def build_user_content(text: str, attachments: list[Attachment]) -> str | list[dict[str, Any]]:
    """Bygg en användartur. Utan bilagor → enkel sträng (oförändrat). Med bilagor
    → OpenAI-multimodalt blockformat (text + ev. bilder)."""
    if not attachments:
        return text
    blocks: list[dict[str, Any]] = [{"type": "text", "text": text}]
    for a in attachments:
        if a.kind == "text":
            blocks.append({"type": "text", "text": f"[Bilaga: {a.name}]\n{a.text}"})
        else:
            blocks.append({"type": "image_url", "image_url": {"url": a.data_uri}})
    return blocks
