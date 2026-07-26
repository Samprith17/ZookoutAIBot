import logging
from typing import Dict, List, Any, Optional
from v2.ai.profile import profile_manager
from v2.search.search_engine import load_deals
from v2.telegram.handlers import get_favourites

logger = logging.getLogger(__name__)


class CustomerSavingsAgent:
    """
    Milestone 12 - Customer Savings Agent:
    Proactively learns user savings preferences, detects deal opportunities,
    tracks notified deals, and provides honest data explanations.
    """

    def __init__(self):
        # user_id -> Set of deal IDs notified to avoid duplicates
        self.notified_deals: Dict[int, set] = {}

    def get_notified_deals(self, user_id: int) -> set:
        if user_id not in self.notified_deals:
            self.notified_deals[user_id] = set()
        return self.notified_deals[user_id]

    def mark_notified(self, user_id: int, deal_id: str):
        self.get_notified_deals(user_id).add(deal_id)

    def get_savings_profile_summary(self, user_id: int) -> str:
        """Generates a comprehensive summary of the user's Customer Savings Profile."""
        profile = profile_manager.get_profile(user_id)
        favs = get_favourites(user_id)
        history = profile_manager.get_recently_viewed(user_id)

        top_cat = profile["categories"].most_common(1)[0][0] if profile["categories"] else "Not specified"
        top_loc = profile["locations"].most_common(1)[0][0] if profile["locations"] else "Mumbai"
        top_merch = profile["merchants"].most_common(1)[0][0] if profile["merchants"] else "None recorded"
        top_occ = profile["occasions"].most_common(1)[0][0] if profile["occasions"] else "None recorded"

        avg_b = int(sum(profile["budgets"]) / len(profile["budgets"])) if profile["budgets"] else None
        budget_str = f"Under ₹{avg_b}" if avg_b else "Flexible"

        # Calculate estimated savings realized from saved/viewed deals
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

        summary = (
            "💰 Your Customer Savings Profile:\n\n"
            f"📂 Favourite Category: {top_cat}\n"
            f"🏷️ Favourite Merchant: {top_merch}\n"
            f"💰 Typical Budget: {budget_str}\n"
            f"📍 Preferred Location: {top_loc}\n"
            f"❤️ Saved Favourites: {len(favs)} deals\n"
            f"📜 Recently Viewed: {len(history)} deals\n"
            f"🎉 Preferred Occasion: {top_occ}\n"
            f"📊 Total Searches: {profile['search_count']}\n\n"
            f"💵 Estimated Total Tracked Savings: ₹{int(est_savings)}\n\n"
            "⚠️ Catalog Note: Deal expiry dates & real-time inventory updates are unavailable in current dataset. All opportunities reflect active curated deals."
        )
        return summary

    def detect_opportunities(self, user_id: int, limit: int = 4) -> List[Dict[str, Any]]:
        """
        Detects relevant deal opportunities based on user's savings profile:
        1. Favourite merchant matches
        2. Deals fitting usual budget
        3. High-discount deals (>= 40% OFF) in favourite categories
        4. Matches recent interests/queries
        """
        profile = profile_manager.get_profile(user_id)
        favs = get_favourites(user_id)
        notified = self.get_notified_deals(user_id)

        all_deals = load_deals()
        scored_deals = []

        top_cat = profile["categories"].most_common(1)[0][0].lower() if profile["categories"] else None
        top_merch = profile["merchants"].most_common(1)[0][0].lower() if profile["merchants"] else None
        top_loc = profile["locations"].most_common(1)[0][0].lower() if profile["locations"] else "mumbai"
        avg_budget = sum(profile["budgets"]) / len(profile["budgets"]) if profile["budgets"] else None

        fav_deal_ids = {d.get("id") for d in favs}

        for deal in all_deals:
            deal_id = deal.get("id")
            if deal_id in notified:
                continue

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

            # 1. Favourite Merchant Match
            if top_merch and top_merch in brand:
                score += 5.0
                reasons.append(f"Matches your favourite brand ({deal.get('brand')}).")

            # 2. Category Match & High Discount
            if top_cat and top_cat in cat:
                score += 3.0
                reasons.append(f"Matches your favourite category ({deal.get('display_category')}).")
                if disc >= 40:
                    score += 4.0
                    reasons.append(f"High savings offer with {disc}% OFF!")
            elif disc >= 50:
                score += 2.0
                reasons.append(f"Hot discount value: {disc}% OFF.")

            # 3. Budget Match
            if avg_budget and price > 0 and price <= avg_budget:
                score += 3.0
                reasons.append(f"Fits your usual budget of under ₹{int(avg_budget)} (Price: {deal.get('formatted_price')}).")

            # 4. Location Match
            if top_loc and top_loc in loc:
                score += 2.0
                reasons.append(f"Located in your preferred area ({deal.get('display_location')}).")

            # 5. Favourite deal bonus
            if deal_id in fav_deal_ids:
                score += 4.0
                reasons.append("Saved in your favourites list.")

            if score > 0:
                deal_copy = dict(deal)
                deal_copy["opportunity_score"] = score
                deal_copy["opportunity_reasons"] = reasons
                scored_deals.append(deal_copy)

        # Sort by opportunity score descending
        scored_deals.sort(key=lambda x: x["opportunity_score"], reverse=True)
        return scored_deals[:limit]

    def explain_opportunity(self, user_id: int, deal: Dict[str, Any]) -> str:
        """Generates explicit 'Why you're seeing this' explanation bullets."""
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

        if top_cat and top_cat.lower() in deal_cat.lower():
            reasons.append(f"You often search for {top_cat}s.")

        if avg_budget:
            reasons.append(f"Fits your usual budget (under ₹{int(avg_budget)}).")

        if top_merch and top_merch.lower() in deal_brand.lower():
            reasons.append(f"Matches your favourite brand ({top_merch}).")

        if top_loc and top_loc.lower() in deal_loc.lower():
            reasons.append(f"Located in your preferred area ({top_loc}).")

        if disc and disc >= 40:
            reasons.append(f"High savings offer ({disc}% OFF).")

        if profile["recent_queries"]:
            last_q = profile["recent_queries"][0]
            reasons.append(f"Matches recent search activity: '{last_q}'")

        if not reasons:
            reasons.append("Curated savings offer based on popular community choices.")

        return "\n".join([f"• {r}" for r in reasons])


savings_agent = CustomerSavingsAgent()
