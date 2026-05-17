import json

from src.extraction.statsbomb_extractor import (
    ensure_directories,
    extract_competitions,
    extract_matches
)

from src.transformation.matches_transformer import (
    transform_matches
)

from src.loading.duckdb_loader import (
    save_dataframe
)


if __name__ == "__main__":
    ensure_directories()

    extract_competitions()

    # Example:
    # Competition 43 = FIFA World Cup
    # Season 3 = 2018

    extract_matches(
        competition_id=43,
        season_id=3
    )

    with open("data/bronze/matches_43_3.json", 
              "r",
              encoding = "utf-8"
              ) as f:
           
           matches_data = json.load(f)

    matches_df = transform_matches(matches_data)

    save_dataframe(matches_df, "matches")
    
    print("matches dataframe loaded into duckdb")
