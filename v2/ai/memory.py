import time
from typing import Dict, Any


class ConversationMemoryManager:
    """
    Manages short-term conversational context per Telegram user ID.
    Context automatically expires after 20 minutes (1200 seconds) of inactivity.
    Prevents location bleed across independent queries while preserving continuation context (cheaper/luxury/pagination).
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
        Clears location/category state for independent search queries to avoid location bleed,
        while maintaining context for continuation modifiers (cheaper, luxury, budget).
        """
        current_context = self.get_context(user_id)
        now = time.time()

        intent_type = new_intent.get("type", "search")
        if intent_type in ["greeting", "help", "thanks", "bye", "out_of_scope", "faq", "planner"]:
            return new_intent

        query_text = (new_intent.get("query") or "").lower()

        # Continuation Modifiers Check
        is_continuation = any(w in query_text for w in [
            "cheaper", "lower price", "less expensive", "more affordable",
            "luxury", "premium", "budget", "pocket friendly", "cheap", "show more", "next", "more deals"
        ])

        if not is_continuation:
            # Standalone / Independent search query: start fresh with new_intent to prevent location bleed
            merged = dict(new_intent)
        else:
            merged = dict(current_context)
            if any(w in query_text for w in ["cheaper", "lower price", "less expensive", "more affordable"]):
                old_max = merged.get("max_price")
                if old_max and old_max > 300:
                    merged["max_price"] = int(old_max * 0.6)
                else:
                    merged["max_price"] = 500

            elif any(w in query_text for w in ["luxury", "premium"]):
                merged["min_price"] = 1500
                prefs = merged.get("preferences") or []
                if "luxury" not in prefs:
                    prefs.append("luxury")
                merged["preferences"] = prefs

            elif any(w in query_text for w in ["budget", "pocket friendly", "cheap"]):
                merged["max_price"] = 500

            # Merge explicit fields from new_intent into continuation context
            for k, v in new_intent.items():
                if v is not None and k != "type":
                    merged[k] = v

        # Always enforce explicit new location/area/city/category if present in current message
        if new_intent.get("location") is not None:
            merged["location"] = new_intent.get("location")
            merged["area"] = new_intent.get("area")
            merged["city"] = new_intent.get("city")

        if new_intent.get("category") is not None:
            merged["category"] = new_intent.get("category")

        # Save merged context with timestamp
        merged["_last_updated"] = now
        self.sessions[user_id] = merged

        return merged

    def clear_context(self, user_id: int) -> None:
        """Resets conversation context for a user."""
        if user_id in self.sessions:
            del self.sessions[user_id]


# Singleton instance
memory_manager = ConversationMemoryManager()
