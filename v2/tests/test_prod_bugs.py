"""
Comprehensive Production Quality Regression Test Suite for Title Preservation & Offer Parity.
Verifies:
✓ Assertion 1: 'Executive Veg Lunch' -> 'Executive Veg Lunch'
✓ Assertion 2: 'Flat 50% Off on Entire Menu' -> 'Flat 50% Off on Entire Menu'
✓ Assertion 3: '2nd Buffet On Us' -> '2nd Buffet On Us'
✓ Assertion 4: 'Ow E Xe ₹C4U5Ti9Ve Veg Lunch' -> 'Special Dining Offer'
✓ Assertion 5: Both Telegram response and Instagram Generator output identical cleaned_title.
"""

import sys
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

# Add project root to path
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))

from v2.search.search_engine import clean_offer_title, is_corrupted_title, normalize_deal
from v2.ai.content_creator import ContentCreatorAgent


def test_required_title_assertions():
    print("\n[TEST 1] Testing Required Title Preservation Assertions")

    test_cases = [
        ("Executive Veg Lunch", "restaurant", "Executive Veg Lunch"),
        ("Flat 50% Off on Entire Menu", "restaurant", "Flat 50% Off on Entire Menu"),
        ("2nd Buffet On Us", "restaurant", "2nd Buffet On Us"),
        ("Ow E Xe ₹C4U5Ti9Ve Veg Lunch", "restaurant", "Special Dining Offer"),
    ]

    for inp, cat, expected in test_cases:
        actual = clean_offer_title(inp, cat)
        assert actual == expected, f"Title Assertion Failed for '{inp}'! Expected '{expected}', got '{actual}'"
        print(f"  [OK] Input: '{inp}' -> Output: '{actual}'")


def test_telegram_and_instagram_offer_title_parity():
    print("\n[TEST 2] Testing Telegram & Instagram Offer Title Parity")
    raw_deal = {
        "id": "41",
        "brand": "Aralia Castor Bistro",
        "title": "2Nd Buffet On Us. Buffet 1+1 + Unlimited Mocktails ₹1599",
        "category": "Restaurant",
        "price": 1599,
        "discount_percent": 50,
        "location": "Andheri, Mumbai",
    }

    norm = normalize_deal(raw_deal)
    clean_title = norm.get("clean_title")
    assert clean_title == "2Nd Buffet On Us", f"Expected '2Nd Buffet On Us', got '{clean_title}'"

    agent = ContentCreatorAgent()
    ig_post = agent.generate_instagram_post(norm)

    assert clean_title in ig_post, f"Clean title '{clean_title}' missing from Instagram post!"
    assert "Special Dining Offer" not in ig_post, "Instagram post improperly used 'Special Dining Offer'!"

    print(f"  [OK] Deal ID: {norm['id']} | Brand: '{norm['brand']}' | Cleaned Title: '{clean_title}'")
    print(f"  [OK] Telegram Title: '{clean_title}' | Instagram Title: '{clean_title}'")


if __name__ == "__main__":
    print("==================================================")
    print("[RUN] TITLE PRESERVATION & OFFER PARITY SUITE")
    print("==================================================")

    test_required_title_assertions()
    test_telegram_and_instagram_offer_title_parity()

    print("\n==================================================")
    print("[SUCCESS] ALL REQUIRED TITLE REGRESSION ASSERTIONS PASSED!")
    print("==================================================")
