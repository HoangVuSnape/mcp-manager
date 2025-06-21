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
        "file": "examples/swagger-pet-store.json",
        "apiBaseUrl": "https://example.com",
    }
    spec = server._load_spec(spec_cfg)
    client = httpx.AsyncClient(base_url=spec_cfg["apiBaseUrl"])
    sub_server = server.FastMCPOpenAPI(openapi_spec=spec, client=client)
    tools = asyncio.run(sub_server.get_tools())
    asyncio.run(client.aclose())
    assert len(tools) > 0
    assert server._get_prefix(spec_cfg) == "swagger-pet-store"
