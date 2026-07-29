import time
from typing import Dict, Any, Optional

MODIFIER_KEYWORDS = [
    "cheaper", "cheapest", "lower price", "higher discount", "highest discount", "highest",
    "best discount", "discount", "luxury", "premium", "make it", "change to", "actually",
    "under", "below", "budget", "only", "instead", "change location", "change budget",
    "massage", "couples", "couple", "buffet", "nearby", "near"
]


class ConversationMemoryManager:
    """
    AI Deal Concierge Conversation Memory Manager:
    - Maintains multi-turn dialog state across messages (category, location, budget, occasion).
    - Resets active conversation state after a search completes when a new top-level intent arrives.
    - Preserves context for explicit follow-up modifiers ('Show cheaper options', 'Actually make it under ₹1500').
    - Enforces a 15-minute session timeout (TTL).
    """

    def __init__(self, ttl_seconds: int = 900):  # 15 minutes (900 seconds) TTL
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

    def is_session_active(self, user_id: int) -> bool:
        """Returns True if user has an active, non-expired search session with context."""
        ctx = self.get_context(user_id)
        return bool(ctx and (ctx.get("category") or ctx.get("location") or ctx.get("max_price")))

    def mark_completed(self, user_id: int):
        """Marks current search session as completed after recommendations are delivered."""
        if user_id in self.sessions:
            self.sessions[user_id]["_completed"] = True
            self.sessions[user_id]["_pending_field"] = None

    def get_pending_field(self, user_id: int) -> Optional[str]:
        """Returns currently pending field name ('location', 'budget', 'occasion') if any."""
        session = self.sessions.get(user_id, {})
        return session.get("_pending_field")

    def set_pending_field(self, user_id: int, field_name: Optional[str]):
        """Sets or clears pending field for multi-turn prompt flow."""
        if user_id not in self.sessions:
            self.sessions[user_id] = {"_last_updated": time.time(), "_completed": False}
        self.sessions[user_id]["_pending_field"] = field_name

    def update_context(self, user_id: int, new_intent: Dict[str, Any]) -> Dict[str, Any]:
        """
        Merges new intent fields with existing conversation context or starts a fresh conversation.
        """
        current_context = self.get_context(user_id)
        session = self.sessions.get(user_id, {})
        is_completed = session.get("_completed", False)
        pending_field = session.get("_pending_field")
        now = time.time()

        intent_type = new_intent.get("type", "search")
        if intent_type in ["greeting", "help", "thanks", "bye", "out_of_scope", "faq", "planner"]:
            return new_intent

        query_text = (new_intent.get("query") or "").lower()

        # Check if query is an explicit modifier / continuation
        is_modifier = any(w in query_text for w in MODIFIER_KEYWORDS)
        was_pending = pending_field is not None

        # Handle answers to pending questions
        if pending_field == "location" and (new_intent.get("location") or new_intent.get("area")):
            self.set_pending_field(user_id, None)
            was_pending = True
        elif pending_field == "budget" and new_intent.get("max_price"):
            self.set_pending_field(user_id, None)
            was_pending = True
        elif pending_field == "occasion" and new_intent.get("occasion"):
            self.set_pending_field(user_id, None)
            was_pending = True

        # Determine if this should start a FRESH conversation state:
        # A new top-level intent starts fresh if:
        # - Search was already completed and current message is not a continuation modifier or pending answer
        # - Or there is no active context and no pending field
        is_new_request = (is_completed and not is_modifier and not was_pending) or (
            not current_context and not was_pending and not is_modifier
        )

        if is_new_request:
            merged = dict(new_intent)
            merged["_completed"] = False
            merged["_pending_field"] = None
        elif current_context and (was_pending or is_modifier or not new_intent.get("category") or new_intent.get("category") == current_context.get("category") or new_intent.get("type") == "occasion"):
            # Merge with existing active context
            merged = dict(current_context)

            # Apply modifiers & dining_type filters
            if "buffet" in query_text or new_intent.get("dining_type") == "buffet" or new_intent.get("meal_type") == "buffet":
                merged["dining_type"] = "buffet"
                merged["meal_type"] = "buffet"
                merged["category"] = "restaurant"
            elif "cheaper" in query_text or "lower price" in query_text:
                old_max = merged.get("max_price")
                merged["max_price"] = int(old_max * 0.7) if old_max and old_max > 300 else 500
            elif "higher discount" in query_text or "best discount" in query_text or "highest discount" in query_text or "highest" in query_text:
                merged["sort_by_discount"] = True
            elif "luxury" in query_text or "premium" in query_text:
                merged["min_price"] = 1500

            # Override merged fields from new_intent if present
            for k, v in new_intent.items():
                if v is not None and k != "type":
                    merged[k] = v

            # If user explicitly changed location, reset sort_by_discount to ensure fresh location search priority
            if new_intent.get("location") or new_intent.get("area"):
                merged["sort_by_discount"] = False
        else:
            merged = dict(new_intent)
            merged["_completed"] = False

        # For a brand new top-level request, reset location, budget, and occasion unless explicitly specified in new_intent
        if is_new_request:
            merged["location"] = new_intent.get("location")
            merged["area"] = new_intent.get("area")
            merged["city"] = new_intent.get("city")
            merged["max_price"] = new_intent.get("max_price")
            merged["occasion"] = new_intent.get("occasion")
            merged["_completed"] = False

        # Save updated context
        merged["_last_updated"] = now
        self.sessions[user_id] = merged
        return merged

    def clear_context(self, user_id: int) -> None:
        """Resets conversation context for a user."""
        if user_id in self.sessions:
            del self.sessions[user_id]


# Singleton instance
memory_manager = ConversationMemoryManager()
