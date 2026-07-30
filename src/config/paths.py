"""
Filesystem paths used throughout the project.
"""

from pathlib import Path

# Project root
PROJECT_ROOT = Path(__file__).resolve().parents[2]

# Data folders
DATA_DIR = PROJECT_ROOT / "data"

BRONZE_DIR = DATA_DIR / "bronze"
SILVER_DIR = DATA_DIR / "silver"
GOLD_DIR = DATA_DIR / "gold"

# Logs
LOG_DIR = PROJECT_ROOT / "logs"

# Database
DATABASE_PATH = PROJECT_ROOT / "football.db"
