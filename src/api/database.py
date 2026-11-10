import os
from pathlib import Path

import duckdb
from fastapi import HTTPException

from src.config.paths import DATABASE_PATH


def get_db():
    """FastAPI dependency yielding a read-only DuckDB connection.

    Read-only so the API can never modify the warehouse. The path can be
    overridden with the FOOTBALL_DB_PATH environment variable.
    """

    path = Path(os.environ.get("FOOTBALL_DB_PATH", DATABASE_PATH))

    if not path.exists():
        raise HTTPException(
            status_code=503,
            detail="Database not found. Run the pipeline first.",
        )

    conn = duckdb.connect(str(path), read_only=True)

    try:
        yield conn

    finally:
        conn.close()


def fetch_all(conn, sql, params=None):
    """Run a query and return the rows as a list of dicts."""

    cursor = conn.execute(sql, params or [])
    columns = [column[0] for column in cursor.description]

    return [dict(zip(columns, row)) for row in cursor.fetchall()]


def fetch_one(conn, sql, params=None):
    """Run a query and return the first row as a dict, or None."""

    rows = fetch_all(conn, sql, params)

    return rows[0] if rows else None
