import re

import duckdb
from src.config.paths import DATABASE_PATH

# A plain identifier, optionally schema-qualified (e.g. "silver.events")
TABLE_NAME_PATTERN = re.compile(
    r"^[A-Za-z_][A-Za-z0-9_]*(\.[A-Za-z_][A-Za-z0-9_]*)?$"
)


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
        table_name: Name of the destination table, optionally prefixed
            with a schema ("silver.events"). The schema is created if it
            does not exist. Must be plain SQL identifiers (letters,
            digits, underscores).

    Raises:
        ValueError: If table_name is not a valid identifier.
    """

    if not TABLE_NAME_PATTERN.match(table_name):
        raise ValueError(f"Invalid table name: {table_name!r}")

    conn = get_connection()

    try:
        if "." in table_name:
            schema = table_name.split(".")[0]
            conn.execute(f"CREATE SCHEMA IF NOT EXISTS {schema}")

        conn.register("dataframe_to_load", df)

        conn.execute(f"""
            CREATE OR REPLACE TABLE {table_name}
            AS SELECT * FROM dataframe_to_load
        """)

    finally:
        conn.close()
