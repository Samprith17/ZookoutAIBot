import logging
from typing import Dict, List, Any, Optional
from collections import Counter

logger = logging.getLogger(__name__)


class UserProfileManager:
    """
    AI Personalization & Preference Learning Manager (Milestone 10):
    Continuously learns user preferences with recency-weighted decay, tracks view history,
    and generates adaptive recommendations with clear explanations.
    """

    def __init__(self, decay_factor: float = 0.82):
        self.decay_factor = decay_factor
        # user_id -> profile_dict
        self.profiles: Dict[int, Dict[str, Any]] = {}
        # user_id -> List[deal_dict] (Max 10)
        self.recent_history: Dict[int, List[Dict[str, Any]]] = {}

    def get_profile(self, user_id: int) -> Dict[str, Any]:
        """Returns or initializes user preference profile."""
        if user_id not in self.profiles:
            self.profiles[user_id] = {
                "categories": Counter(),
                "locations": Counter(),
                "occasions": Counter(),
                "budgets": [],
                "merchants": Counter(),
                "recent_queries": [],
                "search_count": 0,
            }
        return self.profiles[user_id]

    def _apply_decay(self, counter: Counter):
        """Applies recency decay factor to existing counts so recent behavior outweighs past history."""
        for key in list(counter.keys()):
            counter[key] *= self.decay_factor
            if counter[key] < 0.05:
                del counter[key]

    def update_profile_from_intent(self, user_id: int, intent: Dict[str, Any]):
        """Updates user profile based on search intents with preference decay."""
        profile = self.get_profile(user_id)
        profile["search_count"] += 1

        self._apply_decay(profile["categories"])
        self._apply_decay(profile["locations"])
        self._apply_decay(profile["occasions"])
        self._apply_decay(profile["merchants"])

        cat = intent.get("category")
        if cat:
            profile["categories"][cat.title()] += 1.0

        loc = intent.get("area") or intent.get("location") or intent.get("city")
        if loc:
            profile["locations"][loc.title()] += 1.0

        occ = intent.get("occasion")
        if occ:
            profile["occasions"][occ] += 1.0

        max_price = intent.get("max_price")
        if max_price is not None and max_price > 0:
            profile["budgets"].append(float(max_price))
            profile["budgets"] = profile["budgets"][-10:]  # Keep last 10 budgets

        query = intent.get("query")
        if query and query not in profile["recent_queries"]:
            profile["recent_queries"].insert(0, query)
            profile["recent_queries"] = profile["recent_queries"][:5]

    def update_profile_from_favourite(self, user_id: int, deal: Dict[str, Any]):
        """Updates user profile when a deal is saved to favourites."""
        profile = self.get_profile(user_id)

        self._apply_decay(profile["categories"])
        self._apply_decay(profile["locations"])
        self._apply_decay(profile["merchants"])

        cat = deal.get("category")
        if cat and cat != "Unknown":
            profile["categories"][cat.title()] += 2.0  # Double weight for saved deals

        brand = deal.get("brand")
        if brand:
            profile["merchants"][brand] += 2.0

        loc = deal.get("location")
        if loc and loc.lower() != "mumbai":
            profile["locations"][loc.title()] += 2.0

        try:
            price = float(str(deal.get("price", "0")).replace(",", ""))
            if price > 0:
                profile["budgets"].append(price)
                profile["budgets"] = profile["budgets"][-10:]
        except Exception:
            pass

    def add_recently_viewed(self, user_id: int, deal: Dict[str, Any]):
        """Adds deal to user's recently viewed list (max 10)."""
        if user_id not in self.recent_history:
            self.recent_history[user_id] = []

        history = self.recent_history[user_id]
        deal_id = deal.get("id")

        history = [d for d in history if d.get("id") != deal_id]
        history.insert(0, deal)

        self.recent_history[user_id] = history[:10]

    def get_recently_viewed(self, user_id: int) -> List[Dict[str, Any]]:
        """Returns last 10 viewed deals."""
        return self.recent_history.get(user_id, [])

    def reset_profile(self, user_id: int):
        """Resets all learned profile preferences and history for a user."""
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

        top_occ = None
        if profile["occasions"]:
            top_occ = profile["occasions"].most_common(1)[0][0]

        if not top_cat and not top_loc and not avg_budget and not top_occ:
            return None

        return {
            "type": "personalized",
            "category": top_cat.lower() if top_cat else "restaurant",
            "city": "Mumbai",
            "area": top_loc if top_loc != "Mumbai" else None,
            "location": top_loc or "Mumbai",
            "min_price": None,
            "max_price": int(avg_budget) if avg_budget else None,
            "occasion": top_occ,
            "preferences": [],
            "query": f"Personalized for {top_cat or 'Deals'}",
        }

    def get_personalization_reasons(self, user_id: int, deal: Dict[str, Any]) -> List[str]:
        """Generates clear, data-backed explanation bullets for personalized recommendations."""
        profile = self.get_profile(user_id)
        reasons = []

        if profile["categories"]:
            top_cat = profile["categories"].most_common(1)[0][0]
            reasons.append(f"You often choose {top_cat}s.")

        if profile["budgets"]:
            avg_b = sum(profile["budgets"]) / len(profile["budgets"])
            reasons.append(f"Your typical budget is under ₹{int(avg_b)}.")

        if profile["locations"]:
            top_loc = profile["locations"].most_common(1)[0][0]
            reasons.append(f"You usually search in {top_loc}.")

        if profile["recent_queries"]:
            last_q = profile["recent_queries"][0]
            reasons.append(f"Based on your recent search: '{last_q}'")

        if not reasons:
            reasons.append("Handpicked top offer based on your activity")

        return reasons


profile_manager = UserProfileManager()
