"""Gold layer tests on a tiny hand-built Silver dataset.

Match 1: team A (10) v team B (20).
  p1, p2 play for A (p2 joins at 60:00); p3 plays for B.
  p1 scores in open play, p3 scores in a penalty shootout (must not count).
"""

import duckdb
import pandas as pd
import pytest

from src.gold.build_gold import build_gold


def event(event_id, index, period, minute, second, possession, team_id,
          player_id, event_type, x=None, y=None):
    teams = {10: "A", 20: "B"}
    return {
        "event_id": event_id, "match_id": 1, "index": index,
        "period": period, "minute": minute, "second": second,
        "possession": possession, "possession_team_id": team_id,
        "possession_team": teams[team_id], "play_pattern": "Regular Play",
        "team_id": team_id, "team": teams[team_id], "player_id": player_id,
        "event_type": event_type, "location_x": x, "location_y": y,
    }


@pytest.fixture
def conn():
    conn = duckdb.connect(":memory:")
    conn.execute("CREATE SCHEMA silver")

    tables = {
        "events": [
            event("e1", 1, 1, 10, 0, 1, 10, 1, "Pass", 40, 40),
            event("e2", 2, 1, 10, 5, 1, 10, 1, "Pass", 50, 40),
            event("e3", 3, 1, 10, 9, 1, 10, 1, "Shot", 100, 40),
            event("e4", 4, 5, 120, 0, 3, 20, 3, "Shot", 108, 40),
            event("e5", 5, 1, 20, 0, 2, 20, 3, "Duel", 50, 40),
            event("e6", 6, 2, 90, 0, 2, 20, 3, "Interception", 50, 40),
        ],
        "pass_events": [
            {"event_id": "e1", "is_completed": True, "goal_assist": False,
             "shot_assist": False, "pass_type": "Recovery",
             "end_x": 80.0, "end_y": 40.0},
            {"event_id": "e2", "is_completed": False, "goal_assist": False,
             "shot_assist": False, "pass_type": "Recovery",
             "end_x": 60.0, "end_y": 40.0},
        ],
        "shot_events": [
            {"event_id": "e3", "outcome": "Goal", "xg": 0.5},
            {"event_id": "e4", "outcome": "Goal", "xg": 0.8},
        ],
        "duel_events": [
            {"event_id": "e5", "duel_type": "Tackle", "outcome": "Won"},
        ],
        "lineups": [
            {"match_id": 1, "player_id": 1, "player_name": "P1",
             "player_nickname": None, "country": "X"},
            {"match_id": 1, "player_id": 2, "player_name": "P2",
             "player_nickname": None, "country": "X"},
            {"match_id": 1, "player_id": 3, "player_name": "P3",
             "player_nickname": None, "country": "Y"},
        ],
        "lineup_positions": [
            {"match_id": 1, "player_id": 1, "team_id": 10,
             "from_seconds": 0, "to_seconds": None},
            {"match_id": 1, "player_id": 2, "team_id": 10,
             "from_seconds": 3600, "to_seconds": None},
            {"match_id": 1, "player_id": 3, "team_id": 20,
             "from_seconds": 0, "to_seconds": None},
        ],
        "matches": [
            {"match_id": 1, "match_date": "2018-06-19", "home_team": "A",
             "away_team": "B", "home_score": 1, "away_score": 0},
        ],
    }

    for name, rows in tables.items():
        frame = pd.DataFrame(rows)
        conn.register("frame", frame)
        conn.execute(f"CREATE TABLE silver.{name} AS SELECT * FROM frame")
        conn.unregister("frame")

    build_gold(conn)

    yield conn

    conn.close()


def player(conn, player_id):
    return conn.execute(
        "SELECT * FROM gold.player_match_stats WHERE player_id = ?",
        [player_id],
    ).fetchdf().iloc[0]


def test_minutes_played_from_lineup_positions(conn):
    # Open-ended spells run to the latest event clock in the match. The
    # starter is on from 0:00 and the substitute from 60:00, so the
    # starter plays exactly 60 minutes more.
    p1, p2 = player(conn, 1), player(conn, 2)

    assert p1["minutes_played"] - p2["minutes_played"] == 60.0
    assert p1["minutes_played"] > 0


def test_goals_and_xg_count_open_play_only(conn):
    p1, p3 = player(conn, 1), player(conn, 3)

    assert p1["goals"] == 1
    assert p1["xg"] == 0.5
    assert p3["goals"] == 0  # shootout goal excluded
    assert p3["shots"] == 0


def test_pass_metrics(conn):
    p1 = player(conn, 1)

    assert p1["passes"] == 2
    assert p1["passes_completed"] == 1
    assert p1["progressive_passes"] == 1  # 40m -> 80m is 50% closer


def test_defensive_metrics(conn):
    p3 = player(conn, 3)

    assert p3["tackles"] == 1
    assert p3["tackles_won"] == 1
    assert p3["interceptions"] == 1


def test_team_goals_exclude_shootout(conn):
    rows = conn.execute(
        "SELECT team, goals FROM gold.team_match_stats ORDER BY team"
    ).fetchall()

    assert rows == [("A", 1), ("B", 0)]


def test_possession_flags_goal(conn):
    row = conn.execute(
        "SELECT ended_in_goal, passes, shots FROM gold.possessions "
        "WHERE possession = 1"
    ).fetchone()

    assert row == (True, 2, 1)


def test_match_summary_joins_both_teams(conn):
    row = conn.execute(
        "SELECT home_team, away_team, home_xg FROM gold.match_summary"
    ).fetchone()

    assert row == ("A", "B", 0.5)


def test_tournament_stats_aggregate_players(conn):
    row = conn.execute(
        "SELECT appearances, goals FROM gold.player_tournament_stats "
        "WHERE player_id = 1"
    ).fetchone()

    assert row == (1, 1)
