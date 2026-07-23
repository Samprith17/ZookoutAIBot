import re
from typing import Dict

# Categories and their related keywords
CATEGORY_KEYWORDS = {
    "restaurant": [
        "restaurant", "restaurants", "food", "dinner", "lunch", "breakfast", "biryani", "pizza", "dining"
    ],
    "spa": [
        "spa", "massage", "relax", "wellness", "body massage"
    ],
    "cafe": [
        "cafe", "coffee", "tea", "bakery"
    ],
    "hotel": [
        "hotel", "stay", "resort", "staycation"
    ],
    "bar": [
        "bar", "pub", "brewery", "cocktail", "beer", "club", "nightlife"
    ],
    "salon": [
        "salon", "haircut", "beauty", "parlor", "facial", "manicure", "pedicure"
    ],
    "fitness": [
        "fitness", "gym", "workout", "yoga"
    ],
    "entertainment": [
        "movie", "event", "water park", "gaming", "bowling", "adventure", "attraction", "kids"
    ]
}

# Supported locations
LOCATIONS = [
    "andheri", "bandra", "powai", "juhu", "thane", "borivali", "mumbai", "dadar", "worli", "lower parel"
]

# Greetings
GREETINGS = [
    "hi", "hello", "hey", "good morning", "good afternoon", "good evening"
]

# Help & FAQs
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

THANKS = [
    "thanks", "thank you", "thx", "cheers"
]

BYE = [
    "bye", "goodbye", "see you"
]

OUT_OF_SCOPE_KEYWORDS = [
    "python", "coding", "programming", "politics", "medicine", "doctor", "homework", "weather", "sports", "cricket", "football"
]


def detect_intent(message: str) -> Dict:
    text = (message or "").lower().strip()

    intent = {
        "type": "search",
        "category": None,
        "location": None,
        "max_price": None,
        "faq_answer": None,
        "query": message,
    }

    # Greeting
    if text in GREETINGS:
        intent["type"] = "greeting"
        return intent

    # Help
    if text in HELP_WORDS:
        intent["type"] = "help"
        return intent

    # Thanks
    if text in THANKS:
        intent["type"] = "thanks"
        return intent

    # Goodbye
    if text in BYE:
        intent["type"] = "bye"
        return intent

    # Check for Out of Scope queries
    if any(re.search(r"\b" + re.escape(word) + r"\b", text) for word in OUT_OF_SCOPE_KEYWORDS):
        intent["type"] = "out_of_scope"
        return intent

    # Check for FAQ questions
    for faq_key, answer in FAQ_QUESTIONS.items():
        if faq_key in text:
            intent["type"] = "faq"
            intent["faq_answer"] = answer
            return intent

    # Detect category
    for category, keywords in CATEGORY_KEYWORDS.items():
        if any(keyword in text for keyword in keywords):
            intent["category"] = category
            break

    # Detect location
    for location in LOCATIONS:
        if location in text:
            intent["location"] = location.title()
            break

    # Detect budget
    match = re.search(
        r"(?:under|below|less than)\s*₹?\s*(\d+)",
        text,
    )

    if match:
        intent["max_price"] = int(match.group(1))

    return intent