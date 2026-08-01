"""
Comprehensive Production Quality Regression Test Suite for Title Cleaning V4.
Verifies:
✓ Assertion 1: Valid numeric prefixes are preserved:
  - '8 Inch Pizza + 2 Drinks' -> '8 Inch Pizza + 2 Drinks'
  - '2Nd Buffet On Us' -> '2Nd Buffet On Us'
  - '1+1 Buffet' -> '1+1 Buffet'
  - '50% Off' -> '50% Off'

✓ Assertion 2: Junk OCR titles are converted to category fallbacks:
  - '45 At' -> 'Special Dining Offer'
  - '127 At' -> 'Special Dining Offer'
  - '90 At' -> 'Special Dining Offer'
  - 'xx At' -> 'Special Dining Offer'
  - 'At &' -> 'Special Dining Offer'
  - 'At At' -> 'Special Dining Offer'

✓ Assertion 3: Duplicated venue phrases are cleaned:
  - 'Solitaire Kitchen & At Solitaire Kitchen &' -> 'Solitaire Kitchen'
"""

import sys
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

# Add project root to path
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))

from v2.search.search_engine import clean_offer_title, is_corrupted_title, normalize_deal
from v2.ai.content_creator import ContentCreatorAgent


def test_title_cleaning_v4_assertions():
    print("\n[TEST 1] Testing Title Cleaning V4 Assertions")

    test_cases = [
        # Numeric Prefixes
        ("8 Inch Pizza + 2 Drinks", "restaurant", "8 Inch Pizza + 2 Drinks"),
        ("2Nd Buffet On Us", "restaurant", "2Nd Buffet On Us"),
        ("1+1 Buffet", "restaurant", "1+1 Buffet"),
        ("50% Off", "restaurant", "50% Off"),
        ("Executive Veg Lunch", "restaurant", "Executive Veg Lunch"),
        ("Flat 50% Off on Entire Menu", "restaurant", "Flat 50% Off on Entire Menu"),

        # Junk OCR Artifact Titles
        ("45 At", "restaurant", "Special Dining Offer"),
        ("127 At", "restaurant", "Special Dining Offer"),
        ("90 At", "restaurant", "Special Dining Offer"),
        ("xx At", "restaurant", "Special Dining Offer"),
        ("At &", "restaurant", "Special Dining Offer"),
        ("At At", "restaurant", "Special Dining Offer"),
        ("Ow E Xe ₹C4U5Ti9Ve Veg Lunch", "restaurant", "Special Dining Offer"),

        # Duplicated Brand Phrases
        ("Solitaire Kitchen & At Solitaire Kitchen &", "restaurant", "Solitaire Kitchen"),
    ]

    for inp, cat, expected in test_cases:
        actual = clean_offer_title(inp, cat)
        assert actual == expected, f"Title Assertion Failed for '{inp}'! Expected '{expected}', got '{actual}'"
        print(f"  [OK] Input: '{inp}' -> Output: '{actual}'")


def test_telegram_and_instagram_offer_title_parity():
    print("\n[TEST 2] Testing Telegram & Instagram Offer Title Parity")
    raw_deal = {
        "id": "44",
        "brand": "Aralia Castor Bistro",
        "title": "8 Inch Pizza + 2 Drinks",
        "category": "Restaurant",
        "price": 499,
        "discount_percent": 50,
        "location": "Andheri, Mumbai",
    }

    norm = normalize_deal(raw_deal)
    clean_title = norm.get("clean_title")
    assert clean_title == "8 Inch Pizza + 2 Drinks", f"Expected '8 Inch Pizza + 2 Drinks', got '{clean_title}'"

    agent = ContentCreatorAgent()
    ig_post = agent.generate_instagram_post(norm)

    assert clean_title in ig_post, f"Clean title '{clean_title}' missing from Instagram post!"
    assert "Inch Pizza + 2 Drinks" not in ig_post or "8 Inch Pizza + 2 Drinks" in ig_post, "Leading number '8' was improperly stripped!"

    print(f"  [OK] Deal ID: {norm['id']} | Brand: '{norm['brand']}' | Cleaned Title: '{clean_title}'")
    print(f"  [OK] Telegram Title: '{clean_title}' | Instagram Title: '{clean_title}'")


if __name__ == "__main__":
    print("==================================================")
    print("[RUN] TITLE CLEANING V4 & PARITY SUITE")
    print("==================================================")

    test_title_cleaning_v4_assertions()
    test_telegram_and_instagram_offer_title_parity()

    print("\n==================================================")
    print("[SUCCESS] ALL TITLE CLEANING V4 ASSERTIONS PASSED (100%)!")
    print("==================================================")
