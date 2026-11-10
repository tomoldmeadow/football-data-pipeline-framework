"""Gold layer tests on the tiny hand-built Silver dataset in fixtures.py."""

import duckdb
import pytest

from src.gold.build_gold import build_gold
from tests.fixtures import create_silver


@pytest.fixture
def conn():
    conn = duckdb.connect(":memory:")
    create_silver(conn)
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


def test_overlapping_spells_are_not_double_counted(conn):
    # Mirrors a source quirk: a starter with a second "Player On" spell
    # that overlaps the first. P1 starts 0:00 and gets an extra overlap.
    before = player(conn, 1)["minutes_played"]

    conn.execute(
        "INSERT INTO silver.lineup_positions VALUES "
        "(1, 1, 10, 3000, NULL, TRUE)"
    )
    build_gold(conn)

    assert player(conn, 1)["minutes_played"] == before


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
