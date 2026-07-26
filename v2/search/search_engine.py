import json
import re
from pathlib import Path
from typing import List, Dict, Any, Optional
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


def clean_offer_title(deal: Dict[str, Any]) -> str:
    """
    Intelligent Offer Title Extraction & OCR Cleanup Engine (Milestone 12.3):
    Rejects OCR junk, trailing concatenated words, and replaces corrupted titles
    with clean human-readable titles or generic category fallback labels:
    - Restaurant Offer
    - Spa Offer
    - Salon Offer
    - Entertainment Offer
    - Cafe Offer
    - Hotel Offer
    """
    title = (deal.get("title") or "").strip()
    brand = (deal.get("brand") or "").strip()
    category = (deal.get("category") or "").strip()
    desc = (deal.get("description") or "").strip()
    tags = [str(t).strip() for t in deal.get("tags", []) if str(t).strip()]
    full_text = f"{title} {desc}"

    # Specific OCR Junk Patterns
    if re.search(r"Any\s+Spa\s+Therapy.*Flat\s+50%", full_text, flags=re.IGNORECASE):
        return "Spa Therapy – Flat 50% Off"

    if re.search(r"Flat\s+50%\s+Off.*on.*(?:Menu|Bill)", full_text, flags=re.IGNORECASE):
        if "menu" in full_text.lower():
            return "Flat 50% Off on Entire Menu"
        return "Flat 50% Off on Total Bill"

    if re.search(r"Executive\s+Veg\s+Lunch", full_text, flags=re.IGNORECASE):
        return "Executive Veg Lunch"

    # Human-written clean pattern matches from description
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
            if len(clean) >= 5:
                return clean[:70].title()

    # Clean title directly if it does not contain heavy OCR junk or single-word junk
    ocr_junk = r"\b(?:Offline|Anot|Wr|E|St|Cveis|Hpearya|Oitf|Pmaays|Smpiau|Tphree|HThoete|SHyodteelw|Soukb|Gsatalauxryant|Bbiulliyn|Bsuhyo|Midnight|Athyi|Imcpel|Imsaelnotna|Acto|Term Results)\b"
    if not re.search(ocr_junk, title, flags=re.IGNORECASE):
        cleaned_t = title
        cleaned_t = re.sub(r"\b\d+\s+At\b.*", "", cleaned_t, flags=re.IGNORECASE)
        cleaned_t = re.sub(r"\b[A-Za-z]\s+[A-Za-z]\s+[A-Za-z]\b.*", "", cleaned_t)
        cleaned_t = re.sub(r"\s+", " ", cleaned_t).strip()
        cleaned_t = re.sub(r"\b(?:[Bv]uy|sppaaiyre|Bbiulliyn|Bsuhyo|Bvouuyc|vooutc|Athyi|B\s+U\s+Yp|Pmaays)\b.*", "", cleaned_t, flags=re.IGNORECASE).strip()

        if len(cleaned_t) >= 6 and not cleaned_t.isdigit():
            return cleaned_t[:70]

    # Fallback using Category (Milestone 12.3 Generic OCR Labels)
    cat_str = category.lower() if category and category != "Unknown" else "special experience"
    if "restaurant" in cat_str or "dining" in cat_str or "food" in cat_str:
        return "Restaurant Offer"
    if "spa" in cat_str or "massage" in cat_str:
        return "Spa Offer"
    if "salon" in cat_str or "beauty" in cat_str:
        return "Salon Offer"
    if "cafe" in cat_str or "coffee" in cat_str:
        return "Cafe Offer"
    if "hotel" in cat_str or "resort" in cat_str:
        return "Hotel Offer"
    if "entertainment" in cat_str or "adventure" in cat_str or "gaming" in cat_str or "water park" in cat_str:
        return "Entertainment Offer"

    return "Special Offer"


def display_category(req_category: Optional[str], deal: Dict[str, Any]) -> str:
    """Category Normalization (Milestone 12.3): Converts None/N/A/Unknown into clean category strings."""
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
    """
    Shared Deal Normalization Layer (Milestone 12.3).
    Constructs a single normalized deal object reused across Search, Recommendation Engine,
    Experience Planner, Savings Agent, Comparison, and Personalization.
    Exposes: Brand, Category, Offer, Price, Discount, Location, Source, Confidence.
    """
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
    if raw_loc and raw_loc.lower() not in ["none", "n/a", "", "null"]:
        if "mumbai" in raw_loc.lower():
            display_location = raw_loc.title()
        else:
            display_location = f"{raw_loc.title()}, Mumbai"
    else:
        display_location = "Mumbai"

    disc = deal.get("discount_percent")
    if disc is None or not isinstance(disc, (int, float)):
        try:
            disc = int(deal.get("discount_percent", 0))
        except Exception:
            disc = 0

    is_complete = price > 0 and norm_cat != "Special Experience" and raw_loc.lower() not in ["none", "", "null"]
    confidence = 0.95 if is_complete else 0.65

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

    if req == "cafe":
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
    Search Deals Engine (Milestone 12.3):
    Ranks deals using the Shared Deal Normalization Layer.
    Guarantees no 'Category: N/A', 'Location: None', or raw OCR titles.
    """
    deals = load_deals()
    if not deals:
        return []

    intent = intent or {}
    req_category = intent.get("category")
    req_city = intent.get("city")
    req_location = intent.get("location")
    req_area = intent.get("area")
    min_price = intent.get("min_price")
    max_price = intent.get("max_price")
    req_preferences = intent.get("preferences") or []
    req_occasion = intent.get("occasion")
    user_query = intent.get("query")

    scored_results = []

    for deal in deals:
        title = (deal.get("title") or "").strip()
        brand = (deal.get("brand") or "").strip()
        desc = (deal.get("description") or "").strip()
        category_raw = (deal.get("category") or "").strip()
        location_raw = (deal.get("location") or "").strip()
        tags = [str(t) for t in deal.get("tags", [])]

        full_text = f"{title} {brand} {desc} {category_raw} {location_raw} {' '.join(tags)}".lower()

        try:
            price = float(str(deal.get("price", "0")).replace(",", ""))
        except Exception:
            price = 0.0

        location_str = location_raw.lower()
        cat_str = category_raw.lower()

        # Category Filter
        if req_category and not matches_category(req_category, deal):
            continue

        # Location Filter
        if req_area and req_area.lower() not in location_str and "mumbai" not in location_str:
            if req_location and req_location.lower() not in location_str:
                continue

        score = 50.0
        reasons = []

        # Category Match Score
        if req_category:
            if req_category.lower() in cat_str or req_category.lower() in title.lower():
                score += 30
                reasons.append(f"Matches your requested category ({req_category.title()})")
            else:
                score += 20
                reasons.append(f"Relevant deal in {display_category(req_category, deal)}")

        # Location Match Score
        target_loc = req_area or req_location or req_city
        if target_loc:
            t_loc = target_loc.lower()
            if t_loc in location_str and t_loc != "mumbai":
                score += 25
            elif "mumbai" in location_str or t_loc == "mumbai":
                score += 15

        # Budget Match Score
        if max_price is not None:
            if price > 0 and price <= max_price:
                score += 20
            elif price <= 0:
                score += 5
            else:
                score += 5

        disc = deal.get("discount_percent", 0)
        if disc > 0:
            score += (disc * 0.1)

        # Normalize deal via Shared Deal Normalization Layer
        scored_deal = normalize_deal(deal, req_category, target_loc)
        scored_deal["score"] = round(score, 2)
        scored_deal["reasons"] = reasons
        scored_results.append(scored_deal)

    scored_results.sort(key=lambda x: (x["confidence"], x["score"]), reverse=True)
    return scored_results