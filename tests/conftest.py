"""Delade testfixturer.

Princip (PRD §11): testa på riktigt.

- ``fake_llm`` startar en **riktig** HTTP-server på en ledig port och svarar med
  köade OpenAI-kompatibla svar — så hela kodvägen i ``llm.py`` (request-bygge,
  headers, proxy-hantering, retry, JSON-parse) verkligen exekveras. Ingen
  ``unittest.mock`` av ``urllib``.
- ``mcp_session`` ger en **riktig** ``ClientSession`` kopplad in-process till en
  fejk-MCP-server med kontrollerade verktyg (echo, multi_block, boom,
  structured). Inget mockar ``ClientSession``/``call_tool``/``list_tools``.
"""

from __future__ import annotations

import json
import threading
from collections.abc import Iterator
from contextlib import AbstractAsyncContextManager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

import mcp.types as mcp_types
import pytest
from mcp.client.session import ClientSession
from mcp.shared.memory import create_connected_server_and_client_session
from mcp.types import CallToolResult

from tests.support.fake_mcp import build_fake_mcp_server

JsonDict = dict[str, Any]


class FakeLLM:
    """En riktig HTTP-fejk av en OpenAI-kompatibel /chat/completions-endpoint.

    Köa svar med :meth:`queue` (eller fel-svar med :meth:`queue_status`); varje
    inkommen request registreras i :attr:`requests` för assertion.
    """

    def __init__(self) -> None:
        self._responses: list[tuple[int, JsonDict]] = []
        self.requests: list[JsonDict] = []
        self._server: ThreadingHTTPServer | None = None
        self._thread: threading.Thread | None = None
        self.url: str | None = None

    def queue(self, body: JsonDict, status: int = 200) -> FakeLLM:
        self._responses.append((status, body))
        return self

    def queue_status(self, status: int, times: int = 1) -> FakeLLM:
        """Köa ``times`` fel-svar (t.ex. 503) — exercerar retry-vägen på riktigt."""
        for _ in range(times):
            self._responses.append((status, {"error": {"message": "transient"}}))
        return self

    def _next(self) -> tuple[int, JsonDict]:
        if self._responses:
            return self._responses.pop(0)
        return (200, {"choices": [{"message": {"content": "(default)"}}]})

    def start(self) -> FakeLLM:
        fake = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args: object) -> None:  # tysta access-loggen
                pass

            def do_POST(self) -> None:  # noqa: N802 (BaseHTTPRequestHandler-API)
                length = int(self.headers.get("Content-Length", 0))
                raw = self.rfile.read(length) if length else b""
                try:
                    body = json.loads(raw) if raw else None
                except json.JSONDecodeError:
                    body = None
                fake.requests.append(
                    {"path": self.path, "headers": dict(self.headers), "body": body}
                )
                status, payload = fake._next()
                data = json.dumps(payload).encode()
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)

        self._server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        port = self._server.server_address[1]
        self.url = f"http://127.0.0.1:{port}/v1"
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)
        self._thread.start()
        return self

    def stop(self) -> None:
        if self._server is not None:
            self._server.shutdown()
            self._server.server_close()


@pytest.fixture
def fake_llm(monkeypatch: pytest.MonkeyPatch) -> Iterator[FakeLLM]:
    """Startad fejk-LLM med ``LLM_*`` pekade på den. Stängs i teardown."""
    fake = FakeLLM().start()
    monkeypatch.setenv("LLM_BASE_URL", fake.url or "")
    monkeypatch.setenv("LLM_API_KEY", "test-key")
    monkeypatch.setenv("LLM_MODEL", "test-model")
    monkeypatch.delenv("LLM_PROXY", raising=False)
    monkeypatch.delenv("LLM_PARAMS", raising=False)
    yield fake
    fake.stop()


def texts_of(result: CallToolResult) -> list[str]:
    """Text ur **alla** text-block i ett verktygssvar, i ordning.

    Smalnar av ContentBlock-unionen till TextContent. Återanvänds av T012:s
    tester (full verktygssvars-trohet) — poängen är att aldrig tyst tappa ett
    block (som ``content[0]`` gör)."""
    return [b.text for b in result.content if isinstance(b, mcp_types.TextContent)]


@pytest.fixture
def connected_session() -> AbstractAsyncContextManager[ClientSession]:
    """En **oöppnad** async context manager för en ClientSession kopplad till
    fejk-MCP-servern. Testet öppnar den själv (``async with connected_session as
    session:``) så att anyios cancel-scopes öppnas/stängs i samma task — annars
    far pytest-asyncios fixtur-teardown i en annan task och anyio failar."""
    return create_connected_server_and_client_session(build_fake_mcp_server())
