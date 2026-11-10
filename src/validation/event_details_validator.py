import pandas as pd


def validate_event_details(details: dict, events: pd.DataFrame):
    """Validate the typed event tables against the central events table.

    Args:
        details: Silver table name -> DataFrame (pass_events, ...).
        events: The central events DataFrame.

    Returns a list of errors. Empty tables are allowed: a small sample of
    matches may legitimately contain no events of a given type.
    """

    errors = []

    known_ids = set(events["event_id"])

    for name, df in details.items():

        if df.empty:
            continue

        if df["event_id"].isnull().any():
            errors.append(f"{name}: null event IDs")

        if df["event_id"].duplicated().any():
            errors.append(f"{name}: duplicate event IDs")

        if not set(df["event_id"]).issubset(known_ids):
            errors.append(f"{name}: event IDs not present in events")

    return errors
