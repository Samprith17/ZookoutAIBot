"""
Comprehensive Quality & Production Bug Regression Test Suite.
Verifies:
✓ Valid titles remain unchanged (Executive Veg Lunch, Flat 50% Off on Entire Menu, 2nd Buffet On Us, etc.).
✓ Only corrupted titles become 'Special Dining Offer'.
✓ Buffet reasoning appears ONLY for genuine buffet deals.
✓ Highest discount sorts matching deals numerically descending without claiming every deal is 0%.
✓ Change location performs a fresh location search.
✓ Location fallback notice still appears after changing location.
✓ Discount messages NEVER suppress location fallback notices.
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
from v2.telegram.bot import build_concierge_reasons


def test_valid_titles_preserved():
    print("\n[TEST 1] Valid Offer Titles Must Remain Unchanged")
    valid_titles = [
        "Executive Veg Lunch",
        "Flat 50% Off on Entire Menu",
        "Sunday Buffet",
        "2nd Buffet On Us",
        "Unlimited Mocktails",
    ]

    for title in valid_titles:
        assert is_corrupted_title(title) is False, f"Valid title incorrectly flagged as corrupted: '{title}'"
        cleaned = clean_offer_title(title, "restaurant")
        assert cleaned == title, f"Valid title modified! Expected '{title}', got '{cleaned}'"

    print("  [OK] Valid offer titles preserved 100%.")


def test_corrupted_titles_replaced():
    print("\n[TEST 2] Corrupted Offer Titles Replaced With Fallback")
    corrupted_samples = [
        "Ow E Xe ₹C4U5Ti9Ve Veg Lunch",
        "₹4E5X9Ecutive",
        "181 A(At Llb Ianncjlaursaiv",
        "Restaurant Offline At Restaurant",
    ]

    for title in corrupted_samples:
        assert is_corrupted_title(title) is True, f"Failed to flag corrupted title: '{title}'"
        cleaned = clean_offer_title(title, "restaurant")
        assert cleaned == "Special Dining Offer", f"Expected 'Special Dining Offer', got '{cleaned}'"

    print("  [OK] Corrupted offer titles replaced with 'Special Dining Offer'.")


def test_buffet_reasoning_factual():
    print("\n[TEST 3] Buffet Reasoning Appears ONLY For Genuine Buffet Deals")
    # Non-buffet deal
    non_buffet_deal = {
        "brand": "Suba Galaxy",
        "title": "Executive Veg Lunch",
        "clean_title": "Executive Veg Lunch",
        "description": "Delicious 3-course dining meal.",
        "category": "Restaurant",
        "tags": ["lunch", "veg"],
    }
    reasons = build_concierge_reasons(non_buffet_deal, {"occasion": "Buffet"})
    assert "Includes a buffet offer." not in reasons, "Invented fake buffet reasoning!"

    # Genuine buffet deal
    buffet_deal = {
        "brand": "Barbeque Nation",
        "title": "Sunday Buffet Spread",
        "clean_title": "Sunday Buffet Spread",
        "description": "Unlimited barbeque lunch buffet.",
        "category": "Restaurant",
        "tags": ["buffet"],
    }
    reasons_buffet = build_concierge_reasons(buffet_deal, {"occasion": "Buffet"})
    assert "Includes a buffet offer." in reasons_buffet, "Failed to include buffet reason on genuine buffet deal!"

    print("  [OK] Buffet reasoning strictly matches deal metadata.")


def test_highest_discount_sorting():
    print("\n[TEST 4] Highest Discount Sorts Matching Dataset")
    user_id = 99999
    memory_manager.clear_context(user_id)

    # Search: I want dinner -> Andheri -> Highest discount
    raw1 = detect_intent("I want dinner")
    i1 = memory_manager.update_context(user_id, raw1)
    raw2 = detect_intent("Andheri")
    i2 = memory_manager.update_context(user_id, raw2)
    raw3 = detect_intent("Highest discount")
    intent = memory_manager.update_context(user_id, raw3)

    results = search_deals(intent)
    assert len(results) > 0, "No results returned for highest discount!"

    discounts = [d["discount_percent"] for d in results]
    print(f"  Discount values returned: {discounts[:5]}")
    assert any(d > 0 for d in discounts), "All discounts were 0%!"

    # Verify descending order
    for idx in range(len(discounts) - 1):
        assert discounts[idx] >= discounts[idx + 1], f"Discounts not in descending order: {discounts}"

    print("  [OK] Highest discount correctly sorted matching dataset.")


def test_location_change_sequence():
    print("\n[TEST 5] Location Change Priority & Fallback Notice Preservation")
    user_id = 88888
    memory_manager.clear_context(user_id)

    # Full User Sequence:
    # 1. I want dinner
    # 2. Andheri
    # 3. ₹2000
    # 4. Only buffet
    # 5. Highest discount
    # 6. Change location to Bandra

    memory_manager.update_context(user_id, detect_intent("I want dinner"))
    memory_manager.update_context(user_id, detect_intent("Andheri"))
    memory_manager.update_context(user_id, detect_intent("₹2000"))
    memory_manager.update_context(user_id, detect_intent("Only buffet"))
    memory_manager.update_context(user_id, detect_intent("Highest discount"))

    # Step 6: Change location to Bandra
    intent6 = memory_manager.update_context(user_id, detect_intent("Change location to Bandra"))
    assert intent6.get("location") == "Bandra", f"Location not updated to Bandra! Got: {intent6.get('location')}"

    results6 = search_deals(intent6)
    assert len(results6) > 0, "No results returned for Bandra search!"
    assert intent6.get("fallback_notice") == "No deals found in Bandra. Showing nearby locations.", (
        f"Expected Bandra fallback notice, got: '{intent6.get('fallback_notice')}'"
    )

    print("  [OK] Location change performed fresh search and preserved location fallback notice!")


if __name__ == "__main__":
    print("==================================================")
    print("[RUN] PRODUCTION QUALITY REGRESSION SUITE")
    print("==================================================")

    test_valid_titles_preserved()
    test_corrupted_titles_replaced()
    test_buffet_reasoning_factual()
    test_highest_discount_sorting()
    test_location_change_sequence()

    print("\n==================================================")
    print("[SUCCESS] ALL 5 QUALITY REGRESSION TESTS 100% PASSED!")
    print("==================================================")
