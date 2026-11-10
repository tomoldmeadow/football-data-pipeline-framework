from pathlib import Path

from src.utils.logger import get_logger

logger = get_logger(__name__)

SQL_DIR = Path(__file__).parent / "sql"


def build_gold(conn):
    """Rebuild every Gold table from the Silver layer.

    Runs the SQL files in src/gold/sql in filename order (they depend on
    each other, so the numeric prefixes matter). Each file is a set of
    CREATE OR REPLACE TABLE statements, so rebuilding is idempotent.

    Args:
        conn: An open DuckDB connection containing the Silver tables.
    """

    conn.execute("CREATE SCHEMA IF NOT EXISTS gold")

    for sql_file in sorted(SQL_DIR.glob("*.sql")):

        logger.info(f"Building Gold: {sql_file.name}")

        conn.execute(sql_file.read_text(encoding="utf-8"))
