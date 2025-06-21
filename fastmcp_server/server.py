import json
import os
import asyncio
import sys
from fastmcp import FastMCP
from fastmcp.server.openapi import FastMCPOpenAPI
from starlette.applications import Starlette
from starlette.routing import Mount, Route
import httpx
import uvicorn
from starlette.responses import JSONResponse
from starlette.requests import Request

DEFAULT_CONFIG = {
    "swagger": [
        {
            "file": "examples/swagger-pet-store.json",
            "apiBaseUrl": "https://petstore.swagger.io/v2",
            "prefix": "petstore"
        }
    ],
    "server": {
        "host": "0.0.0.0",
        "port": 3000
    }
}

def load_config(source: str | None = None) -> dict:
    """Load configuration from a local file or remote URL."""
    if source is None:
        source = os.environ.get("CONFIG_URL", "config.json")

    if source.startswith("http://") or source.startswith("https://"):
        try:
            resp = httpx.get(source)
            resp.raise_for_status()
            cfg = resp.json()
        except Exception as exc:
            print(f"Failed to fetch config from {source}: {exc}")
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

async def main(config_source: str | None = None) -> None:
    """Start the FastMCP server with configuration from a file or URL."""
    if config_source is None:
        # default to config.json in the same directory or CONFIG_URL env var
        config_source = os.environ.get("CONFIG_URL", os.path.join(os.path.dirname(__file__), "config.json"))

    cfg = load_config(config_source)

    root_server = FastMCP(name="Swagger MCP Server")
    app = Starlette()

    server_info: list[tuple[str, int]] = []

    for spec_cfg in cfg["swagger"]:
        # Load the OpenAPI spec from a file or URL
        if spec_cfg.get("file"):
            file_path = spec_cfg["file"]
            if not os.path.isabs(file_path):
                file_path = os.path.join(os.path.dirname(__file__), file_path)
            with open(file_path, "r", encoding="utf-8") as f:
                spec = json.load(f)
        elif spec_cfg.get("url"):
            try:
                resp = httpx.get(spec_cfg["url"])
                resp.raise_for_status()
                spec = resp.json()
            except Exception as exc:
                print(f"Failed to fetch spec {spec_cfg['url']}: {exc}")
                continue
        else:
            print("Swagger config entry must include 'file' or 'url'")
            continue

        client = httpx.AsyncClient(base_url=spec_cfg["apiBaseUrl"])

        sub_server = FastMCPOpenAPI(
            openapi_spec=spec,
            client=client,
            name=f"{spec_cfg.get('prefix', 'api')} server",
        )

        tool_count = len(await sub_server.get_tools())

        if spec_cfg.get("prefix"):
            prefix = spec_cfg["prefix"]
        else:
            if spec_cfg.get("file"):
                prefix = os.path.splitext(os.path.basename(spec_cfg["file"]))[0]
            else:
                prefix = os.path.splitext(os.path.basename(spec_cfg["url"].split("?")[0]))[0]

        server_info.append((prefix, tool_count))

        # Mount tools into the shared root server
        root_server.mount(prefix, sub_server)

        # Mount individual SSE app for this swagger file
        app.mount(f"/{prefix}", sub_server.sse_app())

    print(f"Loaded {len(server_info)} Swagger servers:")
    for prefix, count in server_info:
        print(f"  - {prefix}: {count} tools")
    try:
        total_tools = len(await root_server.get_tools())
        print(f"Total tools available: {total_tools}")
    except Exception:
        pass

    async def health(_: Request):
        return JSONResponse({"status": "ok"})

    app.add_route("/health", health, methods=["GET"])

    # Mount shared server at root (after /health route)
    app.mount("/", root_server.sse_app())

    config = uvicorn.Config(app, host=cfg["server"]["host"], port=cfg["server"]["port"])
    server_uvicorn = uvicorn.Server(config)
    await server_uvicorn.serve()

if __name__ == "__main__":
    # Optional config path or URL can be provided as the first argument
    config_arg = sys.argv[1] if len(sys.argv) > 1 else None
    asyncio.run(main(config_arg))
