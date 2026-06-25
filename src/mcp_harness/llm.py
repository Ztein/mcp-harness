"""Provider-agnostisk LLM-klient för scripts (T152).

Allt är config (princip 1) — ingen leverantör, URL eller modell hårdkodad:

    LLM_BASE_URL   OpenAI-kompatibel bas, t.ex. https://<host>/v1   (obligatorisk)
    LLM_API_KEY    API-nyckel                                        (obligatorisk)
    LLM_MODEL      modellsträng                                      (obligatorisk)
    LLM_PROXY      ev. proxy-URL för utgående anrop                  (valfri)
    LLM_PARAMS     ev. extra body-parametrar som JSON, t.ex.
                   {"temperature": 0}                                (valfri)

Saknad obligatorisk config → fail-hard med tydligt meddelande (princip 2).
On-prem/air-gapped pekar LLM_BASE_URL på den interna OpenAI-kompatibla endpointen.
"""

from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.request
from typing import Any


def _require(name: str) -> str:
    val = os.environ.get(name, "").strip()
    if not val:
        raise SystemExit(
            f"❌ {name} saknas. Sätt LLM-config i .env (LLM_BASE_URL, LLM_API_KEY, "
            "LLM_MODEL — ev. LLM_PROXY/LLM_PARAMS). Ingen leverantör är hårdkodad "
            "(princip 1)."
        )
    return val


def llm_model(override: str | None = None) -> str:
    """Modellsträng: explicit override (t.ex. --model) annars LLM_MODEL."""
    return override or _require("LLM_MODEL")


def _extra_params() -> dict[str, Any]:
    raw = os.environ.get("LLM_PARAMS", "").strip()
    if not raw:
        return {}
    try:
        parsed: dict[str, Any] = json.loads(raw)
        return parsed
    except json.JSONDecodeError as exc:
        raise SystemExit(f"❌ LLM_PARAMS är inte giltig JSON: {exc}") from exc


def _opener() -> urllib.request.OpenerDirector:
    proxy = os.environ.get("LLM_PROXY", "").strip()
    handler = (
        urllib.request.ProxyHandler({"http": proxy, "https": proxy})
        if proxy
        else urllib.request.ProxyHandler({})  # tom = ignorera ev. system-proxy
    )
    return urllib.request.build_opener(handler)


def chat_completion(
    messages: list[dict[str, Any]],
    tools: list[dict[str, Any]] | None = None,
    *,
    model: str | None = None,
    extra: dict[str, Any] | None = None,
    max_retries: int = 3,
    timeout: float = 180.0,
) -> dict[str, Any]:
    """Ett OpenAI-kompatibelt /chat/completions-anrop. Returnerar HELA svaret
    (inkl. usage). Retry på transienta nätverksfel. `extra` är per-anrop-
    body-parametrar (t.ex. {"temperature": 0}) — överstyr LLM_PARAMS."""
    base = _require("LLM_BASE_URL").rstrip("/")
    key = _require("LLM_API_KEY")
    body: dict[str, Any] = {
        "model": llm_model(model),
        "messages": messages,
        **_extra_params(),
        **(extra or {}),
    }
    if tools is not None:
        body["tools"] = tools
        body["tool_choice"] = "auto"
    req = urllib.request.Request(
        f"{base}/chat/completions",
        data=json.dumps(body).encode(),
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
    )
    opener = _opener()
    last: Exception | None = None
    for attempt in range(max_retries):
        try:
            with opener.open(req, timeout=timeout) as resp:
                parsed: dict[str, Any] = json.load(resp)
                return parsed
        except (TimeoutError, urllib.error.URLError, ConnectionError) as exc:
            last = exc
            # T161: varje misslyckat försök syns — annars ser operatören bara
            # en hängande terminal under hela backoff-summan.
            if attempt < max_retries - 1:
                wait = 2**attempt
                print(
                    f"  LLM-anrop misslyckades (försök {attempt + 1}/{max_retries}): "
                    f"{type(exc).__name__}: {exc} — väntar {wait}s",
                    file=sys.stderr,
                )
                time.sleep(wait)
    raise last or TimeoutError("LLM-anrop misslyckades")
