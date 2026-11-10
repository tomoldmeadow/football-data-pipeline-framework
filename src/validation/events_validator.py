import pandas as pd

REQUIRED_COLUMNS = [
    "event_id",
    "match_id",
    "period",
    "timestamp",
    "event_type",
    "location_x",
    "location_y",
]

# StatsBomb periods: 1-2 regulation, 3-4 extra time, 5 penalty shootout
VALID_PERIODS = {1, 2, 3, 4, 5}

# StatsBomb pitch is 120 x 80
PITCH_LENGTH = 120
PITCH_WIDTH = 80

TIMESTAMP_PATTERN = r"^\d{2}:\d{2}:\d{2}(\.\d+)?$"


def validate_events(df: pd.DataFrame):
    """Validate the events DataFrame.

    Returns a tuple of (errors, warnings). Errors mean the data is not
    safe to load. Warnings are suspicious but not blocking. Optional
    fields such as player or location are legitimately null for some
    event types, so they are not checked for nulls.
    """

    errors = []
    warnings = []

    if df.empty:
        errors.append("Events dataframe is empty")
        return errors, warnings

    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]

    if missing:
        errors.append(f"Missing required columns: {missing}")
        return errors, warnings

    # --- Errors ---

    if df["event_id"].isnull().any():
        errors.append("Null event IDs found")

    if df["event_id"].duplicated().any():
        errors.append(
            f"Duplicate event IDs found: "
            f"{int(df['event_id'].duplicated().sum())}"
        )

    if df["match_id"].isnull().any():
        errors.append("Null match IDs found")

    if df["event_type"].isnull().any():
        errors.append("Null event types found")

    invalid_periods = ~df["period"].isin(VALID_PERIODS)

    if invalid_periods.any():
        errors.append(
            f"Invalid match periods found: "
            f"{sorted(df.loc[invalid_periods, 'period'].dropna().unique().tolist())}"
        )

    bad_timestamps = ~df["timestamp"].astype(str).str.match(TIMESTAMP_PATTERN)

    if bad_timestamps.any():
        errors.append(
            f"Malformed timestamps found: {int(bad_timestamps.sum())}"
        )

    # --- Warnings ---

    out_of_bounds = (
        (df["location_x"] < 0) | (df["location_x"] > PITCH_LENGTH)
        | (df["location_y"] < 0) | (df["location_y"] > PITCH_WIDTH)
    )

    if out_of_bounds.any():
        warnings.append(
            f"Coordinates outside the {PITCH_LENGTH}x{PITCH_WIDTH} "
            f"pitch: {int(out_of_bounds.sum())} events"
        )

    half_located = df["location_x"].isnull() != df["location_y"].isnull()

    if half_located.any():
        warnings.append(
            f"Events with only one of location_x/location_y: "
            f"{int(half_located.sum())}"
        )

    return errors, warnings
