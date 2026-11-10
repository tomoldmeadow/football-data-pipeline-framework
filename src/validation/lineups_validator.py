import pandas as pd


def validate_lineups(lineups: pd.DataFrame, positions: pd.DataFrame):
    """Validate lineup and position DataFrames. Returns a list of errors."""

    errors = []

    if lineups.empty:
        errors.append("Lineups dataframe is empty")
        return errors

    if lineups["player_id"].isnull().any():
        errors.append("Null player IDs in lineups")

    if lineups.duplicated(["match_id", "player_id"]).any():
        errors.append("Duplicate (match_id, player_id) in lineups")

    if positions.empty:
        errors.append("Lineup positions dataframe is empty")
        return errors

    if positions["from_seconds"].isnull().any():
        errors.append("Lineup positions with an unreadable start time")

    ends_before_start = (
        positions["to_seconds"].notnull()
        & (positions["to_seconds"] < positions["from_seconds"])
    )

    if ends_before_start.any():
        errors.append("Lineup positions that end before they start")

    return errors
