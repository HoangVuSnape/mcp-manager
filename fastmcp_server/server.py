"""FastMCP server exposing OpenAPI specs as MCP tools."""

import asyncio
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

from .utils.config_utils import DEFAULT_CONFIG, export_config, load_config
from .utils.db_utils import (
    load_config_from_postgres,
    save_config_to_postgres,
)
from .utils.openapi_utils import _get_prefix, _load_spec
from .utils import db_utils  # expose db_utils for tests

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Runtime storage for loaded OpenAPI specs and their configs
spec_data: dict[str, dict] = {}
spec_configs: dict[str, dict] = {}



async def create_app(cfg: dict, db_url: str | None = None) -> FastAPI:
    """Build and return the FastAPI application for the given config."""
    root_server = FastMCP(name="Swagger MCP Server")
    app = FastAPI()

    # Initialise database connection if provided
    db_url = db_url or cfg.get("database")
    session_maker = None
    if db_url:
        session_maker = await db.init_db(db_url)
    if session_maker is None:
        session_maker = await db.init_db("sqlite+aiosqlite:///:memory:")
    app.state.db_session = session_maker
    app.state.root_server = root_server

    server_info: list[tuple[str, int]] = []
    clients: list[httpx.AsyncClient] = []

    for spec_cfg in cfg["swagger"]:
        logger.info("Loading Swagger spec: %s", spec_cfg.get("path", "unknown"))
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

        # Apply stored tool enable states
        async with session_maker() as session:
            for ts in await db.get_tool_statuses(session, prefix):
                tools = await sub_server.get_tools()
                if ts.name in tools:
                    if ts.enabled:
                        tools[ts.name].enable()
                    else:
                        tools[ts.name].disable()

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

    async def set_tool_enabled(request: Request) -> JSONResponse:
        """Enable or disable a specific tool by prefix and name."""
        data = await request.json()
        prefix = data.get("prefix")
        name = data.get("name")
        enabled = data.get("enabled", False)
        if not prefix or not name:
            return JSONResponse({"error": "prefix and name required"}, status_code=400)
        server = root_server._mounted_servers.get(prefix)
        if server is None:
            return JSONResponse({"error": "prefix not found"}, status_code=404)
        tools = await server.get_tools()
        if name not in tools:
            return JSONResponse({"error": "tool not found"}, status_code=404)
        tool = tools[name]
        if enabled:
            tool.enable()
        else:
            tool.disable()
        async with app.state.db_session() as session:
            await db.set_tool_enabled(session, prefix, name, bool(enabled))
        return JSONResponse({"tool": name, "enabled": bool(enabled)})

    app.add_api_route("/health", health, methods=["GET"])
    app.add_api_route("/list-server", list_servers, methods=["GET"])
    app.add_api_route("/add-server", add_server, methods=["POST"])
    app.add_api_route(
        "/export-server/{prefix}", export_server, methods=["GET"], name="export"
    )
    app.add_api_route("/tool-enabled", set_tool_enabled, methods=["POST"])

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

    # Support comma separated list of config paths or URLs
    if "," in str(config_source):
        sources = [s.strip() for s in str(config_source).split(",") if s.strip()]
    else:
        sources = config_source

    extra_sources = os.environ.get("EXTRA_CONFIGS")
    if extra_sources:
        env_list = [s.strip() for s in extra_sources.split(",") if s.strip()]
        if isinstance(sources, list):
            sources.extend(env_list)
        else:
            sources = [sources] + env_list

    cfg = load_config(sources)

    db_url = os.environ.get("DB_URL")
    if db_url:
        db_cfg = load_config_from_postgres(db_url)
        if db_cfg:
            cfg = db_cfg
        else:
            save_config_to_postgres(cfg, db_url)

    export_path = os.environ.get("EXPORT_CONFIG")
    if export_path:
        export_config(cfg, export_path)
    app = await create_app(cfg)

    config = uvicorn.Config(
        app, host=cfg["server"]["host"], port=cfg["server"]["port"]
    )
    server_uvicorn = uvicorn.Server(config)
    await server_uvicorn.serve()

if __name__ == "__main__":
    # Optional config path or URL can be provided as the first argument
    config_arg = sys.argv[1] if len(sys.argv) > 1 else None
    asyncio.run(main(config_arg))
