"""Delad fejk-MCP-server (T002 + T044).

Verktygsdefinitionerna används både av unit-testernas in-process-fixtur
(``connected_session``) och av den **körbara** Streamable-HTTP-servern för riktig
E2E. Samma server, två transporter — så agent-drivna scenarier (T040) kan köras
``CLI-process → riktig HTTP → MCP-server`` mot en kontrollerbar server.

Kör fristående:

    uv run python -m tests.support.fake_mcp --port 8765 --key test-key

Verktyg: ``echo`` (en runtripp), ``multi_block`` (flera content-block),
``boom`` (kastar fel), ``structured`` (JSON-struktur).
"""

from __future__ import annotations

import argparse
from collections.abc import Awaitable, Callable
from typing import Any

import mcp.types as mcp_types
from mcp.server.fastmcp import FastMCP

JsonDict = dict[str, Any]


def build_fake_mcp_server(host: str = "127.0.0.1", port: int = 8765) -> FastMCP:
    """En minimal MCP-server med kontrollerade verktyg, enbart för tester."""
    srv = FastMCP("test-mcp", host=host, port=port)

    @srv.tool()
    def echo(text: str) -> str:
        return text

    @srv.tool()
    def multi_block() -> list[mcp_types.TextContent]:
        return [
            mcp_types.TextContent(type="text", text="block-A"),
            mcp_types.TextContent(type="text", text="block-B"),
        ]

    @srv.tool()
    def boom() -> str:
        raise ValueError("avsiktligt fel")

    @srv.tool()
    def structured() -> JsonDict:
        return {"id": "abc-123", "status": "ok", "missing": ["alpha", "beta"]}

    return srv


class BearerAuthASGI:
    """Rå ASGI-middleware som kräver ``Authorization: Bearer <token>``.

    Rå (inte BaseHTTPMiddleware) för att inte buffra/bryta MCP:s strömmande
    svar. Fel/ingen nyckel → 401 (fail-hard, princip 3)."""

    def __init__(self, app: Any, token: str) -> None:
        self._app = app
        self._expected = f"Bearer {token}".encode()

    async def __call__(
        self,
        scope: dict[str, Any],
        receive: Callable[[], Awaitable[Any]],
        send: Callable[..., Awaitable[None]],
    ) -> None:
        if scope["type"] == "http":
            headers = dict(scope.get("headers") or [])
            if headers.get(b"authorization") != self._expected:
                await send(
                    {
                        "type": "http.response.start",
                        "status": 401,
                        "headers": [(b"content-type", b"application/json")],
                    }
                )
                await send({"type": "http.response.body", "body": b'{"error":"unauthorized"}'})
                return
        await self._app(scope, receive, send)


def main() -> None:
    parser = argparse.ArgumentParser(description="Körbar fejk-MCP (Streamable HTTP eller stdio).")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--key", default="test-key", help="förväntad bearer-nyckel")
    parser.add_argument(
        "--stdio", action="store_true", help="kör över stdio istället för HTTP (T034)"
    )
    args = parser.parse_args()

    srv = build_fake_mcp_server(args.host, args.port)
    if args.stdio:
        # I stdio-läge är stdout protokoll-kanalen — skriv ingenting dit.
        srv.run(transport="stdio")
        return

    import uvicorn

    app = BearerAuthASGI(srv.streamable_http_app(), args.key)
    print(f"Test-MCP lyssnar på http://{args.host}:{args.port}/mcp (bearer krävs)")
    uvicorn.run(app, host=args.host, port=args.port, log_level="warning")


if __name__ == "__main__":
    main()
