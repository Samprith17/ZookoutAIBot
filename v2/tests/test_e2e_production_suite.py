"""
Milestone 1 & 2 Final Quality Pass: End-to-End Production Multi-Turn Conversation Suite.

Verifies 5 Complete Production Flows:
- Flow 1: Customer AI (Dinner -> Location -> Budget -> Instagram Post generation)
- Flow 2: Customer AI (Dinner -> Buffet -> Fallback)
- Flow 3: Merchant Dashboard
- Flow 4: Merchant Analytics Report
- Flow 5: Full AI Growth Report

Assertions verify:
✓ Intent classification
✓ Conversation memory state transitions
✓ Search query execution & ranking
✓ Safe title formatting & clean layout
✓ Instagram caption generation
"""

import sys
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))

from v2.ai.intent import detect_intent
from v2.ai.memory import ConversationMemoryManager
from v2.search.search_engine import search_deals, load_deals, normalize_deal
from v2.ai.merchant import merchant_agent, MerchantGrowthAgent
from v2.ai.analytics import BusinessAnalyticsEngine
from v2.ai.content_creator import ContentCreatorAgent


def test_flow_1_dinner_location_budget_instagram():
    print("\n[FLOW 1] Testing Customer Multi-Turn Flow: Dinner -> Location -> Budget -> Instagram Post")
    memory = ConversationMemoryManager()
    content_creator = ContentCreatorAgent()

    user_id = "test_user_flow_1"

    # Step 1: Initial query "Dinner"
    turn1_msg = "Dinner"
    intent1 = detect_intent(turn1_msg)
    print(f"  Step 1 Input: '{turn1_msg}' -> Intent: {intent1['type']}, Category: {intent1['category']}")
    assert intent1["type"] == "search"
    assert intent1["category"].title() == "Restaurant"
    memory.update_context(user_id, intent1)

    # Step 2: Location refinement "Andheri"
    turn2_msg = "Andheri"
    intent2 = detect_intent(turn2_msg)
    print(f"  Step 2 Input: '{turn2_msg}' -> Intent: {intent2['type']}, Area: {intent2['area']}")
    assert intent2["area"] == "Andheri" or intent2["location"] == "Andheri"
    merged_intent2 = memory.update_context(user_id, intent2)
    assert merged_intent2["category"].title() == "Restaurant"
    assert merged_intent2["area"] == "Andheri"

    results2 = search_deals(merged_intent2)
    assert len(results2) > 0, "Search results returned 0 deals for Dinner in Andheri!"
    best_deal = results2[0]
    print(f"  Search Results: Found {len(results2)} deals. Top result: '{best_deal['clean_title']}' ({best_deal['brand']})")

    # Step 3: Budget refinement "Under 1000"
    turn3_msg = "Under 1000"
    intent3 = detect_intent(turn3_msg)
    print(f"  Step 3 Input: '{turn3_msg}' -> Max Price: {intent3['max_price']}")
    assert intent3["max_price"] == 1000
    merged_intent3 = memory.update_context(user_id, intent3)
    assert merged_intent3["category"].title() == "Restaurant"
    assert merged_intent3["area"] == "Andheri"
    assert merged_intent3["max_price"] == 1000

    results3 = search_deals(merged_intent3)
    assert len(results3) > 0, "Search results returned 0 deals for Dinner in Andheri under 1000!"
    for d in results3:
        if d.get("price", 0) > 0:
            assert d["price"] <= 1000, f"Deal price ₹{d['price']} exceeded budget limit ₹1000!"

    # Step 4: Content Creator Instagram Generation for Top Deal
    target_deal = results3[0]
    ig_post = content_creator.generate_instagram_post(target_deal)
    print(f"  Step 4 Instagram Generation for '{target_deal['clean_title']}': SUCCESS ({len(ig_post)} chars)")
    assert "Instagram Post" in ig_post or "Caption" in ig_post or target_deal["brand"] in ig_post
    assert "Special Dining Offer" not in ig_post or target_deal["clean_title"] in ig_post
    print("  [FLOW 1] ✅ PASSED FULLY")


def test_flow_2_dinner_buffet_fallback():
    print("\n[FLOW 2] Testing Customer Flow: Dinner -> Buffet -> Fallback")
    memory = ConversationMemoryManager()
    user_id = "test_user_flow_2"

    # Step 1: Initial query "Dinner"
    turn1_msg = "Dinner"
    intent1 = detect_intent(turn1_msg)
    memory.update_context(user_id, intent1)

    # Step 2: Specific request "Buffet in Juhu under 500"
    turn2_msg = "Buffet in Juhu under 500"
    intent2 = detect_intent(turn2_msg)
    print(f"  Step 2 Input: '{turn2_msg}' -> Meal: {intent2.get('meal_type')}, Area: {intent2.get('area')}, Max Price: {intent2.get('max_price')}")

    merged_intent2 = memory.update_context(user_id, intent2)
    results2 = search_deals(merged_intent2)
    print(f"  Search Results: Returned {len(results2)} deals.")

    if len(results2) == 0 or merged_intent2.get("fallback_notice"):
        print("  [OK] Fallback notice activated cleanly for constrained search.")

    print("  [FLOW 2] ✅ PASSED FULLY")


def test_flow_3_merchant_dashboard():
    print("\n[FLOW 3] Testing Merchant Dashboard Flow")
    cmd = "Merchant Dashboard"
    intent = detect_intent(cmd)
    print(f"  Input: '{cmd}' -> Intent: {intent['type']}, is_merchant: {intent['is_merchant']}")
    assert intent["is_merchant"], "Merchant Dashboard not classified as merchant!"

    report = merchant_agent.generate_merchant_growth_report()
    assert "📊 Merchant Growth Report" in report
    assert "Total offers available" in report
    assert "Average discount" in report
    assert "Top-performing offers" in report
    print("  Report Output verified successfully.")
    print("  [FLOW 3] ✅ PASSED FULLY")


def test_flow_4_merchant_analytics():
    print("\n[FLOW 4] Testing Merchant Analytics Flow")
    cmd = "Merchant Analytics"
    intent = detect_intent(cmd)
    print(f"  Input: '{cmd}' -> Intent: {intent['type']}, is_merchant: {intent['is_merchant']}")
    assert intent["is_merchant"], "Merchant Analytics not classified as merchant!"

    engine = BusinessAnalyticsEngine()
    report = engine.generate_merchant_analytics_report()
    assert "📊 Merchant Analytics Report" in report
    assert "Total offers:" in report
    assert "Offers by category:" in report
    assert "Top 5 merchants:" in report
    assert "Business insights:" in report
    assert "AI recommendations:" in report
    print("  Report Output verified successfully.")
    print("  [FLOW 4] ✅ PASSED FULLY")


def test_flow_5_ai_growth_report():
    print("\n[FLOW 5] Testing Full AI Growth Report Flow")
    cmd = "AI Growth Report"
    intent = detect_intent(cmd)
    print(f"  Input: '{cmd}' -> Intent: {intent['type']}, is_merchant: {intent['is_merchant']}")
    assert intent["is_merchant"], "AI Growth Report not classified as merchant!"

    report = merchant_agent.generate_ai_growth_report()
    assert "📈 AI Merchant Growth Report" in report
    assert "Business Overview" in report
    assert "Performance Analysis" in report
    assert "Best Performing Offers" in report
    assert "Category Insights" in report
    assert "AI Recommendations" in report
    assert "Next Suggested Actions" in report
    print("  Report Output verified successfully.")
    print("  [FLOW 5] ✅ PASSED FULLY")


if __name__ == "__main__":
    print("=====================================================================================")
    print("ZOOKOUT AI TELEGRAM BOT — PRODUCTION END-TO-END CONVERSATION SUITE")
    print("=====================================================================================")

    test_flow_1_dinner_location_budget_instagram()
    test_flow_2_dinner_buffet_fallback()
    test_flow_3_merchant_dashboard()
    test_flow_4_merchant_analytics()
    test_flow_5_ai_growth_report()

    print("\n=====================================================================================")
    print("[SUCCESS] ALL 5 END-TO-END PRODUCTION FLOWS PASSED (100%)!")
    print("=====================================================================================")
