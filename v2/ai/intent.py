import re
from typing import Dict

# All supported categories and their keywords
CATEGORY_KEYWORDS = {
    "restaurant": ["restaurant", "restaurants", "food", "dining", "dinner", "lunch", "buffet", "biryani", "pizza", "thali"],
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

LOCATIONS = [
    "andheri", "bandra", "powai", "juhu", "thane", "borivali", "mumbai", "dadar", "worli", "lower parel", "malad", "vashi"
]

GREETINGS = [
    "hi", "hello", "hey", "good morning", "good afternoon", "good evening"
]

HELP_WORDS = [
    "help", "support", "what can you do", "how to use"
]

FAQ_QUESTIONS = {
    "what is zookout": "Zookout is India's premier local experiences platform, offering top deals for dining, spas, salons, entertainment, and getaways!",
    "how to book": "You can discover deals on Zookout, select your preferred voucher, and complete the booking directly online or through our app.",
    "how do vouchers work": "After purchasing a voucher on Zookout, show your voucher code or QR code at the merchant venue upon arrival.",
    "cancellation": "Cancellation policies depend on the specific deal terms. Please check the deal voucher details before booking.",
    "payment methods": "We accept UPI, Credit/Debit cards, Net Banking, and major mobile wallets."
}

THANKS = ["thanks", "thank you", "thx", "cheers"]
BYE = ["bye", "goodbye", "see you"]

OUT_OF_SCOPE_KEYWORDS = [
    "python", "coding", "programming", "politics", "medicine", "doctor", "homework", "weather", "sports", "cricket", "football"
]


def detect_intent(message: str) -> Dict:
    text = (message or "").lower().strip()

    intent = {
        "type": "search",
        "category": None,
        "location": None,
        "min_price": None,
        "max_price": None,
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

    # Category Detection (Multi-word categories first, e.g., 'water park')
    sorted_categories = sorted(CATEGORY_KEYWORDS.items(), key=lambda x: max(len(k) for k in x[1]), reverse=True)
    for category, keywords in sorted_categories:
        if any(re.search(r"\b" + re.escape(keyword) + r"\b", text) for keyword in keywords):
            intent["category"] = category
            break

    # Location Detection
    for location in LOCATIONS:
        if location in text:
            intent["location"] = location.title()
            break

    # Range Budget Detection: "between 500 and 1000" or "500 to 1000"
    range_match = re.search(r"(?:between|from)?\s*₹?\s*(\d+)\s*(?:and|to|-)\s*₹?\s*(\d+)", text)
    if range_match:
        intent["min_price"] = int(range_match.group(1))
        intent["max_price"] = int(range_match.group(2))
    else:
        # Max Budget Detection: "under ₹1000", "below 1500", "less than 2000"
        max_match = re.search(r"(?:under|below|less than)\s*₹?\s*(\d+)", text)
        if max_match:
            intent["max_price"] = int(max_match.group(1))

    return intent