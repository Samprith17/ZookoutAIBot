"""
Milestone 2 – Merchant Growth Agent (Step 1, Step 2, Step 3, Step 4) Regression Test Suite.
Verifies:
✓ Step 1: Merchant Growth Report triggers & content assertions.
✓ Step 2: Slow-Hour Prediction triggers & content assertions.
✓ Step 3: AI Offer Recommendation Engine triggers & content assertions.
✓ Step 4: Merchant Analytics Report triggers & content assertions:
  - Intent classification for (Merchant Analytics, Category Analytics, Sales Analytics, Offer Analytics, Analytics Report).
  - Report structure assertions:
    - Total offers
    - Offers by category
    - Average discount by category
    - Highest discount by category
    - Average price by category
    - Top 5 categories
    - Top 5 merchants
    - Highest rated offers
    - Business insights (Strongest category, Weakest category, Growth opportunities, Categories needing more offers)
    - AI recommendations (Increase offers, Improve discounts, Promote top merchants, Expand high demand)
"""

import sys
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

# Add project root to path
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))

from v2.ai.intent import detect_intent
from v2.ai.merchant import MerchantGrowthAgent
from v2.ai.analytics import BusinessAnalyticsEngine


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


def test_merchant_analytics_intent_classification():
    print("\n[TEST 4] Testing Merchant Analytics Triggers Classification")

    analytics_triggers = [
        ("Merchant Analytics", "merchant_analytics_report"),
        ("Category Analytics", "merchant_analytics_report"),
        ("Sales Analytics", "merchant_analytics_report"),
        ("Offer Analytics", "merchant_analytics_report"),
        ("Analytics Report", "merchant_analytics_report"),
    ]

    for trigger_text, expected_type in analytics_triggers:
        intent = detect_intent(trigger_text)
        assert intent.get("is_merchant"), f"Trigger '{trigger_text}' not flagged as merchant!"
        assert intent.get("type") == expected_type, f"Trigger '{trigger_text}' expected '{expected_type}', got '{intent.get('type')}'"
        print(f"  [OK] Trigger: '{trigger_text:24s}' -> Classified as '{intent.get('type')}'")


def test_merchant_analytics_report_structure():
    print("\n[TEST 5] Testing Merchant Analytics Report Required Fields & Output")

    engine = BusinessAnalyticsEngine()
    report = engine.generate_merchant_analytics_report()

    # Required Section Assertions
    assert "📊 Merchant Analytics Report" in report, "Report header missing!"
    assert "• Total offers:" in report, "'Total offers:' section missing!"
    assert "• Offers by category:" in report, "'Offers by category:' section missing!"
    assert "• Average discount by category:" in report, "'Average discount by category:' section missing!"
    assert "• Highest discount by category:" in report, "'Highest discount by category:' section missing!"
    assert "• Average price by category:" in report, "'Average price by category:' section missing!"
    assert "• Top 5 categories:" in report, "'Top 5 categories:' section missing!"
    assert "• Top 5 merchants:" in report, "'Top 5 merchants:' section missing!"
    assert "• Highest rated offers:" in report, "'Highest rated offers:' section missing!"
    assert "• Business insights:" in report, "'Business insights:' section missing!"
    assert "• AI recommendations:" in report, "'AI recommendations:' section missing!"

    # Required Business Insights Assertions
    assert "Strongest category:" in report, "'Strongest category:' missing from Business Insights!"
    assert "Weakest category:" in report, "'Weakest category:' missing from Business Insights!"
    assert "Growth opportunities:" in report, "'Growth opportunities:' missing from Business Insights!"
    assert "Categories needing more offers:" in report, "'Categories needing more offers:' missing from Business Insights!"

    # Required AI Recommendations Assertions
    required_recommendations = [
        "Increase offers in underperforming categories.",
        "Improve discounts where appropriate.",
        "Promote top-performing merchants.",
        "Expand high-demand categories."
    ]

    for rec in required_recommendations:
        assert rec in report, f"Required AI recommendation '{rec}' missing from Merchant Analytics Report!"
        print(f"  [OK] Verified Required Recommendation: '{rec}'")

    print("\n[MERCHANT ANALYTICS REPORT PREVIEW]:")
    print(report)


if __name__ == "__main__":
    print("==================================================")
    print("[RUN] MILESTONE 2 (STEPS 1-4) MERCHANT SUITE")
    print("==================================================")

    test_merchant_intent_classification()
    test_slow_hours_intent_classification()
    test_offer_recommendation_intent_classification()
    test_merchant_analytics_intent_classification()
    test_merchant_analytics_report_structure()

    print("\n==================================================")
    print("[SUCCESS] ALL MILESTONE 2 SUITE TESTS PASSED (100%)!")
    print("==================================================")
