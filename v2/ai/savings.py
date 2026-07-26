import logging
from typing import Dict, List, Any, Optional
from v2.ai.profile import profile_manager
from v2.search.search_engine import load_deals
from v2.telegram.handlers import get_favourites

logger = logging.getLogger(__name__)


class CustomerSavingsAgent:
    """
    Milestone 12.1 - Complete Customer Savings Agent Engine:
    Manages dedicated Customer Savings Profiles, detects price-prioritized deal opportunities,
    tracks notified deal history, and provides honest, non-fictional explanations.
    """

    def __init__(self):
        # user_id -> Set of deal IDs notified to prevent duplicate alerts
        self.notified_deals: Dict[int, set] = {}

    def get_notified_deals(self, user_id: int) -> set:
        if user_id not in self.notified_deals:
            self.notified_deals[user_id] = set()
        return self.notified_deals[user_id]

    def mark_notified(self, user_id: int, deal_id: str):
        self.get_notified_deals(user_id).add(deal_id)

    def get_savings_profile_summary(self, user_id: int) -> str:
        """
        Displays dedicated 'My Savings' Response:
        Favourite Categories, Favourite Merchants, Typical Budget, Preferred Location,
        Estimated Savings, Number of Favourite Deals, Recent Activity.
        """
        profile = profile_manager.get_profile(user_id)
        favs = get_favourites(user_id)
        history = profile_manager.get_recently_viewed(user_id)

        top_cats = ", ".join([f"{k}" for k, v in profile["categories"].most_common(2)]) if profile["categories"] else "Not specified yet"
        top_loc = profile["locations"].most_common(1)[0][0] if profile["locations"] else "Mumbai"
        top_merch = ", ".join([f"{k}" for k, v in profile["merchants"].most_common(2)]) if profile["merchants"] else "None recorded yet"
        top_occ = profile["occasions"].most_common(1)[0][0] if profile["occasions"] else "None recorded"

        avg_b = int(sum(profile["budgets"]) / len(profile["budgets"])) if profile["budgets"] else None
        budget_str = f"Under ₹{avg_b}" if avg_b else "Flexible"

        # Calculate estimated savings realized from saved/viewed deals with known prices
        est_savings = 0.0
        for deal in favs + history:
            disc = deal.get("discount_percent", 0)
            try:
                p = float(str(deal.get("price", "0")).replace(",", ""))
                if p > 0 and disc > 0:
                    orig = p / max(0.01, (1.0 - (disc / 100.0)))
                    est_savings += (orig - p)
            except Exception:
                pass

        last_query = profile["recent_queries"][0] if profile["recent_queries"] else "None"

        summary = (
            "💰 Customer Savings Profile\n\n"
            f"📂 Favourite Categories: {top_cats}\n"
            f"🏷️ Favourite Merchants: {top_merch}\n"
            f"💰 Typical Budget: {budget_str}\n"
            f"📍 Preferred Location: {top_loc}\n"
            f"🎉 Preferred Occasion: {top_occ}\n"
            f"❤️ Saved Favourite Deals: {len(favs)} deals\n"
            f"📜 Recently Viewed Deals: {len(history)} deals\n"
            f"🔍 Last Recent Search: {last_query}\n"
            f"📊 Total Searches Recorded: {profile['search_count']}\n\n"
            f"💵 Estimated Tracked Savings: ₹{int(est_savings)}\n\n"
            "⚠️ Catalog Note: Expiry dates & real-time inventory are unavailable in current dataset. All opportunities reflect active curated deals."
        )
        return summary

    def detect_opportunities(self, user_id: int, limit: int = 4) -> List[Dict[str, Any]]:
        """
        Detects price-prioritized deal opportunities based on user profile:
        Prefers deals with known prices (price > 0), only showing unknown-price deals if no priced alternatives exist.
        """
        profile = profile_manager.get_profile(user_id)
        favs = get_favourites(user_id)
        notified = self.get_notified_deals(user_id)

        all_deals = load_deals()

        top_cat = profile["categories"].most_common(1)[0][0].lower() if profile["categories"] else None
        top_merch = profile["merchants"].most_common(1)[0][0].lower() if profile["merchants"] else None
        top_loc = profile["locations"].most_common(1)[0][0].lower() if profile["locations"] else "mumbai"
        avg_budget = sum(profile["budgets"]) / len(profile["budgets"]) if profile["budgets"] else None
        fav_deal_ids = {d.get("id") for d in favs}

        # Separate priced deals from unknown-price deals to enforce price preference
        priced_deals = []
        unknown_deals = []

        for deal in all_deals:
            deal_id = deal.get("id")
            if deal_id in notified:
                continue

            try:
                price = float(str(deal.get("price", "0")).replace(",", ""))
            except Exception:
                price = 0.0

            if price > 0:
                priced_deals.append(deal)
            else:
                unknown_deals.append(deal)

        candidate_pool = priced_deals if priced_deals else unknown_deals

        scored_deals = []
        for deal in candidate_pool:
            score = 0.0
            reasons = []

            cat = (deal.get("category") or "").lower()
            brand = (deal.get("brand") or "").lower()
            loc = (deal.get("location") or "").lower()
            disc = deal.get("discount_percent", 0)

            try:
                price = float(str(deal.get("price", "0")).replace(",", ""))
            except Exception:
                price = 0.0

            # Favourite Merchant Match
            if top_merch and top_merch in brand:
                score += 5.0
                reasons.append(f"Favourite merchant match ({deal.get('brand')})")

            # Favourite Category Match & High Discount
            if top_cat and top_cat in cat:
                score += 3.0
                reasons.append(f"Favourite category match ({deal.get('display_category')})")
                if disc >= 40:
                    score += 4.0
                    reasons.append(f"High discount ({disc}% OFF)")
            elif disc >= 50:
                score += 2.0
                reasons.append(f"High discount ({disc}% OFF)")

            # Budget Match
            if avg_budget and price > 0 and price <= avg_budget:
                score += 3.0
                reasons.append(f"Budget match (Fits under ₹{int(avg_budget)})")

            # Preferred Location Match
            if top_loc and top_loc in loc:
                score += 2.0
                reasons.append(f"Location match ({deal.get('display_location')})")

            # Saved Deal Bonus
            if deal.get("id") in fav_deal_ids:
                score += 4.0
                reasons.append("Saved in your favourites")

            if score > 0:
                deal_copy = dict(deal)
                deal_copy["opportunity_score"] = score
                deal_copy["opportunity_reasons"] = reasons
                scored_deals.append(deal_copy)

        # Fallback if no specific profile score built yet
        if not scored_deals:
            for deal in candidate_pool[:limit]:
                deal_copy = dict(deal)
                disc = deal.get("discount_percent", 0)
                reasons = ["Popular recommendation"]
                if disc > 0:
                    reasons.append(f"High discount ({disc}% OFF)")
                deal_copy["opportunity_score"] = 1.0
                deal_copy["opportunity_reasons"] = reasons
                scored_deals.append(deal_copy)

        scored_deals.sort(key=lambda x: x["opportunity_score"], reverse=True)
        return scored_deals[:limit]

    def explain_recommendation(self, user_id: int, deal: Dict[str, Any]) -> str:
        """
        Generates explicit, non-fictional explanation bullets for 'Why did I get this?'.
        Matches exact prompt format:
        • Favourite category match
        • Budget match
        • Recent search match
        • High discount
        • Popular recommendation
        """
        profile = profile_manager.get_profile(user_id)
        reasons = []

        top_cat = profile["categories"].most_common(1)[0][0] if profile["categories"] else None
        top_merch = profile["merchants"].most_common(1)[0][0] if profile["merchants"] else None
        avg_budget = sum(profile["budgets"]) / len(profile["budgets"]) if profile["budgets"] else None
        top_loc = profile["locations"].most_common(1)[0][0] if profile["locations"] else None

        deal_cat = deal.get("category", "")
        deal_brand = deal.get("brand", "")
        deal_loc = deal.get("location", "")
        disc = deal.get("discount_percent", 0)

        try:
            price = float(str(deal.get("price", "0")).replace(",", ""))
        except Exception:
            price = 0.0

        if top_cat and top_cat.lower() in deal_cat.lower():
            reasons.append(f"Favourite category match ({top_cat})")

        if avg_budget and price > 0 and price <= avg_budget:
            reasons.append(f"Budget match (Fits under ₹{int(avg_budget)})")

        if profile["recent_queries"]:
            last_q = profile["recent_queries"][0]
            reasons.append(f"Recent search match ({last_q})")

        if top_merch and top_merch.lower() in deal_brand.lower():
            reasons.append(f"Favourite merchant match ({top_merch})")

        if top_loc and top_loc.lower() in deal_loc.lower():
            reasons.append(f"Location match ({top_loc})")

        if disc and disc >= 40:
            reasons.append(f"High discount ({disc}% OFF)")

        if not reasons:
            reasons.append("Popular recommendation")

        return "\n".join([f"• {r}" for r in reasons])


savings_agent = CustomerSavingsAgent()
