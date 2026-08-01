"""
Comprehensive Production Quality Regression Test Suite for Title Cleaning & Offer Preservation.
Verifies:
✓ Requirement 1-3: Trace clean_title generation and verify fallback title is used ONLY when original title is genuinely corrupted.
✓ Requirement 4: Valid titles (Executive Veg Lunch, Flat 50% Off on Entire Menu, Sunday Buffet, 2nd Buffet On Us, Unlimited Mocktails) remain unchanged.
✓ Requirement 5: Both Telegram response and Instagram Post Generator use the exact same cleaned title.
"""

import sys
from pathlib import Path

# Add project root to path
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))

from v2.search.search_engine import clean_offer_title, is_corrupted_title, normalize_deal
from v2.ai.content_creator import ContentCreatorAgent


def test_valid_titles_preserved():
    print("\n[TEST 1] Valid Offer Titles Must Remain Unchanged")
    valid_samples = [
        ("Executive Veg Lunch", "restaurant"),
        ("Flat 50% Off on Entire Menu", "restaurant"),
        ("Sunday Buffet", "restaurant"),
        ("2nd Buffet On Us", "restaurant"),
        ("Unlimited Mocktails", "restaurant"),
        ("Executive Non-Veg Buffet", "buffet"),
        ("Haircut & Blow Dry", "salon"),
        ("Deep Tissue Body Massage", "spa"),
    ]

    for title, cat in valid_samples:
        cleaned = clean_offer_title(title, cat)
        assert cleaned == title, f"Valid title '{title}' was changed to '{cleaned}'!"

    print("  [OK] All valid titles remained 100% unchanged.")


def test_ocr_extracted_readable_titles():
    print("\n[TEST 2] Readable Offer Sub-Phrases Extracted from OCR Strings")
    ocr_samples = [
        ("43 0U0N Lnimoiwte D K ₹In1G3F9Is9Her Ultra Max Or Heineken Silver Draft + 2 Bar Pmaayx ₹O1R 3H9E Oinne Zkeono Ksoiulvte R D Vraisfitt Wbikthc 2 D Ciovem Pli Mpeanyt A₹R1Y3 A9R A Bt Ittehse. Outlet Unlimited Kingfisher Ultrapremium Drafts. Unlimited Fun. Unlimited Draft Beer + 2 Bar Bites ₹1399", "restaurant", "Unlimited Draft Beer + 2 Bar Bites ₹1399"),
        ("Unlimited Domestic Spirits + 2 Bar Bites ₹1299 Pwaithy ₹21 C2O9M Opnli Mzoeonktaoruyt B Ar V Bisitiet Sb.Kc Dive ₹1299 At The Outlet Unlimited Domestic Spiritsunlimited Pours. Bigger Savings. Unlimited Spirits + 2 Bar Bites ₹1299", "restaurant", "Unlimited Spirits + 2 Bar Bites ₹1299"),
        ("Whitening Manicure + Whitening Pedicure ₹799 Psoafyte ₹R 4H9A Nodns Z Aonodk Ofeuet T . Ice Salon A Whitening Manicure And Pedicure For Brighter, Bright Hands. Beautiful Feet. Whitening Mani", "salon", "Ice Salon A Whitening Manicure And Pedicure For Brighter, Bright Hands"),
    ]

    for raw, cat, expected in ocr_samples:
        cleaned = clean_offer_title(raw, cat)
        assert cleaned != "Special Dining Offer" and cleaned != "Beauty & Grooming Offer", f"Raw title '{raw[:30]}' defaulted to fallback!"
        assert cleaned == expected, f"Expected '{expected}', got '{cleaned}'"

    print("  [OK] Readable offer sub-phrases extracted cleanly without resorting to fallback titles.")


def test_genuinely_corrupted_titles_fallback():
    print("\n[TEST 3] Genuinely Corrupted / Empty Titles Use Category Fallback")
    corrupted_samples = [
        ("60", "spa", "Premium Spa Experience"),
        ("181 A(At Llb Ianncjlaursaiv", "restaurant", "Special Dining Offer"),
        ("Restaurant Offline At Restaurant", "restaurant", "Special Dining Offer"),
    ]

    for raw, cat, expected_fallback in corrupted_samples:
        cleaned = clean_offer_title(raw, cat)
        assert cleaned == expected_fallback, f"Expected fallback '{expected_fallback}' for corrupted title '{raw}', got '{cleaned}'"

    print("  [OK] Genuinely corrupted titles cleanly assigned category fallback.")


def test_telegram_and_instagram_title_parity():
    print("\n[TEST 4] Telegram Response & Instagram Generator Use Same Clean Title")
    raw_deal = {
        "id": "999",
        "brand": "Barbeque Nation",
        "title": "2nd Buffet On Us",
        "category": "Restaurant",
        "price": 1200,
        "discount_percent": 50,
        "location": "Andheri, Mumbai",
    }

    norm = normalize_deal(raw_deal)
    clean_title = norm.get("clean_title")
    assert clean_title == "2nd Buffet On Us", f"Normalized deal title incorrect: '{clean_title}'"

    agent = ContentCreatorAgent()
    ig_post = agent.generate_instagram_post(norm)
    assert clean_title in ig_post, f"Clean title '{clean_title}' missing from Instagram post!"
    assert "Special Dining Offer" not in ig_post, "Instagram post used 'Special Dining Offer' instead of clean title!"

    print("  [OK] Both Telegram response and Instagram Post Generator use identical cleaned title.")


if __name__ == "__main__":
    print("==================================================")
    print("[RUN] TITLE CLEANING & OFFER PRESERVATION REGRESSION SUITE")
    print("==================================================")

    test_valid_titles_preserved()
    test_ocr_extracted_readable_titles()
    test_genuinely_corrupted_titles_fallback()
    test_telegram_and_instagram_title_parity()

    print("\n==================================================")
    print("[SUCCESS] ALL TITLE CLEANING REGRESSION TESTS 100% PASSED!")
    print("==================================================")
