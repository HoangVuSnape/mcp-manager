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


def test_load_multiple_configs(tmp_path):
    cfg1 = {
        "swagger": [{"path": "one.json", "apiBaseUrl": "http://a", "prefix": "a"}],
        "server": {"host": "0.0.0.0", "port": 1},
    }
    cfg2 = {
        "swagger": [{"path": "two.json", "apiBaseUrl": "http://b", "prefix": "b"}]
    }
    p1 = tmp_path / "c1.json"
    p2 = tmp_path / "c2.json"
    p1.write_text(json.dumps(cfg1))
    p2.write_text(json.dumps(cfg2))
    cfg = server.load_config([str(p1), str(p2)])
    assert len(cfg["swagger"]) == 2


def test_save_and_load_config_postgres(monkeypatch):
    executed = {}

    class FakeCursor:
        def __init__(self):
            self._result = [json.dumps({"swagger": [], "server": {"port": 5}})]

        def execute(self, query, params=None):
            executed.setdefault("queries", []).append((query, params))

        def fetchone(self):
            return [self._result[0]]

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            pass

    class FakeConn:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            pass

        def cursor(self):
            return FakeCursor()

        def close(self):
            executed["closed"] = True

    def fake_connect(dsn):
        executed["dsn"] = dsn
        return FakeConn()

    monkeypatch.setattr(server.db_utils.psycopg2, "connect", fake_connect)

    cfg = {"swagger": [], "server": {"port": 5}}
    server.save_config_to_postgres(cfg, "db")
    loaded = server.load_config_from_postgres("db")
    assert loaded["server"]["port"] == 5


def test_tool_enable_api():
    cfg = server.load_config()
    cfg["database"] = "sqlite+aiosqlite:///:memory:"

    app = asyncio.run(server.create_app(cfg))
    prefix = cfg["swagger"][0]["prefix"]

    async def get_first_tool() -> str:
        srv = app.state.root_server._mounted_servers[prefix]
        tools = await srv.get_tools()
        return next(iter(tools))

    tool_name = asyncio.run(get_first_tool())

    async def disable() -> httpx.Response:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            return await client.post(
                "/tool-enabled",
                json={"prefix": prefix, "name": tool_name, "enabled": False},
            )

    resp = asyncio.run(disable())
    assert resp.status_code == 200

    async def check_tool() -> bool:
        srv = app.state.root_server._mounted_servers[prefix]
        tools = await srv.get_tools()
        return tools[tool_name].enabled

    assert asyncio.run(check_tool()) is False

    async def check_db() -> bool:
        async with app.state.db_session() as session:
            statuses = await server.db.get_tool_statuses(session, prefix)
            return [s for s in statuses if s.name == tool_name][0].enabled

    assert asyncio.run(check_db()) is False
