import pandas as pd

from src.validation.events_validator import validate_events


def valid_df():
    return pd.DataFrame([
        {
            "event_id": "a", "match_id": 1, "period": 1,
            "timestamp": "00:00:01.000", "event_type": "Pass",
            "location_x": 60.0, "location_y": 40.0,
        },
        {
            "event_id": "b", "match_id": 1, "period": 2,
            "timestamp": "00:46:10.250", "event_type": "Shot",
            "location_x": None, "location_y": None,
        },
    ])


def test_valid_frame_has_no_errors_or_warnings():
    errors, warnings = validate_events(valid_df())

    assert errors == []
    assert warnings == []


def test_empty_frame_is_an_error_and_does_not_crash():
    errors, _ = validate_events(pd.DataFrame())

    assert errors == ["Events dataframe is empty"]


def test_missing_columns_reported():
    errors, _ = validate_events(valid_df().drop(columns=["period"]))

    assert any("Missing required columns" in e for e in errors)


def test_duplicate_event_ids_reported():
    df = valid_df()
    df.loc[1, "event_id"] = "a"

    errors, _ = validate_events(df)

    assert any("Duplicate event IDs" in e for e in errors)


def test_null_ids_and_types_reported():
    df = valid_df()
    df.loc[0, "event_id"] = None
    df.loc[0, "match_id"] = None
    df.loc[1, "event_type"] = None

    errors, _ = validate_events(df)

    assert "Null event IDs found" in errors
    assert "Null match IDs found" in errors
    assert "Null event types found" in errors


def test_invalid_period_reported():
    df = valid_df()
    df.loc[0, "period"] = 9

    errors, _ = validate_events(df)

    assert any("Invalid match periods" in e for e in errors)


def test_malformed_timestamp_reported():
    df = valid_df()
    df.loc[0, "timestamp"] = "not-a-time"

    errors, _ = validate_events(df)

    assert any("Malformed timestamps" in e for e in errors)


def test_out_of_bounds_coordinates_are_warning_not_error():
    df = valid_df()
    df.loc[0, "location_x"] = 150.0

    errors, warnings = validate_events(df)

    assert errors == []
    assert any("outside" in w for w in warnings)


def test_null_location_is_not_flagged():
    errors, warnings = validate_events(valid_df())

    assert errors == [] and warnings == []
