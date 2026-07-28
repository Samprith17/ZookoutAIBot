"""
Production Bug & Quality Verification Test Suite (Bugs 1-5).
Verifies:
1. Factual Buffet Reasoning (only appears on genuine buffet deals).
2. Corrupted Offer Title Cleaning (malformed OCR titles become 'Special Dining Offer').
3. Highest Discount Sorting (numeric descending sorting: 50%, 40%, 25%, 10%, 0%).
4. Data Validation (invalid prices, discounts, and locations are normalized with defaults).
5. Search Context & Location Fallbacks.
"""

import sys
from pathlib import Path

# Add project root to path
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))

from v2.ai.intent import detect_intent
from v2.ai.memory import memory_manager
from v2.search.search_engine import (
    search_deals,
    is_corrupted_title,
    clean_offer_title,
    normalize_deal,
)
from v2.ai.content_creator import content_creator_agent
from v2.telegram.bot import build_concierge_reasons


def test_bug_1_factual_buffet_reasoning():
    print("\n[TEST 1] BUG 1 — Factual Buffet Reasoning")
    # Non-buffet deal mock
    non_buffet_deal = {
        "brand": "Suba Galaxy",
        "title": "A La Carte Dining",
        "clean_title": "A La Carte Dining",
        "description": "Delicious single course dining experience.",
        "category": "Restaurant",
        "tags": ["dining"],
        "keywords": ["suba", "galaxy"],
    }
    intent_buffet = {"occasion": "Buffet", "category": "restaurant"}
    reasons_non_buffet = build_concierge_reasons(non_buffet_deal, intent_buffet)
    assert "Perfect atmosphere for a Buffet" not in reasons_non_buffet, "Invented fake buffet reasoning!"
    assert "Includes a buffet offer" not in reasons_non_buffet, "Appended buffet reason for non-buffet deal!"

    # Genuine buffet deal mock
    buffet_deal = {
        "brand": "Barbeque Nation",
        "title": "Grand Lunch Buffet",
        "clean_title": "Grand Lunch Buffet",
        "description": "Unlimited barbeque buffet spread.",
        "category": "Restaurant",
        "tags": ["buffet", "barbeque"],
        "keywords": ["buffet", "lunch"],
    }
    reasons_buffet = build_concierge_reasons(buffet_deal, intent_buffet)
    assert "Includes a buffet offer." in reasons_buffet, "Failed to include buffet reason on genuine buffet deal!"
    print("  [OK] Factual buffet reasoning verified. Buffet reasoning only appears on genuine buffet deals.")


def test_bug_2_corrupted_offer_titles():
    print("\n[TEST 2] BUG 2 — Corrupted Offer Title Cleaning & Fallbacks")
    corrupted_samples = [
        "Ow E Xe ₹C4U5Ti9Ve Veg Lunch",
        "₹4E5X9Ecutive Veg Lunch",
        "Restaurant Offline At Restaurant",
        "181 A(At Llb Ianncjlaursaiv",
    ]

    for title in corrupted_samples:
        assert is_corrupted_title(title) is True, f"Failed to detect corrupted title: '{title}'"
        cleaned = clean_offer_title(title, "restaurant")
        assert cleaned == "Special Dining Offer", f"Expected 'Special Dining Offer', got '{cleaned}'"

    print("  [OK] Corrupted offer titles detected and replaced with 'Special Dining Offer'.")


def test_bug_3_highest_discount_sorting():
    print("\n[TEST 3] BUG 3 — Highest Discount Numeric Descending Sorting")
    user_id = 33333
    memory_manager.clear_context(user_id)

    raw = detect_intent("Highest discount")
    intent = memory_manager.update_context(user_id, raw)
    intent["category"] = "restaurant"
    intent["sort_by_discount"] = True

    results = search_deals(intent)
    assert len(results) > 0

    discounts = [d["discount_percent"] for d in results]

    # Verify strictly non-increasing / descending numeric order
    for i in range(len(discounts) - 1):
        assert discounts[i] >= discounts[i + 1], f"Discounts not in descending order: {discounts}"

    print(f"  [OK] Highest discount numerically sorted descending: {discounts[:5]}")


def test_bug_4_data_validation():
    print("\n[TEST 4] BUG 4 — Data Validation & Clean Defaults")
    malformed_deal = {
        "id": "123",
        "brand": "Restaurant Offline At Restaurant",
        "title": "₹4E5X9Ecutive Veg Lunch",
        "price": "invalid_price_string",
        "discount_percent": "invalid_discount",
        "location": "",
        "category": "restaurant",
    }

    normalized = normalize_deal(malformed_deal)
    assert normalized["brand"] == "Zookout Merchant"
    assert normalized["clean_title"] == "Special Dining Offer"
    assert normalized["price"] == 0.0
    assert normalized["discount_percent"] == 0
    assert normalized["display_location"] == "Mumbai"

    print("  [OK] Data validation replaced malformed inputs with clean defaults.")


def test_bug_5_instagram_price_suppression():
    print("\n[TEST 5] BUG 5 — Price Unavailable Suppression in Instagram Post")
    mock_deal_no_price = {
        "brand": "Barbeque Nation",
        "clean_title": "Grand Buffet",
        "formatted_price": "Price unavailable",
        "discount_percent": 50,
        "display_location": "Mumbai",
        "display_category": "Restaurant",
    }

    post = content_creator_agent.generate_instagram_post(mock_deal_no_price)
    assert "Price unavailable" not in post, "Found 'Price unavailable' in Instagram post!"
    assert "for just Price unavailable" not in post, "Found 'for just Price unavailable' in Instagram post!"
    assert "Flat 50% OFF" in post or "50%" in post
    print("  [OK] Instagram post clean price verified. 'Price unavailable' text completely eliminated.")


if __name__ == "__main__":
    print("==================================================")
    print("[RUN] PRODUCTION BUG & QUALITY REGRESSION SUITE")
    print("==================================================")

    test_bug_1_factual_buffet_reasoning()
    test_bug_2_corrupted_offer_titles()
    test_bug_3_highest_discount_sorting()
    test_bug_4_data_validation()
    test_bug_5_instagram_price_suppression()

    print("\n==================================================")
    print("[SUCCESS] ALL 5 PRODUCTION BUGS & QUALITY CHECKS 100% PASSED!")
    print("==================================================")
