import pandas as pd

from src.transformation.lineups_transformer import (
    clock_to_seconds,
    transform_lineups,
)


def sample_lineups():
    return [{
        "team_id": 768,
        "team_name": "England",
        "lineup": [
            {
                "player_id": 1,
                "player_name": "Starter",
                "player_nickname": None,
                "jersey_number": 9,
                "country": {"id": 68, "name": "England"},
                "positions": [{
                    "position_id": 22,
                    "position": "Right Center Forward",
                    "from": "00:00",
                    "to": "87:23",
                    "from_period": 1,
                    "to_period": 2,
                    "start_reason": "Starting XI",
                    "end_reason": "Substitution - Off (Tactical)",
                }],
            },
            {
                "player_id": 2,
                "player_name": "Unused Sub",
                "jersey_number": 12,
                "positions": [],
            },
        ],
    }]


def test_clock_to_seconds():
    assert clock_to_seconds("00:00") == 0
    assert clock_to_seconds("45:00") == 2700
    assert clock_to_seconds("112:33") == 6753


def test_clock_to_seconds_handles_bad_values():
    assert clock_to_seconds(None) is None
    assert clock_to_seconds("abc") is None
    assert clock_to_seconds("12") is None


def test_lineups_and_positions_split():
    lineups, positions = transform_lineups(sample_lineups(), match_id=7)

    assert lineups["player_id"].tolist() == [1, 2]
    assert lineups["match_id"].unique().tolist() == [7]

    # The unused substitute has no position rows
    assert positions["player_id"].tolist() == [1]
    assert positions.iloc[0]["from_seconds"] == 0
    assert positions.iloc[0]["to_seconds"] == 87 * 60 + 23


def test_missing_country_does_not_crash():
    lineups, _ = transform_lineups(sample_lineups(), match_id=7)

    assert pd.isna(lineups.iloc[1]["country"])
