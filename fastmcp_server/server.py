"""FastMCP server exposing OpenAPI specs as MCP tools."""

import asyncio
import json
import logging
import os
import sys
from fastmcp import FastMCP
from fastmcp.server.openapi import FastMCPOpenAPI
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import httpx
import uvicorn
from . import db

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
    },
    "database": "sqlite+aiosqlite:///fastmcp.db"
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

    if "database" not in cfg:
        db_url = os.environ.get("DB_URL")
        if db_url:
            cfg["database"] = db_url
        else:
            cfg["database"] = DEFAULT_CONFIG["database"]
    return cfg


async def create_app(cfg: dict, db_url: str | None = None) -> FastAPI:
    """Build and return the FastAPI application for the given config."""
    root_server = FastMCP(name="Swagger MCP Server")
    app = FastAPI()

    server_info: list[tuple[str, int]] = []
    clients: list[httpx.AsyncClient] = []
    spec_configs: dict[str, dict] = {}
    spec_data: dict[str, dict] = {}

    db_url = db_url or cfg.get("database")
    session_maker = await db.init_db(db_url)
    app.state.db_session = session_maker

    specs: list[dict] = []
    seen: set[str] = set()
    for spec_cfg in cfg.get("swagger", []):
        spec_cfg["prefix"] = _get_prefix(spec_cfg)
        if spec_cfg["prefix"] not in seen:
            seen.add(spec_cfg["prefix"])
            specs.append(spec_cfg)

    async with session_maker() as session:
        for stored in await db.get_specs(session):
            stored["prefix"] = _get_prefix(stored)
            if stored["prefix"] not in seen:
                seen.add(stored["prefix"])
                specs.append(stored)

    cfg["swagger"] = specs
    for spec_cfg in specs:
        spec_configs[_get_prefix(spec_cfg)] = spec_cfg

    for spec_cfg in specs:
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
        spec_data[_get_prefix(spec_cfg)] = spec

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

    async def add_server(request: Request):
        """Dynamically mount a new Swagger specification."""
        spec_cfg = await request.json()
        prefix = _get_prefix(spec_cfg)

        if any(p == prefix for p, _ in server_info):
            return JSONResponse({"error": "prefix already exists"}, status_code=400)

        try:
            spec = _load_spec(spec_cfg)
        except (httpx.HTTPError, ValueError) as exc:
            return JSONResponse({"error": str(exc)}, status_code=400)

        client = httpx.AsyncClient(base_url=spec_cfg["apiBaseUrl"])
        sub_server = FastMCPOpenAPI(
            openapi_spec=spec,
            client=client,
            name=f"{spec_cfg.get('prefix', 'api')} server",
        )
        spec_data[prefix] = spec
        spec_configs[prefix] = spec_cfg

        tool_count = len(await sub_server.get_tools())

        root_server.mount(prefix, sub_server)
        app.mount(f"/{prefix}", sub_server.sse_app())

        server_info.append((prefix, tool_count))
        clients.append(client)
        cfg.setdefault("swagger", []).append(spec_cfg)

        async with app.state.db_session() as session:
            await db.add_spec(session, spec_cfg)

        return JSONResponse({"added": prefix, "tools": tool_count})

    async def export_server(prefix: str, _: Request) -> JSONResponse:
        """Return the stored OpenAPI specification for a prefix."""
        if prefix not in spec_data:
            return JSONResponse({"error": "prefix not found"}, status_code=404)
        return JSONResponse(spec_data[prefix])

    app.add_api_route("/health", health, methods=["GET"])
    app.add_api_route("/list-server", list_servers, methods=["GET"])
    app.add_api_route("/add-server", add_server, methods=["POST"])
    app.add_api_route(
        "/export-server/{prefix}", export_server, methods=["GET"], name="export"
    )

    # Mount shared server at root (after /health route)
    app.mount("/", root_server.sse_app())

    async def close_clients() -> None:
        for client in clients:
            await client.aclose()
        await session_maker.bind.dispose()

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
    app = await create_app(cfg, cfg.get("database"))

    config = uvicorn.Config(
        app, host=cfg["server"]["host"], port=cfg["server"]["port"]
    )
    server_uvicorn = uvicorn.Server(config)
    await server_uvicorn.serve()



if __name__ == "__main__":
    # Optional config path or URL can be provided as the first argument
    config_arg = sys.argv[1] if len(sys.argv) > 1 else None
    asyncio.run(main(config_arg))
