from pathlib import Path
import requests
import json

from src.config.settings import (
    COMPETITIONS_URL,
    MATCHES_URL_TEMPLATE,
    EVENTS_URL_TEMPLATE
)

from src.utils.logger import get_logger

logger = get_logger(__name__)

BRONZE_PATH = Path("data/bronze")


def ensure_directories():
    BRONZE_PATH.mkdir(parents=True, exist_ok=True)


def download_json(url: str):
    response = requests.get(url)

    response.raise_for_status()

    return response.json()


def save_json(data, filepath: Path):
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def extract_competitions():
    logger.info("Downloading competitions data...")

    data = download_json(COMPETITIONS_URL)

    save_json(data, BRONZE_PATH / "competitions.json")

    logger.info("Competitions data saved.")


def extract_matches(competition_id: int, season_id: int):
    logger.info(f"Downloading matches for comp {competition_id}, season {season_id}")

    url = MATCHES_URL_TEMPLATE.format(
        competition_id=competition_id,
        season_id=season_id
    )

    data = download_json(url)

    filename = f"matches_{competition_id}_{season_id}.json"

    save_json(data, BRONZE_PATH / filename)

    logger.info("Matches data saved.")


def extract_events(match_id: int):

    logger.info(f"Downloading events for match {match_id}")

    url = EVENTS_URL_TEMPLATE.format(
        match_id=match_id
    )

    data = download_json(url)

    filename = f"events_{match_id}.json"

    save_json(
        data,
        BRONZE_PATH / filename
    )

    logger.info(f"Events saved for match {match_id}")
