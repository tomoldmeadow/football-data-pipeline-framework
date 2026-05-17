import duckdb

DB_PATH = "football.db"


def get_connection():
    return duckdb.connect(DB_PATH)


def save_dataframe(df, table_name: str):

    conn = get_connection()

    conn.execute(f"""
        CREATE OR REPLACE TABLE {table_name}
        AS SELECT * FROM df
    """)

    conn.close()
