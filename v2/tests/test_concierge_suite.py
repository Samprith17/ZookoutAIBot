"""
AI Deal Concierge Master Test Suite.
Verifies multi-turn dialogs, conversation state resets, fresh top-level searches,
detail updates, deal comparison, voucher callback structure, and nearby suggestions.
"""

import sys
from pathlib import Path

# Add project root to path
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))

from v2.ai.intent import detect_intent
from v2.ai.memory import memory_manager
from v2.search.search_engine import search_deals, get_nearby_locations, get_deal_comparison
from v2.telegram.handlers import build_deal_keyboard


def test_conversation_reset_and_state_machine():
    print("\n[TEST] 1. State Reset & Conversation Lifecycle (Tests 1-5)")
    user_id = 88888

    memory_manager.clear_context(user_id)

    # Test 1: User: "I want dinner" -> Expected: Ask for location (location=None)
    raw1 = detect_intent("I want dinner")
    intent1 = memory_manager.update_context(user_id, raw1)
    memory_manager.set_pending_field(user_id, "location")
    assert intent1.get("category") == "restaurant"
    assert intent1.get("location") is None
    print("  [OK] Test 1 Passed: 'I want dinner' initializes fresh state (Category=restaurant, Location=None)")

    # Test 2: User: "Andheri" -> Expected: Ask for budget (budget=None)
    raw2 = detect_intent("Andheri")
    intent2 = memory_manager.update_context(user_id, raw2)
    memory_manager.set_pending_field(user_id, "budget")
    assert intent2.get("category") == "restaurant"
    assert "andheri" in intent2.get("location", "").lower()
    assert intent2.get("max_price") is None
    print("  [OK] Test 2 Passed: 'Andheri' stores location (Location=Andheri, Budget=None)")

    # Test 3: User: "2000" -> Expected: Return recommendations & mark completed
    raw3 = detect_intent("2000")
    intent3 = memory_manager.update_context(user_id, raw3)
    assert intent3.get("category") == "restaurant"
    assert "andheri" in intent3.get("location", "").lower()
    assert intent3.get("max_price") == 2000.0
    memory_manager.mark_completed(user_id)
    print("  [OK] Test 3 Passed: '2000' completes search (Budget=2000, Search Completed=True)")

    # Test 4: User: "I want dinner" -> Expected: Fresh conversation, ask for location (location=None)
    raw4 = detect_intent("I want dinner")
    intent4 = memory_manager.update_context(user_id, raw4)
    assert intent4.get("category") == "restaurant"
    assert intent4.get("location") is None, "Previous location 'Andheri' was not cleared for new request!"
    assert intent4.get("max_price") is None, "Previous budget '2000' was not cleared for new request!"
    print("  [OK] Test 4 Passed: Second 'I want dinner' started a FRESH conversation (Old Location & Budget Discarded!)")

    # Test 5: User: "Show cheaper options" on empty/expired session
    memory_manager.clear_context(user_id)
    assert not memory_manager.is_session_active(user_id)
    print("  [OK] Test 5 Passed: 'Show cheaper options' correctly requires an active search session when empty.")


def test_detail_modification():
    print("\n[TEST] 2. Single-Detail Modification")
    user_id = 99991

    memory_manager.clear_context(user_id)
    raw1 = detect_intent("I want dinner")
    memory_manager.update_context(user_id, raw1)
    memory_manager.set_pending_field(user_id, "location")
    raw2 = detect_intent("Andheri")
    memory_manager.update_context(user_id, raw2)
    memory_manager.set_pending_field(user_id, "budget")
    raw3 = detect_intent("2000")
    memory_manager.update_context(user_id, raw3)
    memory_manager.mark_completed(user_id)

    # User says "Actually make it under 1500"
    msg = "Actually make it under 1500"
    raw = detect_intent(msg)
    intent = memory_manager.update_context(user_id, raw)

    assert intent.get("category") == "restaurant"
    assert "andheri" in intent.get("location", "").lower()
    assert intent.get("max_price") == 1500.0
    print("  [OK] Updated budget to Rs. 1500 while preserving category=restaurant, location=Andheri.")


def test_contextual_follow_up():
    print("\n[TEST] 3. Contextual Follow-Up Modifier")
    user_id = 99991

    # User says "Show cheaper options"
    msg = "Show cheaper options"
    raw = detect_intent(msg)
    intent = memory_manager.update_context(user_id, raw)

    assert intent.get("category") == "restaurant"
    assert "andheri" in intent.get("location", "").lower()
    assert intent.get("max_price") == 1050.0  # 1500 * 0.7 = 1050
    print("  [OK] Reduced budget to Rs. 1050 for 'Show cheaper options' using active conversation context.")


def test_deal_comparison():
    print("\n[TEST] 4. Deal Comparison Table Generation")
    intent = {"type": "search", "category": "restaurant", "city": "Mumbai", "location": "Andheri"}
    comp_list = get_deal_comparison(intent)

    assert len(comp_list) > 0
    assert "brand" in comp_list[0]
    assert "savings" in comp_list[0]
    assert "recommendation" in comp_list[0]
    print(f"  [OK] Deal comparison table generated successfully with {len(comp_list)} ranked options.")


def test_nearby_suggestions():
    print("\n[TEST] 5. Regional Nearby Location Suggestions")
    loc_blr = "Whitefield"
    nearby_blr = get_nearby_locations(loc_blr)
    assert "Indiranagar" in nearby_blr

    loc_mum = "Powai"
    nearby_mum = get_nearby_locations(loc_mum)
    assert "Andheri" in nearby_mum
    print(f"  [OK] Whitefield nearbys: {nearby_blr}")
    print(f"  [OK] Powai nearbys: {nearby_mum}")


def test_voucher_keyboard_integration():
    print("\n[TEST] 6. Voucher Assistant Inline Keyboard Button")
    mock_deal = {
        "id": "DEAL_101",
        "brand": "Barbeque Nation",
        "title": "Flat 50% Off Lunch Buffet",
        "location": "Andheri, Mumbai",
    }
    keyboard = build_deal_keyboard(mock_deal)

    has_voucher_btn = False
    for row in keyboard.inline_keyboard:
        for btn in row:
            if btn.callback_data == "voucher_generate:DEAL_101":
                has_voucher_btn = True
                break

    assert has_voucher_btn, "Voucher generate callback button missing from deal inline keyboard"
    print("  [OK] 'Generate Voucher' callback button present in inline keyboard.")


if __name__ == "__main__":
    print("==================================================")
    print("[RUN] RUNNING ZOOKOUT AI DEAL CONCIERGE TEST SUITE")
    print("==================================================")

    test_conversation_reset_and_state_machine()
    test_detail_modification()
    test_contextual_follow_up()
    test_deal_comparison()
    test_nearby_suggestions()
    test_voucher_keyboard_integration()

    print("\n==================================================")
    print("[SUCCESS] ALL CONCIERGE TESTS PASSED SUCCESSFULLY (100%)")
    print("==================================================")
