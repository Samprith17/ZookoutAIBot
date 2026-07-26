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

# Milestone 8 & 9 & 10 & 11 & 12 Occasion & Mood Mapping
OCCASION_MAP = {
    "Romantic Evening": (["romantic", "candle light", "date night", "romantic dinner", "romantic evening", "anniversary", "date"], "restaurant"),
    "Birthday Celebration": (["birthday", "bday", "b-day", "birthday celebration", "celebrate promotion", "celebrate success", "celebrate"], "restaurant"),
    "Relaxation & Wellness": (["relax", "relax today", "relaxing day", "need a massage", "feeling stressed", "stress", "wellness"], "spa"),
    "Coffee & Cafe Meetup": (["coffee meeting", "coffee with friends", "cafe meetup"], "cafe"),
    "Business Lunch & Meeting": (["business meeting", "business lunch", "corporate meeting", "formal meeting"], "restaurant"),
    "Family Outing & Dinner": (["family dinner", "family lunch", "family outing", "kids outing"], "restaurant"),
    "Friends Meetup": (["friends meetup", "weekend with friends", "weekend outing", "friends", "hangout", "get together"], "cafe")
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
    "any suggestions?", "any suggestions", "best deals today", "suggest a spa",
    "personalized recommendations", "recommended for me"
]

COMPARISON_KEYWORDS = [
    "compare", "comparison", "which is better", "which restaurant is better",
    "which spa is better", "which cafe is better", "best restaurant under",
    "best spa under", "best deal under", "compare deals", "compare these"
]

PAGINATION_WORDS = [
    "show more", "next", "previous", "any other options", "any other options?", "more deals", "other options"
]

PLANNER_TRIGGERS = [
    "plan", "create", "organize", "build", "itinerary", "schedule", "planner"
]

SAVINGS_TRIGGERS = ["my savings", "savings", "show savings", "my savings profile", "/savings"]
OPPORTUNITY_TRIGGERS = ["show opportunities", "opportunities", "deals for me", "savings opportunities", "new opportunities", "/opportunities"]
SAVED_DEALS_TRIGGERS = ["saved deals", "my saved deals"]
WHY_THIS_TRIGGERS = [
    "why did i get this?", "why did i get this", "why this deal?", "why this deal",
    "why this recommendation?", "why this recommendation", "why did i get this deal", "why did i get this deal?"
]

RECENT_WORDS = ["recent", "recently viewed", "history", "/history"]
PROFILE_WORDS = ["my preferences", "my profile", "show my interests", "/profile"]
RESET_PROFILE_WORDS = ["reset profile", "reset preferences", "forget my preferences", "clear history", "/reset_profile"]
FAVOURITES_WORDS = ["my favourites", "favorites", "favourites", "/favourites"]
CLEAR_FAVOURITES_WORDS = ["clear favourites", "delete favourites", "/clear_favourites"]

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
    AI Customer Savings Agent & Multi-Constraint Classifier (Milestone 12.1 Strict Priority Router).
    Guarantees 'My Savings', 'Show Opportunities', 'Why did I get this?', and 'Recommend something' route to 4 distinct handlers.
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
        "meal_type": None,
        "special_keywords": [],
        "faq_answer": None,
        "query": message,
    }

    # 1. System Commands & Savings Agent Commands (HIGHEST PRIORITY ROUTING)
    if text in ["/start", "start"]:
        intent["type"] = "greeting"
        return intent

    if any(st in text for st in SAVINGS_TRIGGERS):
        intent["type"] = "savings"
        return intent

    if any(ot in text for ot in OPPORTUNITY_TRIGGERS):
        intent["type"] = "opportunities"
        return intent

    if any(wt in text for wt in WHY_THIS_TRIGGERS):
        intent["type"] = "why_this"
        return intent

    if text in RECENT_WORDS:
        intent["type"] = "recent"
        return intent

    if text in FAVOURITES_WORDS or text in SAVED_DEALS_TRIGGERS:
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

    # Constraint Extraction
    if "today" in text:
        intent["date"] = "today"
    elif "tomorrow" in text:
        intent["date"] = "tomorrow"
    elif "saturday" in text:
        intent["date"] = "saturday"
    elif "sunday" in text:
        intent["date"] = "sunday"
    elif "weekend" in text:
        intent["date"] = "this weekend"

    if "morning" in text:
        intent["time_filter"] = "morning"
    elif "afternoon" in text:
        intent["time_filter"] = "afternoon"
    elif "evening" in text:
        intent["time_filter"] = "evening"
    elif "tonight" in text:
        intent["time_filter"] = "tonight"
    elif "late night" in text:
        intent["time_filter"] = "late night"

    if "lunch" in text:
        intent["meal_type"] = "lunch"
    elif "dinner" in text:
        intent["meal_type"] = "dinner"
    elif "breakfast" in text:
        intent["meal_type"] = "breakfast"
    elif "buffet" in text:
        intent["meal_type"] = "buffet"

    if "solo" in text:
        intent["group_size"] = "solo"
    elif "couple" in text or "for 2" in text or "for two" in text:
        intent["group_size"] = "couple"
    elif "family" in text or "group" in text:
        intent["group_size"] = "family"

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

    for occ_title, (keywords, default_cat) in OCCASION_MAP.items():
        if any(re.search(r"\b" + re.escape(kw) + r"\b", text) for kw in keywords):
            intent["occasion"] = occ_title
            if not intent["category"]:
                intent["category"] = default_cat
            break

    # 5. AI EXPERIENCE PLANNER INTENT CHECK
    is_planner_trigger = any(re.search(r"\b" + re.escape(pt) + r"\b", text) for pt in PLANNER_TRIGGERS) or any(text.startswith(p) for p in ["plan ", "create ", "organize ", "build "])
    if is_planner_trigger:
        intent["type"] = "planner"
        return intent

    # 6. Occasion Intent Check
    if intent["occasion"]:
        if not any(ck in text for ck in COMPARISON_KEYWORDS):
            intent["type"] = "occasion"
            return intent

    # 7. Comparison Intent Check
    if any(ck in text for ck in COMPARISON_KEYWORDS) or ("compare" in text and ("restaurant" in text or "restaurants" in text or "spa" in text or "spas" in text or "cafe" in text or "cafes" in text or "hotel" in text or "hotels" in text or "deal" in text or "deals" in text)):
        intent["type"] = "compare"
        return intent

    # 8. Pagination Intent
    if any(pw in text for pw in PAGINATION_WORDS):
        intent["type"] = "pagination"
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
    has_date_time = intent["date"] is not None or intent["time_filter"] is not None or intent["meal_type"] is not None

    if intent["category"] or intent["location"] or budget_found or intent["occasion"] or intent["preferences"] or is_modifier or has_date_time:
        intent["type"] = "search"
        return intent

    if any(re.search(r"\b" + re.escape(word) + r"\b", text) for word in OUT_OF_SCOPE_KEYWORDS):
        intent["type"] = "out_of_scope"
        return intent

    # 11. Fallback Intent
    intent["type"] = "fallback"
    logger.info(f"[NLU Extracted Intent]: {intent}")
    return intent