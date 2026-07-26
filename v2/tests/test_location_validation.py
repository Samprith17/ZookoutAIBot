import sys
import logging

sys.stdout.reconfigure(encoding='utf-8')

from v2.ai.intent import detect_intent
from v2.search.search_engine import search_deals, load_deals
from v2.ai.analytics import analytics_engine

logging.basicConfig(level=logging.ERROR)


def run_location_validation_tests():
    print("=" * 80)
    print("LOCATION CONSISTENCY & PRODUCTION VALIDATION TEST SUITE")
    print("=" * 80)

    all_deals = load_deals()
    print(f"Total Raw Deals Loaded: {len(all_deals)}")

    # Test Queries List from User Prompt
    test_queries = [
        ("Deals in Mumbai", "search", True, len(all_deals)),
        ("Deals in Andheri", "search", True, None),
        ("Deals in Bandra", "search", True, None),
        ("Deals in Powai", "search", False, None),
        ("Deals in Koramangala", "search", False, 0),
        ("Restaurants in Mumbai", "search", True, None),
        ("Restaurants in Andheri", "search", False, None),
        ("Spa in Mumbai", "search", True, None),
        ("Spa in Andheri", "search", True, None),
    ]

    print("\n--- 1. VERIFYING SEARCH QUERIES ---")
    for query, expected_type, expect_results, expected_count in test_queries:
        intent = detect_intent(query)
        results = search_deals(intent)
        count = len(results)

        loc_extracted = intent.get("location") or intent.get("area") or intent.get("city")

        print(f"QUERY: {query:25} | INTENT: {intent['type']:8} | LOC: {str(loc_extracted):12} | RESULTS: {count:3} deals")

        assert intent["type"] == expected_type, f"Expected intent '{expected_type}' for '{query}', got '{intent['type']}'"

        if expected_count is not None:
            assert count == expected_count, f"Expected exactly {expected_count} deals for '{query}', got {count}"

        if expect_results:
            assert count > 0, f"Expected results > 0 for '{query}', got 0"
            for d in results:
                # Verify location formatting
                display_loc = d.get("display_location", "")
                assert display_loc, "display_location must not be empty"

                # Verify sub-area isolation for Andheri
                if "Andheri" in query:
                    assert "Andheri" in display_loc, f"Non-Andheri deal returned for '{query}': {d}"

    print("✅ ALL SEARCH LOCATION QUERIES PASSED 100%!")

    # 2. Verify Analytics & Business Dashboard Location Consistency
    print("\n--- 2. VERIFYING BUSINESS DASHBOARD & ANALYTICS ---")
    dash = analytics_engine.generate_business_dashboard()
    summary = analytics_engine.generate_catalog_summary()
    loc_analytics = analytics_engine.generate_location_analytics()

    print("Business Dashboard Output snippet:")
    print("\n".join(dash.split("\n")[:6]))

    assert "Total Locations:" in dash, "Dashboard must contain 'Total Locations:'"
    assert "Cities:" in dash, "Dashboard must contain 'Cities:' count"
    assert "Areas:" in dash, "Dashboard must contain 'Areas:' count"

    # Extract location metric from dashboard and summary
    dash_loc_line = [line for line in dash.split("\n") if "Total Locations:" in line][0]
    summary_loc_line = [line for line in summary.split("\n") if "Total Locations:" in line][0]

    print(f"\nDashboard Location Line: {dash_loc_line}")
    print(f"Summary Location Line:   {summary_loc_line}")

    assert dash_loc_line.split(":")[-1].strip() == summary_loc_line.split(":")[-1].strip(), "Dashboard and Summary location counts must match!"

    print("\n==========================================================================")
    print("ALL PRODUCTION LOCATION CONSISTENCY TESTS PASSED 100%!")
    print("==========================================================================")


if __name__ == "__main__":
    run_location_validation_tests()
