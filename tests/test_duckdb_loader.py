import duckdb
import pandas as pd
import pytest

from src.loading import duckdb_loader


@pytest.fixture
def temp_db(tmp_path, monkeypatch):
    monkeypatch.setattr(duckdb_loader, "DATABASE_PATH", tmp_path / "test.db")
    return tmp_path / "test.db"


def test_save_dataframe_replaces_instead_of_appending(temp_db):
    duckdb_loader.save_dataframe(pd.DataFrame({"a": [1, 2]}), "t")
    duckdb_loader.save_dataframe(pd.DataFrame({"a": [3]}), "t")

    conn = duckdb.connect(str(temp_db))
    rows = conn.execute("SELECT a FROM t").fetchall()
    conn.close()

    assert rows == [(3,)]


def test_save_dataframe_rejects_bad_table_name(temp_db):
    with pytest.raises(ValueError):
        duckdb_loader.save_dataframe(pd.DataFrame({"a": [1]}), "t; DROP TABLE x")
