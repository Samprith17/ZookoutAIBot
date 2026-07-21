"""Intent detection for Version 2 of Zookout AI."""
from enum import Enum


class Intent(Enum):
    Greeting = "Greeting"
    Help = "Help"
    SearchDeals = "SearchDeals"
    Favorites = "Favorites"
    Unknown = "Unknown"


INTENT_KEYWORDS = {
    Intent.Greeting: ["hi", "hello", "hey"],
    Intent.Help: ["help", "how to", "what can you do"],
    Intent.SearchDeals: [
        "restaurant",
        "restaurants",
        "food",
        "buffet",
        "cafe",
        "coffee",
        "spa",
        "massage",
        "hotel",
        "stay",
        "salon",
        "beauty",
        "shopping",
        "waterpark",
        "weekend",
    ],
    Intent.Favorites: ["favorite", "favorites", "saved", "bookmarked"],
}


def detect_intent(text: str) -> Intent:
    normalized = (text or "").lower().strip()
    for intent, keywords in INTENT_KEYWORDS.items():
        for keyword in keywords:
            if keyword in normalized:
                return intent
    return Intent.Unknown
