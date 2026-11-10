from src.transformation.events_transformer import transform_events


def make_event(**overrides):
    event = {
        "id": "abc",
        "index": 1,
        "period": 1,
        "timestamp": "00:00:01.000",
        "minute": 0,
        "second": 1,
        "duration": 0.5,
        "possession": 2,
        "possession_team": {"name": "France"},
        "play_pattern": {"name": "Regular Play"},
        "team": {"name": "France"},
        "player": {"name": "Paul Pogba"},
        "position": {"name": "Center Midfield"},
        "type": {"name": "Pass"},
        "location": [60.0, 40.0],
    }
    event.update(overrides)
    return event


def test_match_id_is_taken_from_argument():
    df = transform_events([make_event()], match_id=7585)

    assert df["match_id"].tolist() == [7585]


def test_common_fields_are_extracted():
    row = transform_events([make_event()], match_id=1).iloc[0]

    assert row["event_id"] == "abc"
    assert row["event_type"] == "Pass"
    assert row["player"] == "Paul Pogba"
    assert row["possession_team"] == "France"
    assert row["location_x"] == 60.0
    assert row["location_y"] == 40.0


def test_missing_player_and_position_become_null():
    event = make_event()
    del event["player"]
    del event["position"]

    row = transform_events([event], match_id=1).iloc[0]

    assert row["player"] is None
    assert row["position"] is None


def test_missing_location_becomes_null():
    event = make_event()
    del event["location"]

    row = transform_events([event], match_id=1).iloc[0]

    assert row["location_x"] is None or row["location_x"] != row["location_x"]
    assert row["location_y"] is None or row["location_y"] != row["location_y"]


def test_malformed_location_does_not_crash():
    df = transform_events([make_event(location=[10.0])], match_id=1)

    assert len(df) == 1
