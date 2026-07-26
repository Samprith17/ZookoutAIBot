import sys
import logging

sys.stdout.reconfigure(encoding='utf-8')

from v2.search.search_engine import clean_location_string
from v2.ai.content_creator import content_creator_agent

logging.basicConfig(level=logging.ERROR)


def run_verification_tests():
    print("=" * 80)
    print("LOCATION DEDUPLICATION & INSTAGRAM HASHTAG VERIFICATION TEST")
    print("=" * 80)

    # Issue 1: Location Deduplication Verification
    location_test_cases = [
        ("Andheri, Andheri, Mumbai", "Andheri, Mumbai"),
        ("Bandra, Mumbai", "Bandra, Mumbai"),
        ("Mumbai", "Mumbai"),
        ("Powai, Powai, Mumbai", "Powai, Mumbai"),
        ("andheri, Andheri, mumbai", "Andheri, Mumbai"),
    ]

    print("\n--- 1. VERIFYING LOCATION DEDUPLICATION ---")
    for inp, expected in location_test_cases:
        output = clean_location_string(inp)
        status = "✅ PASSED" if output == expected else f"❌ FAILED (got '{output}')"
        print(f"INPUT:  '{inp}'\nOUTPUT: '{output}' -> STATUS: {status}\n")
        assert output == expected, f"Failed location deduplication for '{inp}': expected '{expected}', got '{output}'"

    print("✅ LOCATION DEDUPLICATION TEST PASSED 100%!")

    # Issue 2: Instagram Hashtags Verification
    print("\n--- 2. VERIFYING INSTAGRAM HASHTAG GENERATION ---")
    test_deal = {
        "brand": "Orchids Wellness",
        "display_category": "Spa",
        "display_location": "Andheri, Andheri, Mumbai",
        "clean_title": "Thai Spa Therapy",
        "formatted_price": "₹999",
        "discount_percent": 50
    }

    hashtags = content_creator_agent.generate_hashtags(test_deal)
    print(f"INPUT LOCATION: '{test_deal['display_location']}' | CATEGORY: '{test_deal['display_category']}'")
    print(f"GENERATED HASHTAGS: {hashtags}\n")

    assert "#AndheriSpa" in hashtags, "Hashtags must contain #AndheriSpa"
    assert "#MumbaiSpa" in hashtags, "Hashtags must contain #MumbaiSpa"
    assert "#Andheri,Andheri,MumbaiSpa" not in hashtags, "Invalid hashtag with commas/duplicates detected"
    assert "," not in hashtags, "Hashtags must not contain commas"

    print("✅ INSTAGRAM HASHTAG GENERATION TEST PASSED 100%!")

    print("=" * 80)
    print("ALL VERIFICATION EXAMPLES PASSED 100%!")
    print("=" * 80)


if __name__ == "__main__":
    run_verification_tests()
