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

from src.utils.logger import get_logger

logger = get_logger("pipeline")


if __name__ == "__main__":

    logger.info("Pipeline started")

    ensure_directories()

    logger.info("Extracting competitions...")
    extract_competitions()

    # Example:
    # Competition 43 = FIFA World Cup
    # Season 3 = 2018

    logger.info("Extracting matches...")
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
    
    logger.info("Pipeline finished successfully")
    logger.info("matches dataframe loaded into duckdb")
