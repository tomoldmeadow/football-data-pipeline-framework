import pandas as pd


def transform_matches(matches_data):

    rows = []

    for match in matches_data:

        rows.append({
            "match_id": match["match_id"],
            "match_date": match["match_date"],
            "home_team": match["home_team"]["home_team_name"],
            "away_team": match["away_team"]["away_team_name"],
            "home_score": match["home_score"],
            "away_score": match["away_score"]
        })

    return pd.DataFrame(rows)
