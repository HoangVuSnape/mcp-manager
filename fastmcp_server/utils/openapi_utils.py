"""OpenAPI specification helpers for the FastMCP Swagger server."""

import json
import logging
import os

import httpx

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _get_prefix(spec_cfg: dict) -> str:
    """Return mount prefix for a swagger spec."""
    if spec_cfg.get("prefix"):
        return spec_cfg["prefix"]
    path = spec_cfg.get("path", "")
    base = os.path.basename(path.split("?")[0])
    return os.path.splitext(base)[0]


def _load_spec(spec_cfg: dict) -> dict:
    """Load an OpenAPI specification from a path (local file or URL)."""
    path = spec_cfg.get("path")
    logger.info("Loading OpenAPI spec from: %s", path)
    if not path:
        raise ValueError("Swagger config entry must include 'path'")
    if path.startswith("http://") or path.startswith("https://"):
        resp = httpx.get(path)
        resp.raise_for_status()
        return resp.json()
    if not os.path.isabs(path):
        path = os.path.join(os.path.dirname(__file__), "../"+path)
    logger.info("Loading OpenAPI spec from local file: %s", path)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)
