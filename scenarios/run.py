#!/usr/bin/env python3
"""Körhjälp för agent-driven E2E (T040).

Matar ett scenarios turer till mcp-harness CLI:t (piped stdin) och sparar
underlag (transkript + rådata + exit-kod) under ``scenarios/reports/`` så en
bedömare (agent/människa) kan döma PASS/FAIL semantiskt och spana förbättringar.

    uv run python scenarios/run.py scenarios/01-explore-unknown-mcp.md
    uv run python scenarios/run.py scenarios/02-tool-choice-scoping.md \
        --tools structured,multi_block --label B

Förutsätter att .env är ifylld (LLM_* + MCP_URL/MCP_KEY) och att test-MCP:n körs.
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REPORTS = Path(__file__).resolve().parent / "reports"
SYSTEM = Path(__file__).resolve().parent / "system.md"

_TURNS = re.compile(r"```turns\n(.*?)```", re.DOTALL)


def load_dotenv(path: Path) -> None:
    """Minimal .env-laddare (KEY=VALUE per rad). Ingen extern dependency."""
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip())


def extract_turns(scenario: Path) -> list[str]:
    text = scenario.read_text(encoding="utf-8")
    match = _TURNS.search(text)
    if not match:
        raise SystemExit(f"❌ inget ```turns-block i {scenario}")
    return [ln for ln in match.group(1).splitlines() if ln.strip()]


def main() -> int:
    parser = argparse.ArgumentParser(description="Kör ett E2E-scenario genom mcp-harness.")
    parser.add_argument("scenario", type=Path)
    parser.add_argument("--tools", help="allowlist som skickas vidare till CLI:t (scoping-variant)")
    parser.add_argument("--label", default="", help="suffix för rapportfilnamn, t.ex. B")
    args = parser.parse_args()

    load_dotenv(ROOT / ".env")
    for required in ("LLM_BASE_URL", "LLM_API_KEY", "LLM_MODEL", "MCP_URL", "MCP_KEY"):
        if not os.environ.get(required):
            raise SystemExit(f"❌ {required} saknas — fyll .env (se .env.example).")

    turns = extract_turns(args.scenario)
    REPORTS.mkdir(parents=True, exist_ok=True)
    stem = args.scenario.stem + (f".{args.label}" if args.label else "")
    transcript = REPORTS / f"{stem}.transcript.md"
    raw_path = REPORTS / f"{stem}.raw.txt"

    cmd = [
        sys.executable,
        "-m",
        "mcp_harness.cli",
        "--system",
        str(SYSTEM),
        "--transcript",
        str(transcript),
    ]
    if args.tools:
        cmd += ["--tools", args.tools]

    # Färskt transkript per körning — CLI:t öppnar i append-läge, så en gammal
    # körning skulle annars ligga kvar och fördubbla rapporten.
    transcript.unlink(missing_ok=True)
    stdin = "\n".join(turns) + "\n"
    proc = subprocess.run(cmd, input=stdin, capture_output=True, text=True, cwd=ROOT)
    raw_path.write_text(
        f"$ {' '.join(cmd)}\n--- STDIN ---\n{stdin}\n--- STDOUT ---\n{proc.stdout}\n"
        f"--- STDERR ---\n{proc.stderr}\n--- EXIT {proc.returncode} ---\n",
        encoding="utf-8",
    )

    print(proc.stdout)
    if proc.stderr.strip():
        print("--- STDERR ---", proc.stderr, sep="\n", file=sys.stderr)
    print(f"\n[scenario {stem}] exit={proc.returncode}")
    print(f"  transkript: {transcript}")
    print(f"  rådata:     {raw_path}")
    return proc.returncode


if __name__ == "__main__":
    raise SystemExit(main())
