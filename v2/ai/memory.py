import time
from typing import Dict, Any, Optional


class ConversationMemoryManager:
    """
    AI Deal Concierge Conversation Memory Manager:
    - Maintains multi-turn dialog state across messages (category, location, budget, occasion).
    - Supports single-detail modifications ('Actually make it under ₹1500').
    - Supports contextual follow-ups ('Show cheaper options', 'Higher discount', 'Luxury options').
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

    def get_pending_field(self, user_id: int) -> Optional[str]:
        """Returns currently pending field name ('location', 'budget', 'occasion') if any."""
        session = self.sessions.get(user_id, {})
        return session.get("_pending_field")

    def set_pending_field(self, user_id: int, field_name: Optional[str]):
        """Sets or clears pending field for multi-turn prompt flow."""
        if user_id not in self.sessions:
            self.sessions[user_id] = {"_last_updated": time.time()}
        self.sessions[user_id]["_pending_field"] = field_name

    def update_context(self, user_id: int, new_intent: Dict[str, Any]) -> Dict[str, Any]:
        """
        Merges new intent fields with existing conversation context.
        Supports single-detail modifications ('Actually make it under ₹1500')
        and preserves active multi-turn session state.
        """
        current_context = self.get_context(user_id)
        now = time.time()

        intent_type = new_intent.get("type", "search")
        if intent_type in ["greeting", "help", "thanks", "bye", "out_of_scope", "faq", "planner"]:
            return new_intent

        query_text = (new_intent.get("query") or "").lower()

        # Check for single-detail modification or continuation
        is_modification = any(w in query_text for w in [
            "make it", "change to", "actually", "under", "below", "cheaper",
            "higher discount", "luxury", "budget", "only"
        ])

        pending_field = self.get_pending_field(user_id)
        was_pending = pending_field is not None

        # Handle explicit answers to pending questions
        if pending_field == "location" and (new_intent.get("location") or new_intent.get("area")):
            self.set_pending_field(user_id, None)
        elif pending_field == "budget" and new_intent.get("max_price"):
            self.set_pending_field(user_id, None)
        elif pending_field == "occasion" and new_intent.get("occasion"):
            self.set_pending_field(user_id, None)

        if current_context and (was_pending or is_modification or not new_intent.get("category") or new_intent.get("category") == current_context.get("category") or new_intent.get("type") == "occasion"):
            # Merge with existing context
            merged = dict(current_context)

            # Apply modifiers
            if "cheaper" in query_text or "lower price" in query_text:
                old_max = merged.get("max_price")
                merged["max_price"] = int(old_max * 0.7) if old_max and old_max > 300 else 500
            elif "higher discount" in query_text or "best discount" in query_text:
                merged["sort_by_discount"] = True
            elif "luxury" in query_text or "premium" in query_text:
                merged["min_price"] = 1500

            # Override merged fields from new_intent if present
            for k, v in new_intent.items():
                if v is not None and k != "type":
                    merged[k] = v
        else:
            # New standalone query: start with new_intent
            merged = dict(new_intent)

        # Always enforce explicit new intent fields
        if new_intent.get("location") is not None:
            merged["location"] = new_intent.get("location")
            merged["area"] = new_intent.get("area")
            merged["city"] = new_intent.get("city")

        if new_intent.get("category") is not None:
            merged["category"] = new_intent.get("category")

        if new_intent.get("max_price") is not None:
            merged["max_price"] = new_intent.get("max_price")

        if new_intent.get("occasion") is not None:
            merged["occasion"] = new_intent.get("occasion")

        # Save updated context
        merged["_last_updated"] = now

        # Retain pending_field in session if still set
        if pending_field and not new_intent.get("location") and not new_intent.get("max_price") and not new_intent.get("occasion"):
            merged["_pending_field"] = pending_field

        self.sessions[user_id] = merged
        return merged

    def clear_context(self, user_id: int) -> None:
        """Resets conversation context for a user."""
        if user_id in self.sessions:
            del self.sessions[user_id]


# Singleton instance
memory_manager = ConversationMemoryManager()
