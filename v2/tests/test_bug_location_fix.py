import sys
import logging

sys.stdout.reconfigure(encoding='utf-8')

from v2.ai.intent import detect_intent
from v2.ai.memory import memory_manager
from v2.search.search_engine import search_deals
from v2.telegram.bot import generate_no_deals_response

logging.basicConfig(level=logging.ERROR)


def run_sequential_location_bug_tests():
    print("=" * 80)
    print("SEQUENTIAL LOCATION STATE BUG VALIDATION TEST SUITE")
    print("=" * 80)

    user_id = 99999
    memory_manager.clear_context(user_id)

    # 1. Spa in Andheri
    msg1 = "Spa in Andheri"
    raw_intent1 = detect_intent(msg1)
    intent1 = memory_manager.update_context(user_id, raw_intent1)
    loc1 = intent1.get("location") or intent1.get("area")
    cat1 = intent1.get("category")
    no_deals_1 = generate_no_deals_response(raw_intent1)

    print(f"\n1. Message: '{msg1}'")
    print(f"   Intent Location: {loc1} | Category: {cat1}")
    print(f"   No Deals Response Line: {[l for l in no_deals_1.splitlines() if 'No Deals Found' in l or 'Location' in l][0]}")

    assert loc1 == "Andheri", f"Expected Location 'Andheri', got '{loc1}'"
    assert cat1 == "spa", f"Expected Category 'spa', got '{cat1}'"
    assert "Location: Andheri" in no_deals_1, "No Deals response must show Location: Andheri"

    # 2. Restaurants in Bandra (Must NOT reuse Andheri in criteria!)
    msg2 = "Restaurants in Bandra"
    raw_intent2 = detect_intent(msg2)
    intent2 = memory_manager.update_context(user_id, raw_intent2)
    loc2 = intent2.get("location") or intent2.get("area")
    cat2 = intent2.get("category")
    no_deals_2 = generate_no_deals_response(raw_intent2)

    print(f"\n2. Message: '{msg2}'")
    print(f"   Intent Location: {loc2} | Category: {cat2}")
    print(f"   No Deals Response Line: {[l for l in no_deals_2.splitlines() if 'No Deals Found' in l or 'Location' in l][0]}")

    assert loc2 == "Bandra", f"Expected Location 'Bandra', got '{loc2}'"
    assert cat2 == "restaurant", f"Expected Category 'restaurant', got '{cat2}'"
    assert "(Category: Restaurant, Location: Bandra)" in no_deals_2, "No Deals response must show Location: Bandra (NOT Andheri!)"

    # 3. Deals in Mumbai
    msg3 = "Deals in Mumbai"
    raw_intent3 = detect_intent(msg3)
    intent3 = memory_manager.update_context(user_id, raw_intent3)
    loc3 = intent3.get("location") or intent3.get("city")

    print(f"\n3. Message: '{msg3}'")
    print(f"   Intent Location: {loc3}")
    assert loc3 == "Mumbai", f"Expected Location 'Mumbai', got '{loc3}'"

    # 4. Restaurants in Powai
    msg4 = "Restaurants in Powai"
    raw_intent4 = detect_intent(msg4)
    intent4 = memory_manager.update_context(user_id, raw_intent4)
    loc4 = intent4.get("location") or intent4.get("area")
    cat4 = intent4.get("category")
    no_deals_4 = generate_no_deals_response(raw_intent4)

    print(f"\n4. Message: '{msg4}'")
    print(f"   Intent Location: {loc4} | Category: {cat4}")
    print(f"   No Deals Response Line: {[l for l in no_deals_4.splitlines() if 'No Deals Found' in l or 'Location' in l][0]}")

    assert loc4 == "Powai", f"Expected Location 'Powai', got '{loc4}'"
    assert cat4 == "restaurant", f"Expected Category 'restaurant', got '{cat4}'"
    assert "(Category: Restaurant, Location: Powai)" in no_deals_4, "No Deals response must show Location: Powai"

    # 5. Spa in Juhu
    msg5 = "Spa in Juhu"
    raw_intent5 = detect_intent(msg5)
    intent5 = memory_manager.update_context(user_id, raw_intent5)
    loc5 = intent5.get("location") or intent5.get("area")
    cat5 = intent5.get("category")
    no_deals_5 = generate_no_deals_response(raw_intent5)

    print(f"\n5. Message: '{msg5}'")
    print(f"   Intent Location: {loc5} | Category: {cat5}")
    print(f"   No Deals Response Line: {[l for l in no_deals_5.splitlines() if 'No Deals Found' in l or 'Location' in l][0]}")

    assert loc5 == "Juhu", f"Expected Location 'Juhu', got '{loc5}'"
    assert cat5 == "spa", f"Expected Category 'spa', got '{cat5}'"
    assert "(Category: Spa, Location: Juhu)" in no_deals_5, "No Deals response must show Location: Juhu"

    print("\n==========================================================================")
    print("ALL 5 SEQUENTIAL LOCATION STATE BUG TESTS PASSED 100%!")
    print("==========================================================================")


if __name__ == "__main__":
    run_sequential_location_bug_tests()
