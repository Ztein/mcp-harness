"""T031 — harness-profiler: bas-ramning runt skillen, scoping, approximation-not.

Profiler är data (PRD §5). Bas-ramningen läggs *runt* användarens skill utan att
skriva över den. En profil bär en ärlig 'skiljer sig här'-not (PRD §11) så en
grön körning inte misstas för 'verifierad i den riktiga harnessen'.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from mcp_harness.profiles import frame_system, load_profile


def test_raw_builtin_no_framing(tmp_path: Path) -> None:
    profile = load_profile("raw", search_dir=tmp_path)  # ingen fil → inbyggd raw
    assert frame_system(profile, "MIN SKILL") == "MIN SKILL"
    assert profile.approximation_note  # raw bär ändå en ärlig not


def test_profile_wraps_skill(tmp_path: Path) -> None:
    (tmp_path / "p.json").write_text(
        '{"name":"p","base_system":"HARNESS-RAMNING","approximation_note":"skiljer sig X"}',
        encoding="utf-8",
    )
    profile = load_profile("p", search_dir=tmp_path)
    framed = frame_system(profile, "MIN SKILL")
    assert "HARNESS-RAMNING" in framed
    assert "MIN SKILL" in framed  # skillen finns kvar, inte överskriven
    assert framed.index("HARNESS-RAMNING") < framed.index("MIN SKILL")  # ramning runt


def test_profile_scoping_loaded(tmp_path: Path) -> None:
    (tmp_path / "s.json").write_text('{"name":"s","tools_allow":["echo","boom"]}', encoding="utf-8")
    profile = load_profile("s", search_dir=tmp_path)
    assert profile.tools_allow == ["echo", "boom"]


def test_profile_carries_approximation_note(tmp_path: Path) -> None:
    (tmp_path / "n.json").write_text(
        '{"name":"n","approximation_note":"approximerar Intric, men X skiljer"}',
        encoding="utf-8",
    )
    assert "Intric" in load_profile("n", search_dir=tmp_path).approximation_note


def test_profile_not_found_fails_loudly(tmp_path: Path) -> None:
    with pytest.raises(SystemExit):
        load_profile("finns-ej", search_dir=tmp_path)


def test_profile_broken_json_fails_loudly(tmp_path: Path) -> None:
    (tmp_path / "bad.json").write_text("{trasig", encoding="utf-8")
    with pytest.raises(SystemExit):
        load_profile("bad", search_dir=tmp_path)
