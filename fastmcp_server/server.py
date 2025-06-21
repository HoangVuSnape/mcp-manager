import json
import os
import asyncio
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

def load_config(path: str = "config.json") -> dict:
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            cfg = json.load(f)
    else:
        cfg = DEFAULT_CONFIG
    if isinstance(cfg.get("swagger"), dict):
        cfg["swagger"] = [cfg["swagger"]]
    return cfg

async def main() -> None:
    cfg = load_config(os.path.join(os.path.dirname(__file__), "config.json"))

    root_server = FastMCP(name="Swagger MCP Server")
    app = Starlette()

    for spec_cfg in cfg["swagger"]:
        file_path = os.path.join(os.path.dirname(__file__), spec_cfg["file"])
        with open(file_path, "r", encoding="utf-8") as f:
            spec = json.load(f)

        client = httpx.AsyncClient(base_url=spec_cfg["apiBaseUrl"])

        sub_server = FastMCPOpenAPI(
            openapi_spec=spec,
            client=client,
            name=f"{spec_cfg.get('prefix', 'api')} server",
        )

        prefix = spec_cfg.get("prefix") or os.path.splitext(os.path.basename(spec_cfg["file"]))[0]

        # Mount tools into the shared root server
        root_server.mount(prefix, sub_server)

        # Mount individual SSE app for this swagger file
        app.mount(f"/{prefix}", sub_server.sse_app())

    async def health(_: Request):
        return JSONResponse({"status": "ok"})

    app.add_route("/health", health, methods=["GET"])

    # Mount shared server at root (after /health route)
    app.mount("/", root_server.sse_app())

    config = uvicorn.Config(app, host=cfg["server"]["host"], port=cfg["server"]["port"])
    server_uvicorn = uvicorn.Server(config)
    await server_uvicorn.serve()

if __name__ == "__main__":
    asyncio.run(main())
