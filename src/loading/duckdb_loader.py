import duckdb
from src.config.paths import DATABASE_PATH


def get_connection():
    return duckdb.connect(str(DATABASE_PATH))


def save_dataframe(df, table_name: str):
    """Write a DataFrame to the DuckDB database as a table.

    Opens a connection to the database at DATABASE_PATH and runs
    CREATE OR REPLACE TABLE, so any existing table with the same name
    is overwritten rather than appended to.

    Args:
        df: The pandas DataFrame to persist. DuckDB resolves it by its
            variable name, so it must stay named ``df`` in this scope.
        table_name: Name of the destination table. It is interpolated
            directly into the SQL, so it must come from trusted code,
            never from user input.
    """

    conn = get_connection()

    conn.execute(f"""
        CREATE OR REPLACE TABLE {table_name}
        AS SELECT * FROM df
    """)

    conn.close()
