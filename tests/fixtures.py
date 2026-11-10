"""Shared tiny Silver dataset for Gold and API tests.

Match 1: team A (10) v team B (20), won 1-0 by A.
  p1, p2 play for A (p2 joins at 60:00); p3 plays for B.
  p1 scores in open play, p3 scores in a penalty shootout (must not count).
"""

import pandas as pd


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
        "timestamp": f"00:{minute:02d}:{second:02d}.000",
        "player": f"P{player_id}", "position": "Forward",
        "under_pressure": False,
    }



def create_silver(conn):
    """Create the silver schema and tables on an open DuckDB connection."""

    conn.execute("CREATE SCHEMA IF NOT EXISTS silver")

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
             "from_seconds": 0, "to_seconds": None, "is_valid": True},
            {"match_id": 1, "player_id": 2, "team_id": 10,
             "from_seconds": 3600, "to_seconds": None, "is_valid": True},
            # Bad source spell: ends before it starts, must be ignored
            {"match_id": 1, "player_id": 2, "team_id": 10,
             "from_seconds": 6677, "to_seconds": 3600, "is_valid": False},
            {"match_id": 1, "player_id": 3, "team_id": 20,
             "from_seconds": 0, "to_seconds": None, "is_valid": True},
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
