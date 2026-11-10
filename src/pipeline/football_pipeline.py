import json
import pandas as pd
import requests

from src.config.settings import (
    DEFAULT_COMPETITION_ID,
    DEFAULT_SEASON_ID,
    MAX_MATCHES,
    FAIL_ON_VALIDATION_ERROR
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


    # One failed download should not abort the whole run
    failed_matches = []

    for match_id in match_ids:

        try:
            extract_events(match_id)

        except requests.RequestException as error:
            logger.error(
                f"Failed to download events for match {match_id}: {error}"
            )
            failed_matches.append(match_id)

    if failed_matches:
        logger.warning(
            f"{len(failed_matches)} match download(s) failed: {failed_matches}"
        )

    match_ids = [m for m in match_ids if m not in failed_matches]

    # Keep matches and events in scope together (MAX_MATCHES, failures)
    matches_data = [
        match for match in matches_data
        if match["match_id"] in match_ids
    ]


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


    events_df = pd.concat(all_events, ignore_index=True)


    # -------------------
    # Validation
    # -------------------

    matches_errors = validate_matches(matches_df)

    events_errors, events_warnings = validate_events(events_df)

    for warning in events_warnings:
        logger.warning(f"Events validation warning: {warning}")

    all_errors = matches_errors + events_errors

    for error in all_errors:
        logger.error(f"Validation error: {error}")

    if all_errors and FAIL_ON_VALIDATION_ERROR:
        raise ValueError(
            f"Validation failed with {len(all_errors)} error(s)"
        )

    logger.info("Validation passed")


    # -------------------
    # Loading
    # -------------------

    save_dataframe(matches_df, "matches")

    save_dataframe(events_df, "events")


    logger.info("Pipeline completed")
