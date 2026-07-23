import logging
from typing import Dict, List, Any, Optional
from collections import Counter

logger = logging.getLogger(__name__)


class UserProfileManager:
    """
    AI Personalization & Profile Manager (Milestone 6):
    Learns user preferences, tracks recently viewed deals, generates smart intents,
    and supports profile management commands.
    """

    def __init__(self):
        # user_id -> profile_dict
        self.profiles: Dict[int, Dict[str, Any]] = {}
        # user_id -> List[deal_dict] (Max 10)
        self.recent_history: Dict[int, List[Dict[str, Any]]] = {}

    def get_profile(self, user_id: int) -> Dict[str, Any]:
        """Returns or initializes user profile."""
        if user_id not in self.profiles:
            self.profiles[user_id] = {
                "categories": Counter(),
                "locations": Counter(),
                "budgets": [],
                "merchants": Counter(),
                "search_count": 0,
            }
        return self.profiles[user_id]

    def update_profile_from_intent(self, user_id: int, intent: Dict[str, Any]):
        """Updates user profile based on search intents."""
        profile = self.get_profile(user_id)
        profile["search_count"] += 1

        cat = intent.get("category")
        if cat:
            profile["categories"][cat.title()] += 1

        loc = intent.get("area") or intent.get("location") or intent.get("city")
        if loc:
            profile["locations"][loc.title()] += 1

        max_price = intent.get("max_price")
        if max_price is not None and max_price > 0:
            profile["budgets"].append(float(max_price))

    def update_profile_from_favourite(self, user_id: int, deal: Dict[str, Any]):
        """Updates user profile when a deal is saved to favourites."""
        profile = self.get_profile(user_id)

        cat = deal.get("category")
        if cat and cat != "Unknown":
            profile["categories"][cat.title()] += 2  # Stronger weight for saved deals

        brand = deal.get("brand")
        if brand:
            profile["merchants"][brand] += 2

        loc = deal.get("location")
        if loc and loc.lower() != "mumbai":
            profile["locations"][loc.title()] += 2

        try:
            price = float(str(deal.get("price", "0")).replace(",", ""))
            if price > 0:
                profile["budgets"].append(price)
        except Exception:
            pass

    def add_recently_viewed(self, user_id: int, deal: Dict[str, Any]):
        """Adds deal to user's recently viewed list (max 10)."""
        if user_id not in self.recent_history:
            self.recent_history[user_id] = []

        history = self.recent_history[user_id]
        deal_id = deal.get("id")

        # Remove duplicate if already present
        history = [d for d in history if d.get("id") != deal_id]
        history.insert(0, deal)

        self.recent_history[user_id] = history[:10]

    def get_recently_viewed(self, user_id: int) -> List[Dict[str, Any]]:
        """Returns last 10 viewed deals."""
        return self.recent_history.get(user_id, [])

    def reset_profile(self, user_id: int):
        """Resets all profile preferences and history for a user."""
        if user_id in self.profiles:
            del self.profiles[user_id]
        if user_id in self.recent_history:
            del self.recent_history[user_id]

    def get_personalized_intent(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Generates a search intent based on top learned preferences."""
        profile = self.get_profile(user_id)

        top_cat = None
        if profile["categories"]:
            top_cat = profile["categories"].most_common(1)[0][0]

        top_loc = None
        if profile["locations"]:
            top_loc = profile["locations"].most_common(1)[0][0]

        avg_budget = None
        if profile["budgets"]:
            avg_budget = sum(profile["budgets"]) / len(profile["budgets"])

        if not top_cat and not top_loc and not avg_budget:
            return None  # No learned profile yet

        return {
            "type": "personalized",
            "category": top_cat.lower() if top_cat else "restaurant",
            "city": "Mumbai",
            "area": top_loc,
            "location": top_loc,
            "min_price": None,
            "max_price": int(avg_budget) if avg_budget else None,
            "occasion": None,
            "preferences": [],
            "query": f"Personalized for {top_cat or 'Deals'}",
        }

    def get_personalization_reasons(self, user_id: int, deal: Dict[str, Any]) -> List[str]:
        """Generates honest, data-backed reasons for personalized recommendations."""
        profile = self.get_profile(user_id)
        reasons = []

        if profile["categories"]:
            top_cat = profile["categories"].most_common(1)[0][0]
            deal_cat = deal.get("category", "")
            if top_cat.lower() in deal_cat.lower() or deal_cat.lower() in top_cat.lower():
                reasons.append(f"Recommended because you often search for {top_cat}")

        if profile["budgets"]:
            avg_b = sum(profile["budgets"]) / len(profile["budgets"])
            try:
                price = float(str(deal.get("price", "0")).replace(",", ""))
                if price > 0 and price <= avg_b * 1.2:
                    reasons.append(f"Fits your typical budget (under ₹{int(avg_b)})")
            except Exception:
                pass

        if profile["locations"]:
            top_loc = profile["locations"].most_common(1)[0][0]
            if top_loc.lower() in (deal.get("location") or "").lower():
                reasons.append(f"Located in your preferred area ({top_loc})")

        if profile["merchants"]:
            top_m = profile["merchants"].most_common(1)[0][0]
            if top_m.lower() in (deal.get("brand") or "").lower():
                reasons.append(f"Matches your saved merchant ({top_m})")

        if not reasons:
            reasons.append("Handpicked top offer based on your activity")

        return reasons


profile_manager = UserProfileManager()
