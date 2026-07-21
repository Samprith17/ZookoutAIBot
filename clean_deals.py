"""Clean raw OCR deal data into structured deal records."""
import json
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Dict, List, Tuple

BASE_DIR = Path(__file__).resolve().parent
INPUT_PATH = BASE_DIR / "data" / "deals.json"
OUTPUT_PATH = BASE_DIR / "data" / "clean_deals.json"

CATEGORY_KEYWORDS: Dict[str, Tuple[str, ...]] = {
    "Restaurant": (
        "restaurant",
        "restaurants",
        "food",
        "dinner",
        "lunch",
        "buffet",
        "breakfast",
        "bar",
        "pizza",
        "thali",
        "meal",
        "starter",
        "main course",
    ),
    "Salon": (
        "salon",
        "haircut",
        "hair",
        "blow dry",
        "grooming",
        "beard",
        "root touch",
        "makeover",
        "unisex",
        "stylist",
        "wash",
    ),
    "Spa": (
        "spa",
        "massage",
        "wellness",
        "therapy",
        "treatment",
        "relax",
        "facial",
        "detox",
    ),
    "Cafe": (
        "cafe",
        "coffee",
        "espresso",
        "latte",
        "tea",
        "brunch",
        "pastry",
        "dessert",
    ),
    "Hotel": (
        "hotel",
        "stay",
        "resort",
        "suite",
        "room",
        "booking",
        "check-in",
        "nights",
    ),
    "Entertainment": (
        "entertainment",
        "amusement",
        "club",
        "party",
        "movie",
        "show",
        "night out",
        "fun",
        "weekend",
    ),
    "Clinic": (
        "clinic",
        "consultation",
        "doctor",
        "dental",
        "medical",
        "health",
        "wellness",
        "expert consultation",
    ),
    "Shopping": (
        "shopping",
        "shop",
        "product",
        "store",
        "gift",
        "fashion",
        "accessory",
        "e-commerce",
        "nutrition",
    ),
    "Waterpark": (
        "waterpark",
        "theme park",
        "ride",
        "pool",
        "splash",
        "wave",
    ),
    "Wellness": (
        "wellness",
        "health",
        "fitness",
        "yoga",
        "detox",
        "nutrition",
        "beauty",
        "retreat",
    ),
}

TAG_KEYWORDS = (
    "haircut",
    "wash",
    "blow dry",
    "beard",
    "makeover",
    "buffet",
    "breakfast",
    "dinner",
    "lunch",
    "coffee",
    "dessert",
    "pizza",
    "mocktail",
    "cocktail",
    "beer",
    "wine",
    "massage",
    "spa",
    "wellness",
    "treatment",
    "ticket",
    "restaurant",
    "cafe",
    "hotel",
    "consultation",
    "product",
    "nutrition",
    "beauty",
    "premium",
    "waterpark",
    "thali",
    "starter",
    "main course",
    "couple",
    "group",
    "free",
    "offer",
    "package",
    "deal",
)

NOISE_PATTERNS = (
    r"buy this voucher",
    r"visit( the)?( outlet)?",
    r"show voucher",
    r"pay( ₹)?[\d,]+",
    r"enjoy",
    r"now @",
    r"worth ₹?[\d,]+",
    r"offline",
    r"online",
    r"at the (outlet|restaurant|salon|spa|bar|cafe|hotel)",
    r"at (restaurant|salon|spa|bar|cafe|hotel|outlet)",
    r"buy 1 get 1 free",
    r"flat \d{1,3}% off",
    r"voucher",
    r"package",
    r"offer",
    r"deal",
    r"special",
    r"now",
    r"@₹",
    r"@ \\₹",
)

CITY_NAMES = (
    "Mumbai",
    "Delhi",
    "Bengaluru",
    "Bangalore",
    "Chennai",
    "Kolkata",
    "Pune",
    "Goa",
    "Hyderabad",
    "Noida",
    "Gurgaon",
    "Lucknow",
)


@dataclass
class DealRecord:
    id: int
    brand: str = ""
    category: str = ""
    title: str = ""
    description: str = ""
    price: int = 0
    original_price: int = 0
    discount: str = ""
    location: str = ""
    website: str = ""
    tags: List[str] = field(default_factory=list)


class CleanDealsParser:
    def __init__(self, input_path: Path = INPUT_PATH, output_path: Path = OUTPUT_PATH):
        self.input_path = input_path
        self.output_path = output_path

    def load_deals(self) -> List[Dict[str, str]]:
        with self.input_path.open("r", encoding="utf-8") as source_file:
            return json.load(source_file)

    def save_deals(self, deals: List[DealRecord]) -> None:
        with self.output_path.open("w", encoding="utf-8") as target_file:
            json.dump([asdict(deal) for deal in deals], target_file, indent=4, ensure_ascii=False)

    def normalize_text(self, text: str) -> str:
        text = text.replace("\u2014", "-")
        text = text.replace("\u2013", "-")
        text = text.replace("\u2018", "'")
        text = text.replace("\u2019", "'")
        text = text.replace("\u201c", '"')
        text = text.replace("\u201d", '"')
        text = text.replace("\u2192", " ")
        text = text.replace("@", " @ ")
        text = text.replace("+", " + ")
        text = text.replace("/", " / ")
        text = text.replace("\n", " ")
        text = re.sub(r"[₹â‚¹]+", "₹", text)
        text = re.sub(r"[^A-Za-z0-9₹%.,'\-+()&/\s]", " ", text)
        text = re.sub(r"(?<=[A-Za-z])\d+(?=[A-Za-z])", "", text)
        text = re.sub(r"\s+", " ", text).strip()
        return text

    def clean_noise(self, text: str) -> str:
        cleaned = text
        for pattern in NOISE_PATTERNS:
            cleaned = re.sub(pattern, "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"\s+", " ", cleaned).strip(" -.,@")
        return cleaned

    def parse_brand(self, url: str) -> str:
        match = re.search(r"/brand/([^/]+)", url)
        if match:
            slug = match.group(1)
            parts = [part for part in slug.split("-") if not re.fullmatch(r"[0-9a-f]{8,}", part)]
            brand = " ".join(parts)
            brand = re.sub(r"\b(brand|hotel|restaurant|salon|spa|cafe|resort|outlet|club|bar)\b", "", brand, flags=re.IGNORECASE)
            brand = re.sub(r"\s+", " ", brand).strip()
            return brand.title()

        return ""

    def detect_category(self, text: str, brand: str) -> str:
        text_lower = text.lower()
        scores = {category: 0 for category in CATEGORY_KEYWORDS}
        for category, keywords in CATEGORY_KEYWORDS.items():
            for keyword in keywords:
                if keyword in text_lower:
                    scores[category] += 1

        if brand.lower().endswith("spa"):
            scores["Spa"] += 1
        if brand.lower().endswith("salon"):
            scores["Salon"] += 1

        best_category = max(scores, key=scores.get)
        return best_category if scores[best_category] > 0 else "Restaurant"

    def parse_location(self, url: str, text: str) -> str:
        match = re.search(r"https?://[^/]+/([^/]+)/", url)
        if match:
            city = match.group(1).strip().title()
            if city and city.lower() not in {"brand", "deals"}:
                return city
        for city in CITY_NAMES:
            if re.search(rf"\b{re.escape(city)}\b", text, re.IGNORECASE):
                return city
        return ""

    def parse_price_values(self, text: str) -> Tuple[int, int, str]:
        cleaned = re.sub(r"[^\d₹%,\.\s]", " ", text)
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        price = 0
        original_price = 0
        discount = ""

        worth_match = re.search(r"worth\s*₹\s*([\d,]+)", cleaned, re.IGNORECASE)
        if worth_match:
            original_price = int(worth_match.group(1).replace(",", ""))

        pay_match = re.search(r"pay\s*₹\s*([\d,]+)", cleaned, re.IGNORECASE)
        if pay_match:
            price = int(pay_match.group(1).replace(",", ""))

        now_match = re.search(r"now\s*@\s*₹\s*([\d,]+)", cleaned, re.IGNORECASE)
        if now_match:
            price = int(now_match.group(1).replace(",", ""))

        at_match = re.search(r"@\s*₹\s*([\d,]+)", cleaned)
        if at_match and price == 0:
            price = int(at_match.group(1).replace(",", ""))

        if price == 0:
            numeric_values = [int(value.replace(",", "")) for value in re.findall(r"₹\s*([\d,]+)", cleaned) if value.replace(",", "").isdigit()]
            if numeric_values:
                price = numeric_values[-1]

        discount_match = re.search(r"(\d{1,3})\s*%\s*(off)?", cleaned, re.IGNORECASE)
        if discount_match:
            discount = f"{discount_match.group(1)}%"

        if discount == "" and original_price > 0 and price > 0 and original_price > price:
            discount = f"{round((original_price - price) * 100 / original_price)}%"

        if price == 0 and original_price > 0:
            price = original_price

        return price, original_price, discount

    def extract_title(self, text: str, brand: str, category: str) -> str:
        title = re.split(
            r"\b(?:worth|now\s*@|pay|@|show voucher|enjoy|flat \d+% off|buy 1 get 1 free|buy 1 breakfast|buy 1 dinner|buy 1 buffet|get 1 free|package|special|deal)\b",
            text,
            flags=re.IGNORECASE,
        )[0]
        title = title.split("-")[-1]
        title = re.sub(r"\b(restaurant|salon|spa|bar|cafe|hotel|outlet|offline|online)\b", "", title, flags=re.IGNORECASE)
        if brand:
            title = re.sub(re.escape(brand), "", title, flags=re.IGNORECASE)
        title = re.sub(r"\b\d+\b", "", title)
        title = self.clean_noise(title)
        title = re.sub(r"\s+", " ", title).strip(" -.,@")
        if not title:
            return "Deal"
        if len(title) > 120:
            title = title[:120].rsplit(" ", 1)[0]
        return title.title()

    def extract_description(self, text: str, title: str, category: str) -> str:
        description = text
        if title:
            description = re.sub(re.escape(title), "", description, flags=re.IGNORECASE)
        enjoy_match = re.search(r"enjoy\s+(.+?)(?:\.|$)", description, re.IGNORECASE)
        if enjoy_match:
            description = enjoy_match.group(1)
        else:
            parts = re.split(r"[\.\!\?@₹]", description)
            for part in parts:
                candidate = part.strip()
                if len(candidate) > 40 and not re.search(r"\b(?:worth|pay|buy|visit|show|voucher|free|online|offline|pay)\b", candidate, re.IGNORECASE):
                    description = candidate
                    break
        description = self.clean_noise(description)
        description = re.sub(r"\s+", " ", description).strip(" -.,@")
        if len(description) > 180:
            description = description[:180].rsplit(" ", 1)[0]
        return description.capitalize() if description else ""

    def extract_tags(self, text: str, title: str, category: str) -> List[str]:
        tags = set()
        source_text = f"{text.lower()} {title.lower()} {category.lower()}"
        for keyword in TAG_KEYWORDS:
            if keyword in source_text:
                tags.add(keyword)
        if category:
            tags.add(category.lower())
        return sorted(tags)[:10]

    def clean_record(self, deal: Dict[str, str], index: int) -> DealRecord:
        raw_text = deal.get("text", "")
        url = deal.get("url", "")
        normalized = self.normalize_text(raw_text)
        brand = self.parse_brand(url)
        category = self.detect_category(normalized, brand)
        title = self.extract_title(normalized, brand, category)
        description = self.extract_description(normalized, title, category)
        price, original_price, discount = self.parse_price_values(normalized)
        location = self.parse_location(url, normalized)
        tags = self.extract_tags(normalized, title, category)

        return DealRecord(
            id=index,
            brand=brand,
            category=category,
            title=title,
            description=description,
            price=price,
            original_price=original_price,
            discount=discount,
            location=location,
            website=url,
            tags=tags,
        )

    def run(self) -> List[DealRecord]:
        deals = self.load_deals()
        clean_deals = [self.clean_record(deal, idx + 1) for idx, deal in enumerate(deals)]
        self.save_deals(clean_deals)
        return clean_deals


def main() -> None:
    parser = CleanDealsParser()
    clean_deals = parser.run()
    print(f"Saved {len(clean_deals)} cleaned deals to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
