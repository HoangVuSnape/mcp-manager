"""Configuration helpers for the FastMCP Swagger server."""

import json
import logging
import os
from typing import Any

import httpx

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DEFAULT_CONFIG = {
    "swagger": [
        {
            "path": "examples/swagger-pet-store.json",
            "apiBaseUrl": "https://petstore.swagger.io/v2",
            "prefix": "petstore",
        }
    ],
    "server": {"host": "0.0.0.0", "port": 3000},
}


def _load_single_config(source: str) -> dict:
    """Load a single configuration file or URL."""
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
    return cfg


def export_config(cfg: dict, path: str) -> None:
    """Write configuration to a JSON file."""
    with open(path, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2)


def load_config(source: str | list[str] | None = None) -> dict:
    """Load configuration from one or more paths or URLs."""
    if source is None:
        source = os.environ.get("CONFIG_URL", "config.json")

    if isinstance(source, list):
        merged: dict[str, Any] = {"swagger": [], "server": {}}
        for s in source:
            cfg = load_config(s)
            merged["swagger"].extend(cfg.get("swagger", []))
            if not merged["server"] and cfg.get("server"):
                merged["server"] = cfg["server"]
        if not merged["server"]:
            merged["server"] = DEFAULT_CONFIG["server"]
        return merged

    return _load_single_config(source)
