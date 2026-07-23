import time
from typing import Dict, Any


class ConversationMemoryManager:
    """
    Manages conversational context per Telegram user/chat ID with automatic TTL expiration.
    """

    def __init__(self, ttl_seconds: int = 1800):  # Default: 30 minutes TTL
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

        # Return clean copy without internal metadata keys
        return {k: v for k, v in session.items() if not k.startswith("_")}

    def update_context(self, user_id: int, new_intent: Dict[str, Any]) -> Dict[str, Any]:
        """
        Merges new intent fields with existing conversation context.
        If a new distinct category is requested, updates category and resets price/occasion.
        """
        current_context = self.get_context(user_id)
        now = time.time()

        intent_type = new_intent.get("type", "search")
        if intent_type in ["greeting", "help", "thanks", "bye", "out_of_scope", "faq"]:
            return new_intent

        merged = dict(current_context)

        new_cat = new_intent.get("category")
        old_cat = current_context.get("category")

        if new_cat and old_cat and new_cat != old_cat:
            # User switched category (e.g., from 'restaurant' to 'spa')
            merged["category"] = new_cat
            merged["min_price"] = new_intent.get("min_price")
            merged["max_price"] = new_intent.get("max_price")
            merged["occasion"] = new_intent.get("occasion")
            merged["preferences"] = new_intent.get("preferences")
            merged["time_filter"] = new_intent.get("time_filter")
        else:
            # Merge fields if specified in new_intent
            context_keys = [
                "category", "city", "area", "location", "min_price",
                "max_price", "occasion", "preferences", "group_size", "time_filter"
            ]
            for key in context_keys:
                val = new_intent.get(key)
                if val is not None:
                    merged[key] = val

        # Save merged context with updated timestamp
        merged["_last_updated"] = now
        self.sessions[user_id] = merged

        # Return full merged intent dictionary
        result_intent = dict(new_intent)
        for key in ["category", "city", "area", "location", "min_price", "max_price", "occasion", "preferences", "group_size", "time_filter"]:
            if merged.get(key) is not None:
                result_intent[key] = merged[key]

        return result_intent

    def clear_context(self, user_id: int) -> None:
        """Resets context for a given user."""
        if user_id in self.sessions:
            del self.sessions[user_id]


# Singleton instance
memory_manager = ConversationMemoryManager()
