import json
import logging
import re
from typing import Dict, List, Any, Optional
from pathlib import Path
from v2.constants import NEARBY_AREAS_MAP

logger = logging.getLogger(__name__)

DATA_FILE = Path(__file__).resolve().parent.parent.parent / "data" / "clean_deals.json"

KNOWN_AREAS = [
    "Andheri", "Bandra", "Juhu", "Powai", "Borivali", "Malad", "Lower Parel",
    "Worli", "Dadar", "Thane", "Koramangala", "Indiranagar", "Whitefield",
    "HSR Layout", "MG Road", "Dahisar", "Kandivali", "Goregaon", "Mulund", "Prabhadevi"
]


def is_corrupted_title(title: str) -> bool:
    """
    Detects OCR artifact junk, corrupted offer titles, and malformed catalog strings.
    Valid titles MUST NOT be flagged as corrupted:
    - 'Executive Veg Lunch' -> Valid
    - '8 Inch Pizza + 2 Drinks' -> Valid
    - 'Coffee + Dessert For 2' -> Valid
    - '2nd Buffet On Us' -> Valid
    - 'Flat 50% Off on Entire Menu' -> Valid

    Corrupted titles MUST be flagged:
    - 'At Llb Ianncjlaursaiv' -> Corrupted
    - '181 A(At Llb Ianncjlaursaiv' -> Corrupted
    - 'Ow E Xe ₹C4U5Ti9Ve Veg Lunch' -> Corrupted
    - '₹4E5X9Ecutive' -> Corrupted
    - 'S + Maineat For Two, For One' -> Corrupted
    - 'Restaurant Offline At Restaurant' -> Corrupted
    """
    if not title:
        return True
    p = title.strip()
    if len(p) < 3:
        return True

    p_lower = p.lower()

    # Known OCR junk tokens
    junk_tokens = ["llb", "ianncj", "awto", "anot", "trthhe", "pwaays", "pblaeya", "maineat", "bsuhyo", "bbiulliyn", "sveorutsc", "bcuoyu", "rtsheis", "coen", "pchaoyi", "v0o%u", "n9ly9", "just wh", "imcpel", "imsaelnot", "om de", "face d"]
    if any(k in p_lower for k in junk_tokens):
        return True

    # Unspaced brackets / malformed prefixes e.g. 'A(At' or '181 A('
    if re.search(r"[A-Za-z0-9]\([A-Za-z0-9]", p):
        return True

    # Genuine unprintable/OCR junk symbols (% is allowed for discounts like 50%)
    junk_symbols = ["@", "#", "*", "^", "~", "`", "$", "|", "§", "©", "®", "¥", "¤"]
    if sum(p.count(sym) for sym in junk_symbols) >= 2:
        return True

    # OCR Garbage pattern: Alternating uppercase letters and digits inside a single word
    if re.search(r"\b[A-Za-z0-9]*\d+[A-Z]+\d+[A-Za-z0-9]*\b", p):
        return True

    words = p.split()
    if not words:
        return True

    ordinals = {"1st", "2nd", "3rd", "4th", "5th", "6th", "7th", "8th", "9th", "10th"}

    for w in words:
        w_lower = w.lower()
        if w_lower in ordinals or w_lower.isdigit():
            continue

        w_clean = re.sub(r"[^\w]", "", w)
        if not w_clean:
            continue

        # 4+ consecutive consonants e.g., 'Ianncj', 'Trthhe'
        if re.search(r"[bcdfghjklmnpqrstvwxz]{4,}", w_clean, re.IGNORECASE):
            return True

        # 3+ letter word with 0 vowels e.g., 'Llb', 'N9Ly9'
        vowel_count = sum(1 for c in w_clean.lower() if c in "aeiouy")
        if len(w_clean) >= 3 and vowel_count == 0 and not w_clean.isdigit():
            return True

    return False


def get_clean_title_fallback(category: str) -> str:
    """Returns clean category fallback title for corrupted offer titles."""
    c = (category or "").lower()
    if "buffet" in c:
        return "Special Buffet Offer"
    if any(k in c for k in ["restaurant", "dining", "food"]):
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
    """
    Milestone 1 Final Production Title Cleaning Engine V5:
    - Detects catalog placeholders like 'Restaurant Offline', 'Cafe Offline' and converts directly to category fallback.
    - Detects OCR artifact junk (Llb, Ianncj, A(At, Trthhe, Awto) and converts to category fallback.
    - Never removes valid numeric prefixes (8 Inch Pizza, 2Nd Buffet On Us, 1+1 Buffet, 50% Off).
    - Preserves valid offer titles and extracts readable offer phrases from OCR strings.
    """
    if not title or len(title.strip()) < 3 or is_placeholder_title(title):
        return get_clean_title_fallback(category)

    t = title.strip()

    # Strip malformed leading OCR prefix like '181 A(' or 'A(At'
    t = re.sub(r"^\d{3,}\s+[A-Za-z]\([A-Za-z]*\s*", "", t)
    t = re.sub(r"^[A-Za-z]\(At\s*", "", t, flags=re.IGNORECASE)

    # Isolated 'At' prefix e.g. 'At Llb Ianncjlaursaiv' -> Check rest of phrase
    if re.match(r"^At\s+[A-Za-z0-9\s]+$", t, re.IGNORECASE):
        sub_p = re.sub(r"^At\s+", "", t, flags=re.IGNORECASE).strip()
        if is_corrupted_title(sub_p):
            return get_clean_title_fallback(category)

    # Detect junk titles like '45 At', '127 At', '90 At', 'xx At', 'At &', 'At At', 'At Restrobar'
    if re.match(r"^(?:\d+|\w+)?\s*At(?:\s+(?:&|\+|At|[A-Za-z0-9]+))?$", t, re.IGNORECASE):
        return get_clean_title_fallback(category)
    if re.match(r"^At\s+(?:&|\+|At)\s*$", t, re.IGNORECASE) or t.lower() in ["at &", "at at", "at"]:
        return get_clean_title_fallback(category)

    # Explicit OCR garbage titles that must use clean fallback
    if "maineat" in t.lower() or t.lower().startswith("s +"):
        return get_clean_title_fallback(category)

    # 1. Deduplicate repeated brand / venue phrases
    t = re.sub(r"\b([A-Za-z0-9\s]{3,})\s*(?:&|\+)?\s*(?:I\s+)?At\s+\1(?:\s*&|\+)?\b", r"\1", t, flags=re.IGNORECASE)
    t = re.sub(r"\b([A-Za-z0-9\s]{3,})\s*(?:&|\+)?\s*At\s+.*$", r"\1", t, flags=re.IGNORECASE)
    t = re.sub(r"\s+At\s+[A-Za-z0-9\s]+$", "", t, flags=re.IGNORECASE)

    # 2. Deduplicate consecutive duplicate words
    t = re.sub(r"\b(\w+)(?:\s+\1)+\b", r"\1", t, flags=re.IGNORECASE)

    # 3. Strip explicit 3-digit catalog IDs
    t = re.sub(r"^\d{3,}\s*(?:&|\+|\-)\s*(?=[A-Za-z])", "", t)
    t = re.sub(r"^\d{3,}\s+[A-Za-z]\(", "", t)
    t = re.sub(r"^\d+\s*&\s+(?=[A-Za-z])", "", t)

    # 4. Strip trailing OCR noise markers
    t = re.sub(r"\s+Pchaoyi\s*.*$", "", t, flags=re.IGNORECASE)

    # Clean punctuation and trailing symbols like &
    t = re.sub(r"\s+", " ", t).strip()
    t = re.sub(r"[\s&\+\-,\:\;/\\]+$", "", t).strip()

    # Split by OCR noise keywords or venue tags to isolate clean title
    split_markers = [
        r"\s+At The Outlet\s*", r"\s+On Zookout\s*", r"\s+Pmaays\s*", r"\s+Pwaithy\s*",
        r"\s+Praeyd\s*", r"\s+Ppareym\s*", r"\s+Psoafyte\s*", r"\s+Pflaawy\s*", r"\s+Pdrayy\s*",
        r"\s+Pmaeyn\s*", r"\s+Pblaeya\s*", r"\s+Bsuhyo\b", r"\s+Bbiulliyn\b", r"\s+Awto\b", r"\s+Anot\b"
    ]
    parts = re.split("|".join(split_markers), t, flags=re.IGNORECASE)

    candidates = []
    for p in reversed(parts):
        p_clean = re.sub(r"^\d{3,}\s+", "", p.strip())
        p_clean = re.sub(r"\s+", " ", p_clean).strip()
        p_clean = re.sub(r"[\s&\+\-,\:\;/\\]+$", "", p_clean).strip()

        if len(p_clean) >= 3 and not is_corrupted_title(p_clean):
            if any(len(w) >= 3 and sum(1 for c in w.lower() if c in "aeiouy") >= 1 for w in p_clean.split()):
                candidates.append(p_clean)

    if candidates:
        for c in candidates:
            c_lower = c.lower()
            if any(k in c_lower for k in ["buffet", "lunch", "dinner", "unlimited", "off", "bogo", "1+1", "beer", "wine", "spirits", "facial", "massage", "haircut", "pedicure", "manicure", "coffee", "mocktail", "cocktail", "starters", "drinks", "pizza"]):
                return c
        return candidates[0]

    # Clean punctuation and trailing symbols
    t = re.sub(r"\s+", " ", t).strip()
    t = re.sub(r"[\s&\+\-,\:\;/\\]+$", "", t).strip()

    # Reject junk titles
    if re.match(r"^(?:\d+|\w+)?\s*At(?:\s+(?:&|\+|At|[A-Za-z0-9]+))?$", t, re.IGNORECASE):
        return get_clean_title_fallback(category)

    if not t or len(t) < 3 or t.isdigit() or is_corrupted_title(t):
        return get_clean_title_fallback(category)

    return t


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
    """Extracts local area from deal fields (location, title, description, keywords, tags)."""
    loc = deal.get("location") or ""
    parts = [p.strip() for p in loc.split(",") if p.strip()]
    if parts and parts[0].lower() not in ["mumbai", "bangalore", "bengaluru"]:
        return parts[0]

    full_text = f"{deal.get('title','')} {deal.get('description','')} {' '.join(deal.get('tags',[]))} {' '.join(deal.get('keywords',[]))}".lower()

    for area in KNOWN_AREAS:
        if area.lower() in full_text:
            return area

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


def extract_discount_percent(deal: Dict[str, Any]) -> int:
    """
    Parses numeric discount percentage from discount_percent, discount string, BOGO offer terms (1+1 = 50%),
    title, description, or tags.
    """
    # 1. Check explicit discount_percent field
    raw_disc = deal.get("discount_percent")
    try:
        if raw_disc is not None and str(raw_disc).strip() not in ["", "None", "null", "N/A"]:
            val = int(float(str(raw_disc).replace("%", "").strip()))
            if 0 < val <= 100:
                return val
    except Exception:
        pass

    full_text = f"{deal.get('title','')} {deal.get('description','')} {deal.get('discount','')} {' '.join(deal.get('tags',[]))} {' '.join(deal.get('keywords',[]))}".lower()

    # 2. Check for BOGO / 1+1 / 2nd Free / Half Price (50% Off)
    if any(k in full_text for k in ["1+1", "buy 1 get 1", "buy one get one", "2nd buffet on us", "half price", "bogo", "50%"]):
        return 50

    # 3. Check for discount percentage in text
    matches = re.findall(r"(\d+)\s*%\s*(?:off|discount|flat)", full_text, re.IGNORECASE)
    if matches:
        val = int(matches[0])
        if 0 < val <= 100:
            return val

    matches_any = re.findall(r"(\d+)\s*%", full_text)
    if matches_any:
        val = int(matches_any[0])
        if 0 < val <= 100:
            return val

    return 0


FALLBACK_TITLES = [
    "Special Buffet Offer", "Special Dining Offer", "Premium Spa Experience",
    "Beauty & Grooming Offer", "Hotel Experience", "Cafe Special",
    "Entertainment Offer", "Special Catalog Offer"
]


def is_placeholder_title(t: str) -> bool:
    """Detects catalog placeholders like 'Restaurant Offline', 'Cafe Offline', 'Salon Offline', 'Spa Offline', 'Hotel Offline'."""
    if not t or len(t.strip()) < 3:
        return True
    t_lower = t.strip().lower()

    if any(k in t_lower for k in ["offline", "test brand", "anot wr e st"]):
        return True

    if re.match(r"^(?:restaurant|cafe|salon|spa|hotel|waterpark|activity)?\s*offline(?:\s+at\s+.*)?$", t_lower, re.IGNORECASE):
        return True

    if t_lower in ["60", "full", "(weekdays)", "30"]:
        return True

    return False


def recover_title_from_deal(deal: Dict[str, Any]) -> str:
    """Attempts to recover clean readable offer title from deal description or sub-phrases."""
    cat = deal.get("category", "")
    raw_t = deal.get("title", "")
    desc = deal.get("description", "")

    if not is_placeholder_title(raw_t):
        cleaned_raw = clean_offer_title(raw_t, cat)
        if cleaned_raw and not is_corrupted_title(cleaned_raw) and cleaned_raw not in FALLBACK_TITLES:
            return cleaned_raw

    if desc:
        desc_parts = re.split(r"\s+[\-\–\—]\s+", desc)
        for part in desc_parts[1:]:
            part_clean = re.sub(r"^\d+\s+", "", part.strip())
            sub_markers = [r"\s+At The Outlet", r"\s+On Zookout", r"Pmaays", r"Pwaithy", r"Praeyd", r"Ppareym", r"Psoafyte", r"Pflaawy", r"Pdrayy", r"Pmaeyn", r"Pblaeya"]
            sub_parts = re.split("|".join(sub_markers), part_clean, flags=re.IGNORECASE)
            candidate = sub_parts[0].strip()

            c_title = clean_offer_title(candidate, cat)
            if c_title and not is_placeholder_title(c_title) and not is_corrupted_title(c_title) and c_title not in FALLBACK_TITLES:
                return c_title

    return get_clean_title_fallback(cat)


def normalize_deal(deal: Dict[str, Any], category: Optional[str] = None, location: Optional[str] = None) -> Dict[str, Any]:
    """Normalizes and validates deal fields with fallbacks and clean formatting."""
    deal_area = extract_deal_area(deal)
    if deal_area:
        raw_loc = f"{deal_area.title()}, Mumbai"
    else:
        raw_loc = deal.get("location") or "Mumbai"

    cleaned_loc = clean_location_string(raw_loc)
    cat = deal.get("category") or category or "Experience"

    # Validate Price
    raw_price = deal.get("price")
    try:
        if raw_price is None or str(raw_price).strip() in ["", "None", "null", "N/A", "Price unavailable"]:
            price = 0.0
        else:
            price = float(str(raw_price).replace(",", "").replace("₹", "").strip())
            if price < 0:
                price = 0.0
    except Exception:
        price = 0.0

    # Extract & Validate Discount Percent
    disc = extract_discount_percent(deal)

    formatted_price = f"₹{int(price):,}" if price > 0 else "Price unavailable"
    savings = int(price * (disc / 100.0)) if price > 0 and disc > 0 else 0

    # Validate Clean Title (with Description Recovery for Placeholders)
    raw_title = deal.get("clean_title") or deal.get("title") or ""
    clean_title = clean_offer_title(raw_title, cat)

    if is_placeholder_title(clean_title) or clean_title in FALLBACK_TITLES or is_corrupted_title(clean_title):
        recovered = recover_title_from_deal(deal)
        if recovered and not is_placeholder_title(recovered) and not is_corrupted_title(recovered):
            clean_title = recovered

    # Validate Brand Name
    brand = (deal.get("brand") or "").strip()
    if not brand or is_corrupted_title(brand):
        brand = "Zookout Merchant"

    return {
        "id": str(deal.get("id", "UNKNOWN")),
        "brand": brand,
        "title": deal.get("title", "Special Offer"),
        "clean_title": clean_title,
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
        return any(k in cat or k in text_content for k in ["restaurant", "dining", "food", "buffet", "bistro", "barbeque", "eatery"])
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
    6. Offer quality & Real Catalog Title Priority
    """
    req_category = intent.get("category")
    max_price = intent.get("max_price")
    sort_by_discount = intent.get("sort_by_discount", False)
    user_query = (intent.get("query") or "").lower().strip()

    is_buffet_requested = (
        any(w in user_query for w in ["buffet", "only buffet", "buffet only", "i want buffet", "show buffet"])
        or intent.get("dining_type") == "buffet"
        or intent.get("meal_type") == "buffet"
        or intent.get("occasion") == "Buffet"
    )

    try:
        price = float(str(deal.get("price", "0")).replace(",", ""))
    except Exception:
        price = 0.0

    disc = extract_discount_percent(deal)
    rating = float(deal.get("rating", 4.5))
    confidence = float(deal.get("confidence", 0.9))

    clean_t = clean_offer_title(deal.get("title", ""), req_category or "")
    desc = deal.get("description", "")
    tags = [str(t).lower() for t in deal.get("tags", [])]
    keywords = [str(k).lower() for k in deal.get("keywords", [])]
    full_text = f"{clean_t} {deal.get('title','')} {desc} {' '.join(tags)} {' '.join(keywords)}".lower()

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

    # 6. Offer Quality & Real Catalog Title Priority Bonus
    fallback_titles = [
        "Special Buffet Offer", "Special Dining Offer", "Premium Spa Experience",
        "Beauty & Grooming Offer", "Hotel Experience", "Cafe Special",
        "Entertainment Offer", "Special Catalog Offer"
    ]
    is_real_title = clean_t not in fallback_titles and len(clean_t) >= 5

    if is_real_title:
        quality_score = 25.0  # Priority bonus for genuine readable catalog offer titles!
    elif disc > 0:
        quality_score = 0.0
    else:
        quality_score = -10.0

    # Normal dinner search does NOT prioritize buffet offers over regular dining
    if not is_buffet_requested and "buffet" in full_text:
        quality_score -= 2.0

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

    # ONLY add buffet reasoning if user explicitly requested buffet AND the deal contains buffet
    is_buffet = "buffet" in full_text
    if is_buffet_requested and is_buffet:
        reasons.append("Includes a buffet offer.")

    if disc > 0:
        reasons.append(f"{disc}% discount.")

    normalized = normalize_deal(deal, req_category)
    normalized["discount_percent"] = disc
    normalized["score"] = round(total_score, 2)
    normalized["reasons"] = reasons
    return normalized


def search_deals(intent: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    AI Deal Concierge Search Engine:
    - Search Hierarchy: Exact Area -> Nearby Areas -> City -> Entire Catalog
    - Mandatory Buffet Filter: Filters candidates strictly for buffet deals when requested BEFORE ranking
    - Explicit Fallback Notices: Attaches fallback_notice to intent when expanding search or when no buffet deals exist
    - Highest Discount Sorting: Sorts matching dataset by numeric discount_percent descending
    """
    deals = load_deals()
    if not deals:
        logger.info("[SEARCH_DEALS] Catalog empty, returning []")
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

    # Check for Buffet filtering requirement
    is_buffet_requested = (
        any(w in user_query for w in ["buffet", "only buffet", "buffet only", "i want buffet", "show buffet"])
        or intent.get("dining_type") == "buffet"
        or intent.get("meal_type") == "buffet"
        or intent.get("occasion") == "Buffet"
    )

    target_area = req_area or (req_location if req_location not in ["mumbai", "bangalore", "bengaluru", ""] else None)
    target_city = req_city or (req_location if req_location in ["mumbai", "bangalore", "bengaluru"] else None)

    logger.info(f"[SEARCH_DEALS ENTRY] user_query='{user_query}' | is_buffet_requested={is_buffet_requested} | target_area='{target_area}' | target_city='{target_city}' | max_price={max_price}")

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

    logger.info(f"[CANDIDATE FILTER] Count after Category & Price filter: {len(candidate_deals)}")

    # 2. MANDATORY BUFFET FILTER (EXECUTED BEFORE RANKING)
    if is_buffet_requested:
        buffet_deals = []
        for deal in candidate_deals:
            clean_t = clean_offer_title(deal.get("title", ""), deal.get("category", "buffet"))
            full_txt = f"{clean_t} {deal.get('title','')} {deal.get('description','')} {deal.get('category','')} {' '.join(deal.get('tags',[]))} {' '.join(deal.get('keywords',[]))}".lower()
            if "buffet" in full_txt:
                buffet_deals.append(deal)

        logger.info(f"[BUFFET FILTER LOG] Candidates before buffet filter: {len(candidate_deals)} | Candidates after buffet filter: {len(buffet_deals)}")

        if buffet_deals:
            candidate_deals = buffet_deals
            intent["fallback_notice"] = None
        else:
            loc_disp = target_area.title() if target_area else "your location"
            logger.info(f"[BUFFET FILTER LOG] 0 buffet deals found for {loc_disp}. Returning [] with fallback notice.")
            intent["fallback_notice"] = f"I couldn't find buffet deals in {loc_disp} or nearby locations.\n\nWould you like to see all restaurant deals instead?"
            return []

    # 3. Location Filtering Pipeline: Exact Area -> Nearby Areas -> City -> Catalog
    matched_scored_deals = []

    if target_area:
        # Step 1: Exact Area Match across location, title, desc, tags, keywords
        exact_deals = []
        for deal in candidate_deals:
            deal_area = (extract_deal_area(deal) or "").lower()
            full_txt = f"{deal.get('location','')} {deal.get('title','')} {deal.get('description','')} {' '.join(deal.get('tags',[]))} {' '.join(deal.get('keywords',[]))}".lower()
            if target_area == deal_area or target_area in full_txt:
                exact_deals.append(deal)

        logger.info(f"[LOCATION PIPELINE] Exact area ('{target_area}') matches count: {len(exact_deals)}")

        if exact_deals:
            intent["fallback_notice"] = None
            for d in exact_deals:
                matched_scored_deals.append(compute_weighted_score(d, intent, "exact"))
        else:
            # Step 2: Nearby Areas Fallback
            nearby_list = get_nearby_locations(target_area)
            nearby_deals = []
            for deal in candidate_deals:
                deal_area = (extract_deal_area(deal) or "").lower()
                full_txt = f"{deal.get('location','')} {deal.get('title','')} {deal.get('description','')} {' '.join(deal.get('tags',[]))} {' '.join(deal.get('keywords',[]))}".lower()
                if any(nb.lower() in deal_area or nb.lower() in full_txt for nb in nearby_list):
                    nearby_deals.append(deal)

            logger.info(f"[LOCATION PIPELINE] Nearby areas ({nearby_list}) matches count: {len(nearby_deals)}")

            if nearby_deals:
                intent["fallback_notice"] = f"No deals found in {target_area.title()}. Showing nearby locations."
                for d in nearby_deals:
                    matched_scored_deals.append(compute_weighted_score(d, intent, "nearby"))
            elif is_buffet_requested:
                # If buffet mode is active and 0 buffet deals exist in exact or nearby area, return empty list with fallback notice!
                logger.info(f"[BUFFET LOCATION FALLBACK] 0 buffet deals in {target_area} or nearby areas. Returning []")
                intent["fallback_notice"] = f"I couldn't find buffet deals in {target_area.title()} or nearby locations.\n\nWould you like to see all restaurant deals instead?"
                return []
            else:
                # Step 3: City Fallback for general dining
                city_deals = candidate_deals
                if city_deals:
                    intent["fallback_notice"] = f"No deals found in {target_area.title()}. Showing nearby locations."
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

    # 4. Weighted Ranking & Highest Discount Sorting
    if sort_by_discount:
        for d in matched_scored_deals:
            d["discount_percent"] = extract_discount_percent(d)

        matched_scored_deals.sort(
            key=lambda x: (x.get("discount_percent", 0), x.get("score", 0)),
            reverse=True
        )

        if not intent.get("fallback_notice"):
            max_disc = max((x.get("discount_percent", 0) for x in matched_scored_deals), default=0)
            if max_disc == 0:
                intent["fallback_notice"] = "No higher-discount deals are available for your current filters."
    else:
        matched_scored_deals.sort(
            key=lambda x: (x["score"], x["confidence"]),
            reverse=True
        )

    # Log deal metadata for returned deals
    if is_buffet_requested:
        logger.info(f"[BUFFET SEARCH EXIT] Returning {len(matched_scored_deals)} scored buffet deals.")
        for idx, d in enumerate(matched_scored_deals[:4]):
            logger.info(f"[BUFFET METADATA DEAL {idx+1}] ID: {d.get('id')} | Brand: '{d.get('brand')}' | Title: '{d.get('clean_title')}' | Tags: {d.get('tags')} | Keywords: {d.get('keywords')}")

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