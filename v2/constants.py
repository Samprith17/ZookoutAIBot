"""Version 2 constants for Zookout AI deal search."""
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
RAW_DEALS_PATH = DATA_DIR / "deals.json"
CLEAN_DEALS_PATH = DATA_DIR / "clean_deals.json"

NEARBY_AREAS_MAP = {
    # Mumbai
    "Andheri": ["Bandra", "Juhu", "Powai", "Malad", "Goregaon"],
    "Bandra": ["Andheri", "Juhu", "Lower Parel", "Khar", "Santacruz"],
    "Juhu": ["Andheri", "Bandra", "Vile Parle", "Khar"],
    "Powai": ["Andheri", "Ghatkopar", "Kanjurmarg", "Vikhroli", "Thane"],
    "Borivali": ["Kandivali", "Malad", "Dahisar"],
    "Malad": ["Goregaon", "Borivali", "Kandivali", "Andheri"],
    "Lower Parel": ["Worli", "Dadar", "Bandra", "Mahalaxmi"],
    "Worli": ["Lower Parel", "Dadar", "Prabhadevi"],
    "Dadar": ["Lower Parel", "Worli", "Matunga", "Mahim"],
    "Thane": ["Mulund", "Powai", "Bhandup"],

    # Bangalore
    "Koramangala": ["Indiranagar", "HSR Layout", "MG Road", "BTM Layout"],
    "Indiranagar": ["Koramangala", "MG Road", "Domlur", "Hal"],
    "Whitefield": ["Indiranagar", "Koramangala", "Marathahalli", "MG Road"],
    "HSR Layout": ["Koramangala", "BTM Layout", "Bellandur"],
    "MG Road": ["Indiranagar", "Koramangala", "Brigade Road", "Church Street"]
}
