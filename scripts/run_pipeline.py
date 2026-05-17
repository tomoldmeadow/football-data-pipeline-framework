from src.extraction.statsbomb_extractor import (
    ensure_directories,
    extract_competitions,
    extract_matches
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
