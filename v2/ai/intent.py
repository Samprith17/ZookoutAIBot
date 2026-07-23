import re
import logging
from typing import Dict, List, Any

logger = logging.getLogger(__name__)

# Categories and their related keywords
CATEGORY_KEYWORDS = {
    "restaurant": ["restaurant", "restaurants", "food", "dining", "dinner", "lunch", "breakfast", "buffet", "biryani", "pizza", "thali"],
    "cafe": ["cafe", "coffee", "tea", "bakery", "bistro", "snacks"],
    "spa": ["spa", "massage", "relax", "wellness", "body massage", "therapy"],
    "salon": ["salon", "haircut", "hair", "beauty", "parlor", "facial", "manicure", "pedicure", "grooming"],
    "beauty": ["beauty", "salon", "facial", "makeup", "parlor"],
    "hotel": ["hotel", "stay", "room", "accommodation"],
    "resort": ["resort", "staycation", "villa", "getaway"],
    "pub": ["pub", "bar", "brewery", "beer", "cocktail", "liquor", "drink", "club", "nightlife"],
    "bar": ["bar", "pub", "brewery", "beer", "cocktail", "liquor", "drink", "club", "nightlife"],
    "brewery": ["brewery", "beer", "pub", "bar"],
    "adventure": ["adventure", "outdoor", "trek", "camping", "rafting", "activity"],
    "gaming": ["gaming", "bowling", "arcade", "game", "vr", "play"],
    "movie": ["movie", "cinema", "film", "multiplex", "ticket"],
    "event": ["event", "concert", "show", "pass", "exhibition"],
    "water park": ["water park", "waterpark", "water", "slides", "pool", "amusement"],
    "fitness": ["fitness", "gym", "workout", "crossfit", "yoga"],
    "kids": ["kids", "child", "children"],
    "family": ["family", "outing"]
}

# Occasions
OCCASIONS = {
    "romantic": ["romantic", "candle light", "date night", "romantic dinner"],
    "birthday": ["birthday", "bday", "b-day", "birthday celebration"],
    "anniversary": ["anniversary"],
    "family": ["family", "family dinner", "family lunch"],
    "friends": ["friends", "hangout", "get together"],
    "business meeting": ["business", "corporate", "meeting", "formal"],
    "date night": ["date night", "date"],
    "solo": ["solo", "alone"],
    "couple": ["couple", "couples", "pair"],
    "kids": ["kids", "children", "child"]
}

# Preferences
PREFERENCES = {
    "rooftop": ["rooftop", "roof top", "sky lounge", "terrace"],
    "buffet": ["buffet", "all you can eat"],
    "outdoor": ["outdoor", "open air", "patio", "garden"],
    "indoor": ["indoor", "ac", "air conditioned"],
    "pet friendly": ["pet friendly", "pets allowed", "dog friendly", "cat friendly"],
    "live music": ["live music", "band", "dj", "live performance"],
    "poolside": ["poolside", "pool side", "pool"],
    "luxury": ["luxury", "5 star", "premium"],
    "fine dining": ["fine dining", "gourmet"],
    "budget friendly": ["budget friendly", "pocket friendly", "cheap"],
    "vegetarian": ["veg", "vegetarian", "pure veg"],
    "vegan": ["vegan"],
    "cocktails": ["cocktail", "cocktails", "drinks", "bar"],
    "coffee": ["coffee", "brew", "cappuccino", "espresso"],
    "desserts": ["dessert", "desserts", "cake", "ice cream"]
}

# Time Filters & Temporal Expressions
TIME_FILTERS = {
    "tonight": ["tonight", "this evening"],
    "today": ["today"],
    "tomorrow": ["tomorrow"],
    "weekend": ["weekend", "saturday", "sunday"],
    "lunch": ["lunch", "afternoon meal"],
    "dinner": ["dinner", "night meal"],
    "breakfast": ["breakfast", "morning meal"],
    "evening": ["evening"],
    "morning": ["morning"],
    "afternoon": ["afternoon"],
    "late night": ["late night"]
}

# Supported Locations
LOCATIONS = [
    "andheri", "bandra", "powai", "juhu", "thane", "borivali", "mumbai", "dadar", "worli", "lower parel", "malad", "vashi"
]

GREETINGS = ["hi", "hello", "hey", "good morning", "good afternoon", "good evening"]
HELP_WORDS = ["help", "support", "what can you do", "how to use"]
THANKS = ["thanks", "thank you", "thx", "cheers"]
BYE = ["bye", "goodbye", "see you"]

FAQ_QUESTIONS = {
    "what is zookout": "Zookout is India's premier local experiences platform, offering top deals for dining, spas, salons, entertainment, and getaways!",
    "how to book": "You can discover deals on Zookout, select your preferred voucher, and complete the booking directly online or through our app.",
    "how do vouchers work": "After purchasing a voucher on Zookout, show your voucher code or QR code at the merchant venue upon arrival.",
    "cancellation": "Cancellation policies depend on the specific deal terms. Please check the deal voucher details before booking.",
    "payment methods": "We accept UPI, Credit/Debit cards, Net Banking, and major mobile wallets."
}

OUT_OF_SCOPE_KEYWORDS = [
    "python", "coding", "programming", "politics", "medicine", "doctor", "homework", "weather", "sports", "cricket", "football"
]


def detect_intent(message: str) -> Dict[str, Any]:
    """
    Advanced Multi-Constraint Natural Language Intent Parser.
    Extracts category, city, area, location, budget, occasion, preferences, group size, time filter, and special keywords.
    """
    text = (message or "").lower().strip()

    intent = {
        "type": "search",
        "category": None,
        "city": None,
        "area": None,
        "location": None,
        "min_price": None,
        "max_price": None,
        "occasion": None,
        "preferences": [],
        "group_size": None,
        "date": None,
        "time": None,
        "day": None,
        "time_filter": None,
        "special_keywords": [],
        "faq_answer": None,
        "query": message,
    }

    if text in GREETINGS:
        intent["type"] = "greeting"
        return intent

    if text in HELP_WORDS:
        intent["type"] = "help"
        return intent

    if text in THANKS:
        intent["type"] = "thanks"
        return intent

    if text in BYE:
        intent["type"] = "bye"
        return intent

    if any(re.search(r"\b" + re.escape(word) + r"\b", text) for word in OUT_OF_SCOPE_KEYWORDS):
        intent["type"] = "out_of_scope"
        return intent

    for faq_key, answer in FAQ_QUESTIONS.items():
        if faq_key in text:
            intent["type"] = "faq"
            intent["faq_answer"] = answer
            return intent

    # 1. Category Extraction (Prioritizing multi-word keywords)
    sorted_categories = sorted(CATEGORY_KEYWORDS.items(), key=lambda x: max(len(k) for k in x[1]), reverse=True)
    for category, keywords in sorted_categories:
        if any(re.search(r"\b" + re.escape(keyword) + r"\b", text) for keyword in keywords):
            intent["category"] = category
            break

    # 2. Location & Area Extraction
    for loc in LOCATIONS:
        if loc in text:
            intent["location"] = loc.title()
            if loc == "mumbai":
                intent["city"] = "Mumbai"
            else:
                intent["area"] = loc.title()
                intent["city"] = "Mumbai"
            break

    # 3. Occasion Extraction
    for occasion, keywords in OCCASIONS.items():
        if any(re.search(r"\b" + re.escape(kw) + r"\b", text) for kw in keywords):
            intent["occasion"] = occasion
            break

    # 4. Preference Extraction
    extracted_prefs = []
    for pref, keywords in PREFERENCES.items():
        if any(re.search(r"\b" + re.escape(kw) + r"\b", text) for kw in keywords):
            extracted_prefs.append(pref)
    intent["preferences"] = extracted_prefs

    # 5. Time Filter & Day Extraction
    extracted_times = []
    for t_filter, keywords in TIME_FILTERS.items():
        if any(re.search(r"\b" + re.escape(kw) + r"\b", text) for kw in keywords):
            extracted_times.append(t_filter)
    if extracted_times:
        intent["time_filter"] = extracted_times[0]
        if "tonight" in extracted_times or "today" in extracted_times:
            intent["day"] = "today"
        elif "tomorrow" in extracted_times:
            intent["day"] = "tomorrow"

    # 6. Group Size Extraction (e.g. "for 4", "for 2", or "couple")
    gs_match = re.search(r"(?:for|group of)\s*(\d+)", text)
    if gs_match:
        intent["group_size"] = int(gs_match.group(1))
    elif "couple" in text:
        intent["group_size"] = 2
    elif "solo" in text:
        intent["group_size"] = 1

    # 7. Budget Range & Max Price Extraction
    range_match = re.search(r"(?:between|from)?\s*₹?\s*(\d+)\s*(?:and|to|-)\s*₹?\s*(\d+)", text)
    if range_match:
        intent["min_price"] = int(range_match.group(1))
        intent["max_price"] = int(range_match.group(2))
    else:
        max_match = re.search(r"(?:under|below|less than)\s*₹?\s*(\d+)", text)
        if max_match:
            intent["max_price"] = int(max_match.group(1))

    # Internal Debug Logging of Extracted Intent
    logger.info(f"[NLU Extracted Intent]: {intent}")
    print("[NLU Debug Intent]:", intent)

    return intent