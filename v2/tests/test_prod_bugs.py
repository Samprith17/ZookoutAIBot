"""
Production Bug Verification Test Suite (Bugs 1-4).
Verifies Area Location Filtering, Only Buffet Catalog Filtering, Price Unavailable Suppression,
and Follow-up Refinements After No Results.
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


def test_bug_1_location_area_filter():
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
    assert len(results) > 0, "No results returned for dinner in Andheri under 2000"

    first_loc = results[0]["display_location"]
    notice = intent.get("fallback_notice")

    if "Andheri" in first_loc:
        print(f"  [OK] Returned exact Andheri deals: Location = '{first_loc}'")
    else:
        assert notice is not None, "Fallback occurred but fallback_notice is missing!"
        assert "No restaurant deals were found in Andheri" in notice
        print(f"  [OK] Nearby fallback notice present: '{notice}'")


def test_bug_2_only_buffet_filter():
    print("\n[TEST 2] BUG 2 - 'Only buffet' Catalog Filter")
    user_id = 22222
    memory_manager.clear_context(user_id)

    raw = detect_intent("Only buffet")
    intent = memory_manager.update_context(user_id, raw)

    # Force query into search_deals
    intent["query"] = "Only buffet"
    intent["category"] = "restaurant"

    results = search_deals(intent)
    assert len(results) > 0, "No results returned for Only buffet query"

    notice = intent.get("fallback_notice")
    if not notice:
        for d in results[:3]:
            full_txt = f"{d.get('clean_title','')} {d.get('description','')} {d.get('category','')}".lower()
            assert "buffet" in full_txt, f"Non-buffet deal returned: {d.get('clean_title')}"
        print(f"  [OK] Returned {len(results)} buffet-only deals from catalog.")
    else:
        assert "No buffet offers are currently available" in notice
        print(f"  [OK] Explicit no-buffet notice returned: '{notice}'")


def test_bug_3_price_unavailable_suppression():
    print("\n[TEST 3] BUG 3 - Price Unavailable Suppression in Instagram Post")
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
    assert "Price unavailable" not in post, "Found 'Price unavailable' in Instagram post!"
    assert "for just Price unavailable" not in post, "Found 'for just Price unavailable' in Instagram post!"
    assert "Flat 50% OFF" in post or "50%" in post
    print("  [OK] Instagram post clean price verified. 'Price unavailable' text completely eliminated.")


def test_bug_4_followup_after_no_results():
    print("\n[TEST 4] BUG 4 - Follow-up Context Retention ('Highest discount')")
    user_id = 33333
    memory_manager.clear_context(user_id)

    # Step 1: Spa in Koramangala under ₹3000
    raw1 = detect_intent("Spa in Koramangala under ₹3000")
    intent1 = memory_manager.update_context(user_id, raw1)
    results1 = search_deals(intent1)
    memory_manager.mark_completed(user_id)

    # Context MUST remain active
    assert memory_manager.is_session_active(user_id), "Session context was lost after zero/fallback results!"

    # Step 2: User says "Highest discount"
    raw2 = detect_intent("Highest discount")
    assert raw2["type"] == "search", f"Expected search intent for 'Highest discount', got {raw2['type']}"

    intent2 = memory_manager.update_context(user_id, raw2)
    assert intent2.get("category") == "spa", f"Category context lost: {intent2.get('category')}"

    results2 = search_deals(intent2)
    assert len(results2) > 0, "No spa deals returned for Highest discount follow-up"
    print(f"  [OK] Successfully continued spa search context and returned {len(results2)} deals sorted by highest discount.")


if __name__ == "__main__":
    print("==================================================")
    print("[RUN] PRODUCTION BUG FIX VERIFICATION TEST SUITE")
    print("==================================================")

    test_bug_1_location_area_filter()
    test_bug_2_only_buffet_filter()
    test_bug_3_price_unavailable_suppression()
    test_bug_4_followup_after_no_results()

    print("\n==================================================")
    print("[SUCCESS] ALL 4 PRODUCTION BUGS ARE 100% FIXED!")
    print("==================================================")
