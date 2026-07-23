import json
from pathlib import Path
from typing import List, Dict
from rapidfuzz import fuzz

ROOT_DIR = Path(__file__).resolve().parents[2]
DATA_FILE = ROOT_DIR / "data" / "clean_deals.json"


def load_deals() -> List[Dict]:
    """Load all deals from clean_deals.json"""
    if not DATA_FILE.exists():
        return []
    with open(DATA_FILE, "r", encoding="utf-8") as file:
        return json.load(file)


DEALS = load_deals()


def matches_category(req_category: str, deal: Dict) -> bool:
    """Strictly checks if a deal belongs to the requested category or its valid synonyms."""
    cat = (deal.get("category") or "").lower().strip()
    title = (deal.get("title") or "").lower()
    desc = (deal.get("description") or "").lower()
    tags = [str(t).lower() for t in deal.get("tags", [])]
    text_content = f"{title} {desc} {' '.join(tags)}"

    if not req_category:
        return True

    req = req_category.lower().strip()

    # Category Isolation Rules
    if req == "spa":
        return cat == "spa" or "spa" in text_content or "massage" in text_content

    if req in ["salon", "beauty"]:
        return cat in ["salon", "clinic"] or "salon" in text_content or "beauty" in text_content or "hair" in text_content

    if req == "restaurant":
        return cat in ["restaurant", "cafe"] or "restaurant" in text_content or "buffet" in text_content or "thali" in text_content

    if req == "cafe":
        return cat in ["cafe", "restaurant"] or "cafe" in text_content or "coffee" in text_content

    if req in ["hotel", "resort"]:
        return cat in ["hotel", "unknown"] or "hotel" in text_content or "resort" in text_content or "stay" in text_content

    if req in ["pub", "bar", "brewery"]:
        bar_keywords = ["beer", "pub", "bar", "cocktail", "liquor", "bottle", "drink", "imfl", "imported"]
        return any(k in text_content for k in bar_keywords)

    if req in ["adventure", "gaming", "movie", "event", "water park", "kids", "family", "entertainment"]:
        entertainment_keywords = [
            "waterpark", "water park", "pass", "day pass", "gaming", "bowling",
            "movie", "cinema", "adventure", "outdoor", "ticket", "entry", "park"
        ]
        return cat in ["entertainment", "hotel", "unknown"] or any(k in text_content for k in entertainment_keywords)

    # General Fallback Match
    return req in cat or req in text_content


def search_deals(intent: Dict) -> List[Dict]:
    """
    Structured deal search algorithm prioritizing:
    1. Category isolation
    2. Budget enforcement (min_price & max_price)
    3. Location matching & Fuzzy relevance scoring
    """

    req_category = intent.get("category")
    req_location = intent.get("location")
    min_price = intent.get("min_price")
    max_price = intent.get("max_price")
    user_query = intent.get("query", "").strip()

    candidate_deals = []

    # Step 1: Filter deals strictly by Category & Price Limits
    for deal in DEALS:
        # Category Filter
        if req_category and not matches_category(req_category, deal):
            continue

        # Price Filter
        try:
            price = float(str(deal.get("price", "999999")).replace(",", ""))
        except Exception:
            price = 999999.0

        if min_price is not None and price < min_price:
            continue

        if max_price is not None and price > max_price:
            continue

        candidate_deals.append(deal)

    if not candidate_deals:
        return []

    # Step 2: Relevance & Location Scoring using Rapidfuzz
    scored_results = []
    for deal in candidate_deals:
        score = 0
        title = deal.get("title", "")
        brand = deal.get("brand", "")
        desc = deal.get("description", "")
        location_str = (deal.get("location") or "").lower()

        # Category Match Bonus
        if req_category and req_category.lower() in deal.get("category", "").lower():
            score += 30

        # Location Bonus
        if req_location:
            loc = req_location.lower()
            if loc in location_str or (loc == "mumbai" and location_str != ""):
                score += 40
            else:
                # Deduct points if location requested but doesn't match location string
                score -= 10

        # Rapidfuzz Title & Brand Relevance Matching
        if user_query:
            title_score = fuzz.partial_ratio(user_query.lower(), title.lower())
            brand_score = fuzz.partial_ratio(user_query.lower(), brand.lower())
            desc_score = fuzz.partial_ratio(user_query.lower(), desc.lower())
            score += (title_score * 0.4) + (brand_score * 0.3) + (desc_score * 0.1)

        # Create copy of deal with score key
        scored_deal = dict(deal)
        scored_deal["score"] = score
        scored_results.append(scored_deal)

    # Sort results by score descending
    scored_results.sort(key=lambda x: x["score"], reverse=True)

    return scored_results