"""
Comprehensive Quality & Production Bug Regression Test Suite (Bugs 1-4).
Verifies:
✓ Bug 1: Valid offer titles remain unchanged (Executive Veg Lunch, Flat 50% Off on Entire Menu, 2nd Buffet On Us, Unlimited Mocktails, Sunday Buffet).
✓ Bug 2: Highest discount returns non-zero (e.g. 50%) discount deals for restaurant and buffet queries.
✓ Bug 3: Buffet reasoning appears ONLY for genuine buffet deals (matching displayed deal metadata).
✓ Bug 4: Instagram generator uses real offer titles (e.g. Executive Veg Lunch, Flat 50% Off on Entire Menu, 2nd Buffet On Us).
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


def test_bug_1_valid_titles_preserved():
    print("\n[TEST 1] BUG 1 — Valid Offer Titles Must Remain Unchanged")
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
        print(f"  BEFORE: '{title}' -> AFTER: '{cleaned}' [PASS]")

    print("  [OK] All valid offer titles preserved 100%.")


def test_bug_2_highest_discount_returns_non_zero_deals():
    print("\n[TEST 2] BUG 2 — Highest Discount Returns Non-Zero (50%) Deals")
    user_id = 999111
    memory_manager.clear_context(user_id)

    # Full User Sequence:
    # 1. I want dinner -> Andheri -> ₹2000
    # 2. Only buffet
    # 3. Highest discount
    memory_manager.update_context(user_id, detect_intent("I want dinner"))
    memory_manager.update_context(user_id, detect_intent("Andheri"))
    memory_manager.update_context(user_id, detect_intent("₹2000"))
    memory_manager.update_context(user_id, detect_intent("Only buffet"))
    intent = memory_manager.update_context(user_id, detect_intent("Highest discount"))

    results = search_deals(intent)
    assert len(results) > 0, "No results returned for highest discount buffet search!"

    discounts = [d["discount_percent"] for d in results]
    print(f"  Returned discounts: {discounts[:5]}")
    top_discount = discounts[0]
    assert top_discount > 0, f"Top discount was 0%! Expected 50%+, got {top_discount}%"
    assert top_discount >= 50, f"Expected 50% discount for BOGO/Buffet deal, got {top_discount}%"

    print("  [OK] Highest discount correctly returned 50% discount deals instead of 0%.")


def test_bug_3_buffet_reasoning_matches_displayed_deal():
    print("\n[TEST 3] BUG 3 — Buffet Reasoning Strictly Matches Displayed Deal")
    # Non-buffet deal mock
    non_buffet_deal = {
        "brand": "Suba Galaxy",
        "title": "Executive Veg Lunch",
        "clean_title": "Executive Veg Lunch",
        "description": "Delicious 3-course dining meal.",
        "category": "Restaurant",
        "tags": ["lunch", "veg"],
    }
    reasons = build_concierge_reasons(non_buffet_deal, {"query": "dining"})
    assert "Includes a buffet offer." not in reasons, "Added fake buffet reasoning to non-buffet deal!"

    # Genuine buffet deal mock
    buffet_deal = {
        "brand": "Barbeque Nation",
        "title": "Sunday Buffet Spread",
        "clean_title": "Sunday Buffet Spread",
        "description": "Unlimited barbeque lunch buffet.",
        "category": "Restaurant",
        "tags": ["buffet"],
    }
    reasons_buffet = build_concierge_reasons(buffet_deal, {"query": "buffet"})
    assert "Includes a buffet offer." in reasons_buffet, "Failed to include buffet reason on genuine buffet deal!"

    print("  [OK] Buffet reasoning strictly matches displayed deal metadata.")


def test_bug_4_instagram_uses_real_offer_title():
    print("\n[TEST 4] BUG 4 — Instagram Posts Use Real Offer Title")
    valid_deals = [
        {"brand": "Taj Restaurant", "clean_title": "Executive Veg Lunch", "formatted_price": "₹499", "discount_percent": 50, "display_location": "Andheri, Mumbai", "display_category": "Restaurant"},
        {"brand": "Barbeque Nation", "clean_title": "Flat 50% Off on Entire Menu", "formatted_price": "₹699", "discount_percent": 50, "display_location": "Powai, Mumbai", "display_category": "Restaurant"},
        {"brand": "Banjara Dining", "clean_title": "2nd Buffet On Us", "formatted_price": "₹899", "discount_percent": 50, "display_location": "Bandra, Mumbai", "display_category": "Restaurant"},
    ]

    for deal in valid_deals:
        post = content_creator_agent.generate_instagram_post(deal)
        expected_title = deal["clean_title"]
        assert expected_title in post, f"Instagram post missing real title! Expected '{expected_title}' in post:\n{post}"
        assert "Special Dining Offer" not in post, f"Instagram post used fallback title instead of real title '{expected_title}'!"
        print(f"  Real Title: '{expected_title}' -> Present in Instagram post [PASS]")

    print("  [OK] Instagram posts cleanly format real offer titles.")


if __name__ == "__main__":
    print("==================================================")
    print("[RUN] PRODUCTION BUG REGRESSION SUITE (BUGS 1-4)")
    print("==================================================")

    test_bug_1_valid_titles_preserved()
    test_bug_2_highest_discount_returns_non_zero_deals()
    test_bug_3_buffet_reasoning_matches_displayed_deal()
    test_bug_4_instagram_uses_real_offer_title()

    print("\n==================================================")
    print("[SUCCESS] ALL 4 PRODUCTION BUGS 100% RESOLVED & VERIFIED!")
    print("==================================================")
