import re

import duckdb
from src.config.paths import DATABASE_PATH

TABLE_NAME_PATTERN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def get_connection():
    return duckdb.connect(str(DATABASE_PATH))


def save_dataframe(df, table_name: str):
    """Write a DataFrame to the DuckDB database as a table.

    Load strategy: full refresh. CREATE OR REPLACE TABLE rewrites the
    table on every run, so re-running never duplicates rows or leaves an
    obsolete schema behind. The pipeline rebuilds each table from the
    Bronze files in scope, so the table always mirrors Bronze.

    Args:
        df: The pandas DataFrame to persist.
        table_name: Name of the destination table. Must be a plain SQL
            identifier (letters, digits, underscores).

    Raises:
        ValueError: If table_name is not a valid identifier.
    """

    if not TABLE_NAME_PATTERN.match(table_name):
        raise ValueError(f"Invalid table name: {table_name!r}")

    conn = get_connection()

    try:
        conn.register("dataframe_to_load", df)

        conn.execute(f"""
            CREATE OR REPLACE TABLE {table_name}
            AS SELECT * FROM dataframe_to_load
        """)

    finally:
        conn.close()
