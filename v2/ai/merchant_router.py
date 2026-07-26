"""
Milestone 15 - Merchant & Business Intelligence Router (Updated with Priority Order)
Dedicated router that intercepts all merchant growth, offer review, dashboard, health, promotion, marketing content creator, and business intelligence analytics commands.
Guarantees merchant & business queries NEVER fall back to customer search, planner, recommendations, or comparison.
"""
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

MERCHANT_ROUTES = {
    # Milestone 15 Business Intelligence & Analytics Routes (High Priority)
    "analytics_dashboard": ["business dashboard", "my business dashboard", "bi dashboard", "/business_dashboard"],
    "analytics_summary": ["catalog summary", "summary report", "/catalog_summary"],
    "analytics_category": ["category analytics", "top categories", "/category_analytics"],
    "analytics_brand": ["brand analytics", "top brands", "/brand_analytics"],
    "analytics_location": ["location analytics", "top locations", "/location_analytics"],
    "analytics_discount": ["discount analytics", "/discount_analytics"],
    "analytics_price": ["price analytics", "/price_analytics"],
    "analytics_health": ["catalog health", "/catalog_health"],
    "analytics_distribution": ["offer distribution", "distribution", "/distribution"],
    "analytics_insights": ["business insights", "/business_insights"],
    "analytics_improvements": ["what should we improve?", "what should we improve", "improvement suggestions", "how can the catalog improve?", "/catalog_improvements"],
    "analytics_help": ["business help", "explain analytics", "/business_help"],

    # Milestone 14 AI Content Creator Routes
    "content_instagram": ["create instagram post", "instagram post", "generate instagram post", "ig post", "instagram promo", "ig promo", "/instagram"],
    "content_facebook": ["create facebook post", "facebook post", "generate facebook post", "fb post", "facebook promo", "fb promo", "/facebook"],
    "content_whatsapp": ["create whatsapp promotion", "whatsapp promotion", "whatsapp promo", "/whatsapp"],
    "content_sms": ["create sms campaign", "sms campaign", "sms promo", "/sms"],
    "content_push": ["create push notification", "push notification", "push promo", "/push"],
    "content_caption": ["create promotional caption", "promotional caption", "caption generator", "/caption"],
    "content_hashtags": ["generate hashtags", "hashtags", "hashtag generator", "/hashtags"],
    "content_festival": ["create festival promotion", "festival promotion", "festival promo", "/festival"],
    "content_weekend": ["weekend promotion", "create weekend promotion", "weekend promo", "/weekend_promo"],
    "content_birthday": ["birthday promotion", "create birthday promotion", "birthday promo", "/birthday_promo"],
    "content_email": ["create email campaign", "email campaign", "email promo", "/email"],
    "content_help": ["marketing help", "how should i promote this offer?", "what social media platform is best?", "how can i improve engagement?", "/marketing_help"],

    # Milestone 13 Merchant Agent Routes
    "merchant_review": ["review my offer", "review offer", "review deal", "/review_offer"],
    "merchant_score": ["offer score", "offer quality score", "quality score", "score offer", "/offer_score"],
    "merchant_growth": ["growth suggestions", "growth advice", "growth recommendations", "/growth"],
    "merchant_improve": ["improve description", "improve title", "/improve_desc"],
    "merchant_dashboard": ["merchant dashboard", "my merchant dashboard", "/merchant_dashboard"],
    "merchant_health": ["offer health", "health check", "deal health", "/offer_health"],
    "merchant_compare": ["compare my offers", "compare my deals", "my offer comparison", "/compare_offers"],
    "merchant_promote": ["which offer should i promote?", "which offer should i promote", "what deal to promote", "which offer to promote", "/promote"],
    "merchant_get_customers": ["how can i get more customers?", "how can i get more customers", "get more customers", "/more_customers"],
    "merchant_help": ["merchant help", "merchant guide", "/merchant_help"],
    "merchant_improve_help": ["how can i improve?", "how can i improve", "how to improve", "/how_to_improve"],
}


def route_merchant_intent(message: str) -> Optional[Dict[str, Any]]:
    """
    Evaluates message against Merchant, Content Creator, and Business Analytics Routes.
    Returns merchant intent dict if matched, or None if customer query.
    """
    text = (message or "").lower().strip()

    for intent_type, triggers in MERCHANT_ROUTES.items():
        if any(tr == text or text.startswith(tr) or text.endswith(tr) for tr in triggers):
            logger.info(f"[Merchant/Analytics Router Intercepted]: {intent_type} for message: '{message}'")
            return {
                "type": intent_type,
                "is_merchant": True,
                "query": message
            }

    return None
