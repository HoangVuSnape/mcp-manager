import json
import os
import asyncio
from fastmcp import FastMCP
from fastmcp.server.openapi import FastMCPOpenAPI
from fastmcp.server.http import create_sse_app
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
        root_server.mount(prefix, sub_server)

    @root_server.custom_route("/health", methods=["GET"])
    async def health(_: Request):
        return JSONResponse({"status": "ok"})

    app = create_sse_app(server=root_server, message_path="/messages", sse_path="/sse")
    config = uvicorn.Config(app, host=cfg["server"]["host"], port=cfg["server"]["port"])
    server_uvicorn = uvicorn.Server(config)
    await server_uvicorn.serve()

if __name__ == "__main__":
    asyncio.run(main())
