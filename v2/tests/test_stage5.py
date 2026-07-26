import sys
import logging

sys.stdout.reconfigure(encoding='utf-8')

from v2.ai.intent import detect_intent
from v2.search.search_engine import search_deals
from v2.telegram.bot import generate_no_deals_response

logging.basicConfig(level=logging.ERROR)


def run_stage5_tests():
    print('=' * 80)
    print('STAGE 5 SEARCH INTELLIGENCE & LOCATION UNDERSTANDING VALIDATION')
    print('=' * 80)

    # Task 1: Location-Only Intent Detection
    location_queries = ['Bandra', 'Andheri', 'Powai', 'Juhu', 'Pune', 'Aundh', 'Kota', 'Dadabari', 'Parihar Chowk', 'Deals in Bandra', 'Deals in Kota']

    print('\n--- TASK 1: LOCATION-ONLY INTENT DETECTION ---')
    for q in location_queries:
        intent = detect_intent(q)
        itype = intent['type']
        loc = intent.get('location') or intent.get('area') or intent.get('city')
        status = '✅ PASSED' if itype == 'search' and loc is not None else f'❌ FAILED (got {itype}, loc={loc})'
        print(f'QUERY: {q:20} -> TYPE: {itype:10} | LOC: {str(loc):15} | STATUS: {status}')
        assert itype == 'search' and loc is not None, f'Location intent detection failed for {q}'

    print('✅ TASK 1 PASSED 100%!')

    # Task 2: Stop Incorrect Mumbai Fallback
    print('\n--- TASK 2: STOP INCORRECT MUMBAI FALLBACK ---')
    kota_intent = detect_intent('Deals in Kota')
    kota_results = search_deals(kota_intent)
    print(f'Query: "Deals in Kota" -> search_deals() returned {len(kota_results)} deals')
    assert len(kota_results) == 0, 'Incorrectly returned deals for non-existent location Kota!'
    print('✅ TASK 2 PASSED 100%!')

    # Task 3: Natural Language Search Relevance
    print('\n--- TASK 3: NATURAL LANGUAGE SEARCH RELEVANCE ---')
    nl_query = 'buffet in Andheri under 500'
    nl_intent = detect_intent(nl_query)
    nl_results = search_deals(nl_intent)
    print(f'Query: "{nl_query}" -> {len(nl_results)} deals returned')
    for d in nl_results[:2]:
        print(f' - {d["brand"]}: {d["clean_title"]} at {d["formatted_price"]} ({d["display_location"]})')
    assert len(nl_results) > 0, 'No deals returned for valid natural language query'
    print('✅ TASK 3 PASSED 100%!')

    # Task 4: Dataset-Aware No Deals Response
    print('\n--- TASK 4: DATASET-AWARE NO DEALS RESPONSE ---')
    no_deals_msg = generate_no_deals_response(kota_intent)
    print(no_deals_msg)
    assert '🔍 No Deals Found for "Deals in Kota"' in no_deals_msg, 'Missing header in no deals response'
    assert 'Locations Available' in no_deals_msg, 'Missing active locations overview'
    assert 'Categories Available' in no_deals_msg, 'Missing active categories overview'
    print('✅ TASK 4 PASSED 100%!')

    print('\n===========================================================================')
    print('STAGE 5 SEARCH INTELLIGENCE & LOCATION UNDERSTANDING VERIFIED 100%')
    print('===========================================================================')


if __name__ == "__main__":
    run_stage5_tests()
