import duckdb
import pytest
from fastapi.testclient import TestClient

from src.api.main import app
from src.gold.build_gold import build_gold
from tests.fixtures import create_silver


@pytest.fixture
def client(tmp_path, monkeypatch):
    db_path = tmp_path / "api_test.db"

    conn = duckdb.connect(str(db_path))
    create_silver(conn)
    build_gold(conn)
    conn.close()

    monkeypatch.setenv("FOOTBALL_DB_PATH", str(db_path))

    return TestClient(app)


def test_health(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "matches": 1}


def test_missing_database_returns_503(tmp_path, monkeypatch):
    monkeypatch.setenv("FOOTBALL_DB_PATH", str(tmp_path / "nope.db"))

    response = TestClient(app).get("/matches")

    assert response.status_code == 503


def test_missing_gold_tables_return_503(tmp_path, monkeypatch):
    db_path = tmp_path / "empty.db"
    duckdb.connect(str(db_path)).close()
    monkeypatch.setenv("FOOTBALL_DB_PATH", str(db_path))

    response = TestClient(app).get("/matches")

    assert response.status_code == 503


# --- Matches ---

def test_list_matches_and_team_filter(client):
    assert len(client.get("/matches").json()) == 1
    assert len(client.get("/matches?team=a").json()) == 1
    assert client.get("/matches?team=zzz").json() == []


def test_get_match_includes_both_teams(client):
    body = client.get("/matches/1").json()

    assert body["home_team"] == "A"
    assert [t["team"] for t in body["teams"]] == ["A", "B"]
    assert body["teams"][0]["goals"] == 1


def test_unknown_match_is_404(client):
    assert client.get("/matches/999").status_code == 404
    assert client.get("/matches/999/events").status_code == 404


def test_match_events_filters_and_order(client):
    events = client.get("/matches/1/events").json()

    assert [e["index"] for e in events] == sorted(e["index"] for e in events)

    shots = client.get("/matches/1/events?event_type=Shot").json()
    assert {e["event_type"] for e in shots} == {"Shot"}

    period5 = client.get("/matches/1/events?period=5").json()
    assert [e["event_id"] for e in period5] == ["e4"]


def test_events_rejects_bad_period(client):
    assert client.get("/matches/1/events?period=9").status_code == 422


# --- Players ---

def test_list_players_sorted_by_goals(client):
    players = client.get("/players?sort_by=goals").json()

    assert players[0]["player_id"] == 1
    assert players[0]["goals"] == 1


def test_list_players_filters(client):
    assert len(client.get("/players?q=p2").json()) == 1
    assert client.get("/players?min_minutes=100000").json() == []


def test_invalid_sort_column_is_rejected(client):
    response = client.get("/players?sort_by=goals;DROP TABLE x")

    assert response.status_code == 400


def test_get_player_detail(client):
    body = client.get("/players/1").json()

    assert body["player_name"] == "P1"
    assert body["country"] == "X"
    assert client.get("/players/999").status_code == 404


def test_player_statistics_per_match(client):
    rows = client.get("/players/1/statistics").json()

    assert len(rows) == 1
    assert rows[0]["match_id"] == 1
    assert rows[0]["goals"] == 1
    assert client.get("/players/999/statistics").status_code == 404


def test_compare_players_returns_per_90_in_requested_order(client):
    body = client.get("/players/compare?ids=3&ids=1").json()

    assert [p["player_id"] for p in body] == [3, 1]
    assert body[1]["per_90"]["goals_per_90"] > 0
    assert body[0]["per_90"]["goals_per_90"] == 0


def test_compare_requires_two_to_five_known_players(client):
    assert client.get("/players/compare?ids=1").status_code == 422
    assert client.get("/players/compare?ids=1&ids=999").status_code == 404


# --- Teams ---

def test_teams_and_team_statistics(client):
    teams = client.get("/teams").json()
    assert [t["team"] for t in teams] == ["A", "B"]

    body = client.get("/teams/10/statistics").json()

    assert body["totals"]["matches"] == 1
    assert body["totals"]["goals"] == 1
    assert body["totals"]["goals_against"] == 0
    assert body["matches"][0]["opponent"] == "B"
    assert client.get("/teams/999/statistics").status_code == 404
