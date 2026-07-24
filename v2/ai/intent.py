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
    "andheri", "bandra", "powai", "juhu", "thane", "borivali", "mumbai", "dadar", "worli", "lower parel", "malad", "vashi"
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
    Intelligent Intent Classifier (Milestone 6.3 Prioritized Architecture).
    Priority: 1. Commands -> 2. Greetings -> 3. Help -> 4. General Questions -> 5. Day Planner -> 6. Recommendations -> 7. Search -> 8. Fallback
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

    # 1. Commands (Highest Priority)
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

    # 5. Day Planner Intent (Flexible Pattern & Typo Tolerance)
    planner_pattern = r"\b(?:plan|lan|pln|schedule|itinerary)?\s*(?:my\s*)?(?:saturday|sunday|weekend|date|day|family|outing)\b"
    if re.search(planner_pattern, text) or any(pk in text for pk in PLANNER_KEYWORDS) or "planner" in text or "itinerary" in text:
        intent["type"] = "planner"
        max_match = re.search(r"(?:under|below|less than|budget of)\s*₹?\s*(\d+)", text)
        if max_match:
            intent["max_price"] = int(max_match.group(1))
        return intent

    # 6. Recommendation Intent
    if any(rk in text for rk in PERSONALIZED_WORDS):
        intent["type"] = "personalized"
        return intent

    # 7. Search Intent Extraction
    category_found = False
    sorted_categories = sorted(CATEGORY_KEYWORDS.items(), key=lambda x: max(len(k) for k in x[1]), reverse=True)
    for category, keywords in sorted_categories:
        if any(re.search(r"\b" + re.escape(keyword) + r"\b", text) for keyword in keywords):
            intent["category"] = category
            category_found = True
            break

    location_found = False
    for loc in LOCATIONS:
        if loc in text:
            intent["location"] = loc.title()
            if loc == "mumbai":
                intent["city"] = "Mumbai"
            else:
                intent["area"] = loc.title()
                intent["city"] = "Mumbai"
            location_found = True
            break

    # Occasions
    for occasion, keywords in OCCASIONS.items():
        if any(re.search(r"\b" + re.escape(kw) + r"\b", text) for kw in keywords):
            intent["occasion"] = occasion
            break

    # Preferences
    extracted_prefs = []
    for pref, keywords in PREFERENCES.items():
        if any(re.search(r"\b" + re.escape(kw) + r"\b", text) for kw in keywords):
            extracted_prefs.append(pref)
    intent["preferences"] = extracted_prefs

    # Budget Range & Max Price
    range_match = re.search(r"(?:between|from)?\s*₹?\s*(\d+)\s*(?:and|to|-)\s*₹?\s*(\d+)", text)
    if range_match:
        intent["min_price"] = int(range_match.group(1))
        intent["max_price"] = int(range_match.group(2))
    else:
        max_match = re.search(r"(?:under|below|less than)\s*₹?\s*(\d+)", text)
        if max_match:
            intent["max_price"] = int(max_match.group(1))

    budget_found = intent["max_price"] is not None or intent["min_price"] is not None

    if category_found or location_found or budget_found or intent["occasion"] or intent["preferences"]:
        intent["type"] = "search"
        return intent

    if any(re.search(r"\b" + re.escape(word) + r"\b", text) for word in OUT_OF_SCOPE_KEYWORDS):
        intent["type"] = "out_of_scope"
        return intent

    # 8. Fallback Intent
    intent["type"] = "fallback"
    logger.info(f"[NLU Extracted Intent]: {intent}")
    return intent