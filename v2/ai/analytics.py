import logging
import statistics
from typing import Dict, List, Any
from collections import Counter
from v2.search.search_engine import normalize_deal
from v2.ai.merchant import merchant_agent

logger = logging.getLogger(__name__)


class BusinessAnalyticsEngine:
    """
    Milestone 15 - AI-Powered Business Intelligence & Analytics Engine:
    Analyzes normalized catalog datasets dynamically and generates data-backed business insights,
    catalog health diagnostics, category/brand/location/price analytics, and improvement suggestions.
    Strict Rule: Uses strictly normalized catalog data; never invents revenue, profit, bookings, CTR, or conversion rates.
    """

    def get_dataset(self) -> List[Dict[str, Any]]:
        """Retrieves normalized merchant dataset (reuses merchant_agent.get_merchant_dataset())."""
        return merchant_agent.get_merchant_dataset()

    def generate_business_dashboard(self) -> str:
        """FEATURE 1: Business Dashboard."""
        dataset = self.get_dataset()
        total_offers = len(dataset)

        brands = {d.get("brand") for d in dataset if d.get("brand")}
        categories = {d.get("display_category") for d in dataset if d.get("display_category")}
        locations = {d.get("display_location") for d in dataset if d.get("display_location")}

        priced_deals = [d for d in dataset if float(str(d.get("price", "0")).replace(",", "")) > 0]
        prices = [float(str(d.get("price", "0")).replace(",", "")) for d in priced_deals]

        avg_price = int(sum(prices) / max(1, len(prices))) if prices else 0
        min_price = int(min(prices)) if prices else 0
        max_price = int(max(prices)) if prices else 0

        discounts = [d.get("discount_percent", 0) for d in dataset]
        avg_discount = int(sum(discounts) / max(1, total_offers))
        max_discount = max(discounts) if discounts else 0

        scores = [merchant_agent.evaluate_offer_score(d)["total_score"] for d in dataset]
        avg_score = int(sum(scores) / max(1, len(scores)))

        return (
            "📊 Business Intelligence Dashboard\n\n"
            f"• Total Active Offers: {total_offers}\n"
            f"• Total Brands Listed: {len(brands)}\n"
            f"• Total Categories: {len(categories)}\n"
            f"• Total Locations: {len(locations)}\n\n"
            "💰 Pricing & Value Metrics:\n"
            f"• Average Payable Price: ₹{avg_price}\n"
            f"• Lowest Catalog Price: ₹{min_price}\n"
            f"• Highest Catalog Price: ₹{max_price}\n\n"
            "🎁 Discount Metrics:\n"
            f"• Average Catalog Discount: {avg_discount}%\n"
            f"• Highest Discount Available: {max_discount}%\n\n"
            "🏆 Catalog Quality:\n"
            f"• Average Offer Quality Score: {avg_score}/100\n\n"
            "ℹ️ Note: Metrics are calculated strictly from active catalog listing parameters."
        )

    def generate_catalog_summary(self) -> str:
        """FEATURE 2: Catalog Summary."""
        dataset = self.get_dataset()
        total = len(dataset)

        brands = Counter(d.get("brand") for d in dataset if d.get("brand"))
        categories = Counter(d.get("display_category") for d in dataset if d.get("display_category"))
        locations = Counter(d.get("display_location") for d in dataset if d.get("display_location"))

        prices = [float(str(d.get("price", "0")).replace(",", "")) for d in dataset if float(str(d.get("price", "0")).replace(",", "")) > 0]
        discounts = [d.get("discount_percent", 0) for d in dataset]

        min_p, max_p = (int(min(prices)), int(max(prices))) if prices else (0, 0)
        avg_p = int(sum(prices) / max(1, len(prices))) if prices else 0

        min_d, max_d = (min(discounts), max(discounts)) if discounts else (0, 0)
        avg_d = int(sum(discounts) / max(1, total))

        return (
            "📑 Catalog Summary Report\n\n"
            f"• Total Listed Offers: {total}\n"
            f"• Unique Brands: {len(brands)}\n"
            f"• Unique Categories: {len(categories)}\n"
            f"• Unique Locations: {len(locations)}\n\n"
            f"💵 Price Range: ₹{min_p} – ₹{max_p} (Avg: ₹{avg_p})\n"
            f"🎁 Discount Range: {min_d}% – {max_d}% (Avg: {avg_d}%)\n\n"
            f"📂 Top Categories: {', '.join([k for k, v in categories.most_common(3)])}\n"
            f"📍 Top Locations: {', '.join([k for k, v in locations.most_common(3)])}"
        )

    def generate_category_analytics(self) -> str:
        """FEATURE 3: Category Analytics."""
        dataset = self.get_dataset()
        cat_map: Dict[str, List[Dict[str, Any]]] = {}

        for d in dataset:
            cat = d.get("display_category", "Special Experience")
            if cat not in cat_map:
                cat_map[cat] = []
            cat_map[cat].append(d)

        cat_stats = []
        for cat, deals in cat_map.items():
            count = len(deals)
            priced = [float(str(d.get("price", "0")).replace(",", "")) for d in deals if float(str(d.get("price", "0")).replace(",", "")) > 0]
            avg_p = int(sum(priced) / max(1, len(priced))) if priced else 0
            avg_d = int(sum(d.get("discount_percent", 0) for d in deals) / max(1, count))
            avg_s = int(sum(merchant_agent.evaluate_offer_score(d)["total_score"] for d in deals) / max(1, count))
            cat_stats.append((cat, count, avg_p, avg_d, avg_s))

        cat_stats.sort(key=lambda x: x[1], reverse=True)

        most_populated = cat_stats[0][0]
        highest_rated = max(cat_stats, key=lambda x: x[4])[0]
        lowest_rated = min(cat_stats, key=lambda x: x[4])[0]

        reply = "📂 Category Analytics Breakdown\n\n"
        for cat, count, avg_p, avg_d, avg_s in cat_stats:
            reply += f"• {cat}: {count} offers | Avg Price: ₹{avg_p} | Avg Discount: {avg_d}% | Quality: {avg_s}/100\n"

        reply += (
            f"\n📊 Key Insights:\n"
            f"• Most Populated Category: {most_populated} ({cat_stats[0][1]} offers)\n"
            f"• Highest Rated Category: {highest_rated}\n"
            f"• Lowest Rated Category: {lowest_rated}"
        )
        return reply

    def generate_brand_analytics(self) -> str:
        """FEATURE 4: Brand Analytics."""
        dataset = self.get_dataset()
        brand_map: Dict[str, List[Dict[str, Any]]] = {}

        for d in dataset:
            brand = d.get("brand", "Unknown Merchant")
            if brand not in brand_map:
                brand_map[brand] = []
            brand_map[brand].append(d)

        brand_stats = []
        missing_data_brands = []

        for brand, deals in brand_map.items():
            count = len(deals)
            priced = [float(str(d.get("price", "0")).replace(",", "")) for d in deals if float(str(d.get("price", "0")).replace(",", "")) > 0]
            avg_p = int(sum(priced) / max(1, len(priced))) if priced else 0
            avg_d = int(sum(d.get("discount_percent", 0) for d in deals) / max(1, count))
            scores = [merchant_agent.evaluate_offer_score(d)["total_score"] for d in deals]
            avg_s = int(sum(scores) / max(1, count))

            if len(priced) < count or any(d.get("clean_title") != d.get("title") for d in deals):
                missing_data_brands.append(brand)

            brand_stats.append((brand, count, avg_p, avg_d, avg_s))

        brand_stats.sort(key=lambda x: x[4], reverse=True)
        top_brand = brand_stats[0]

        reply = "🏷️ Brand Analytics & Performance\n\n"
        reply += f"• Total Brands Tracked: {len(brand_stats)}\n"
        reply += f"• Best Scoring Brand: {top_brand[0]} ({top_brand[4]}/100 Avg Score)\n\n"
        reply += "Top Brand Breakdown:\n"

        for brand, count, avg_p, avg_d, avg_s in brand_stats[:5]:
            reply += f"• {brand}: {count} offers | Avg Price: ₹{avg_p} | Avg Discount: {avg_d}% | Score: {avg_s}/100\n"

        if missing_data_brands:
            reply += f"\n⚠️ Brands Needing Data Cleanups ({len(missing_data_brands)}): {', '.join(missing_data_brands[:3])}"

        return reply

    def generate_location_analytics(self) -> str:
        """FEATURE 5: Location Analytics."""
        dataset = self.get_dataset()
        loc_map: Dict[str, List[Dict[str, Any]]] = {}

        for d in dataset:
            loc = d.get("display_location", "Mumbai")
            if loc not in loc_map:
                loc_map[loc] = []
            loc_map[loc].append(d)

        reply = "📍 Location & City Analytics\n\n"
        for loc, deals in loc_map.items():
            count = len(deals)
            priced = [float(str(d.get("price", "0")).replace(",", "")) for d in deals if float(str(d.get("price", "0")).replace(",", "")) > 0]
            avg_p = int(sum(priced) / max(1, len(priced))) if priced else 0
            cats = Counter(d.get("display_category") for d in deals)
            top_cat = cats.most_common(1)[0][0] if cats else "Restaurant"
            top_brand = Counter(d.get("brand") for d in deals).most_common(1)[0][0]

            reply += (
                f"📍 {loc}:\n"
                f"• Offers Listed: {count}\n"
                f"• Average Pricing: ₹{avg_p}\n"
                f"• Dominant Category: {top_cat}\n"
                f"• Top Brand: {top_brand}\n\n"
            )

        return reply

    def generate_discount_analytics(self) -> str:
        """FEATURE 6: Discount Analytics."""
        dataset = self.get_dataset()
        total = len(dataset)
        discounts = [d.get("discount_percent", 0) for d in dataset]

        avg_d = int(sum(discounts) / max(1, total))
        max_d = max(discounts) if discounts else 0
        no_disc_count = sum(1 for d in discounts if d == 0)

        # Distribution ranges
        tier_0 = no_disc_count
        tier_1 = sum(1 for d in discounts if 1 <= d <= 25)
        tier_2 = sum(1 for d in discounts if 26 <= d <= 50)
        tier_3 = sum(1 for d in discounts if d > 50)

        return (
            "🎁 Discount Distribution & Analytics\n\n"
            f"• Average Catalog Discount: {avg_d}%\n"
            f"• Highest Discount: {max_d}%\n"
            f"• Lowest Discount: 0%\n"
            f"• Offers With No Discount: {no_disc_count} / {total}\n\n"
            "📊 Discount Tier Distribution:\n"
            f"• 0% OFF (Standard Rate): {tier_0} offers\n"
            f"• 1% – 25% OFF: {tier_1} offers\n"
            f"• 26% – 50% OFF: {tier_2} offers\n"
            f"• > 50% OFF (High Savings): {tier_3} offers"
        )

    def generate_price_analytics(self) -> str:
        """FEATURE 7: Price Analytics."""
        dataset = self.get_dataset()
        priced_deals = [d for d in dataset if float(str(d.get("price", "0")).replace(",", "")) > 0]
        prices = sorted([float(str(d.get("price", "0")).replace(",", "")) for d in priced_deals])

        if not prices:
            return "💰 Price Analytics: No pricing data available in catalog."

        avg_p = int(sum(prices) / max(1, len(prices)))
        median_p = int(statistics.median(prices))
        min_p = int(min(prices))
        max_p = int(max(prices))

        p1 = sum(1 for p in prices if p <= 250)
        p2 = sum(1 for p in prices if 251 <= p <= 500)
        p3 = sum(1 for p in prices if 501 <= p <= 1000)
        p4 = sum(1 for p in prices if p > 1000)

        return (
            "💰 Price Distribution & Analytics\n\n"
            f"• Average Payable Price: ₹{avg_p}\n"
            f"• Median Catalog Price: ₹{median_p}\n"
            f"• Lowest Price: ₹{min_p}\n"
            f"• Highest Price: ₹{max_p}\n\n"
            "📊 Price Range Distribution:\n"
            f"• Budget (≤ ₹250): {p1} offers\n"
            f"• Moderate (₹251 – ₹500): {p2} offers\n"
            f"• Premium (₹501 – ₹1000): {p3} offers\n"
            f"• Luxury (> ₹1000): {p4} offers"
        )

    def generate_catalog_health(self) -> str:
        """FEATURE 8: Catalog Health Diagnostic."""
        dataset = self.get_dataset()
        total = len(dataset)

        missing_prices = sum(1 for d in dataset if float(str(d.get("price", "0")).replace(",", "")) == 0)
        missing_locations = sum(1 for d in dataset if not d.get("display_location") or d.get("display_location") == "Location unavailable")
        missing_categories = sum(1 for d in dataset if not d.get("display_category") or d.get("display_category") == "Special Experience")
        ocr_issues = sum(1 for d in dataset if d.get("clean_title") != d.get("title"))
        short_desc = sum(1 for d in dataset if len(d.get("description", "")) < 30)

        title_set = set()
        duplicates = 0
        for d in dataset:
            t = d.get("clean_title", "")
            if t in title_set:
                duplicates += 1
            else:
                title_set.add(t)

        penalty = (missing_prices * 5) + (ocr_issues * 2) + (short_desc * 3) + (duplicates * 5)
        health_score = max(0, 100 - int((penalty / max(1, total)) * 10))

        rating = "Excellent" if health_score >= 80 else ("Good" if health_score >= 60 else ("Fair" if health_score >= 40 else "Poor"))

        return (
            "🩺 Catalog Health Diagnostic\n\n"
            f"🏆 Catalog Health Status: {rating} ({health_score}/100)\n\n"
            "Diagnostic Evaluation:\n"
            f"• Missing Pricing: {missing_prices} / {total}\n"
            f"• OCR Title Artifacts: {ocr_issues} / {total}\n"
            f"• Incomplete Descriptions: {short_desc} / {total}\n"
            f"• Duplicate Listings: {duplicates} / {total}\n"
            f"• Missing Locations: {missing_locations} / {total}\n"
            f"• Generic Category Fallbacks: {missing_categories} / {total}\n\n"
            "ℹ️ Explanation: Rating is computed from missing prices, title OCR artifacts, description length, and listing duplicates."
        )

    def generate_offer_distribution(self) -> str:
        """FEATURE 9: Offer Distribution."""
        dataset = self.get_dataset()

        cats = Counter(d.get("display_category") for d in dataset if d.get("display_category"))
        locs = Counter(d.get("display_location") for d in dataset if d.get("display_location"))
        brands = Counter(d.get("brand") for d in dataset if d.get("brand"))

        cat_text = "\n".join([f"  • {k}: {v} offers" for k, v in cats.most_common(4)])
        loc_text = "\n".join([f"  • {k}: {v} offers" for k, v in locs.most_common(4)])
        brand_text = "\n".join([f"  • {k}: {v} offers" for k, v in brands.most_common(4)])

        return (
            "📊 Offer Distribution Report\n\n"
            "📂 Distribution by Category:\n"
            f"{cat_text}\n\n"
            "📍 Distribution by Location:\n"
            f"{loc_text}\n\n"
            "🏷️ Distribution by Top Brands:\n"
            f"{brand_text}"
        )

    def generate_business_insights(self) -> str:
        """FEATURE 10: Business Insights (Derived strictly from catalog data)."""
        dataset = self.get_dataset()
        total = len(dataset)

        cats = Counter(d.get("display_category") for d in dataset if d.get("display_category"))
        locs = Counter(d.get("display_location") for d in dataset if d.get("display_location"))

        top_cat, top_cat_count = cats.most_common(1)[0] if cats else ("Restaurant", 0)
        top_loc, top_loc_count = locs.most_common(1)[0] if locs else ("Mumbai", 0)

        cat_discounts = {}
        for d in dataset:
            cat = d.get("display_category", "Experience")
            if cat not in cat_discounts:
                cat_discounts[cat] = []
            cat_discounts[cat].append(d.get("discount_percent", 0))

        top_disc_cat = max(cat_discounts.items(), key=lambda x: (sum(x[1]) / len(x[1])))[0]
        top_disc_avg = int(sum(cat_discounts[top_disc_cat]) / len(cat_discounts[top_disc_cat]))

        return (
            "💡 Business Intelligence Insights\n\n"
            "Catalog Observations:\n"
            f"1. 📂 {top_cat} category contains the highest offer density ({top_cat_count} out of {total} offers).\n"
            f"2. 🎁 {top_disc_cat} offers carry the highest average discount level ({top_disc_avg}% OFF).\n"
            f"3. 📍 {top_loc} represents the dominant geographical listing area ({top_loc_count} offers).\n"
            f"4. 💰 The catalog median payable price is ₹{int(statistics.median([float(str(d.get('price', '0')).replace(',', '')) for d in dataset if float(str(d.get('price', '0')).replace(',', '')) > 0]))}.\n\n"
            "ℹ️ Note: Insights are derived strictly from active catalog listing parameters."
        )

    def generate_improvement_suggestions(self) -> str:
        """FEATURE 11: Improvement Suggestions (What should we improve?)."""
        dataset = self.get_dataset()
        total = len(dataset)

        missing_prices = sum(1 for d in dataset if float(str(d.get("price", "0")).replace(",", "")) == 0)
        ocr_issues = sum(1 for d in dataset if d.get("clean_title") != d.get("title"))
        short_desc = sum(1 for d in dataset if len(d.get("description", "")) < 30)

        suggestions = []
        if missing_prices > 0:
            suggestions.append(f"• Pricing Completeness: Add explicit payable prices for {missing_prices} catalog deals currently lacking pricing.")

        if ocr_issues > 0:
            suggestions.append(f"• OCR Cleanliness: Clean title artifacts on {ocr_issues} offers to improve search matching.")

        if short_desc > 0:
            suggestions.append(f"• Description Detail: Expand descriptions for {short_desc} offers with clear inclusion bullets.")

        suggestions.append("• Discount Visibility: Ensure high-discount offers (30%+ OFF) feature bold promotional banners.")
        suggestions.append("• Location Verification: Verify exact sub-area locations for all listed venues.")

        return (
            "🛠️ Catalog Improvement Recommendations\n\n"
            "Actionable Fixes for Catalog Optimization:\n\n"
            + "\n\n".join(suggestions) + "\n\n"
            "ℹ️ Note: Based strictly on current catalog listing quality analysis."
        )

    def generate_business_help(self) -> str:
        """FEATURE 12: Business Help."""
        return (
            "💡 Business Intelligence Help Guide\n\n"
            "Available Analytics Commands:\n"
            "• Business Dashboard: Overview of total offers, brands, categories, prices, and discounts.\n"
            "• Catalog Summary: High-level overview of pricing ranges, discount tiers, and top categories.\n"
            "• Category Analytics: Performance, pricing, and discount breakdown per category.\n"
            "• Brand Analytics: Listing volume and score performance per merchant brand.\n"
            "• Location Analytics: Pricing and offer density breakdown by city and location.\n"
            "• Discount Analytics: Breakdown of discount tiers (0%, 1-25%, 26-50%, 50%+).\n"
            "• Price Analytics: Median price, pricing range distribution, and budget tiers.\n"
            "• Catalog Health: Health score (0-100) evaluating missing prices, OCR quality, and duplicates.\n"
            "• Business Insights: Catalog-derived observations and trends.\n"
            "• What should we improve?: Actionable fixes to optimize catalog listing quality."
        )


analytics_engine = BusinessAnalyticsEngine()
