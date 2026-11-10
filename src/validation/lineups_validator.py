import pandas as pd


def validate_lineups(lineups: pd.DataFrame, positions: pd.DataFrame):
    """Validate lineup and position DataFrames.

    Returns (errors, warnings). Spells that end before they start are a
    known source anomaly, flagged is_valid = False and excluded from
    minutes in Gold, so they are a warning rather than an error.
    """

    errors = []
    warnings = []

    if lineups.empty:
        errors.append("Lineups dataframe is empty")
        return errors, warnings

    if lineups["player_id"].isnull().any():
        errors.append("Null player IDs in lineups")

    if lineups.duplicated(["match_id", "player_id"]).any():
        errors.append("Duplicate (match_id, player_id) in lineups")

    if positions.empty:
        errors.append("Lineup positions dataframe is empty")
        return errors, warnings

    if positions["from_seconds"].isnull().any():
        errors.append("Lineup positions with an unreadable start time")

    invalid_spells = int((~positions["is_valid"]).sum())

    if invalid_spells:
        warnings.append(
            f"{invalid_spells} lineup position spell(s) end before they "
            f"start and will be excluded from minutes played"
        )

    return errors, warnings
