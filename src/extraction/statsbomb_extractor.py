from fileinput import filename
from pathlib import Path
import requests
import json

from src.config.settings import (
    COMPETITIONS_URL,
    MATCHES_URL_TEMPLATE,
    EVENTS_URL_TEMPLATE,
    SKIP_EXISTING_FILES,
    FORCE_REFRESH
)

from src.utils.logger import get_logger
from src.config.paths import BRONZE_DIR

logger = get_logger(__name__)


def ensure_directories():
    BRONZE_DIR.mkdir(parents=True, exist_ok=True)

def skip_file(filename: str, output_file: Path):
    if (SKIP_EXISTING_FILES
         and output_file.exists()
         and not FORCE_REFRESH):
        logger.info(f"{filename} already exists. Skipping.")
        return True
    return False


def download_json(url: str):
    response = requests.get(url)

    response.raise_for_status()

    return response.json()


def save_json(data, filepath: Path):
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def extract_competitions():
    logger.info("Downloading competitions data...")

    filename = "competitions.json"
    output_file = BRONZE_DIR / filename

    if skip_file(filename, output_file):
        return

    data = download_json(COMPETITIONS_URL)

    save_json(data, output_file)

    logger.info("Competitions data saved.")


def extract_matches(competition_id: int, season_id: int):
    logger.info(f"Downloading matches for comp {competition_id}, season {season_id}")

    url = MATCHES_URL_TEMPLATE.format(
        competition_id=competition_id,
        season_id=season_id
    )

    filename = f"matches_{competition_id}_{season_id}.json"
    output_file = BRONZE_DIR / filename

    if skip_file(filename, output_file):
        return

    data = download_json(url)

    save_json(data, output_file)

    logger.info("Matches data saved.")


def extract_events(match_id: int):

    logger.info(f"Downloading events for match {match_id}")

    url = EVENTS_URL_TEMPLATE.format(
        match_id=match_id
    )

    filename = f"events_{match_id}.json"
    output_file = BRONZE_DIR / filename

    if skip_file(filename, output_file):
        return

    data = download_json(url)

    save_json(
        data,
        output_file
    )

    logger.info(f"Events saved for match {match_id}")
