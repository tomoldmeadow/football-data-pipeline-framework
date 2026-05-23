import json

from src.extraction.statsbomb_extractor import (
    ensure_directories,
    extract_competitions,
    extract_matches,
    extract_events
)

from src.transformation.matches_transformer import (
    transform_matches
)

from src.transformation.events_transformer import (
    transform_events
)

from src.loading.duckdb_loader import (
    save_dataframe
)

from src.validation.matches_validator import validate_matches
from src.validation.events_validator import validate_events

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

    with open(
        "data/bronze/events_7585.json",
        "r",
        encoding="utf-8"
    ) as f:

        events_data = json.load(f)

    events_df = transform_events(events_data)

    event_errors = validate_events(events_df)

    if event_errors:
        logger.error(event_errors)
        raise Exception("Event validation failed")

    save_dataframe(events_df, "events")

    logger.info("Events loaded successfully")

    logger.info("Extracting events...")
    extract_events(match_id=7585)

    matches_df = transform_matches(matches_data)

    # Validate the matches dataframe
    errors = validate_matches(matches_df)

    if errors:
        logger.error("Validation failed:")
        for e in errors:
            logger.error(e)
        raise Exception("Pipeline failed validation")
    else:
        logger.info("Validation passed")

    save_dataframe(matches_df, "matches")
    
    logger.info("Pipeline finished successfully")
    logger.info("matches dataframe loaded into duckdb")
