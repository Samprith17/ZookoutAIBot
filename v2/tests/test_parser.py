import unittest
from pathlib import Path
import json

from v2.parser import (
    extract_brand,
    extract_category,
    extract_offer,
    extract_price,
    extract_title,
    parse_all,
    parse_deal,
)


class TestParser(unittest.TestCase):
    def test_extract_brand_from_url(self):
        url = "https://zookout.com/mumbai/brand/sydewok-restaurant-hotel-suba-galaxy-696237178f4b81468c8aef0c-69623c14927a075021c38d5a"
        self.assertEqual(extract_brand("Sample deal text", url), "Sydewok Suba Galaxy")

    def test_extract_category_from_text(self):
        text = "Buy 1 Dinner Buffet, Get 1 FREE - worth ₹2242 now ₹1121"
        self.assertEqual(extract_category(text, ""), "Restaurant")

    def test_extract_price_offer_title(self):
        text = "1 SHyodteelw Soukb Ra eGsatalauxryant - Restaurant Offline At Restaurant - Buy 1 Dinner Buffet, Get 1 FREE - worth ₹2242 now ₹1121"
        self.assertEqual(extract_price(text), 1121)
        self.assertTrue(extract_offer(text).lower().startswith("buy 1 dinner buffet"))
        self.assertIn("dinner", extract_title(text, "", "Restaurant").lower())

    def test_parse_deal_structures_expected_fields(self):
        raw = {
            "url": "https://zookout.com/mumbai/brand/sydewok-restaurant-hotel-suba-galaxy-696237178f4b81468c8aef0c-69623c14927a075021c38d5a",
            "text": "1 SHyodteelw Soukb Ra eGsatalauxryant - Restaurant Offline At Restaurant - Buy 1 Dinner Buffet, Get 1 FREE - worth ₹2242 now ₹1121",
        }
        deal = parse_deal(raw, 1)
        self.assertEqual(deal.id, 1)
        self.assertEqual(deal.brand, "Sydewok Suba Galaxy")
        self.assertEqual(deal.merchant, "Sydewok Suba Galaxy")
        self.assertEqual(deal.category, "Restaurant")
        self.assertEqual(deal.price, 1121)
        self.assertEqual(deal.original_price, 2242)
        self.assertIn(deal.discount_percent, {49, 50})
        self.assertTrue(deal.offer)
        self.assertTrue(deal.title)

    def test_parse_all_returns_non_empty_list(self):
        deals = parse_all()
        self.assertIsInstance(deals, list)
        self.assertGreater(len(deals), 0)
        self.assertTrue(all(hasattr(deal, 'brand') for deal in deals))


if __name__ == '__main__':
    unittest.main()
