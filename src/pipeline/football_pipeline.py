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
    extract_events,
    extract_lineups
)

from src.transformation.matches_transformer import (
    transform_matches
)

from src.transformation.events_transformer import (
    transform_events
)

from src.transformation.lineups_transformer import (
    transform_lineups
)

from src.transformation.event_details_transformer import (
    EVENT_DETAIL_TRANSFORMERS
)

from src.validation.matches_validator import validate_matches
from src.validation.events_validator import validate_events
from src.validation.lineups_validator import validate_lineups
from src.validation.event_details_validator import validate_event_details

from src.loading.duckdb_loader import get_connection, save_dataframe

from src.gold.build_gold import build_gold

from src.utils.logger import get_logger

from src.config.paths import BRONZE_DIR


logger = get_logger("football_pipeline")


def read_bronze(filename):

    with open(BRONZE_DIR / filename, encoding="utf-8") as f:
        return json.load(f)


def extract_match_files(match_ids):
    """Download events and lineups for each match.

    One failed download should not abort the whole run, so failures are
    logged and the match is dropped. Returns the match IDs that succeeded.
    """

    failed_matches = []

    for match_id in match_ids:

        try:
            extract_events(match_id)
            extract_lineups(match_id)

        except requests.RequestException as error:
            logger.error(
                f"Failed to download data for match {match_id}: {error}"
            )
            failed_matches.append(match_id)

    if failed_matches:
        logger.warning(
            f"{len(failed_matches)} match download(s) failed: {failed_matches}"
        )

    return [m for m in match_ids if m not in failed_matches]


def concat_frames(frames):
    """Concatenate per-match frames, ignoring any that are empty."""

    frames = [f for f in frames if not f.empty]

    if not frames:
        return pd.DataFrame()

    return pd.concat(frames, ignore_index=True)


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

    matches_data = read_bronze(
        f"matches_{DEFAULT_COMPETITION_ID}_{DEFAULT_SEASON_ID}.json"
    )

    # Get match IDs dynamically

    match_ids = [
        match["match_id"]
        for match in matches_data
    ]

    # Place max on number of matches to download during development
    if MAX_MATCHES is not None:
        match_ids = match_ids[:MAX_MATCHES]

    match_ids = extract_match_files(match_ids)

    # Keep matches and events in scope together (MAX_MATCHES, failures)
    matches_data = [
        match for match in matches_data
        if match["match_id"] in match_ids
    ]


    # -------------------
    # Transform (Bronze -> Silver)
    # -------------------

    matches_df = transform_matches(matches_data)

    event_frames = []
    lineup_frames = []
    position_frames = []
    detail_frames = {name: [] for name in EVENT_DETAIL_TRANSFORMERS}

    for match_id in match_ids:

        events = read_bronze(f"events_{match_id}.json")

        event_frames.append(transform_events(events, match_id))

        for name, transformer in EVENT_DETAIL_TRANSFORMERS.items():
            detail_frames[name].append(transformer(events))

        lineups, positions = transform_lineups(
            read_bronze(f"lineups_{match_id}.json"),
            match_id
        )

        lineup_frames.append(lineups)
        position_frames.append(positions)

    events_df = concat_frames(event_frames)
    lineups_df = concat_frames(lineup_frames)
    positions_df = concat_frames(position_frames)

    details = {
        name: concat_frames(frames)
        for name, frames in detail_frames.items()
    }


    # -------------------
    # Validation
    # -------------------

    matches_errors = validate_matches(matches_df)

    events_errors, events_warnings = validate_events(events_df)

    for warning in events_warnings:
        logger.warning(f"Events validation warning: {warning}")

    all_errors = (
        matches_errors
        + events_errors
        + validate_lineups(lineups_df, positions_df)
        + validate_event_details(details, events_df)
    )

    for error in all_errors:
        logger.error(f"Validation error: {error}")

    if all_errors and FAIL_ON_VALIDATION_ERROR:
        raise ValueError(
            f"Validation failed with {len(all_errors)} error(s)"
        )

    logger.info("Validation passed")


    # -------------------
    # Loading (Silver)
    # -------------------

    save_dataframe(matches_df, "silver.matches")
    save_dataframe(events_df, "silver.events")
    save_dataframe(lineups_df, "silver.lineups")
    save_dataframe(positions_df, "silver.lineup_positions")

    for name, df in details.items():
        save_dataframe(df, f"silver.{name}")


    # -------------------
    # Gold
    # -------------------

    conn = get_connection()

    try:
        build_gold(conn)

    finally:
        conn.close()


    logger.info("Pipeline completed")
