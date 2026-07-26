import sys
import logging

sys.stdout.reconfigure(encoding='utf-8')

from v2.search.search_engine import clean_offer_title, is_corrupted_title, get_clean_category_fallback

logging.basicConfig(level=logging.ERROR)


def run_title_cleanup_tests():
    print("=" * 80)
    print("CORRUPTED OFFER TITLE CLEANUP VERIFICATION TEST SUITE")
    print("=" * 80)

    test_cases = [
        # (title, category, expected_output)
        ("102 A25T %Ae Oricfhf", "Salon", "Beauty & Grooming Offer"),
        ("Flat 50% Off on Total Bill", "Restaurant", "Flat 50% Off on Total Bill"),
        ("Haircut + Hair Wash + Blow Dry", "Salon", "Haircut + Hair Wash + Blow Dry"),
        ("Spa Therapy – Flat 50% Off", "Spa", "Spa Therapy – Flat 50% Off"),
        ("Executive Veg Lunch", "Restaurant", "Executive Veg Lunch"),
        ("102 A25T %Ae Oricfhf", "Restaurant", "Special Dining Offer"),
        ("102 A25T %Ae Oricfhf", "Spa", "Premium Spa Experience"),
        ("102 A25T %Ae Oricfhf", "Hotel", "Hotel Experience"),
        ("102 A25T %Ae Oricfhf", "Cafe", "Cafe Special"),
        ("102 A25T %Ae Oricfhf", "Entertainment", "Entertainment Offer"),
    ]

    for title, category, expected in test_cases:
        deal = {"title": title, "category": category, "description": ""}
        output = clean_offer_title(deal)
        status = "✅ PASSED" if output == expected else f"❌ FAILED (got '{output}')"
        print(f"INPUT TITLE:    '{title}' (Category: {category})")
        print(f"OUTPUT TITLE:   '{output}'")
        print(f"EXPECTED TITLE: '{expected}' -> {status}\n")

        assert output == expected, f"Failed for '{title}' in category '{category}': expected '{expected}', got '{output}'"

    print("==========================================================================")
    print("ALL TITLE CLEANUP TEST CASES PASSED 100%!")
    print("==========================================================================")


if __name__ == "__main__":
    run_title_cleanup_tests()
