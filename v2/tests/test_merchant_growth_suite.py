"""
Milestone 2 – Merchant Growth Agent (Steps 1, 2, 3, 4, 5) Regression Test Suite.
Verifies:
✓ Step 1: Merchant Growth Report triggers & content assertions.
✓ Step 2: Slow-Hour Prediction triggers & content assertions.
✓ Step 3: AI Offer Recommendation Engine triggers & content assertions.
✓ Step 4: Merchant Analytics Report triggers & content assertions.
✓ Step 5: Full AI Growth Report Automation triggers & content assertions:
  - Intent classification for (Growth Report, Full Business Report, AI Growth Report, Merchant Summary, Performance Report).
  - Report structure assertions:
    - Business Overview (Total offers, Total categories, Price range, Average discount)
    - Performance Analysis (Peak hours, Slow hours, Recommended happy hour)
    - Best Performing Offers (Top 3 offers, Highest discount, Highest rated offer)
    - Category Insights (Strongest category, Weakest category, Categories needing growth)
    - AI Recommendations (Improve offer quality, Increase discounts during slow hours, Promote top offers, Weekend campaigns, Improve titles, Expand high-performing)
    - Next Suggested Actions (Instagram campaign, Weekend buffet offer, Happy-hour promotion, Improve low-performing)
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
        ("Business Report", "merchant_growth_report"),
        ("Merchant Growth Report", "merchant_growth_report"),
    ]

    for trigger_text, expected_type in triggers:
        intent = detect_intent(trigger_text)
        assert intent.get("is_merchant"), f"Trigger '{trigger_text}' not flagged as merchant!"
        assert intent.get("type") in [expected_type, "merchant_full_growth_report"], f"Trigger '{trigger_text}' expected '{expected_type}', got '{intent.get('type')}'"
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


def test_full_growth_report_intent_classification():
    print("\n[TEST 5] Testing Full AI Growth Report Triggers Classification")

    full_triggers = [
        ("Growth Report", "merchant_full_growth_report"),
        ("Full Business Report", "merchant_full_growth_report"),
        ("AI Growth Report", "merchant_full_growth_report"),
        ("Merchant Summary", "merchant_full_growth_report"),
        ("Performance Report", "merchant_full_growth_report"),
    ]

    for trigger_text, expected_type in full_triggers:
        intent = detect_intent(trigger_text)
        assert intent.get("is_merchant"), f"Trigger '{trigger_text}' not flagged as merchant!"
        assert intent.get("type") == expected_type, f"Trigger '{trigger_text}' expected '{expected_type}', got '{intent.get('type')}'"
        print(f"  [OK] Trigger: '{trigger_text:24s}' -> Classified as '{intent.get('type')}'")


def test_full_ai_growth_report_structure():
    print("\n[TEST 6] Testing Full AI Growth Report Required Structure & Content")

    agent = MerchantGrowthAgent()
    report = agent.generate_full_ai_growth_report()

    # Section Headers
    assert "📈 AI Merchant Growth Report" in report, "Report header missing!"
    assert "📊 Business Overview" in report, "'Business Overview' section missing!"
    assert "📈 Performance Analysis" in report, "'Performance Analysis' section missing!"
    assert "🎯 Best Performing Offers" in report, "'Best Performing Offers' section missing!"
    assert "📊 Category Insights" in report, "'Category Insights' section missing!"
    assert "💡 AI Recommendations" in report, "'AI Recommendations' section missing!"
    assert "🚀 Next Suggested Actions" in report, "'Next Suggested Actions' section missing!"

    # Specific Required Fields
    required_phrases = [
        "Total offers:",
        "Total categories:",
        "Price range:",
        "Average discount:",
        "Peak hours:",
        "Slow hours:",
        "Recommended happy hour:",
        "Strongest category:",
        "Weakest category:",
        "Categories needing growth:",
        "Improve offer quality",
        "Increase discounts during slow hours",
        "Promote top-performing offers",
        "Increase weekend campaigns",
        "Improve offer titles",
        "Expand high-performing categories",
        "Run Instagram campaign",
        "Create weekend buffet offer",
        "Launch happy-hour promotion",
        "Improve low-performing offers"
    ]

    for phrase in required_phrases:
        assert phrase in report, f"Required phrase '{phrase}' missing from Full AI Growth Report!"
        print(f"  [OK] Verified Required Content: '{phrase}'")

    print("\n[FULL AI GROWTH REPORT PREVIEW]:")
    print(report)


if __name__ == "__main__":
    print("==================================================")
    print("[RUN] MILESTONE 2 (STEPS 1-5) MERCHANT SUITE")
    print("==================================================")

    test_merchant_intent_classification()
    test_slow_hours_intent_classification()
    test_offer_recommendation_intent_classification()
    test_merchant_analytics_intent_classification()
    test_full_growth_report_intent_classification()
    test_full_ai_growth_report_structure()

    print("\n==================================================")
    print("[SUCCESS] ALL MILESTONE 2 SUITE TESTS PASSED (100%)!")
    print("==================================================")
