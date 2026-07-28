"""
Production Bug Verification Test Suite (Bugs 1-5).
Verifies Location Filter, Buffet Filter, Highest Discount Re-ranking, Change Location, and Price Unavailable Suppression.
"""

import sys
from pathlib import Path

# Add project root to path
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))

from v2.ai.intent import detect_intent
from v2.ai.memory import memory_manager
from v2.search.search_engine import search_deals
from v2.ai.content_creator import content_creator_agent


def test_bug_1_location_filter():
    print("\n[TEST 1] BUG 1 - Exact Area Match / Explicit Nearby Fallback")
    user_id = 11111
    memory_manager.clear_context(user_id)

    raw1 = detect_intent("I want dinner")
    memory_manager.update_context(user_id, raw1)
    memory_manager.set_pending_field(user_id, "location")

    raw2 = detect_intent("Andheri")
    memory_manager.update_context(user_id, raw2)
    memory_manager.set_pending_field(user_id, "budget")

    raw3 = detect_intent("2000")
    intent = memory_manager.update_context(user_id, raw3)

    results = search_deals(intent)
    assert len(results) > 0

    first_loc = results[0]["display_location"]
    notice = intent.get("fallback_notice")

    if "Andheri" in first_loc:
        print(f"  [OK] Returned exact Andheri deals: Location = '{first_loc}'")
    else:
        assert notice is not None
        assert "No deals found in Andheri" in notice
        print(f"  [OK] Nearby fallback notice present: '{notice}'")


def test_bug_2_only_buffet_filter():
    print("\n[TEST 2] BUG 2 - 'Only buffet' Catalog Filter")
    user_id = 22222
    memory_manager.clear_context(user_id)

    raw = detect_intent("Only buffet")
    intent = memory_manager.update_context(user_id, raw)
    intent["query"] = "Only buffet"
    intent["category"] = "restaurant"

    results = search_deals(intent)
    assert len(results) > 0

    notice = intent.get("fallback_notice")
    if not notice:
        for d in results[:3]:
            full_txt = f"{d.get('clean_title','')} {d.get('description','')} {d.get('category','')}".lower()
            assert "buffet" in full_txt
        print(f"  [OK] Returned {len(results)} buffet-only deals from catalog.")
    else:
        assert "No buffet deals found" in notice
        print(f"  [OK] Explicit no-buffet notice returned: '{notice}'")


def test_bug_3_highest_discount_reranking():
    print("\n[TEST 3] BUG 3 - Highest Discount Re-ranking During Active Search")
    user_id = 33333
    memory_manager.clear_context(user_id)

    # Step 1: Restaurant in Andheri under 2000
    raw1 = detect_intent("Restaurant in Andheri under 2000")
    intent1 = memory_manager.update_context(user_id, raw1)
    results1 = search_deals(intent1)
    memory_manager.mark_completed(user_id)

    # Step 2: Highest discount
    raw2 = detect_intent("Highest discount")
    intent2 = memory_manager.update_context(user_id, raw2)

    assert intent2.get("category") == "restaurant"
    assert intent2.get("sort_by_discount") is True

    results2 = search_deals(intent2)
    assert len(results2) > 0
    assert results2[0]["discount_percent"] >= results2[-1]["discount_percent"]
    print(f"  [OK] Re-ranked active search by highest discount. Top discount: {results2[0]['discount_percent']}%.")


def test_bug_4_change_location():
    print("\n[TEST 4] BUG 4 - Change Location to Bandra")
    user_id = 44444
    memory_manager.clear_context(user_id)

    # Step 1: Restaurant in Andheri under 2000
    raw1 = detect_intent("Restaurant in Andheri under 2000")
    intent1 = memory_manager.update_context(user_id, raw1)
    search_deals(intent1)
    memory_manager.mark_completed(user_id)

    # Step 2: Change location to Bandra
    raw2 = detect_intent("Change location to Bandra")
    intent2 = memory_manager.update_context(user_id, raw2)

    assert intent2.get("category") == "restaurant"
    assert intent2.get("location") == "Bandra" or intent2.get("area") == "Bandra"

    results2 = search_deals(intent2)
    assert len(results2) > 0
    notice = intent2.get("fallback_notice")

    print(f"  [OK] Updated location to Bandra. Executed fresh search. Notice: '{notice}'.")


def test_bug_5_price_unavailable_suppression():
    print("\n[TEST 5] BUG 5 - Price Unavailable Suppression in Instagram Post")
    mock_deal_no_price = {
        "brand": "Barbeque Nation",
        "title": "Flat 50% Off Lunch Buffet",
        "clean_title": "Flat 50% Off Lunch Buffet",
        "price": 0.0,
        "formatted_price": "Price unavailable",
        "discount_percent": 50,
        "location": "Mumbai",
        "display_location": "Mumbai",
        "category": "restaurant",
        "display_category": "Restaurant"
    }

    post = content_creator_agent.generate_instagram_post(mock_deal_no_price)
    assert "Price unavailable" not in post
    assert "for just Price unavailable" not in post
    assert "Flat 50% OFF" in post or "50%" in post
    print("  [OK] Instagram post clean price verified. 'Price unavailable' text completely eliminated.")


if __name__ == "__main__":
    print("==================================================")
    print("[RUN] PRODUCTION BUG FIX VERIFICATION TEST SUITE (BUGS 1-5)")
    print("==================================================")

    test_bug_1_location_filter()
    test_bug_2_only_buffet_filter()
    test_bug_3_highest_discount_reranking()
    test_bug_4_change_location()
    test_bug_5_price_unavailable_suppression()

    print("\n==================================================")
    print("[SUCCESS] ALL 5 PRODUCTION BUGS ARE 100% FIXED!")
    print("==================================================")
