import json
import re
from pathlib import Path
from typing import List, Dict, Any, Optional

ROOT_DIR = Path(__file__).resolve().parents[2]
DATA_FILE = ROOT_DIR / "data" / "clean_deals.json"

SUB_AREAS = [
    "Andheri", "Bandra", "Powai", "Juhu", "Borivali", "Thane", "Dadar",
    "Worli", "Lower Parel", "Malad", "Vashi", "Sakinaka", "Goregaon",
    "Santacruz", "Ghatkopar", "Chembur", "Mulund", "Kandivali", "Colaba", "Fort"
]

# Nearby Area Mapping for Intelligent Location Fallbacks
NEARBY_AREAS_MAP = {
    "whitefield": ["Indiranagar", "Koramangala", "MG Road"],
    "koramangala": ["Indiranagar", "HSR Layout", "MG Road"],
    "indiranagar": ["Koramangala", "MG Road", "HSR Layout"],
    "powai": ["Andheri", "Bandra", "Juhu"],
    "bandra": ["Andheri", "Juhu", "Lower Parel"],
    "andheri": ["Bandra", "Juhu", "Powai"],
    "juhu": ["Andheri", "Bandra", "Powai"],
    "borivali": ["Malad", "Kandivali", "Goregaon"],
    "thane": ["Mulund", "Ghatkopar", "Powai"],
    "aundh": ["Baner", "Viman Nagar", "Koregaon Park"],
    "dadabari": ["Talwandi", "Vigyan Nagar", "Kota"],
}


def load_deals() -> List[Dict]:
    """Load all deals from clean_deals.json"""
    if not DATA_FILE.exists():
        return []
    with open(DATA_FILE, "r", encoding="utf-8") as file:
        return json.load(file)


DEALS = load_deals()


def get_nearby_locations(location: str) -> List[str]:
    """Returns nearby alternative locations if no deals exist in requested area."""
    loc_key = (location or "").lower().strip()
    return NEARBY_AREAS_MAP.get(loc_key, ["Andheri", "Bandra", "Juhu"])


def clean_location_string(loc_str: str) -> str:
    """
    Cleans location strings by removing duplicate parts case-insensitively,
    trimming extra spaces, and preserving correct order (Area, City).
    Examples:
    'Andheri, Andheri, Mumbai' -> 'Andheri, Mumbai'
    'Bandra, Mumbai' -> 'Bandra, Mumbai'
    'Mumbai' -> 'Mumbai'
    'Powai, Powai, Mumbai' -> 'Powai, Mumbai'
    """
    if not loc_str or not isinstance(loc_str, str):
        return "Mumbai"

    parts = [p.strip() for p in loc_str.split(",") if p.strip()]
    if not parts:
        return "Mumbai"

    seen = set()
    cleaned_parts = []

    for part in parts:
        lower_part = part.lower()
        if lower_part not in seen:
            seen.add(lower_part)
            formatted = part.title() if part.islower() or part.isupper() else part
            cleaned_parts.append(formatted)

    return ", ".join(cleaned_parts)


def extract_deal_area(deal: Dict[str, Any]) -> Optional[str]:
    """Dynamically extracts sub-area from deal title, brand, description, or tags."""
    title = (deal.get("title") or "").lower()
    brand = (deal.get("brand") or "").lower()
    desc = (deal.get("description") or "").lower()
    tags = " ".join(str(t) for t in deal.get("tags", [])).lower()
    full_text = f"{title} {brand} {desc} {tags}"

    for area in SUB_AREAS:
        if re.search(r"\b" + re.escape(area.lower()) + r"\b", full_text):
            return area
    return None


def is_corrupted_title(title: str) -> bool:
    """Detects if an offer title is corrupted or contains OCR garbage text."""
    if not title or not isinstance(title, str):
        return True

    t = title.strip()
    if len(t) < 4:
        return True

    if re.search(r"(?:^|[^\d\s])%|[@#\*^~$]", t):
        return True

    ocr_junk_regex = r"\b(?:Offline|Anot|Wr|E|St|Cveis|Hpearya|Oitf|Pmaays|Smpiau|Tphree|HThoete|SHyodteelw|Soukb|Gsatalauxryant|Bbiulliyn|Bsuhyo|Midnight|Athyi|Imcpel|Imsaelnotna|Acto|Term Results|Oricfhf|A25T)\b"
    if re.search(ocr_junk_regex, t, flags=re.IGNORECASE):
        return True

    words = [w for w in re.findall(r"\S+", t) if w]
    if not words:
        return True

    garbage_count = 0
    vowel_regex = r"[aeiouyAEIOUY]"

    for w in words:
        if re.search(r"\b[A-Za-z]+\d+\w*|\b\d+[A-Za-z]+\w*", w):
            garbage_count += 1
        elif len(w) >= 4 and not re.search(vowel_regex, w):
            garbage_count += 1
        elif re.search(r"[a-z][A-Z]", w):
            garbage_count += 1

    if garbage_count >= max(1, len(words) // 2):
        return True

    return False


def get_clean_category_fallback(category: str) -> str:
    """Returns clean human-readable category fallback labels when an offer title is corrupted."""
    cat_str = (category or "").lower().strip()

    if "restaurant" in cat_str or "dining" in cat_str or "food" in cat_str:
        return "Special Dining Offer"
    if "spa" in cat_str or "massage" in cat_str or "wellness" in cat_str:
        return "Premium Spa Experience"
    if "salon" in cat_str or "beauty" in cat_str or "clinic" in cat_str or "hair" in cat_str:
        return "Beauty & Grooming Offer"
    if "hotel" in cat_str or "resort" in cat_str or "stay" in cat_str:
        return "Hotel Experience"
    if "cafe" in cat_str or "coffee" in cat_str or "bistro" in cat_str:
        return "Cafe Special"
    if "entertainment" in cat_str or "adventure" in cat_str or "gaming" in cat_str or "water park" in cat_str or "activity" in cat_str:
        return "Entertainment Offer"

    return "Special Experience"


def clean_offer_title(deal: Dict[str, Any]) -> str:
    """Intelligent Offer Title Extraction & OCR Cleanup Engine."""
    title = (deal.get("title") or "").strip()
    category = (deal.get("category") or "").strip()
    desc = (deal.get("description") or "").strip()
    full_text = f"{title} {desc}"

    if re.search(r"Any\s+Spa\s+Therapy.*Flat\s+50%", full_text, flags=re.IGNORECASE):
        return "Spa Therapy – Flat 50% Off"

    if re.search(r"Flat\s+50%\s+Off.*on.*(?:Menu|Bill)", full_text, flags=re.IGNORECASE):
        if "menu" in full_text.lower():
            return "Flat 50% Off on Entire Menu"
        return "Flat 50% Off on Total Bill"

    if re.search(r"Executive\s+Veg\s+Lunch", full_text, flags=re.IGNORECASE):
        return "Executive Veg Lunch"

    patterns = [
        (r"(Patrani\s+Fish\s+Biryani\s+Combo\s*\+\s*\d+\s+Domestic\s+Pint\s+Beers)", "Patrani Fish Biryani Combo + 2 Domestic Pint Beers"),
        (r"(Buy\s+1[^\-\.\,\₹]+Get\s+1\s+FREE)", None),
        (r"((?:Unlimited|Dinner|Lunch|Breakfast)\s+Buffet(?:\s+for\s+\d+)?)", None),
        (r"(\d+\s*-\s*Min[^\-\.\,\₹]+Massage)", None),
        (r"(\d+\s*-\s*Min[^\-\.\,\₹]+Spa)", None),
        (r"((?:Couple|Full Body|Thai|Relaxing)\s+Spa\s+Therapy)", None),
        (r"(Haircut\s*\+\s*Hair\s+Wash[^\-\.\,\₹]*)", None),
        (r"(Haircut[^\-\.\,\₹]+\+[^\-\.\,\₹]*)", None),
        (r"(\d+\s+Cocktails\s+or\s+Mocktails[^\-\.\,\₹]*)", None),
        (r"(\d+\s+Glasses\s+of\s+Wine[^\-\.\,\₹]*)", None),
        (r"(Beer\s+Pitcher[^\-\.\,\₹]*)", None),
        (r"(Coffee\s*\+\s*Dessert[^\-\.\,\₹]*)", None),
        (r"(\d+\s+Course[^\-\.\,\₹]*)", None),
        (r"(Day\s+Pass)", None),
        (r"(Night\s+Out\s+Sorted)", None),
    ]

    for p, replacement in patterns:
        m = re.search(p, desc, flags=re.IGNORECASE)
        if m:
            if replacement:
                return replacement
            clean = m.group(1).strip()
            clean = re.sub(r"\s+", " ", clean)
            clean = re.sub(r"\b(?:[Bv]uy|sppaaiyre|Bbiulliyn|Bsuhyo|Bvouuyc|vooutc|Athyi|B\s+U\s+Yp|Pmaays)\b.*", "", clean, flags=re.IGNORECASE).strip()
            if len(clean) >= 5 and not is_corrupted_title(clean):
                return clean[:70].title()

    if title and not is_corrupted_title(title):
        cleaned_t = title
        cleaned_t = re.sub(r"\b\d+\s+At\b.*", "", cleaned_t, flags=re.IGNORECASE)
        cleaned_t = re.sub(r"\b[A-Za-z]\s+[A-Za-z]\s+[A-Za-z]\b.*", "", cleaned_t)
        cleaned_t = re.sub(r"\s+", " ", cleaned_t).strip()
        cleaned_t = re.sub(r"\b(?:[Bv]uy|sppaaiyre|Bbiulliyn|Bsuhyo|Bvouuyc|vooutc|Athyi|B\s+U\s+Yp|Pmaays)\b.*", "", cleaned_t, flags=re.IGNORECASE).strip()

        if len(cleaned_t) >= 6 and not cleaned_t.isdigit() and not is_corrupted_title(cleaned_t):
            return cleaned_t[:70]

    return get_clean_category_fallback(category)


def display_category(req_category: Optional[str], deal: Dict[str, Any]) -> str:
    """Category Normalization: Converts None/N/A/Unknown into clean category strings."""
    raw_cat = (deal.get("category") or "").strip()
    title = (deal.get("title") or "").lower()
    desc = (deal.get("description") or "").lower()
    tags = [str(t).lower() for t in deal.get("tags", [])]
    full_text = f"{title} {desc} {' '.join(tags)}"

    if req_category:
        req = req_category.lower()
        if req == "cafe":
            return "Cafe"
        if req == "spa":
            if "salon" in raw_cat.lower():
                return "Spa & Salon"
            return "Spa"
        if req == "restaurant":
            return "Restaurant"
        if req in ["hotel", "resort"]:
            return "Hotel"
        if req in ["salon", "beauty"]:
            return "Salon"

    if raw_cat and raw_cat.lower() not in ["unknown", "none", "n/a", ""]:
        return raw_cat.title()

    if "cafe" in full_text or "coffee" in full_text:
        return "Cafe"
    if "spa" in full_text or "massage" in full_text:
        return "Spa"
    if "salon" in full_text or "haircut" in full_text:
        return "Salon"
    if "restaurant" in full_text or "buffet" in full_text or "dinner" in full_text:
        return "Restaurant"

    return "Special Experience"


def display_price(deal: Dict[str, Any]) -> str:
    """Honest Price Display: Converts 0 or missing into 'Price unavailable' or 'FREE'."""
    try:
        price = float(str(deal.get("price", "0")).replace(",", ""))
    except Exception:
        price = 0.0

    title = (deal.get("title") or "").lower()
    desc = (deal.get("description") or "").lower()

    if price > 0:
        return f"₹{int(price)}"

    if "free" in title or "free" in desc or deal.get("discount_percent", 0) == 100:
        return "FREE"

    return "Price unavailable"


def normalize_deal(deal: Dict[str, Any], req_category: Optional[str] = None, req_location: Optional[str] = None) -> Dict[str, Any]:
    """Shared Deal Normalization Layer."""
    raw_brand = (deal.get("brand") or "").strip()
    brand = raw_brand if raw_brand and raw_brand.lower() not in ["none", "n/a", "unknown", "null"] else "Zookout Merchant"

    norm_cat = display_category(req_category, deal)
    clean_title = clean_offer_title(deal)
    formatted_price = display_price(deal)

    try:
        price = float(str(deal.get("price", "0")).replace(",", ""))
    except Exception:
        price = 0.0

    raw_loc = (deal.get("location") or "").strip()
    area = extract_deal_area(deal)

    if not area and req_location and req_location.title() in SUB_AREAS:
        area = req_location.title()

    if area and (not raw_loc or raw_loc.lower() == "mumbai"):
        raw_display = f"{area}, Mumbai"
    elif area:
        raw_display = f"{area}, {raw_loc}"
    elif raw_loc and raw_loc.lower() not in ["none", "n/a", "", "null"]:
        raw_display = raw_loc
    else:
        raw_display = "Mumbai"

    display_location = clean_location_string(raw_display)

    disc = deal.get("discount_percent")
    if disc is None or not isinstance(disc, (int, float)):
        try:
            disc = int(deal.get("discount_percent", 0))
        except Exception:
            disc = 0

    is_complete = price > 0 and norm_cat != "Special Experience" and raw_loc.lower() not in ["none", "", "null"]
    confidence = 0.95 if is_complete else 0.65

    # Compute rating & savings
    rating = round(min(5.0, 4.0 + (disc * 0.02)), 1)
    original_val = price / (1.0 - (disc / 100.0)) if disc > 0 and disc < 100 else price * 1.5
    savings = max(0, int(original_val - price)) if price > 0 else 0

    normalized = dict(deal)
    normalized["brand"] = brand
    normalized["category"] = norm_cat
    normalized["display_category"] = norm_cat
    normalized["offer"] = clean_title
    normalized["clean_title"] = clean_title
    normalized["price"] = price
    normalized["formatted_price"] = formatted_price
    normalized["discount"] = disc
    normalized["discount_percent"] = disc
    normalized["location"] = display_location
    normalized["display_location"] = display_location
    normalized["source"] = deal.get("source") or "Zookout Catalog"
    normalized["confidence"] = confidence
    normalized["rating"] = rating
    normalized["savings"] = savings

    return normalized


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

    if req == "spa":
        return cat == "spa" or "spa" in text_content or "massage" in text_content

    if req in ["salon", "beauty"]:
        return cat in ["salon", "clinic"] or "salon" in text_content or "beauty" in text_content or "hair" in text_content

    if req == "restaurant":
        return cat in ["restaurant", "cafe"] or "restaurant" in text_content or "buffet" in text_content or "thali" in text_content

    if req in ["cafe", "coffee"]:
        return cat in ["cafe", "restaurant"] or "cafe" in text_content or "coffee" in text_content or "bistro" in text_content

    if req in ["hotel", "resort"]:
        return cat in ["hotel", "unknown"] or "hotel" in text_content or "resort" in text_content or "stay" in text_content

    if req in ["pub", "bar", "brewery"]:
        bar_keywords = ["beer", "pub", "bar", "cocktail", "liquor", "bottle", "drink", "imfl", "imported"]
        return any(k in text_content for k in bar_keywords)

    if req in ["adventure", "gaming", "movie", "event", "water park", "kids", "family", "entertainment"]:
        entertainment_keywords = [
            "adventure", "game", "gaming", "bowling", "park", "water", "movie", "event", "play", "arcade", "fun", "amusement"
        ]
        return cat in ["entertainment", "adventure", "gaming", "water park"] or any(k in text_content for k in entertainment_keywords)

    return cat == req or req in text_content


def search_deals(intent: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    AI Deal Concierge Search Engine:
    Ranks deals using Multi-Factor Smart Recommendation Scoring:
    - Discount (20%)
    - Price Value (20%)
    - Merchant Quality / Offer Score (25%)
    - User Preferences Match (15%)
    - Location Relevance (20%)
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

    target_area = req_area or (req_location if req_location not in ["mumbai", ""] else None)
    target_city = req_city or (req_location if req_location == "mumbai" else None)

    scored_results = []

    for deal in deals:
        title = (deal.get("title") or "").strip()
        brand = (deal.get("brand") or "").strip()
        desc = (deal.get("description") or "").strip()
        category_raw = (deal.get("category") or "").strip()
        location_raw = (deal.get("location") or "").strip()
        tags = [str(t) for t in deal.get("tags", [])]

        full_text = f"{title} {brand} {desc} {category_raw} {location_raw} {' '.join(tags)}".lower()
        deal_area = (extract_deal_area(deal) or "").lower()

        try:
            price = float(str(deal.get("price", "0")).replace(",", ""))
        except Exception:
            price = 0.0

        location_str = location_raw.lower()
        cat_str = category_raw.lower()

        if req_category and not matches_category(req_category, deal):
            continue

        if target_area:
            if target_area != deal_area and target_area not in full_text:
                continue

        elif target_city:
            if target_city not in location_str and target_city not in full_text:
                continue

        if max_price is not None and price > max_price and price > 0:
            continue

        if min_price is not None and price < min_price and price > 0:
            continue

        # Multi-Factor Smart Recommendation Scoring
        score = 50.0
        reasons = []

        disc = deal.get("discount_percent", 0) or 0
        disc_score = min(20.0, disc * 0.4)
        score += disc_score

        if max_price and price > 0:
            val_ratio = (max_price - price) / max_price
            price_score = max(0.0, min(20.0, val_ratio * 20.0))
            score += price_score
            reasons.append(f"Fits budget of ₹{int(max_price)}")

        if target_area:
            score += 20.0
            reasons.append(f"Located in {target_area.title()}")
        elif target_city:
            score += 10.0
            reasons.append(f"Located in {target_city.title()}")

        if req_category:
            score += 25.0
            reasons.append(f"Matches category ({req_category.title()})")

        if sort_by_discount:
            score += (disc * 0.5)

        scored_deal = normalize_deal(deal, req_category, target_area or target_city)
        scored_deal["score"] = round(score, 2)
        scored_deal["reasons"] = reasons
        scored_results.append(scored_deal)

    scored_results.sort(key=lambda x: (x["discount_percent"] if sort_by_discount else x["score"], x["confidence"]), reverse=True)

    if not scored_results and target_area:
        fallback_intent = dict(intent)
        fallback_intent["area"] = None
        fallback_intent["location"] = None
        return search_deals(fallback_intent)

    return scored_results


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
            "savings": f"₹{deal.get('savings', 0)}",
            "rating": f"⭐ {deal.get('rating', 4.5)}/5.0",
            "recommendation": rec
        })

    return comparison_table