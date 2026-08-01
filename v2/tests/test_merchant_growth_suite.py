"""
Milestone 2 – Merchant Growth Agent (Step 1, Step 2, Step 3) Regression Test Suite.
Verifies:
✓ Step 1: Merchant Growth Report triggers & content assertions.
✓ Step 2: Slow-Hour Prediction triggers & content assertions.
✓ Step 3: AI Offer Recommendation Engine triggers & content assertions:
  - Intent classification for (Recommend Offers, Best Offer, Offer Suggestions, Growth Recommendations, Improve Sales).
  - Report structure assertions:
    - Best Performing Offer
    - Highest Discount
    - Lowest Performing Offer
    - Suggested New Offers (Buy 1 Get 1, Family Combo, Weekend Buffet, Happy Hour)
    - Pricing Strategy (30-50% during slow hours)
    - Promotion Strategy (Instagram, Weekend campaigns, Lunch before noon)
    - Revenue Tips (Improve titles, Limited-time offers, Rotate weekly)
"""

import sys
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

# Add project root to path
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))

from v2.ai.intent import detect_intent
from v2.ai.merchant import MerchantGrowthAgent


def test_merchant_intent_classification():
    print("\n[TEST 1] Testing Merchant Growth Report Triggers Classification")

    triggers = [
        ("Merchant Dashboard", "merchant_growth_report"),
        ("Business Dashboard", "merchant_growth_report"),
        ("Merchant Insights", "merchant_growth_report"),
        ("Growth Report", "merchant_growth_report"),
        ("Business Report", "merchant_growth_report"),
        ("Merchant Growth Report", "merchant_growth_report"),
    ]

    for trigger_text, expected_type in triggers:
        intent = detect_intent(trigger_text)
        assert intent.get("is_merchant"), f"Trigger '{trigger_text}' not flagged as merchant!"
        assert intent.get("type") == expected_type, f"Trigger '{trigger_text}' expected '{expected_type}', got '{intent.get('type')}'"
        print(f"  [OK] Trigger: '{trigger_text:24s}' -> Classified as '{intent.get('type')}'")


def test_slow_hours_intent_classification():
    print("\n[TEST 2] Testing Slow-Hour Prediction Triggers Classification")

    slow_triggers = [
        ("Slow Hours", "merchant_slow_hours_analysis"),
        ("Peak Hours", "merchant_slow_hours_analysis"),
        ("Business Analysis", "merchant_slow_hours_analysis"),
        ("Sales Prediction", "merchant_slow_hours_analysis"),
        ("Merchant Analytics", "merchant_slow_hours_analysis"),
    ]

    for trigger_text, expected_type in slow_triggers:
        intent = detect_intent(trigger_text)
        assert intent.get("is_merchant"), f"Trigger '{trigger_text}' not flagged as merchant!"
        assert intent.get("type") == expected_type, f"Trigger '{trigger_text}' expected '{expected_type}', got '{intent.get('type')}'"
        print(f"  [OK] Trigger: '{trigger_text:24s}' -> Classified as '{intent.get('type')}'")


def test_offer_recommendation_intent_classification():
    print("\n[TEST 3] Testing AI Offer Recommendation Triggers Classification")

    rec_triggers = [
        ("Recommend Offers", "merchant_offer_recommendations"),
        ("Best Offer", "merchant_offer_recommendations"),
        ("Offer Suggestions", "merchant_offer_recommendations"),
        ("Growth Recommendations", "merchant_offer_recommendations"),
        ("Improve Sales", "merchant_offer_recommendations"),
    ]

    for trigger_text, expected_type in rec_triggers:
        intent = detect_intent(trigger_text)
        assert intent.get("is_merchant"), f"Trigger '{trigger_text}' not flagged as merchant!"
        assert intent.get("type") == expected_type, f"Trigger '{trigger_text}' expected '{expected_type}', got '{intent.get('type')}'"
        print(f"  [OK] Trigger: '{trigger_text:24s}' -> Classified as '{intent.get('type')}'")


def test_offer_recommendation_report_structure():
    print("\n[TEST 4] Testing AI Offer Recommendation Report Structure")

    agent = MerchantGrowthAgent()
    report = agent.generate_ai_offer_recommendation_report()

    # Required Section Assertions
    assert "🎯 AI Offer Recommendation Report" in report, "Report header missing!"
    assert "Best Performing Offer" in report, "'Best Performing Offer' section missing!"
    assert "Highest Discount" in report, "'Highest Discount' section missing!"
    assert "Lowest Performing Offer" in report, "'Lowest Performing Offer' section missing!"
    assert "Suggested New Offers" in report, "'Suggested New Offers' section missing!"
    assert "Pricing Strategy" in report, "'Pricing Strategy' section missing!"
    assert "Promotion Strategy" in report, "'Promotion Strategy' section missing!"
    assert "Revenue Tips" in report, "'Revenue Tips' section missing!"

    # Required Specific Content Assertions
    required_phrases = [
        "Buy 1 Get 1",
        "Family Combo",
        "Weekend Buffet",
        "Happy Hour",
        "Use 30–50% discounts during slow hours.",
        "Promote offers on Instagram.",
        "Run weekend campaigns.",
        "Push lunch offers before noon.",
        "Improve offer titles.",
        "Add limited-time offers.",
        "Rotate promotions weekly."
    ]

    for phrase in required_phrases:
        assert phrase in report, f"Required phrase '{phrase}' missing from AI Offer Recommendation Report!"
        print(f"  [OK] Verified Required Content: '{phrase}'")

    print("\n[AI OFFER RECOMMENDATION REPORT PREVIEW]:")
    print(report)


if __name__ == "__main__":
    print("==================================================")
    print("[RUN] MILESTONE 2 (STEP 1, STEP 2 & STEP 3) MERCHANT SUITE")
    print("==================================================")

    test_merchant_intent_classification()
    test_slow_hours_intent_classification()
    test_offer_recommendation_intent_classification()
    test_offer_recommendation_report_structure()

    print("\n==================================================")
    print("[SUCCESS] ALL MILESTONE 2 SUITE TESTS PASSED (100%)!")
    print("==================================================")
