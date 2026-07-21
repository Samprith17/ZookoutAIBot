import re
from typing import Dict

# Categories and their related keywords
CATEGORY_KEYWORDS = {
    "restaurant": [
        "restaurant",
        "restaurants",
        "food",
        "dinner",
        "lunch",
        "breakfast",
        "biryani",
        "pizza",
    ],
    "spa": [
        "spa",
        "massage",
        "relax",
        "wellness",
    ],
    "cafe": [
        "cafe",
        "coffee",
        "tea",
    ],
    "hotel": [
        "hotel",
        "stay",
        "resort",
    ],
    "bar": [
        "bar",
        "pub",
        "cocktail",
        "beer",
    ],
    "salon": [
        "salon",
        "haircut",
        "beauty",
    ],
    "fitness": [
        "fitness",
        "gym",
        "workout",
    ],
}

# Supported locations
LOCATIONS = [
    "andheri",
    "bandra",
    "powai",
    "juhu",
    "thane",
    "borivali",
    "mumbai",
]

# Greetings
GREETINGS = [
    "hi",
    "hello",
    "hey",
    "good morning",
    "good afternoon",
    "good evening",
]

# Help
HELP_WORDS = [
    "help",
    "support",
    "what can you do",
    "how",
]

# Thanks
THANKS = [
    "thanks",
    "thank you",
    "thx",
]

# Goodbye
BYE = [
    "bye",
    "goodbye",
    "see you",
]


def detect_intent(message: str) -> Dict:
    text = (message or "").lower().strip()

    intent = {
        "type": "search",
        "category": None,
        "location": None,
        "max_price": None,
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