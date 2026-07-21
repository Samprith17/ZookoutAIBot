import json
import re
from pathlib import Path
from typing import Dict, List, Optional

from rapidfuzz import fuzz

BASE_DIR = Path(__file__).resolve().parent
DATA_PATH = BASE_DIR / "data" / "clean_deals.json"

CATEGORY_INTENTS: Dict[str, str] = {
    "fine dining": "Restaurant",
    "restaurant": "Restaurant",
    "restaurants": "Restaurant",
    "food": "Restaurant",
    "dinner": "Restaurant",
    "lunch": "Restaurant",
    "buffet": "Restaurant",
    "salon": "Salon",
    "haircut": "Salon",
    "hair": "Salon",
    "beauty": "Salon",
    "spa": "Spa",
    "massage": "Spa",
    "wellness": "Spa",
    "therapy": "Spa",
    "coffee": "Cafe",
    "cafe": "Cafe",
    "hotel": "Hotel",
    "stay": "Hotel",
    "resort": "Hotel",
    "waterpark": "Entertainment",
    "theme park": "Entertainment",
    "weekend": "Entertainment",
    "fun": "Entertainment",
}

FIELD_WEIGHTS: Dict[str, int] = {
    "category": 40,
    "brand": 30,
    "title": 25,
    "tags": 20,
    "location": 18,
    "description": 12,
}

PHRASE_PATTERN = re.compile(
    r"\b({})\b".format("|".join(re.escape(term) for term in sorted(CATEGORY_INTENTS, key=len, reverse=True))),
    re.I,
)


def load_deals() -> List[Dict[str, object]]:
    with DATA_PATH.open("r", encoding="utf-8") as file_handle:
        return json.load(file_handle)


deals = load_deals()


class DealSearchEngine:
    def __init__(self, deals_data: List[Dict[str, object]]):
        self.deals = deals_data

    @staticmethod
    def normalize_text(value: str) -> str:
        return (value or "").strip().lower()

    def detect_intent(self, query: str) -> Optional[str]:
        normalized = self.normalize_text(query)
        match = PHRASE_PATTERN.search(normalized)
        if match:
            return CATEGORY_INTENTS.get(match.group(1).lower())
        return None

    @staticmethod
    def field_score(query: str, text: str, weight: int) -> float:
        if not text:
            return 0.0

        normalized_text = (text or "").strip().lower()
        normalized_query = query.strip().lower()

        if normalized_query == normalized_text:
            return float(weight)

        if normalized_query in normalized_text:
            return float(weight) * 1.3

        return fuzz.partial_ratio(normalized_query, normalized_text) / 100.0 * float(weight)

    def score_deal(self, query: str, deal: Dict[str, object], intent: Optional[str]) -> float:
        category = self.normalize_text(deal.get("category", ""))
        brand = self.normalize_text(deal.get("brand", ""))
        title = self.normalize_text(deal.get("title", ""))
        description = self.normalize_text(deal.get("description", ""))
        location = self.normalize_text(deal.get("location", ""))
        tags = " ".join(deal.get("tags", [])).lower()

        score = 0.0
        score += self.field_score(query, category, FIELD_WEIGHTS["category"])
        score += self.field_score(query, brand, FIELD_WEIGHTS["brand"])
        score += self.field_score(query, title, FIELD_WEIGHTS["title"])
        score += self.field_score(query, tags, FIELD_WEIGHTS["tags"])
        score += self.field_score(query, location, FIELD_WEIGHTS["location"])
        score += self.field_score(query, description, FIELD_WEIGHTS["description"])

        if intent and intent.lower() == category:
            score += 45.0
        elif intent and intent in tags.split():
            score += 10.0

        return score

    def search(self, query: str, max_results: int = 3) -> List[Dict[str, object]]:
        normalized_query = self.normalize_text(query)
        if not normalized_query:
            return []

        intent = self.detect_intent(normalized_query)
        scored_results: List[tuple[float, Dict[str, object]]] = []

        for deal in self.deals:
            score = self.score_deal(normalized_query, deal, intent)
            if score < 25.0:
                continue
            scored_results.append((score, deal))

        scored_results.sort(key=lambda item: item[0], reverse=True)
        return [deal for _, deal in scored_results[:max_results]]


engine = DealSearchEngine(deals)


def search_deals(query: str, max_results: int = 3) -> List[Dict[str, object]]:
    return engine.search(query, max_results)
