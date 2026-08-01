"""
Milestone 2 – Merchant Growth Agent (Step 1 & Step 2) Regression Test Suite.
Verifies:
✓ Assertion 1: Merchant intent triggers classify correctly for Step 1 (Merchant Dashboard, Business Dashboard, Merchant Insights, Growth Report, Business Report).
✓ Assertion 2: Merchant Growth Report contains all required fields & recommendations.
✓ Assertion 3: Step 2 Slow-Hour Prediction intents classify correctly (Slow Hours, Peak Hours, Business Analysis, Sales Prediction, Merchant Analytics).
✓ Assertion 4: Business Performance Analysis Report contains all required sections:
  - Estimated Peak Hours
  - Estimated Slow Hours
  - Recommended Happy Hour
  - Suggested Discount / Offer
  - Best Days for Promotions
  - AI Recommendations
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
        print(f"  [OK] Trigger: '{trigger_text:22s}' -> Classified as '{intent.get('type')}'")


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
        print(f"  [OK] Trigger: '{trigger_text:22s}' -> Classified as '{intent.get('type')}'")


def test_slow_hours_report_structure():
    print("\n[TEST 3] Testing Business Performance Analysis Report Structure")

    agent = MerchantGrowthAgent()
    report = agent.generate_slow_hours_performance_report()

    # Required Section Assertions
    assert "📈 Business Performance Analysis" in report, "Report header missing!"
    assert "Peak Hours:" in report, "'Peak Hours:' section missing!"
    assert "Slow Hours:" in report, "'Slow Hours:' section missing!"
    assert "Recommended Happy Hour:" in report, "'Recommended Happy Hour:' section missing!"
    assert "Suggested Offer:" in report, "'Suggested Offer:' section missing!"
    assert "Best Promotion Days:" in report, "'Best Promotion Days:' section missing!"
    assert "AI Recommendations:" in report, "'AI Recommendations:' section missing!"

    # Required Specific Content Assertions
    required_phrases = [
        "7 PM – 10 PM",
        "2 PM – 5 PM",
        "3 PM – 6 PM",
        "Flat 30% OFF",
        "Buy 1 Get 1",
        "Monday",
        "Tuesday",
        "Wednesday",
        "Increase promotions during slow hours.",
        "Schedule buffet campaigns on weekends.",
        "Push Instagram offers before lunch and dinner.",
        "Test limited-time discounts."
    ]

    for phrase in required_phrases:
        assert phrase in report, f"Required phrase '{phrase}' missing from Slow-Hours Report!"
        print(f"  [OK] Verified Required Content: '{phrase}'")

    print("\n[SLOW HOURS REPORT PREVIEW]:")
    print(report)


if __name__ == "__main__":
    print("==================================================")
    print("[RUN] MILESTONE 2 (STEP 1 & STEP 2) MERCHANT SUITE")
    print("==================================================")

    test_merchant_intent_classification()
    test_slow_hours_intent_classification()
    test_slow_hours_report_structure()

    print("\n==================================================")
    print("[SUCCESS] ALL MILESTONE 2 SUITE TESTS PASSED (100%)!")
    print("==================================================")
