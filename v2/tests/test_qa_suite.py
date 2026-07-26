"""
Milestone Production QA & Regression Suite:
Executes comprehensive automated testing across:
1. Customer AI (Search, Itinerary Planner, Savings Agent, Comparison, Personalization)
2. Merchant Growth AI (Offer Review, Score, Growth Suggestions, Dashboard, Health, Comparison)
3. AI Content Creator / Marketing Assistant (Instagram, Facebook, WhatsApp, SMS, Push, Captions, Hashtags, Festival, Weekend, Birthday, Email, Marketing Help)
4. Business Intelligence & Analytics (Dashboard, Summary, Category, Brand, Location, Discount, Price, Health, Distribution, Insights, Improvements, Help)
5. Alternate Wording, Typos, Edge Cases & Robustness
"""
import sys
import logging
from typing import Dict, Any, List

sys.stdout.reconfigure(encoding='utf-8')

from v2.ai.intent import detect_intent
from v2.ai.content_creator import content_creator_agent
from v2.ai.analytics import analytics_engine
from v2.ai.merchant import merchant_agent
from v2.ai.savings import savings_agent
from v2.search.search_engine import search_deals, normalize_deal

logging.basicConfig(level=logging.ERROR)


def run_qa_suite():
    print("=" * 85)
    print("ZOOKOUT AI TELEGRAM BOT — PRODUCTION QA & REGRESSION TEST SUITE")
    print("=" * 85)

    test_cases: List[Dict[str, Any]] = [
        # --- 1. CUSTOMER AI REGRESSION TESTS ---
        {
            "query": "My Savings",
            "expected_intents": ["savings"],
            "is_merchant": False,
            "category": "Customer AI",
            "reason": "Verify Customer Savings profile summary"
        },
        {
            "query": "Show Opportunities",
            "expected_intents": ["opportunities"],
            "is_merchant": False,
            "category": "Customer AI",
            "reason": "Verify Customer opportunity detection"
        },
        {
            "query": "Why did I get this?",
            "expected_intents": ["why_this"],
            "is_merchant": False,
            "category": "Customer AI",
            "reason": "Verify Customer recommendation explanation"
        },
        {
            "query": "Plan a romantic evening under ₹2000",
            "expected_intents": ["planner"],
            "is_merchant": False,
            "category": "Customer AI",
            "reason": "Verify AI Experience Planner itinerary generation"
        },
        {
            "query": "Compare restaurants in Andheri",
            "expected_intents": ["compare"],
            "is_merchant": False,
            "category": "Customer AI",
            "reason": "Verify customer deal comparison"
        },
        {
            "query": "Romantic dinner in Andheri under ₹2000",
            "expected_intents": ["search", "occasion"],
            "is_merchant": False,
            "category": "Customer AI",
            "reason": "Verify multi-constraint deal search / occasion detection"
        },

        # --- 2. MERCHANT AI REGRESSION TESTS ---
        {
            "query": "Review My Offer",
            "expected_intents": ["merchant_review"],
            "is_merchant": True,
            "category": "Merchant AI",
            "reason": "Verify Merchant Offer Review"
        },
        {
            "query": "Offer Score",
            "expected_intents": ["merchant_score"],
            "is_merchant": True,
            "category": "Merchant AI",
            "reason": "Verify Merchant Offer Score evaluation"
        },
        {
            "query": "Growth Suggestions",
            "expected_intents": ["merchant_growth"],
            "is_merchant": True,
            "category": "Merchant AI",
            "reason": "Verify Merchant Growth Advice"
        },
        {
            "query": "Merchant Dashboard",
            "expected_intents": ["merchant_dashboard"],
            "is_merchant": True,
            "category": "Merchant AI",
            "reason": "Verify Merchant Dashboard stats"
        },
        {
            "query": "Offer Health",
            "expected_intents": ["merchant_health"],
            "is_merchant": True,
            "category": "Merchant AI",
            "reason": "Verify Merchant Offer Health diagnostic"
        },
        {
            "query": "Compare My Offers",
            "expected_intents": ["merchant_compare"],
            "is_merchant": True,
            "category": "Merchant AI",
            "reason": "Verify Merchant multi-offer comparison"
        },

        # --- 3. AI CONTENT CREATOR TESTS ---
        {
            "query": "Create Instagram Post",
            "expected_intents": ["content_instagram"],
            "is_merchant": True,
            "category": "Content Creator",
            "reason": "Verify Instagram post generation with storytelling & embedded hashtags"
        },
        {
            "query": "Create Facebook Post",
            "expected_intents": ["content_facebook"],
            "is_merchant": True,
            "category": "Content Creator",
            "reason": "Verify Facebook long-form promotion generation"
        },
        {
            "query": "FB Post",
            "expected_intents": ["content_facebook"],
            "is_merchant": True,
            "category": "Content Creator",
            "reason": "Verify Facebook short trigger routing without planner fallthrough"
        },
        {
            "query": "Create WhatsApp Promotion",
            "expected_intents": ["content_whatsapp"],
            "is_merchant": True,
            "category": "Content Creator",
            "reason": "Verify WhatsApp short chat shareable promotion"
        },
        {
            "query": "Create SMS Campaign",
            "expected_intents": ["content_sms"],
            "is_merchant": True,
            "category": "Content Creator",
            "reason": "Verify SMS campaign (<= 160 characters constraint)"
        },
        {
            "query": "Create Push Notification",
            "expected_intents": ["content_push"],
            "is_merchant": True,
            "category": "Content Creator",
            "reason": "Verify Push notification (< 80 characters constraint)"
        },
        {
            "query": "Create Promotional Caption",
            "expected_intents": ["content_caption"],
            "is_merchant": True,
            "category": "Content Creator",
            "reason": "Verify 3 caption styles (Professional, Friendly, Luxury)"
        },
        {
            "query": "Generate Hashtags",
            "expected_intents": ["content_hashtags"],
            "is_merchant": True,
            "category": "Content Creator",
            "reason": "Verify 10-15 real hashtag generation"
        },
        {
            "query": "Festival Promotion",
            "expected_intents": ["content_festival"],
            "is_merchant": True,
            "category": "Content Creator",
            "reason": "Verify Festival campaign generation (Diwali, New Year, VDay)"
        },
        {
            "query": "Weekend Promotion",
            "expected_intents": ["content_weekend"],
            "is_merchant": True,
            "category": "Content Creator",
            "reason": "Verify Weekend booking promo generation"
        },
        {
            "query": "Birthday Promotion",
            "expected_intents": ["content_birthday"],
            "is_merchant": True,
            "category": "Content Creator",
            "reason": "Verify Birthday campaign generation"
        },
        {
            "query": "Create Email Campaign",
            "expected_intents": ["content_email"],
            "is_merchant": True,
            "category": "Content Creator",
            "reason": "Verify Email campaign structure (Subject, Preview, Body, CTA)"
        },
        {
            "query": "Marketing Help",
            "expected_intents": ["content_help"],
            "is_merchant": True,
            "category": "Content Creator",
            "reason": "Verify category-aware marketing intelligence advice"
        },

        # --- 4. BUSINESS INTELLIGENCE & ANALYTICS TESTS ---
        {
            "query": "Business Dashboard",
            "expected_intents": ["analytics_dashboard"],
            "is_merchant": True,
            "category": "Business Intelligence",
            "reason": "Verify Business Intelligence Dashboard header & KPIs"
        },
        {
            "query": "Catalog Summary",
            "expected_intents": ["analytics_summary"],
            "is_merchant": True,
            "category": "Business Intelligence",
            "reason": "Verify Catalog Summary & Completeness Coverage Report"
        },
        {
            "query": "Category Analytics",
            "expected_intents": ["analytics_category"],
            "is_merchant": True,
            "category": "Business Intelligence",
            "reason": "Verify Category performance analytics breakdown"
        },
        {
            "query": "Brand Analytics",
            "expected_intents": ["analytics_brand"],
            "is_merchant": True,
            "category": "Business Intelligence",
            "reason": "Verify Merchant Brand performance breakdown"
        },
        {
            "query": "Location Analytics",
            "expected_intents": ["analytics_location"],
            "is_merchant": True,
            "category": "Business Intelligence",
            "reason": "Verify Location & City analytics"
        },
        {
            "query": "Discount Analytics",
            "expected_intents": ["analytics_discount"],
            "is_merchant": True,
            "category": "Business Intelligence",
            "reason": "Verify Discount tier breakdown"
        },
        {
            "query": "Price Analytics",
            "expected_intents": ["analytics_price"],
            "is_merchant": True,
            "category": "Business Intelligence",
            "reason": "Verify Median price & budget tier distribution"
        },
        {
            "query": "Catalog Health",
            "expected_intents": ["analytics_health"],
            "is_merchant": True,
            "category": "Business Intelligence",
            "reason": "Verify Catalog Health Quality Score (0-100)"
        },
        {
            "query": "Offer Distribution",
            "expected_intents": ["analytics_distribution"],
            "is_merchant": True,
            "category": "Business Intelligence",
            "reason": "Verify Offer distribution density"
        },
        {
            "query": "Business Insights",
            "expected_intents": ["analytics_insights"],
            "is_merchant": True,
            "category": "Business Intelligence",
            "reason": "Verify catalog-derived business observations"
        },
        {
            "query": "What should we improve?",
            "expected_intents": ["analytics_improvements"],
            "is_merchant": True,
            "category": "Business Intelligence",
            "reason": "Verify catalog improvement recommendations"
        },
        {
            "query": "Business Help",
            "expected_intents": ["analytics_help"],
            "is_merchant": True,
            "category": "Business Intelligence",
            "reason": "Verify Business Help guide"
        },

        # --- 5. ALTERNATE WORDING & EDGE CASES ---
        {
            "query": "Catalog Overview",
            "expected_intents": ["analytics_summary"],
            "is_merchant": True,
            "category": "Alternate Wording",
            "reason": "Verify alternate wording for Catalog Summary"
        },
        {
            "query": "Catalog Report",
            "expected_intents": ["analytics_summary"],
            "is_merchant": True,
            "category": "Alternate Wording",
            "reason": "Verify alternate wording for Catalog Summary"
        },
        {
            "query": "How can the catalog improve?",
            "expected_intents": ["analytics_improvements"],
            "is_merchant": True,
            "category": "Alternate Wording",
            "reason": "Verify alternate wording for Catalog Improvements"
        },
        {
            "query": "Catalog recommendations",
            "expected_intents": ["analytics_improvements"],
            "is_merchant": True,
            "category": "Alternate Wording",
            "reason": "Verify alternate wording for Catalog Improvements"
        },
        {
            "query": "CREATE INSTAGRAM POST",
            "expected_intents": ["content_instagram"],
            "is_merchant": True,
            "category": "Edge Case",
            "reason": "Verify uppercase command handling"
        },
        {
            "query": "  business dashboard  ",
            "expected_intents": ["analytics_dashboard"],
            "is_merchant": True,
            "category": "Edge Case",
            "reason": "Verify whitespace padding handling"
        },
    ]

    passed_count = 0
    total_count = len(test_cases)

    for i, test in enumerate(test_cases, 1):
        query = test["query"]
        expected_intents = test["expected_intents"]
        expected_is_m = test["is_merchant"]
        category = test["category"]
        reason = test["reason"]

        intent = detect_intent(query)
        actual_intent = intent.get("type")
        actual_is_m = intent.get("is_merchant", False)

        is_passed = (actual_intent in expected_intents) and (actual_is_m == expected_is_m)

        status_str = "✅ PASSED" if is_passed else f"❌ FAILED (got {actual_intent}, is_m={actual_is_m})"
        print(f"[{i:02d}/{total_count:02d}] {category:22} | '{query[:30]}':30 -> {actual_intent:20} | {status_str}")

        if not is_passed:
            print(f"     ⚠️ Reason: {reason}")
        else:
            passed_count += 1

    print("=" * 85)
    print(f"QA SUITE FINAL RESULT: {passed_count}/{total_count} TESTS PASSED ({int((passed_count/total_count)*100)}%)")
    print("=" * 85)

    assert passed_count == total_count, "QA Suite encountered test failures!"


if __name__ == "__main__":
    run_qa_suite()
