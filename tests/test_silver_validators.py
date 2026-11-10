import pandas as pd

from src.validation.event_details_validator import validate_event_details
from src.validation.lineups_validator import validate_lineups


def lineups():
    return pd.DataFrame({"match_id": [1, 1], "player_id": [1, 2]})


def positions():
    return pd.DataFrame({
        "from_seconds": [0, 3600],
        "to_seconds": [5400, None],
    })


def test_valid_lineups_pass():
    assert validate_lineups(lineups(), positions()) == []


def test_duplicate_and_null_players_reported():
    df = pd.DataFrame({"match_id": [1, 1], "player_id": [1, 1]})
    errors = validate_lineups(df, positions())

    assert "Duplicate (match_id, player_id) in lineups" in errors

    df.loc[0, "player_id"] = None
    assert "Null player IDs in lineups" in validate_lineups(df, positions())


def test_position_ending_before_start_reported():
    bad = pd.DataFrame({"from_seconds": [100], "to_seconds": [50]})

    errors = validate_lineups(lineups(), bad)

    assert "Lineup positions that end before they start" in errors


def test_event_details_must_reference_known_events():
    events = pd.DataFrame({"event_id": ["a", "b"]})
    good = {"pass_events": pd.DataFrame({"event_id": ["a"]})}
    orphan = {"pass_events": pd.DataFrame({"event_id": ["zzz"]})}
    duplicate = {"pass_events": pd.DataFrame({"event_id": ["a", "a"]})}

    assert validate_event_details(good, events) == []
    assert validate_event_details(orphan, events)
    assert validate_event_details(duplicate, events)


def test_empty_detail_tables_are_allowed():
    events = pd.DataFrame({"event_id": ["a"]})

    assert validate_event_details({"dribble_events": pd.DataFrame()}, events) == []
