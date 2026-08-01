"""
Milestone 2 – Merchant Growth Agent (Step 1) Regression Test Suite.
Verifies:
✓ Assertion 1: Merchant intent triggers classify correctly (Merchant Dashboard, Business Dashboard, Merchant Insights, Growth Report, Business Report).
✓ Assertion 2: Merchant Growth Report contains all required fields:
  - Total offers available
  - Average discount
  - Categories available
  - Price range
  - Top-performing offers (based on weighted ranking logic)
  - Suggested improvements (slow hours, limited-time 50%, buffet on weekends, improve generic titles, high-value offers)
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
    print("\n[TEST 1] Testing Merchant Intent Triggers Classification")

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
        print(f"  [OK] Trigger: '{trigger_text}' -> Classified as '{intent.get('type')}'")


def test_merchant_growth_report_structure():
    print("\n[TEST 2] Testing Merchant Growth Report Required Fields & Output")

    agent = MerchantGrowthAgent()
    report = agent.generate_merchant_growth_report()

    # Required Field Assertions
    assert "📊 Merchant Growth Report" in report, "Report header missing!"
    assert "• Total offers available:" in report, "'Total offers available' field missing!"
    assert "• Average discount:" in report, "'Average discount' field missing!"
    assert "• Categories available:" in report, "'Categories available' field missing!"
    assert "• Price range:" in report, "'Price range' field missing!"
    assert "• Top-performing offers" in report, "'Top-performing offers' section missing!"
    assert "• Suggested improvements:" in report, "'Suggested improvements' section missing!"

    # Required Suggested Improvements Assertions
    required_suggestions = [
        "Increase visibility during slow hours.",
        "Run limited-time 50% offers.",
        "Promote buffet deals on weekends.",
        "Improve offer titles if they are generic.",
        "Add more high-value offers in popular categories."
    ]

    for sg in required_suggestions:
        assert sg in report, f"Required suggestion '{sg}' missing from report!"
        print(f"  [OK] Verified Suggestion: '{sg}'")

    print("\n[REPORT PREVIEW]:")
    print(report)


if __name__ == "__main__":
    print("==================================================")
    print("[RUN] MILESTONE 2 - MERCHANT GROWTH AGENT SUITE")
    print("==================================================")

    test_merchant_intent_classification()
    test_merchant_growth_report_structure()

    print("\n==================================================")
    print("[SUCCESS] ALL MILESTONE 2 MERCHANT SUITE TESTS PASSED (100%)!")
    print("==================================================")
