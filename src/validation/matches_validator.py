import pandas as pd


def validate_matches(df: pd.DataFrame):
    errors = []

    if df["match_id"].isnull().any():
        errors.append("Null match_id values found")

    if df.duplicated("match_id").any():
        errors.append("Duplicate match_id values found")

    if df.isnull().any().any():
        errors.append("Null values found in matches table")

    return errors
