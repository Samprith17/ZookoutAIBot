"""Version 2 constants for Zookout AI deal search."""
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
RAW_DEALS_PATH = DATA_DIR / "deals.json"
CLEAN_DEALS_PATH = DATA_DIR / "clean_deals.json"
