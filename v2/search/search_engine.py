import json
from pathlib import Path
from typing import List, Dict

# Locate clean_deals.json
ROOT_DIR = Path(__file__).resolve().parents[2]
DATA_FILE = ROOT_DIR / "data" / "clean_deals.json"


def load_deals() -> List[Dict]:
    """Load all deals from clean_deals.json"""
    if not DATA_FILE.exists():
        print(f"❌ File not found: {DATA_FILE}")
        return []

    with open(DATA_FILE, "r", encoding="utf-8") as file:
        return json.load(file)


DEALS = load_deals()


def search_deals(intent: Dict) -> List[Dict]:
    """
    AI-powered deal search using category, location,
    price and keywords.
    """

    results = []

    category = intent.get("category")
    location = intent.get("location")
    max_price = intent.get("max_price")
    query = intent.get("query", "").lower()

    for deal in DEALS:

        score = 0

        # -------------------------
        # Category Match
        # -------------------------
        if category:
            if category in deal.get("category", "").lower():
                score += 15
            else:
                continue

        # -------------------------
        # Location Match
        # -------------------------
        if location:
            if location.lower() in deal.get("location", "").lower():
                score += 10
            else:
                continue

        # -------------------------
        # Price Match
        # -------------------------
        if max_price is not None:
            try:
                price = float(str(deal.get("price", "999999")).replace(",", ""))
            except Exception:
                price = 999999

            if price <= max_price:
                score += 8
            else:
                continue

        # -------------------------
        # Keyword Match
        # -------------------------
        if query:

            if query in deal.get("title", "").lower():
                score += 5

            if query in deal.get("description", "").lower():
                score += 4

            if query in deal.get("brand", "").lower():
                score += 3

            for tag in deal.get("tags", []):
                if query in tag.lower():
                    score += 2

            for keyword in deal.get("keywords", []):
                if query in keyword.lower():
                    score += 1

        if score > 0:
            deal["score"] = score
            results.append(deal)

    results.sort(key=lambda x: x["score"], reverse=True)

    return results