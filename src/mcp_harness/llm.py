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


class LlmError(RuntimeError):
    """Ett kurerat, handlingsbart LLM-fel (T026, F5).

    Bär ett meddelande som är färdigt att visa operatören — ``run_turn`` lägger
    det verbatim i en ``TurnError`` utan generisk prefix. ``category`` skiljer
    feltyp (timeout/auth/server/connection) för ev. programmatisk gren."""

    def __init__(self, message: str, category: str = "unknown") -> None:
        super().__init__(message)
        self.category = category


def _base() -> str:
    return os.environ.get("LLM_BASE_URL", "?")


def _is_transient_http(code: int) -> bool:
    """5xx, 408 (timeout) och 429 (rate limit) är värda en retry; övriga 4xx inte."""
    return code in (408, 429) or 500 <= code < 600


def _http_message(exc: urllib.error.HTTPError) -> str:
    """Handlingsbar rad för ett icke-transient HTTP-fel (auth/klientfel)."""
    if exc.code in (401, 403):
        return (
            f"LLM auth nekad (HTTP {exc.code}) — kontrollera LLM_API_KEY och "
            f"behörighet mot {_base()}."
        )
    return (
        f"LLM avvisade anropet (HTTP {exc.code}) — kontrollera modell/parametrar "
        f"och LLM_BASE_URL ({_base()})."
    )


def _is_timeout(exc: Exception | None) -> bool:
    return isinstance(exc, TimeoutError) or isinstance(getattr(exc, "reason", None), TimeoutError)


def _final_message(last: Exception | None, *, timeout: float, attempts: int) -> str:
    """Typspecifik, handlingsbar rad när retry-budgeten är slut."""
    if _is_timeout(last):
        return (
            f"LLM timeout: endpoint svarade inte inom {timeout:g}s ({attempts} försök) "
            f"— kontrollera LLM_BASE_URL/last ({_base()})."
        )
    if isinstance(last, urllib.error.HTTPError):
        return (
            f"LLM server-/gateway-fel efter {attempts} försök (HTTP {last.code}) — "
            f"försök igen senare eller kontrollera endpointen ({_base()})."
        )
    return (
        f"LLM-anslutning misslyckades efter {attempts} försök "
        f"({type(last).__name__}: {last}) — kontrollera LLM_BASE_URL ({_base()}) "
        f"och nätverk/proxy."
    )


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
    timeout: float = 60.0,
) -> dict[str, Any]:
    """Ett OpenAI-kompatibelt /chat/completions-anrop. Returnerar HELA svaret
    (inkl. usage). Retry på *transienta* fel (timeout/5xx/429/connection); auth-
    och klientfel (4xx) failar snabbt. Vid uttömd budget reses ``LlmError`` med
    en typspecifik, handlingsbar rad (T026). `extra` är per-anrop-body-parametrar
    (t.ex. {"temperature": 0}) — överstyr LLM_PARAMS."""
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
        except urllib.error.HTTPError as exc:
            # HTTPError ärver URLError → måste fångas FÖRST. Icke-transient (auth/
            # 4xx) failar snabbt; ingen retry på en felaktig nyckel/parameter.
            if not _is_transient_http(exc.code):
                raise LlmError(
                    _http_message(exc),
                    category="auth" if exc.code in (401, 403) else "client",
                ) from exc
            last = exc
        except (TimeoutError, urllib.error.URLError, ConnectionError) as exc:
            last = exc
        # T161: varje misslyckat (transient) försök syns — annars ser operatören
        # bara en hängande terminal under hela backoff-summan.
        if attempt < max_retries - 1:
            wait = 2**attempt
            print(
                f"  LLM-anrop misslyckades (försök {attempt + 1}/{max_retries}): "
                f"{type(last).__name__}: {last} — väntar {wait}s",
                file=sys.stderr,
            )
            time.sleep(wait)
    category = (
        "timeout"
        if _is_timeout(last)
        else ("server" if isinstance(last, urllib.error.HTTPError) else "connection")
    )
    raise LlmError(_final_message(last, timeout=timeout, attempts=max_retries), category=category)
