"""Route handlers and shared state for the Swagger server."""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastmcp import FastMCP
from fastmcp.server.openapi import FastMCPOpenAPI
import httpx

from . import db
from .utils.openapi_utils import _get_prefix, _load_spec

# Runtime storage for loaded OpenAPI specs and their configs
spec_data: dict[str, dict] = {}
spec_configs: dict[str, dict] = {}


async def close_clients(
    clients: list[httpx.AsyncClient], session_maker: db.async_sessionmaker
) -> None:
    for client in clients:
        await client.aclose()
    await session_maker.bind.dispose()


async def health(_: Request) -> JSONResponse:
    return JSONResponse({"status": "ok"})


def make_list_servers_handler(server_info: list[tuple[str, int]]):
    async def list_servers(_: Request) -> JSONResponse:
        return JSONResponse({"servers": [p for p, _ in server_info]})

    return list_servers


def make_add_server_handler(
    root_server: FastMCP,
    app: FastAPI,
    server_info: list[tuple[str, int]],
    clients: list[httpx.AsyncClient],
    cfg: dict,
    session_maker: db.async_sessionmaker,
):
    async def add_server(request: Request) -> JSONResponse:
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

        async with session_maker() as session:
            await db.add_spec(session, spec_cfg)

        return JSONResponse({"added": prefix, "tools": tool_count})

    return add_server


async def export_server(prefix: str, _: Request) -> JSONResponse:
    """Return the stored OpenAPI specification for a prefix."""
    if prefix not in spec_data:
        return JSONResponse({"error": "prefix not found"}, status_code=404)
    return JSONResponse(spec_data[prefix])


def make_set_tool_enabled_handler(
    root_server: FastMCP, session_maker: db.async_sessionmaker
):
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
        async with session_maker() as session:
            await db.set_tool_enabled(session, prefix, name, bool(enabled))
        return JSONResponse({"tool": name, "enabled": bool(enabled)})

    return set_tool_enabled

