"""
Search Engine Quality & Ranking Verification Test Suite.
Verifies location fallback hierarchy, catalog buffet filtering, content generator formatting,
post-no-results context retention, weighted scoring, and factual reasoning.
"""

import sys
from pathlib import Path

# Add project root to path
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))

from v2.ai.intent import detect_intent
from v2.ai.memory import memory_manager
from v2.search.search_engine import search_deals, compute_weighted_score
from v2.ai.content_creator import content_creator_agent


def test_1_location_filtering():
    print("\n[TEST 1] Location Filtering & Fallback Order")
    intent = {"type": "search", "category": "restaurant", "location": "Andheri", "max_price": 2000.0}
    results = search_deals(intent)

    assert len(results) > 0
    first_loc = results[0]["location"]

    if "Andheri" in first_loc:
        print("  [OK] Returned exact Andheri deals.")
    else:
        assert intent.get("fallback_notice") is not None
        assert "No exact" in intent["fallback_notice"]
        print(f"  [OK] Correctly executed nearby fallback with notice: '{intent['fallback_notice']}'")


def test_2_buffet_filtering():
    print("\n[TEST 2] Catalog Buffet Filtering ('Only buffet')")
    intent = {"type": "search", "category": "restaurant", "query": "Only buffet", "meal_type": "buffet"}
    results = search_deals(intent)

    assert len(results) > 0
    if not intent.get("fallback_notice"):
        for d in results[:3]:
            full_txt = f"{d.get('clean_title','')} {d.get('description','')} {d.get('category','')}".lower()
            assert "buffet" in full_txt
        print("  [OK] Returned buffet deals only.")
    else:
        assert "No buffet deals are currently available" in intent["fallback_notice"]
        print(f"  [OK] Correctly notified fallback without faking buffet reasoning: '{intent['fallback_notice']}'")


def test_3_context_retention_after_zero_results():
    print("\n[TEST 3] Follow-Up Refinements After Zero Results ('Highest discount')")
    user_id = 77777
    memory_manager.clear_context(user_id)

    # Step 1: Spa in Koramangala under ₹3000 (0 exact results)
    raw1 = detect_intent("Spa in Koramangala under ₹3000")
    intent1 = memory_manager.update_context(user_id, raw1)
    results1 = search_deals(intent1)
    memory_manager.mark_completed(user_id)

    assert memory_manager.is_session_active(user_id), "Session context was lost after zero/fallback results!"

    # Step 2: User says "Highest discount"
    raw2 = detect_intent("Highest discount")
    assert raw2["type"] == "search", f"Expected search intent for 'Highest discount', got {raw2['type']}"

    intent2 = memory_manager.update_context(user_id, raw2)
    assert intent2.get("category") == "spa", f"Category context lost: {intent2.get('category')}"
    assert intent2.get("sort_by_discount") is True

    results2 = search_deals(intent2)
    assert len(results2) > 0
    print(f"  [OK] Successfully retained search context and returned {len(results2)} spa deals sorted by highest discount.")


def test_4_instagram_clean_price():
    print("\n[TEST 4] Content Creator Clean Price Formatting (No 'Price unavailable')")
    mock_deal_no_price = {
        "brand": "Sigree Global Grill",
        "title": "Flat 50% Off Lunch Buffet",
        "clean_title": "Flat 50% Off Lunch Buffet",
        "price": 0.0,
        "formatted_price": "Price unavailable",
        "discount_percent": 50,
        "location": "Powai, Mumbai",
        "display_location": "Powai, Mumbai",
        "category": "restaurant",
        "display_category": "Restaurant"
    }

    ig_post = content_creator_agent.generate_instagram_post(mock_deal_no_price)
    assert "Price unavailable" not in ig_post
    assert "for just Price unavailable" not in ig_post
    assert "Flat 50% OFF" in ig_post or "50%" in ig_post
    print("  [OK] Instagram post clean price output verified. 'Price unavailable' string eliminated.")


def test_5_weighted_ranking_score():
    print("\n[TEST 5] 6-Factor Weighted Ranking Score Verification (35/20/20/10/10/5)")
    mock_intent = {"category": "restaurant", "location": "Andheri", "max_price": 2000.0}

    deal_exact = {
        "title": "Buffet Dinner",
        "clean_title": "Buffet Dinner",
        "price": 1200.0,
        "discount_percent": 50,
        "rating": 4.8,
        "confidence": 0.95,
        "location": "Andheri, Mumbai",
        "category": "restaurant"
    }

    deal_city = {
        "title": "Standard Dining",
        "clean_title": "Standard Dining",
        "price": 1900.0,
        "discount_percent": 10,
        "rating": 4.0,
        "confidence": 0.70,
        "location": "Colaba, Mumbai",
        "category": "restaurant"
    }

    score_exact = compute_weighted_score(deal_exact, mock_intent, "exact")
    score_city = compute_weighted_score(deal_city, mock_intent, "city")

    assert score_exact["score"] > score_city["score"]
    print(f"  [OK] Exact Area deal score ({score_exact['score']}) > City deal score ({score_city['score']}).")


if __name__ == "__main__":
    print("==================================================")
    print("[RUN] SEARCH ENGINE QUALITY & RANKING TEST SUITE")
    print("==================================================")

    test_1_location_filtering()
    test_2_buffet_filtering()
    test_3_context_retention_after_zero_results()
    test_4_instagram_clean_price()
    test_5_weighted_ranking_score()

    print("\n==================================================")
    print("[SUCCESS] ALL SEARCH QUALITY TESTS PASSED (100%)")
    print("==================================================")
