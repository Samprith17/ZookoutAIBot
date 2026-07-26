import logging
from typing import Dict, List, Any, Optional
from v2.ai.profile import profile_manager
from v2.search.search_engine import load_deals, normalize_deal, display_category
from v2.telegram.handlers import get_favourites

logger = logging.getLogger(__name__)


class CustomerSavingsAgent:
    """
    Milestone 12.3 - Shared Normalization Savings Agent Engine:
    Reuses the Shared Deal Normalization Layer (normalize_deal) across Search, Recommendations,
    Experience Planner, Savings Agent, Comparison, and Personalization.
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
        Uses shared profile data from UserProfileManager and explains savings calculation method.
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
        priced_deals_count = 0

        for deal in favs + history:
            disc = deal.get("discount_percent", 0)
            try:
                p = float(str(deal.get("price", "0")).replace(",", ""))
                if p > 0 and disc > 0:
                    orig = p / max(0.01, (1.0 - (disc / 100.0)))
                    est_savings += (orig - p)
                    priced_deals_count += 1
            except Exception:
                pass

        last_query = profile["recent_queries"][0] if profile["recent_queries"] else "None"

        if priced_deals_count > 0 and est_savings > 0:
            savings_str = f"💵 Estimated Tracked Savings: ₹{int(est_savings)}\nℹ️ Calculated from your {priced_deals_count} saved/viewed deals using original list price vs discounted payable price."
        else:
            savings_str = "💵 Estimated Tracked Savings: Calculation unavailable (no saved/viewed deals with discount data yet)."

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
            f"{savings_str}\n\n"
            "⚠️ Catalog Note: Expiry dates & real-time inventory are unavailable in current dataset. All opportunities reflect active curated deals."
        )
        return summary

    def detect_opportunities(self, user_id: int, limit: int = 4) -> List[Dict[str, Any]]:
        """
        Detects refined deal opportunities using the Shared Deal Normalization Layer:
        Prefers complete records (known price > 0, valid category, valid location, clean title).
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

        complete_priced_deals = []
        partial_deals = []

        for deal in all_deals:
            deal_id = deal.get("id")
            if deal_id in notified:
                continue

            try:
                price = float(str(deal.get("price", "0")).replace(",", ""))
            except Exception:
                price = 0.0

            cat = (deal.get("category") or "").strip()
            loc = (deal.get("location") or "").strip()

            is_complete = price > 0 and cat != "Unknown" and loc.lower() not in ["", "none", "null"]

            if is_complete:
                complete_priced_deals.append(deal)
            else:
                partial_deals.append(deal)

        candidate_pool = complete_priced_deals if complete_priced_deals else partial_deals

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

            if top_merch and top_merch in brand:
                score += 5.0
                reasons.append(f"Favourite merchant match ({deal.get('brand')})")

            if top_cat and top_cat in cat:
                score += 3.0
                reasons.append(f"Favourite category match ({display_category(top_cat, deal)})")
                if disc >= 40:
                    score += 4.0
                    reasons.append(f"High discount ({disc}% OFF)")
            elif disc >= 50:
                score += 2.0
                reasons.append(f"High discount ({disc}% OFF)")

            if avg_budget and price > 0 and price <= avg_budget:
                score += 3.0
                reasons.append(f"Typical budget match (Fits under ₹{int(avg_budget)})")

            if top_loc and top_loc in loc:
                score += 2.0
                reasons.append(f"Preferred location match ({deal.get('location', 'Mumbai')})")

            if deal.get("id") in fav_deal_ids:
                score += 4.0
                reasons.append("Saved in your favourites")

            if score > 0:
                deal_copy = normalize_deal(deal, top_cat, top_loc)
                deal_copy["opportunity_score"] = score
                deal_copy["opportunity_reasons"] = reasons
                scored_deals.append(deal_copy)

        if not scored_deals:
            for deal in candidate_pool[:limit]:
                deal_copy = normalize_deal(deal, top_cat, top_loc)
                deal_copy["opportunity_score"] = 1.0
                deal_copy["opportunity_reasons"] = ["Popular recommendation"]
                scored_deals.append(deal_copy)

        scored_deals.sort(key=lambda x: (x["confidence"], x["opportunity_score"]), reverse=True)
        return scored_deals[:limit]

    def explain_recommendation(self, user_id: int, deal: Dict[str, Any]) -> str:
        """
        Generates explicit, non-fictional explanation bullets based on stored user data:
        • Favourite category match (Restaurant)
        • Favourite merchant match (Kohinoor Continental)
        • Typical budget match (Fits under ₹1000)
        • Recent search match (Restaurant in Mumbai)
        • Saved favourites match
        • High discount (50% OFF)
        """
        profile = profile_manager.get_profile(user_id)
        favs = get_favourites(user_id)
        fav_ids = {d.get("id") for d in favs}

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

        if top_merch and top_merch.lower() in deal_brand.lower():
            reasons.append(f"Favourite merchant match ({top_merch})")

        if avg_budget and price > 0 and price <= avg_budget:
            reasons.append(f"Typical budget match (Fits under ₹{int(avg_budget)})")

        if profile["recent_queries"]:
            last_q = profile["recent_queries"][0]
            reasons.append(f"Recent search match ('{last_q}')")

        if deal.get("id") in fav_ids:
            reasons.append("Saved favourites match")

        if top_loc and top_loc.lower() in deal_loc.lower():
            reasons.append(f"Preferred location match ({top_loc})")

        if disc and disc >= 40:
            reasons.append(f"High discount ({disc}% OFF)")

        if not reasons:
            reasons.append("Popular recommendation")

        return "\n".join([f"• {r}" for r in reasons])


savings_agent = CustomerSavingsAgent()
