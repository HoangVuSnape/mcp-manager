"""FastMCP server exposing OpenAPI specs as MCP tools."""

import asyncio
import json
import logging
import os
import sys
from fastmcp import FastMCP
from fastmcp.server.openapi import FastMCPOpenAPI
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse
import httpx
import uvicorn

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DEFAULT_CONFIG = {
    "swagger": [
        {
            "path": "examples/swagger-pet-store.json",
            "apiBaseUrl": "https://petstore.swagger.io/v2",
            "prefix": "petstore"
        }
    ],
    "server": {
        "host": "0.0.0.0",
        "port": 3000
    }
}


def _get_prefix(spec_cfg: dict) -> str:
    """Return mount prefix for a swagger spec."""
    if spec_cfg.get("prefix"):
        return spec_cfg["prefix"]
    path = spec_cfg.get("path", "")
    base = os.path.basename(path.split("?")[0])
    return os.path.splitext(base)[0]


def _load_spec(spec_cfg: dict) -> dict:
    """Load an OpenAPI specification from a path (local file or URL)."""
    path = spec_cfg.get("path")
    if not path:
        raise ValueError("Swagger config entry must include 'path'")
    if path.startswith("http://") or path.startswith("https://"):
        resp = httpx.get(path)
        resp.raise_for_status()
        return resp.json()
    if not os.path.isabs(path):
        path = os.path.join(os.path.dirname(__file__), path)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def load_config(source: str | None = None) -> dict:
    """Load configuration from a local file or remote URL."""
    if source is None:
        source = os.environ.get("CONFIG_URL", "config.json")

    if source.startswith("http://") or source.startswith("https://"):
        try:
            resp = httpx.get(source)
            resp.raise_for_status()
            cfg = resp.json()
        except httpx.HTTPError as exc:
            logger.error("Failed to fetch config from %s: %s", source, exc)
            cfg = DEFAULT_CONFIG
    else:
        if not os.path.isabs(source):
            source = os.path.join(os.path.dirname(__file__), source)
        if os.path.exists(source):
            with open(source, "r", encoding="utf-8") as f:
                cfg = json.load(f)
        else:
            cfg = DEFAULT_CONFIG

    if isinstance(cfg.get("swagger"), dict):
        cfg["swagger"] = [cfg["swagger"]]
    return cfg


async def create_app(cfg: dict) -> Starlette:
    """Build and return the Starlette application for the given config."""
    root_server = FastMCP(name="Swagger MCP Server")
    app = Starlette()

    server_info: list[tuple[str, int]] = []
    clients: list[httpx.AsyncClient] = []

    for spec_cfg in cfg["swagger"]:
        try:
            spec = _load_spec(spec_cfg)
        except (httpx.HTTPError, ValueError) as exc:
            logger.error("Failed to load spec: %s", exc)
            continue

        client = httpx.AsyncClient(base_url=spec_cfg["apiBaseUrl"])
        clients.append(client)

        sub_server = FastMCPOpenAPI(
            openapi_spec=spec,
            client=client,
            name=f"{spec_cfg.get('prefix', 'api')} server",
        )

        tool_count = len(await sub_server.get_tools())

        prefix = _get_prefix(spec_cfg)

        server_info.append((prefix, tool_count))

        # Mount tools into the shared root server
        root_server.mount(prefix, sub_server)

        # Mount individual SSE app for this swagger specification
        app.mount(f"/{prefix}", sub_server.sse_app())

    logger.info("Loaded %d Swagger servers:", len(server_info))
    for prefix, count in server_info:
        logger.info("  - %s: %d tools", prefix, count)
    try:
        total_tools = len(await root_server.get_tools())
        logger.info("Total tools available: %d", total_tools)
    except Exception as exc:  # noqa: BLE001
        logger.error("Failed to count tools: %s", exc)

    async def health(_: Request):
        return JSONResponse({"status": "ok"})

    async def list_servers(_: Request):
        return JSONResponse({"servers": [p for p, _ in server_info]})

    app.add_route("/health", health, methods=["GET"])
    app.add_route("/list-server", list_servers, methods=["GET"])

    # Mount shared server at root (after /health route)
    app.mount("/", root_server.sse_app())

    async def close_clients() -> None:
        for client in clients:
            await client.aclose()

    app.add_event_handler("shutdown", close_clients)
    return app

async def main(config_source: str | None = None) -> None:
    """Start the FastMCP server with configuration from a file or URL."""
    if config_source is None:
        # default to config.json in the same directory or CONFIG_URL env var
        config_source = os.environ.get(
            "CONFIG_URL",
            os.path.join(os.path.dirname(__file__), "config.json"),
        )

    cfg = load_config(config_source)
    app = await create_app(cfg)

    config = uvicorn.Config(
        app, host=cfg["server"]["host"], port=cfg["server"]["port"]
    )
    server_uvicorn = uvicorn.Server(config)
    await server_uvicorn.serve()

    for client in clients:
        await client.aclose()

if __name__ == "__main__":
    # Optional config path or URL can be provided as the first argument
    config_arg = sys.argv[1] if len(sys.argv) > 1 else None
    asyncio.run(main(config_arg))
