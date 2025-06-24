"""PostgreSQL helper functions for configuration storage."""

import json
import logging

import psycopg2
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)



def _connect_with_retries(dsn: str, retries: int = 5, delay: float = 1.0):
    """Try to connect to the database multiple times before failing."""
    for attempt in range(1, retries + 1):
        try:
            return psycopg2.connect(dsn)
        except psycopg2.OperationalError as exc:  # pragma: no cover - network issue
            logger.warning(
                "Database connection failed (attempt %d/%d): %s",
                attempt,
                retries,
                exc,
            )
            if attempt == retries:
                raise
            time.sleep(delay)
            
            
def load_config_from_postgres(dsn: str, name: str = "default") -> dict | None:
    """Load configuration JSON from a PostgreSQL database."""
    conn = _connect_with_retries(dsn)
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

if __name__ == "__main__":
    # Example usage
    dsn = "dbname=test user=postgres password=secret host=localhost port=5432"
    config = load_config_from_postgres(dsn, "my_config")
    if config:
        print("Loaded config:", config)
    else:
        print("No config found.")

