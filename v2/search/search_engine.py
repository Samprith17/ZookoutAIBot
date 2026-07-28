import json
import logging
from typing import Dict, List, Any, Optional
from pathlib import Path
from v2.constants import NEARBY_AREAS_MAP

logger = logging.getLogger(__name__)

DATA_FILE = Path(__file__).resolve().parent.parent.parent / "data" / "clean_deals.json"


def is_corrupted_title(title: str) -> bool:
    """Detects OCR artifact junk / corrupted offer titles."""
    if not title:
        return True
    t = title.strip()
    if len(t) < 3:
        return True

    junk_symbols = ["%", "@", "#", "*", "^", "~", "`", "$", "|", "§", "©", "®"]
    if sum(t.count(sym) for sym in junk_symbols) >= 2:
        return True

    words = t.split()
    nonsense_count = 0
    for w in words:
        if len(w) > 4 and not any(v in w.lower() for v in ["a", "e", "i", "o", "u", "y"]):
            nonsense_count += 1
        if sum(1 for c in w if c.isdigit()) > 0 and sum(1 for c in w if c.isalpha()) > 0 and len(w) > 3:
            nonsense_count += 1

    if len(words) > 0 and (nonsense_count / len(words)) >= 0.4:
        return True

    return False


def get_clean_title_fallback(category: str) -> str:
    """Returns clean category fallback title for corrupted offer titles."""
    c = (category or "").lower()
    if any(k in c for k in ["restaurant", "dining", "food", "buffet"]):
        return "Special Dining Offer"
    if any(k in c for k in ["spa", "massage", "wellness"]):
        return "Premium Spa Experience"
    if any(k in c for k in ["salon", "hair", "beauty"]):
        return "Beauty & Grooming Offer"
    if any(k in c for k in ["hotel", "resort", "stay"]):
        return "Hotel Experience"
    if any(k in c for k in ["cafe", "coffee"]):
        return "Cafe Special"
    if any(k in c for k in ["entertainment", "gaming", "activity"]):
        return "Entertainment Offer"
    return "Special Catalog Offer"


def clean_offer_title(title: str, category: str = "") -> str:
    """Cleans offer title and applies category fallback if corrupted."""
    if is_corrupted_title(title):
        return get_clean_title_fallback(category)
    return title.strip()


def display_category(category: str) -> str:
    """Returns formatted display category name."""
    if not category:
        return "Experience"
    return category.strip().title()


def load_deals() -> List[Dict[str, Any]]:
    """Loads cleaned deals dataset from JSON file."""
    if not DATA_FILE.exists():
        logger.error(f"Clean deals file missing at {DATA_FILE}")
        return []
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading clean deals: {e}")
        return []


def clean_location_string(location_raw: str) -> str:
    """
    Deduplicates location tokens case-insensitively while preserving 'Area, City' order.
    Example: 'Andheri, Andheri, Mumbai' -> 'Andheri, Mumbai'
    """
    if not location_raw:
        return "Mumbai"

    parts = [p.strip() for p in location_raw.split(",") if p.strip()]
    seen = set()
    cleaned_parts = []

    for part in parts:
        part_lower = part.lower()
        if part_lower not in seen:
            seen.add(part_lower)
            cleaned_parts.append(part)

    return ", ".join(cleaned_parts) if cleaned_parts else "Mumbai"


def extract_deal_area(deal: Dict[str, Any]) -> str:
    """Extracts local area from deal location string."""
    loc = deal.get("location") or ""
    parts = [p.strip() for p in loc.split(",") if p.strip()]
    if parts:
        return parts[0]
    return ""


def get_nearby_locations(location: str) -> List[str]:
    """Returns list of nearby areas for a given location or area."""
    if not location:
        return ["Andheri", "Bandra", "Juhu"]

    loc_clean = location.strip().title()
    for area, nearbys in NEARBY_AREAS_MAP.items():
        if area.lower() in loc_clean.lower() or loc_clean.lower() in area.lower():
            return nearbys

    return ["Andheri", "Bandra", "Juhu"]


def normalize_deal(deal: Dict[str, Any], category: Optional[str] = None, location: Optional[str] = None) -> Dict[str, Any]:
    """Normalizes deal fields with fallbacks and clean formatting."""
    raw_loc = deal.get("location") or location or "Mumbai"
    cleaned_loc = clean_location_string(raw_loc)

    cat = deal.get("category") or category or "Experience"

    try:
        price = float(str(deal.get("price", "0")).replace(",", ""))
    except Exception:
        price = 0.0

    disc = deal.get("discount_percent", 0) or 0
    formatted_price = f"₹{int(price):,}" if price > 0 else "Price unavailable"

    savings = int(price * (disc / 100.0)) if price > 0 and disc > 0 else 0

    return {
        "id": str(deal.get("id", "UNKNOWN")),
        "brand": deal.get("brand", "Merchant"),
        "title": deal.get("title", "Special Offer"),
        "clean_title": deal.get("clean_title") or deal.get("title") or "Special Offer",
        "category": cat,
        "display_category": cat.title(),
        "location": cleaned_loc,
        "display_location": cleaned_loc,
        "price": price,
        "formatted_price": formatted_price,
        "discount_percent": disc,
        "savings": savings,
        "rating": deal.get("rating", 4.5),
        "confidence": deal.get("confidence", 0.9),
        "description": deal.get("description", ""),
        "tags": deal.get("tags", []),
        "score": deal.get("score", 50.0),
        "reasons": deal.get("reasons", [])
    }


def matches_category(req_category: str, deal: Dict[str, Any]) -> bool:
    """Robust category matching against deal fields."""
    if not req_category:
        return True

    req = req_category.strip().lower()
    cat = (deal.get("category") or "").strip().lower()
    title = (deal.get("title") or "").strip().lower()
    desc = (deal.get("description") or "").strip().lower()
    tags = [str(t).lower() for t in deal.get("tags", [])]

    text_content = f"{title} {desc} {' '.join(tags)}"

    if req in ["restaurant", "dining", "food"]:
        return any(k in cat or k in text_content for k in ["restaurant", "dining", "food", "buffet", "cafe", "bistro", "barbeque", "eatery"])
    if req in ["spa", "massage", "wellness"]:
        return any(k in cat or k in text_content for k in ["spa", "massage", "wellness", "therapy", "body", "parlor"])
    if req in ["salon", "hair", "beauty"]:
        return any(k in cat or k in text_content for k in ["salon", "hair", "beauty", "cut", "styling", "facial", "makeover"])
    if req in ["hotel", "resort", "stay"]:
        return any(k in cat or k in text_content for k in ["hotel", "resort", "stay", "room", "inn"])

    return cat == req or req in text_content


def compute_weighted_score(deal: Dict[str, Any], intent: Dict[str, Any], loc_tier: str) -> Dict[str, Any]:
    """
    Computes 6-Factor Weighted Recommendation Score (Max 100.0 points):
    1. Location relevance: 35% (Exact Area: 35, Nearby: 25, City: 15, Catalog: 5)
    2. Budget match: 20% (Fits max_price with savings ratio)
    3. Discount: 20% (Percentage discount)
    4. Rating: 10% (Star rating)
    5. Popularity / Confidence: 10% (Confidence score)
    6. Offer quality: 5% (Clean readable title & non-zero discount)
    """
    req_category = intent.get("category")
    max_price = intent.get("max_price")
    min_price = intent.get("min_price")
    sort_by_discount = intent.get("sort_by_discount", False)
    target_area = (intent.get("area") or intent.get("location") or "").strip().lower()

    try:
        price = float(str(deal.get("price", "0")).replace(",", ""))
    except Exception:
        price = 0.0

    disc = deal.get("discount_percent", 0) or 0
    rating = float(deal.get("rating", 4.5))
    confidence = float(deal.get("confidence", 0.9))

    title = deal.get("title", "")
    desc = deal.get("description", "")
    tags = [str(t).lower() for t in deal.get("tags", [])]
    full_text = f"{title} {desc} {' '.join(tags)}".lower()

    # 1. Location Relevance (35%)
    if loc_tier == "exact":
        loc_score = 35.0
    elif loc_tier == "nearby":
        loc_score = 25.0
    elif loc_tier == "city":
        loc_score = 15.0
    else:
        loc_score = 5.0

    # 2. Budget Match (20%)
    if max_price and price > 0:
        if price <= max_price:
            val_ratio = (max_price - price) / max_price
            budget_score = 10.0 + min(10.0, val_ratio * 10.0)
        else:
            budget_score = 0.0
    else:
        budget_score = 15.0

    # 3. Discount Score (20%)
    disc_score = min(20.0, disc * 0.4)

    # 4. Rating Score (10%)
    rating_score = min(10.0, (rating / 5.0) * 10.0)

    # 5. Popularity / Confidence Score (10%)
    pop_score = min(10.0, confidence * 10.0)

    # 6. Offer Quality Score (5%)
    quality_score = 5.0 if (disc > 0 and len(title) > 5) else 2.5

    # Final Weighted Sum
    total_score = loc_score + budget_score + disc_score + rating_score + pop_score + quality_score

    if sort_by_discount:
        total_score += (disc * 0.5)

    # Build Factual Reasons (ONLY Verifiable Facts)
    reasons = []
    if req_category and matches_category(req_category, deal):
        reasons.append(f"Matches requested category ({req_category.title()}).")

    deal_area = extract_deal_area(deal)
    if loc_tier == "exact" and deal_area:
        reasons.append(f"Located in {deal_area}.")
    elif loc_tier == "nearby" and deal_area:
        reasons.append(f"Located in {deal_area} (Nearby).")

    if max_price and price > 0 and price <= max_price:
        reasons.append(f"Within ₹{int(max_price):,} budget.")

    is_buffet = "buffet" in full_text
    if is_buffet:
        reasons.append("Includes buffet offer.")

    if disc > 0:
        reasons.append(f"{disc}% discount.")

    normalized = normalize_deal(deal, req_category, target_area)
    normalized["score"] = round(total_score, 2)
    normalized["reasons"] = reasons
    return normalized


def search_deals(intent: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    AI Deal Concierge Search Engine:
    - Search Hierarchy: Exact Area -> Nearby Areas -> City -> Entire Catalog
    - Explicit Fallback Notices: Attaches fallback_notice to intent when expanding search
    - Catalog Buffet Filtering: Actual catalog filter for 'buffet'
    - 6-Factor Weighted Scoring Engine (35/20/20/10/10/5)
    """
    deals = load_deals()
    if not deals:
        return []

    intent = intent or {}
    req_category = intent.get("category")
    req_city = (intent.get("city") or "").strip().lower()
    req_location = (intent.get("location") or "").strip().lower()
    req_area = (intent.get("area") or "").strip().lower()

    min_price = intent.get("min_price")
    max_price = intent.get("max_price")
    sort_by_discount = intent.get("sort_by_discount", False)
    user_query = (intent.get("query") or "").lower().strip()

    # Check for Buffet filtering requirement (Issue 2)
    is_buffet_requested = any(w in user_query for w in ["buffet", "only buffet", "buffet only"]) or intent.get("meal_type") == "buffet"

    target_area = req_area or (req_location if req_location not in ["mumbai", "bangalore", "bengaluru", ""] else None)
    target_city = req_city or (req_location if req_location in ["mumbai", "bangalore", "bengaluru"] else None)

    # 1. Base Filter by Category & Price
    candidate_deals = []
    for deal in deals:
        try:
            price = float(str(deal.get("price", "0")).replace(",", ""))
        except Exception:
            price = 0.0

        if req_category and not matches_category(req_category, deal):
            continue

        if max_price is not None and price > max_price and price > 0:
            continue

        if min_price is not None and price < min_price and price > 0:
            continue

        candidate_deals.append(deal)

    # If Buffet requested: Filter candidates first for buffet
    if is_buffet_requested:
        buffet_deals = []
        for deal in candidate_deals:
            full_txt = f"{deal.get('title','')} {deal.get('description','')} {deal.get('category','')} {' '.join(deal.get('tags',[]))}".lower()
            if "buffet" in full_txt:
                buffet_deals.append(deal)

        if buffet_deals:
            candidate_deals = buffet_deals
            intent["fallback_notice"] = None
        else:
            intent["fallback_notice"] = "No buffet deals are currently available. Here are the closest restaurant deals instead."

    # 2. Location Filtering Pipeline: Exact Area -> Nearby Areas -> City -> Catalog
    matched_scored_deals = []

    if target_area:
        # Step 1: Exact Area Match
        exact_deals = []
        for deal in candidate_deals:
            deal_area = (extract_deal_area(deal) or "").lower()
            full_txt = f"{deal.get('location','')} {deal.get('title','')} {deal.get('description','')}".lower()
            if target_area == deal_area or target_area in full_txt:
                exact_deals.append(deal)

        if exact_deals:
            if not intent.get("fallback_notice"):
                intent["fallback_notice"] = None
            for d in exact_deals:
                matched_scored_deals.append(compute_weighted_score(d, intent, "exact"))
        else:
            # Step 2: Nearby Areas Fallback
            nearby_list = get_nearby_locations(target_area)
            nearby_deals = []
            for deal in candidate_deals:
                deal_area = (extract_deal_area(deal) or "").lower()
                full_txt = f"{deal.get('location','')} {deal.get('title','')}".lower()
                if any(nb.lower() in deal_area or nb.lower() in full_txt for nb in nearby_list):
                    nearby_deals.append(deal)

            if nearby_deals:
                if not intent.get("fallback_notice"):
                    intent["fallback_notice"] = f"No exact {req_category or 'deal'}s were found in {target_area.title()}. Showing the closest available deals nearby."
                for d in nearby_deals:
                    matched_scored_deals.append(compute_weighted_score(d, intent, "nearby"))
            else:
                # Step 3: City Fallback
                city_deals = candidate_deals
                if city_deals:
                    if not intent.get("fallback_notice"):
                        intent["fallback_notice"] = f"No exact deals were found in {target_area.title()}. Showing top deals across the city."
                    for d in city_deals:
                        matched_scored_deals.append(compute_weighted_score(d, intent, "city"))

    elif target_city:
        city_deals = []
        for deal in candidate_deals:
            loc_str = (deal.get("location") or "").lower()
            if target_city in loc_str:
                city_deals.append(deal)

        if city_deals:
            intent["fallback_notice"] = None
            for d in city_deals:
                matched_scored_deals.append(compute_weighted_score(d, intent, "city"))
        else:
            for d in candidate_deals:
                matched_scored_deals.append(compute_weighted_score(d, intent, "catalog"))
    else:
        for d in candidate_deals:
            matched_scored_deals.append(compute_weighted_score(d, intent, "catalog"))

    # 3. Weighted Ranking Sort
    matched_scored_deals.sort(
        key=lambda x: (x["discount_percent"] if sort_by_discount else x["score"], x["confidence"]),
        reverse=True
    )

    return matched_scored_deals


def get_deal_comparison(intent: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Returns structured comparison list of top deals for deal comparison report."""
    results = search_deals(intent)
    if not results:
        return []

    top_deals = results[:4]
    comparison_table = []

    for i, deal in enumerate(top_deals):
        disc = deal.get("discount_percent", 0)
        rec = "Best Overall" if i == 0 else ("Highest Discount" if disc >= 40 else "Best Value")
        comparison_table.append({
            "brand": deal.get("brand", "Merchant"),
            "price": deal.get("formatted_price", "N/A"),
            "discount": f"{disc}%",
            "savings": f"₹{deal.get('savings', 0):,}",
            "rating": f"⭐ {deal.get('rating', 4.5)}/5.0",
            "recommendation": rec
        })

    return comparison_table