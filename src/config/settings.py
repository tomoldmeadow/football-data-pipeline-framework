"""
Project-wide configuration settings.

This module contains configurable values that control the behaviour
of the football data pipeline.
"""

# ======================================================
# StatsBomb Open Data
# ======================================================

BASE_URL = "https://raw.githubusercontent.com/statsbomb/open-data/master/data"

COMPETITIONS_URL = f"{BASE_URL}/competitions.json"
MATCHES_URL_TEMPLATE = f"{BASE_URL}/matches/{{competition_id}}/{{season_id}}.json"
EVENTS_URL_TEMPLATE = f"{BASE_URL}/events/{{match_id}}.json"
LINEUPS_URL_TEMPLATE = f"{BASE_URL}/lineups/{{match_id}}.json"

# ======================================================
# Default pipeline configuration
# ======================================================

DEFAULT_COMPETITION_ID = 43     # FIFA World Cup
DEFAULT_SEASON_ID = 3           # 2018

# Number of matches to download during development.
# Set to None to download every available match. There were 64 matches total in the 2018 world cup.
MAX_MATCHES = 5

# Skip downloading files that already exist.
SKIP_EXISTING_FILES = True

# Force refresh of all files
FORCE_REFRESH = False

# ======================================================
# Validation
# ======================================================

FAIL_ON_VALIDATION_ERROR = True

# ======================================================
# Logging
# ======================================================

LOG_LEVEL = "INFO"
