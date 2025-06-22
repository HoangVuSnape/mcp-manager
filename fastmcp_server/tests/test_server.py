import json
import asyncio
import httpx
import pytest
from fastmcp_server import server


def test_load_config_local(tmp_path):
    cfg_path = tmp_path / "config.json"
    cfg_data = {"swagger": [], "server": {"host": "127.0.0.1", "port": 1234}}
    cfg_path.write_text(json.dumps(cfg_data))
    cfg = server.load_config(str(cfg_path))
    assert cfg["server"]["port"] == 1234


def test_load_config_remote(monkeypatch):
    class FakeResp:
        def __init__(self, data):
            self._data = data

        def raise_for_status(self):
            pass

        def json(self):
            return self._data

    def fake_get(url):
        return FakeResp({"swagger": [], "server": {"host": "0.0.0.0", "port": 9999}})

    monkeypatch.setattr(httpx, "get", fake_get)
    cfg = server.load_config("https://example.com/config.json")
    assert cfg["server"]["port"] == 9999


def test_get_prefix_from_file():
    spec_cfg = {
        "path": "examples/swagger-pet-store.json",
        "apiBaseUrl": "https://example.com",
    }
    spec = server._load_spec(spec_cfg)
    client = httpx.AsyncClient(base_url=spec_cfg["apiBaseUrl"])
    sub_server = server.FastMCPOpenAPI(openapi_spec=spec, client=client)
    tools = asyncio.run(sub_server.get_tools())
    asyncio.run(client.aclose())
    assert len(tools) > 0
    assert server._get_prefix(spec_cfg) == "swagger-pet-store"


def test_get_prefix_from_url(monkeypatch):
    spec_data = {"openapi": "3.0.0", "paths": {}, "info": {"title": "t", "version": "1"}}

    class FakeResp:
        def __init__(self, data):
            self._data = data

        def raise_for_status(self):
            pass

        def json(self):
            return self._data

    def fake_get(url):
        return FakeResp(spec_data)

    monkeypatch.setattr(httpx, "get", fake_get)

    spec_cfg = {
        "path": "https://example.com/pet.json",
        "apiBaseUrl": "https://example.com",
    }
    spec = server._load_spec(spec_cfg)
    client = httpx.AsyncClient(base_url=spec_cfg["apiBaseUrl"])
    sub_server = server.FastMCPOpenAPI(openapi_spec=spec, client=client)
    tools = asyncio.run(sub_server.get_tools())
    asyncio.run(client.aclose())
    assert len(tools) == 0
    assert server._get_prefix(spec_cfg) == "pet"


def test_list_server_endpoint():
    cfg = server.load_config()
    cfg["database"] = "sqlite+aiosqlite:///:memory:"

    app = asyncio.run(server.create_app(cfg))

    async def _call() -> httpx.Response:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            return await client.get("/list-server")

    resp = asyncio.run(_call())
    assert resp.status_code == 200
    assert cfg["swagger"][0]["prefix"] in resp.json()["servers"]


def test_add_server_endpoint(monkeypatch):
    spec_data = {"openapi": "3.0.0", "paths": {}, "info": {"title": "t", "version": "1"}}

    class FakeResp:
        def __init__(self, data):
            self._data = data

        def raise_for_status(self):
            pass

        def json(self):
            return self._data

    def fake_get(url):
        return FakeResp(spec_data)

    monkeypatch.setattr(httpx, "get", fake_get)

    cfg = server.load_config()
    cfg["database"] = "sqlite+aiosqlite:///:memory:"
    app = asyncio.run(server.create_app(cfg))

    async def _call() -> tuple[httpx.Response, httpx.Response]:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            add_resp = await client.post(
                "/add-server",
                json={"path": "https://example.com/new.json", "apiBaseUrl": "https://example.com", "prefix": "new"},
            )
            list_resp = await client.get("/list-server")
            return add_resp, list_resp

    add_resp, list_resp = asyncio.run(_call())
    assert add_resp.status_code == 200
    assert "new" in list_resp.json()["servers"]


def test_add_server_persisted(monkeypatch, tmp_path):
    spec_data = {"openapi": "3.0.0", "paths": {}, "info": {"title": "t", "version": "1"}}

    class FakeResp:
        def __init__(self, data):
            self._data = data

        def raise_for_status(self):
            pass

        def json(self):
            return self._data

    def fake_get(url):
        return FakeResp(spec_data)

    monkeypatch.setattr(httpx, "get", fake_get)

    cfg = server.load_config()
    db_url = f"sqlite+aiosqlite:///{tmp_path/'db.sqlite'}"
    cfg["database"] = db_url
    app = asyncio.run(server.create_app(cfg))

    async def _add() -> None:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            await client.post(
                "/add-server",
                json={"path": "https://example.com/new.json", "apiBaseUrl": "https://example.com", "prefix": "new"},
            )

    asyncio.run(_add())

    # Create a new app using the same DB and ensure the server persists
    app2 = asyncio.run(server.create_app(cfg))

    async def _list() -> httpx.Response:
        transport = httpx.ASGITransport(app=app2)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            return await client.get("/list-server")

    list_resp = asyncio.run(_list())
    assert "new" in list_resp.json()["servers"]


def test_export_server_endpoint():
    cfg = server.load_config()
    cfg["database"] = "sqlite+aiosqlite:///:memory:"
    app = asyncio.run(server.create_app(cfg))

    prefix = cfg["swagger"][0]["prefix"]
    expected = server._load_spec(cfg["swagger"][0])

    async def _call() -> httpx.Response:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            return await client.get(f"/export-server/{prefix}")

    resp = asyncio.run(_call())
    assert resp.status_code == 200
    assert resp.json().get("openapi") == expected.get("openapi")


def test_export_server_missing():
    cfg = server.load_config()
    cfg["database"] = "sqlite+aiosqlite:///:memory:"
    app = asyncio.run(server.create_app(cfg))

    async def _call() -> httpx.Response:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            return await client.get("/export-server/absent")

    resp = asyncio.run(_call())
    assert resp.status_code == 404

