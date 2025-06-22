"""PostgreSQL helper functions for configuration storage."""

import json
import logging

import psycopg2

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def save_config_to_postgres(cfg: dict, dsn: str, name: str = "default") -> None:
    """Persist configuration JSON to a PostgreSQL database."""
    conn = psycopg2.connect(dsn)
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    "CREATE TABLE IF NOT EXISTS configs (name TEXT PRIMARY KEY, data JSONB)"
                )
                cur.execute(
                    "INSERT INTO configs (name, data) VALUES (%s, %s) "
                    "ON CONFLICT (name) DO UPDATE SET data = EXCLUDED.data",
                    (name, json.dumps(cfg)),
                )
    finally:
        conn.close()


def load_config_from_postgres(dsn: str, name: str = "default") -> dict | None:
    """Load configuration JSON from a PostgreSQL database."""
    conn = psycopg2.connect(dsn)
    try:
        with conn.cursor() as cur:
            cur.execute(
                "CREATE TABLE IF NOT EXISTS configs (name TEXT PRIMARY KEY, data JSONB)"
            )
            cur.execute("SELECT data FROM configs WHERE name=%s", (name,))
            row = cur.fetchone()
            if row:
                data = row[0]
                if isinstance(data, str):
                    return json.loads(data)
                return data
    finally:
        conn.close()
    return None
