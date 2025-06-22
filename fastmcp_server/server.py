"""FastMCP server exposing OpenAPI specs as MCP tools."""

import asyncio
import logging
import os
import sys
from functools import partial

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastmcp import FastMCP
from fastmcp.server.openapi import FastMCPOpenAPI
import httpx
import uvicorn

from . import db

from .routes import (
    close_clients,
    health,
    make_add_server_handler,
    make_list_servers_handler,
    make_list_tools_handler,
    make_set_tool_enabled_handler,
    export_server,
    spec_data,
)

from .utils.config_utils import DEFAULT_CONFIG, export_config, load_config
from .utils.db_utils import (
    load_config_from_postgres,
    save_config_to_postgres,
)
from .utils.openapi_utils import _get_prefix, _load_spec
from .utils import db_utils  # expose db_utils for tests

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def initialize_db(cfg: dict, db_url: str | None) -> db.async_sessionmaker:
    """Return a database sessionmaker based on the provided config."""
    db_url = db_url or cfg.get("database")
    if db_url:
        return await db.init_db(db_url)
    return await db.init_db("sqlite+aiosqlite:///:memory:")


async def load_specs(
    cfg: dict,
    root_server: FastMCP,
    app: FastAPI,
    session_maker: db.async_sessionmaker,
) -> tuple[list[tuple[str, int]], list[httpx.AsyncClient]]:
    """Load swagger specs and mount them into the root server."""
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

        prefix = _get_prefix(spec_cfg)
        spec_data[prefix] = spec

        tool_count = len(await sub_server.get_tools())
        server_info.append((prefix, tool_count))

        root_server.mount(prefix, sub_server)
        app.mount(f"/{prefix}", sub_server.sse_app())

        async with session_maker() as session:
            for ts in await db.get_tool_statuses(session, prefix):
                tools = await sub_server.get_tools()
                if ts.name in tools:
                    if ts.enabled:
                        tools[ts.name].enable()
                    else:
                        tools[ts.name].disable()

    return server_info, clients




async def create_app(cfg: dict, db_url: str | None = None) -> FastAPI:
    """Build and return the FastAPI application for the given config."""
    root_server = FastMCP(name="Swagger MCP Server")
    app = FastAPI()

    session_maker = await initialize_db(cfg, db_url)
    app.state.db_session = session_maker
    app.state.root_server = root_server

    server_info, clients = await load_specs(cfg, root_server, app, session_maker)

    logger.info("Loaded %d Swagger servers:", len(server_info))
    for prefix, count in server_info:
        logger.info("  - %s: %d tools", prefix, count)
    try:
        total_tools = len(await root_server.get_tools())
        logger.info("Total tools available: %d", total_tools)
    except Exception as exc:  # noqa: BLE001
        logger.error("Failed to count tools: %s", exc)

    app.add_api_route("/health", health, methods=["GET"])
    app.add_api_route(
        "/list-server",
        make_list_servers_handler(server_info),
        methods=["GET"],
    )
    app.add_api_route(
        "/list-tools",
        make_list_tools_handler(root_server),
        methods=["GET"],
    )
    app.add_api_route(
        "/add-server",
        make_add_server_handler(
            root_server,
            app,
            server_info,
            clients,
            cfg,
            session_maker,
        ),
        methods=["POST"],
    )
    app.add_api_route(
        "/export-server/{prefix}", export_server, methods=["GET"], name="export"
    )
    app.add_api_route(
        "/tool-enabled",
        make_set_tool_enabled_handler(root_server, session_maker),
        methods=["POST"],
    )

    # Mount shared server at root (after /health route)
    app.mount("/", root_server.sse_app())

    app.add_event_handler(
        "shutdown",
        partial(close_clients, clients=clients, session_maker=session_maker),
    )
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
