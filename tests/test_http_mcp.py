"""T044 — test-MCP fristående över Streamable HTTP (riktig E2E-brygga).

Startar servern i en tråd (riktig uvicorn) och ansluter med en riktig
``ClientSession`` över HTTP — som CLI:t gör i skarp drift. Verifierar verktygs-
listning och att fel bearer avvisas (fail-hard, princip 3).
"""

from __future__ import annotations

import socket
import threading
import time
from collections.abc import Iterator

import pytest
import uvicorn
from mcp.client.session import ClientSession
from mcp.client.streamable_http import streamablehttp_client

from tests.support.fake_mcp import BearerAuthASGI, build_fake_mcp_server

KEY = "test-key"


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        port: int = s.getsockname()[1]
        return port


@pytest.fixture
def http_mcp() -> Iterator[str]:
    port = _free_port()
    srv = build_fake_mcp_server("127.0.0.1", port)
    app = BearerAuthASGI(srv.streamable_http_app(), KEY)
    config = uvicorn.Config(app, host="127.0.0.1", port=port, log_level="error")
    server = uvicorn.Server(config)
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    deadline = time.monotonic() + 10
    while not server.started:
        if time.monotonic() > deadline:
            raise RuntimeError("test-MCP-servern startade inte i tid")
        time.sleep(0.02)
    yield f"http://127.0.0.1:{port}/mcp"
    server.should_exit = True
    thread.join(timeout=5)


async def test_http_server_lists_tools_over_streamable_http(http_mcp: str) -> None:
    async with (
        streamablehttp_client(http_mcp, headers={"Authorization": f"Bearer {KEY}"}) as (r, w, _),
        ClientSession(r, w) as session,
    ):
        await session.initialize()
        names = {t.name for t in (await session.list_tools()).tools}
    assert {"echo", "multi_block", "boom", "structured"} <= names


async def test_wrong_bearer_rejected(http_mcp: str) -> None:
    # Fel nyckel → anslutningen ska faila (servern svarar 401), inte tyst släppa in.
    with pytest.raises(Exception):  # noqa: B017 (HTTP/anslutningsfel — vi bryr oss om att det reser sig)
        async with (
            streamablehttp_client(http_mcp, headers={"Authorization": "Bearer fel"}) as (r, w, _),
            ClientSession(r, w) as session,
        ):
            await session.initialize()
