import re
import logging
from typing import Dict, List, Any

logger = logging.getLogger(__name__)

# Categories and their related keywords
CATEGORY_KEYWORDS = {
    "restaurant": ["restaurant", "restaurants", "food", "dining", "dinner", "lunch", "breakfast", "buffet", "biryani", "pizza", "thali"],
    "cafe": ["cafe", "cafes", "coffee", "tea", "bakery", "bistro", "snacks"],
    "spa": ["spa", "spas", "massage", "relax", "wellness", "body massage", "therapy"],
    "salon": ["salon", "salons", "haircut", "hair", "beauty", "parlor", "facial", "manicure", "pedicure", "grooming"],
    "beauty": ["beauty", "salon", "facial", "makeup", "parlor"],
    "hotel": ["hotel", "hotels", "stay", "room", "accommodation"],
    "resort": ["resort", "resorts", "staycation", "villa", "getaway"],
    "pub": ["pub", "pubs", "bar", "bars", "brewery", "breweries", "beer", "cocktail", "liquor", "drink", "club", "nightlife"],
    "bar": ["bar", "bars", "pub", "pubs", "brewery", "beer", "cocktail", "liquor", "drink", "club", "nightlife"],
    "brewery": ["brewery", "breweries", "beer", "pub", "bar"],
    "adventure": ["adventure", "outdoor", "trek", "camping", "rafting", "activity"],
    "gaming": ["gaming", "bowling", "arcade", "game", "vr", "play"],
    "movie": ["movie", "movies", "cinema", "film", "multiplex", "ticket"],
    "event": ["event", "events", "concert", "live show", "stage show", "exhibition"],
    "water park": ["water park", "waterpark", "water", "slides", "pool", "amusement"],
    "fitness": ["fitness", "gym", "workout", "crossfit", "yoga"],
    "kids": ["kids", "child", "children"],
    "family": ["family", "outing"]
}

# Milestone 8 Occasion & Mood Mapping: (Keywords, Default Category)
OCCASION_MAP = {
    "Romantic Dinner": (["romantic", "candle light", "date night", "romantic dinner", "anniversary", "date"], "restaurant"),
    "Birthday Celebration": (["birthday", "bday", "b-day", "birthday celebration", "celebrate promotion", "celebrate success", "celebrate"], "restaurant"),
    "Relaxation & Wellness": (["relax", "relax today", "need a massage", "feeling stressed", "stress", "wellness"], "spa"),
    "Coffee & Cafe Meetup": (["coffee meeting", "coffee with friends", "cafe meetup"], "cafe"),
    "Business Lunch & Meeting": (["business meeting", "business lunch", "corporate meeting", "formal meeting"], "restaurant"),
    "Family Outing & Dinner": (["family dinner", "family lunch", "family outing", "kids outing"], "restaurant"),
    "Friends Meetup": (["friends meetup", "friends", "hangout", "get together"], "cafe")
}

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

LOCATIONS = [
    "andheri", "bandra", "powai", "juhu", "thane", "borivali", "mumbai", "dadar", "worli", "lower parel", "malad", "vashi", "airport"
]

GREETINGS = [
    "hi", "hello", "hey", "hi there", "hello bot", "good morning",
    "good afternoon", "good evening", "good night", "how are you", "what's up", "greetings"
]

HELP_WORDS = ["help", "what can you do", "show commands", "guide me", "menu", "/help"]

PERSONALIZED_WORDS = [
    "recommend something", "suggest a deal", "suggest deals", "recommend a restaurant",
    "any recommendations", "any recommendations?", "what should i do today",
    "best deals today", "suggest a spa", "personalized recommendations", "recommended for me"
]

COMPARISON_KEYWORDS = [
    "compare", "comparison", "which is better", "which restaurant is better",
    "which spa is better", "which cafe is better", "best restaurant under",
    "best spa under", "best deal under", "compare deals", "compare these"
]

PAGINATION_WORDS = [
    "show more", "next", "previous", "any other options", "any other options?", "more deals", "other options"
]

RECENT_WORDS = ["recent", "recently viewed", "history", "/history"]
PROFILE_WORDS = ["my preferences", "my profile", "show my interests", "/profile"]
RESET_PROFILE_WORDS = ["reset profile", "forget my preferences", "clear history", "/reset_profile"]
FAVOURITES_WORDS = ["my favourites", "favorites", "saved deals", "favourites", "/favourites"]
CLEAR_FAVOURITES_WORDS = ["clear favourites", "delete favourites", "/clear_favourites"]

PLANNER_KEYWORDS = [
    "plan my saturday", "plan my sunday", "weekend plan", "date night plan",
    "family outing", "plan my weekend", "day planner", "plan my day"
]

FAQ_QUESTIONS = {
    "who are you": "🤖 I am Zookout AI, your intelligent virtual assistant for discovering local deals, dining, spas, salons, and activities across India!",
    "what is zookout": "Zookout is India's local experiences platform offering the best deals for restaurants, cafes, spas, salons, hotels, and events!",
    "how do you work": "I can help you search for deals by category, budget, or location, save your favourites, and give personalized recommendations!",
    "can you help me": "Yes! You can search for restaurants, spas, cafes, or hotels, ask for recommendations, or plan your weekend itinerary!",
    "what is this bot": "🤖 I am Zookout AI, your official assistant for local experiences and discount deals!"
}

OUT_OF_SCOPE_KEYWORDS = [
    "python", "coding", "programming", "politics", "medicine", "doctor", "homework", "weather", "sports", "cricket", "football"
]


def detect_intent(message: str) -> Dict[str, Any]:
    """
    Intelligent Intent Classifier (Milestone 8 Smart Occasion & Mood Integration).
    Priority: 1. Commands -> 2. Greetings -> 3. Help -> 4. General FAQ -> 5. Occasion -> 6. Comparison -> 7. Pagination -> 8. Day Planner -> 9. Recommendations -> 10. Search -> 11. Fallback
    """
    text = (message or "").lower().strip()

    intent = {
        "type": "fallback",
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

    # 1. Commands
    if text in ["/start", "start"]:
        intent["type"] = "greeting"
        return intent

    if text in RECENT_WORDS:
        intent["type"] = "recent"
        return intent

    if text in FAVOURITES_WORDS:
        intent["type"] = "favourites"
        return intent

    if text in CLEAR_FAVOURITES_WORDS:
        intent["type"] = "clear_favourites"
        return intent

    if text in PROFILE_WORDS:
        intent["type"] = "profile"
        return intent

    if text in RESET_PROFILE_WORDS:
        intent["type"] = "reset_profile"
        return intent

    # 2. Greetings Intent
    if any(text == g or text.startswith(g + " ") or text.endswith(" " + g) for g in GREETINGS):
        intent["type"] = "greeting"
        return intent

    # 3. Help Intent
    if any(h in text for h in HELP_WORDS):
        intent["type"] = "help"
        return intent

    # 4. General Questions / FAQ
    for faq_key, answer in FAQ_QUESTIONS.items():
        if faq_key in text:
            intent["type"] = "faq"
            intent["faq_answer"] = answer
            return intent

    # Extract Category, Location, Budget Parameters
    sorted_categories = sorted(CATEGORY_KEYWORDS.items(), key=lambda x: max(len(k) for k in x[1]), reverse=True)
    for category, keywords in sorted_categories:
        if any(re.search(r"\b" + re.escape(keyword) + r"\b", text) for keyword in keywords):
            intent["category"] = category
            break

    for loc in LOCATIONS:
        if loc in text:
            intent["location"] = loc.title()
            if loc == "mumbai":
                intent["city"] = "Mumbai"
            else:
                intent["area"] = loc.title()
                intent["city"] = "Mumbai"
            break

    range_match = re.search(r"(?:between|from)?\s*₹?\s*(\d+)\s*(?:and|to|-)\s*₹?\s*(\d+)", text)
    if range_match:
        intent["min_price"] = int(range_match.group(1))
        intent["max_price"] = int(range_match.group(2))
    else:
        max_match = re.search(r"(?:under|below|less than)\s*₹?\s*(\d+)", text)
        if max_match:
            intent["max_price"] = int(max_match.group(1))

    # 5. Occasion & Mood Intent Extraction (Milestone 8)
    occasion_detected = None
    default_cat_for_occ = None
    for occ_title, (keywords, default_cat) in OCCASION_MAP.items():
        if any(re.search(r"\b" + re.escape(kw) + r"\b", text) for kw in keywords):
            occasion_detected = occ_title
            default_cat_for_occ = default_cat
            break

    if occasion_detected:
        intent["occasion"] = occasion_detected
        if not intent["category"]:
            intent["category"] = default_cat_for_occ
        # Check if query is purely occasion-focused or combined with constraints
        if not any(ck in text for ck in COMPARISON_KEYWORDS) and "plan" not in text:
            intent["type"] = "occasion"
            return intent

    # 6. Comparison Intent Check
    if any(ck in text for ck in COMPARISON_KEYWORDS) or ("compare" in text and ("restaurant" in text or "restaurants" in text or "spa" in text or "spas" in text or "cafe" in text or "cafes" in text or "hotel" in text or "hotels" in text or "deal" in text or "deals" in text)):
        intent["type"] = "compare"
        return intent

    # 7. Pagination Intent
    if any(pw in text for pw in PAGINATION_WORDS):
        intent["type"] = "pagination"
        return intent

    # 8. Day Planner Intent
    planner_pattern = r"\b(?:plan|lan|pln|schedule|itinerary)?\s*(?:my\s*)?(?:saturday|sunday|weekend|date|day|family|outing)\b"
    if re.search(planner_pattern, text) or any(pk in text for pk in PLANNER_KEYWORDS) or "planner" in text or "itinerary" in text:
        intent["type"] = "planner"
        return intent

    # 9. Recommendation Intent
    if any(rk in text for rk in PERSONALIZED_WORDS):
        intent["type"] = "personalized"
        return intent

    # 10. Search Intent
    extracted_prefs = []
    for pref, keywords in PREFERENCES.items():
        if any(re.search(r"\b" + re.escape(kw) + r"\b", text) for kw in keywords):
            extracted_prefs.append(pref)
    intent["preferences"] = extracted_prefs

    budget_found = intent["max_price"] is not None or intent["min_price"] is not None
    is_modifier = any(w in text for w in ["cheaper", "luxury", "premium", "budget", "only", "near", "instead"])

    if intent["category"] or intent["location"] or budget_found or intent["occasion"] or intent["preferences"] or is_modifier:
        intent["type"] = "search"
        return intent

    if any(re.search(r"\b" + re.escape(word) + r"\b", text) for word in OUT_OF_SCOPE_KEYWORDS):
        intent["type"] = "out_of_scope"
        return intent

    # 11. Fallback Intent
    intent["type"] = "fallback"
    logger.info(f"[NLU Extracted Intent]: {intent}")
    return intent