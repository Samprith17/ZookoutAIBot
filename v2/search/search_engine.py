import json
from pathlib import Path
from typing import List, Dict, Any
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

    return req in cat or req in text_content


def search_deals(intent: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    AI Recommendation & Reasoning Engine (Milestone 3):
    1. Category Match (30 pts)
    2. Location Match (25 pts)
    3. Budget Match (20 pts)
    4. Occasion Match (10 pts)
    5. Preference Match (10 pts)
    6. Discount Value (5 pts)
    Generates structured reasoning explanations for recommendations.
    """

    req_category = intent.get("category")
    req_location = intent.get("location")
    req_area = intent.get("area")
    req_city = intent.get("city")
    min_price = intent.get("min_price")
    max_price = intent.get("max_price")
    req_occasion = intent.get("occasion")
    req_preferences = intent.get("preferences") or []
    user_query = intent.get("query", "").strip()

    candidate_deals = []

    # Step 1: Filter deals strictly by Category & Price Limits
    for deal in DEALS:
        if req_category and not matches_category(req_category, deal):
            continue

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

    # Step 2: Multi-Factor Scoring & Reasoning Breakdown
    scored_results = []
    for deal in candidate_deals:
        score = 0.0
        reasons = []
        cat_str = (deal.get("category") or "").lower()
        title = deal.get("title", "")
        brand = deal.get("brand", "")
        desc = deal.get("description", "")
        location_str = (deal.get("location") or "").lower()
        tags = [str(t).lower() for t in deal.get("tags", [])]
        full_text = f"{title} {desc} {' '.join(tags)}".lower()

        try:
            price = float(str(deal.get("price", "0")).replace(",", ""))
        except Exception:
            price = 0.0

        discount = deal.get("discount_percent", 0)

        # 1. Category Match (30 pts)
        if req_category:
            if req_category.lower() in cat_str or req_category.lower() in title.lower():
                score += 30
                reasons.append(f"Matches your requested category ({req_category.title()})")
            else:
                score += 20
                reasons.append(f"Relevant deal in {deal.get('category', 'Zookout')}")

        # 2. Location Match (25 pts)
        target_loc = req_area or req_location or req_city
        if target_loc:
            t_loc = target_loc.lower()
            if t_loc in location_str:
                score += 25
                reasons.append(f"Located in your requested area ({target_loc.title()})")
            elif "mumbai" in location_str or t_loc == "mumbai":
                score += 15
                reasons.append(f"Available in {deal.get('location', 'Mumbai')}")
            else:
                score += 5

        # 3. Budget Match (20 pts)
        if max_price is not None:
            if price <= max_price:
                score += 20
                reasons.append(f"Fits your budget (₹{int(price)} vs under ₹{max_price})")
            else:
                score += 5
        elif min_price is not None:
            if price >= min_price:
                score += 20
                reasons.append(f"Within your price range (₹{int(price)})")

        # 4. Occasion Match (10 pts)
        if req_occasion:
            if req_occasion.lower() in full_text:
                score += 10
                reasons.append(f"Ideal choice for a {req_occasion.title()} experience")

        # 5. Preference Match (10 pts)
        matched_prefs = []
        for pref in req_preferences:
            if pref.lower() in full_text:
                matched_prefs.append(pref.title())
        if matched_prefs:
            score += 10
            reasons.append(f"Offers requested features ({', '.join(matched_prefs)})")

        # 6. Discount & Value Match (5 pts)
        if discount and discount > 0:
            score += min(5.0, discount * 0.1)
            reasons.append(f"Great savings offer ({discount}% OFF)")

        # Rapidfuzz Title Query Bonus
        if user_query:
            rf_score = fuzz.partial_ratio(user_query.lower(), title.lower())
            score += (rf_score * 0.1)

        # Fallback default reason if reasons list is short
        if len(reasons) < 2:
            reasons.append("Highly rated experience on Zookout")

        scored_deal = dict(deal)
        scored_deal["score"] = round(score, 2)
        scored_deal["reasons"] = reasons
        scored_results.append(scored_deal)

    scored_results.sort(key=lambda x: x["score"], reverse=True)
    return scored_results