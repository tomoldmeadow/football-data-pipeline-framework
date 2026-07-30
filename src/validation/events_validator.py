def validate_events(df):

    errors = []

    if df["event_id"].isnull().any():
        errors.append("Null event IDs found")

    if df.empty:
        errors.append("Events dataframe is empty")

    return errors
