"""Harness-profiler (T031, PRD §5) — produktens särdrag.

En profil beskriver hur en värd-harness presenterar MCP:er för sin modell. MVP
fångar: **bas-ramning** runt användarens skill, **scoping** (allowlist), och en
ärlig **approximation-not** (PRD §11) som följer med i loggen — så en grön körning
inte misstas för 'verifierad i den riktiga harnessen'.

Profiler är data (en JSON-fil), inte kod — användare kan skriva och dela egna.
Ramningen läggs *runt* skillen, aldrig över den.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Profile:
    name: str
    base_system: str = ""
    tools_allow: list[str] | None = None
    approximation_note: str = ""


# Inbyggd raw-profil: ingen extra ramning. Bär ändå en ärlig not.
RAW = Profile(
    name="raw",
    approximation_note="raw — ingen extra ramning; speglar ingen specifik harness.",
)


def frame_system(profile: Profile, skill: str) -> str:
    """Lägg profilens bas-ramning *runt* skillen (skillen bevaras oförändrad)."""
    if profile.base_system:
        return f"{profile.base_system}\n\n{skill}"
    return skill


def load_profile(spec: str, *, search_dir: Path | str = "profiles") -> Profile:
    """Ladda en profil per namn (``profiles/<namn>.json``) eller sökväg.

    ``raw`` faller tillbaka på den inbyggda profilen om ingen fil finns.
    Saknad eller trasig profil failar hårt (princip 3)."""
    search = Path(search_dir)
    path = search / f"{spec}.json"
    if not path.exists() and Path(spec).exists():
        path = Path(spec)
    if not path.exists():
        if spec == "raw":
            return RAW
        raise SystemExit(f"❌ profil '{spec}' hittades inte (sökte {search}/{spec}.json).")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"❌ profil {path}: ogiltig JSON: {exc}") from exc
    return Profile(
        name=str(data.get("name", spec)),
        base_system=str(data.get("base_system", "")),
        tools_allow=data.get("tools_allow"),
        approximation_note=str(data.get("approximation_note", "")),
    )
