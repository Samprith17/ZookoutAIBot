from v2.search.search_engine import search_deals
while True:
    query = input("Search: ")

    results = search_deals(query)

    if not results:
        print("❌ No deals found.")
        continue

    print(f"\n✅ Found {len(results)} deal(s)\n")

    for deal in results[:5]:
        print("=" * 50)
        print("Brand:", deal.get("brand"))
        print("Category:", deal.get("category"))
        print("Title:", deal.get("title"))
        print("Price:", deal.get("price"))
        print("Discount:", deal.get("discount_percent"))
        print("Location:", deal.get("location"))
        print("Website:", deal.get("website"))
        print("Score:", deal.get("score"))
        print("=" * 50)