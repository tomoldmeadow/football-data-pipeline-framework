from pathlib import Path
import requests
import json

from src.config.settings import (
    COMPETITIONS_URL,
    MATCHES_URL_TEMPLATE
)

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
    print("Downloading competitions data...")

    data = download_json(COMPETITIONS_URL)

    save_json(data, BRONZE_PATH / "competitions.json")

    print("Competitions data saved.")


def extract_matches(competition_id: int, season_id: int):
    print(f"Downloading matches for comp {competition_id}, season {season_id}")

    url = MATCHES_URL_TEMPLATE.format(
        competition_id=competition_id,
        season_id=season_id
    )

    data = download_json(url)

    filename = f"matches_{competition_id}_{season_id}.json"

    save_json(data, BRONZE_PATH / filename)

    print("Matches data saved.")
