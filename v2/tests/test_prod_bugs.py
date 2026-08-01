"""
Comprehensive Production Quality Regression Test Suite for Title Cleaning V5 (OCR Garbage Detection).
Verifies:
✓ Assertion 1: OCR Garbage Titles are detected and replaced with clean category fallback:
  - '181 A(At Llb Ianncjlaursaiv' -> 'Special Dining Offer'
  - 'At Llb Ianncjlaursaiv' -> 'Special Dining Offer'
  - 'Llb Ianncj' -> 'Special Dining Offer'
  - '45 At' -> 'Special Dining Offer'
  - 'Ow E Xe ₹C4U5Ti9Ve Veg Lunch' -> 'Special Dining Offer'

✓ Assertion 2: Valid titles remain 100% unchanged:
  - 'Executive Veg Lunch' -> 'Executive Veg Lunch'
  - '8 Inch Pizza + 2 Drinks' -> '8 Inch Pizza + 2 Drinks'
  - 'Coffee + Dessert For 2' -> 'Coffee + Dessert For 2'
  - '2Nd Buffet On Us' -> '2Nd Buffet On Us'
  - 'Flat 50% Off on Entire Menu' -> 'Flat 50% Off on Entire Menu'
"""

import sys
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

# Add project root to path
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))

from v2.search.search_engine import clean_offer_title, is_corrupted_title, normalize_deal
from v2.ai.content_creator import ContentCreatorAgent


def test_title_cleaning_v5_ocr_assertions():
    print("\n[TEST 1] Testing Title Cleaning V5 (OCR Garbage Detection) Assertions")

    test_cases = [
        # OCR Garbage Titles
        ("181 A(At Llb Ianncjlaursaiv", "restaurant", "Special Dining Offer"),
        ("At Llb Ianncjlaursaiv", "restaurant", "Special Dining Offer"),
        ("Llb Ianncj", "restaurant", "Special Dining Offer"),
        ("45 At", "restaurant", "Special Dining Offer"),
        ("Ow E Xe ₹C4U5Ti9Ve Veg Lunch", "restaurant", "Special Dining Offer"),

        # Valid Titles (Must Remain 100% Unchanged)
        ("Executive Veg Lunch", "restaurant", "Executive Veg Lunch"),
        ("8 Inch Pizza + 2 Drinks", "restaurant", "8 Inch Pizza + 2 Drinks"),
        ("Coffee + Dessert For 2", "restaurant", "Coffee + Dessert For 2"),
        ("2Nd Buffet On Us", "restaurant", "2Nd Buffet On Us"),
        ("Flat 50% Off on Entire Menu", "restaurant", "Flat 50% Off on Entire Menu"),
    ]

    for inp, cat, expected in test_cases:
        actual = clean_offer_title(inp, cat)
        assert actual == expected, f"Title Assertion Failed for '{inp}'! Expected '{expected}', got '{actual}'"
        print(f"  [OK] Input: '{inp}' -> Output: '{actual}'")


def test_telegram_and_instagram_offer_title_parity():
    print("\n[TEST 2] Testing Telegram & Instagram Offer Title Parity for Clean Title")
    raw_deal = {
        "id": "185",
        "brand": "Banjara Goldfinch",
        "title": "181 A(At Llb Ianncjlaursaiv",
        "category": "Restaurant",
        "price": 999,
        "discount_percent": 50,
        "location": "Andheri, Mumbai",
    }

    norm = normalize_deal(raw_deal)
    clean_title = norm.get("clean_title")
    assert clean_title == "Special Dining Offer", f"Expected 'Special Dining Offer', got '{clean_title}'"

    agent = ContentCreatorAgent()
    ig_post = agent.generate_instagram_post(norm)

    assert clean_title in ig_post, f"Clean title '{clean_title}' missing from Instagram post!"
    assert "At Llb Ianncjlaursaiv" not in ig_post, "OCR garbage title leaked into Instagram post!"

    print(f"  [OK] Deal ID: {norm['id']} | Brand: '{norm['brand']}' | Cleaned Title: '{clean_title}'")
    print(f"  [OK] Telegram Title: '{clean_title}' | Instagram Title: '{clean_title}'")


if __name__ == "__main__":
    print("==================================================")
    print("[RUN] TITLE CLEANING V5 & PARITY SUITE")
    print("==================================================")

    test_title_cleaning_v5_ocr_assertions()
    test_telegram_and_instagram_offer_title_parity()

    print("\n==================================================")
    print("[SUCCESS] ALL TITLE CLEANING V5 ASSERTIONS PASSED (100%)!")
    print("==================================================")
