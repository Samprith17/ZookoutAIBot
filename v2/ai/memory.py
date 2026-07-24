import time
from typing import Dict, Any


class ConversationMemoryManager:
    """
    Manages short-term conversational context per Telegram user ID (Milestone 6.4).
    Context automatically expires after 20 minutes (1200 seconds) of inactivity.
    """

    def __init__(self, ttl_seconds: int = 1200):  # 20 minutes TTL
        self.ttl_seconds = ttl_seconds
        self.sessions: Dict[int, Dict[str, Any]] = {}

    def get_context(self, user_id: int) -> Dict[str, Any]:
        """Returns active context for user if not expired, else returns empty dict."""
        now = time.time()
        session = self.sessions.get(user_id)
        if not session:
            return {}

        last_updated = session.get("_last_updated", 0)
        if now - last_updated > self.ttl_seconds:
            self.clear_context(user_id)
            return {}

        return {k: v for k, v in session.items() if not k.startswith("_")}

    def update_context(self, user_id: int, new_intent: Dict[str, Any]) -> Dict[str, Any]:
        """
        Merges new intent fields with existing conversation context.
        Supports category switching, budget adjustments (cheaper/luxury), and location refinements.
        """
        current_context = self.get_context(user_id)
        now = time.time()

        intent_type = new_intent.get("type", "search")
        if intent_type in ["greeting", "help", "thanks", "bye", "out_of_scope", "faq", "planner"]:
            return new_intent

        merged = dict(current_context)
        query_text = (new_intent.get("query") or "").lower()

        # Handle Cheaper / Budget Modifiers
        if any(w in query_text for w in ["cheaper", "lower price", "less expensive", "more affordable"]):
            old_max = merged.get("max_price")
            if old_max and old_max > 300:
                merged["max_price"] = int(old_max * 0.6)
            else:
                merged["max_price"] = 500

        elif any(w in query_text for w in ["luxury", "premium", "5 star", "high end"]):
            merged["min_price"] = 1500
            prefs = merged.get("preferences") or []
            if "luxury" not in prefs:
                prefs.append("luxury")
            merged["preferences"] = prefs

        elif any(w in query_text for w in ["budget", "pocket friendly", "cheap"]):
            merged["max_price"] = 500

        # Category Switching vs Field Merging
        new_cat = new_intent.get("category")
        old_cat = current_context.get("category")

        if new_cat and old_cat and new_cat != old_cat:
            # Category switched (e.g. from 'restaurant' to 'spa') -> Preserve location, update category
            merged["category"] = new_cat
            merged["min_price"] = new_intent.get("min_price")
            merged["max_price"] = new_intent.get("max_price")
            merged["occasion"] = new_intent.get("occasion")
            merged["preferences"] = new_intent.get("preferences")
            merged["time_filter"] = new_intent.get("time_filter")
        else:
            context_keys = [
                "category", "city", "area", "location", "min_price",
                "max_price", "occasion", "preferences", "group_size", "time_filter"
            ]
            for key in context_keys:
                val = new_intent.get(key)
                if val is not None:
                    merged[key] = val

        # Save merged context with 20-min TTL timestamp
        merged["_last_updated"] = now
        self.sessions[user_id] = merged

        result_intent = dict(new_intent)
        for key in ["category", "city", "area", "location", "min_price", "max_price", "occasion", "preferences", "group_size", "time_filter"]:
            if merged.get(key) is not None:
                result_intent[key] = merged[key]

        return result_intent

    def clear_context(self, user_id: int) -> None:
        """Resets conversation context for a user."""
        if user_id in self.sessions:
            del self.sessions[user_id]


# Singleton instance
memory_manager = ConversationMemoryManager()
