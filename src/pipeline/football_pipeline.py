import json

from src.config.settings import (
    DEFAULT_COMPETITION_ID,
    DEFAULT_SEASON_ID,
    MAX_MATCHES
)

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

from src.validation.matches_validator import validate_matches
from src.validation.events_validator import validate_events

from src.loading.duckdb_loader import save_dataframe

from src.utils.logger import get_logger

from src.config.paths import BRONZE_DIR


logger = get_logger("football_pipeline")


def run_pipeline():

    logger.info("Pipeline started")

    ensure_directories()


    # -------------------
    # Extraction
    # -------------------

    logger.info("Extracting competitions")

    extract_competitions()


    logger.info("Extracting matches")

    extract_matches(
        competition_id=DEFAULT_COMPETITION_ID,
        season_id=DEFAULT_SEASON_ID
    )


    with open(
        BRONZE_DIR / f"matches_{DEFAULT_COMPETITION_ID}_{DEFAULT_SEASON_ID}.json",
        encoding="utf-8"
    ) as f:

        matches_data = json.load(f)


    # Get match IDs dynamically

    match_ids = [
        match["match_id"]
        for match in matches_data
    ]

    # Place max on number of matches to download during development
    if MAX_MATCHES is not None:
        match_ids = match_ids[:MAX_MATCHES]


    for match_id in match_ids:

        extract_events(match_id)


    # -------------------
    # Transform
    # -------------------

    matches_df = transform_matches(
        matches_data
    )


    # Events

    all_events = []

    for match_id in match_ids:

        with open(
            BRONZE_DIR / f"events_{match_id}.json",
            encoding="utf-8"
        ) as f:

            events = json.load(f)

            events_df = transform_events(
                events,
                match_id
            )

            all_events.append(events_df)


    events_df = pd.concat(all_events)


    # -------------------
    # Validation
    # -------------------

    ...


    # -------------------
    # Loading
    # -------------------

    save_dataframe(matches_df, "matches")

    save_dataframe(events_df, "events")


    logger.info("Pipeline completed")
