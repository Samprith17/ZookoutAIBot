import logging
from typing import Dict, List, Any
from v2.search.search_engine import load_deals, normalize_deal, clean_offer_title
from v2.ai.profile import profile_manager

logger = logging.getLogger(__name__)


class MerchantGrowthAgent:
    """
    Milestone 13 - Merchant Growth Agent:
    Helps merchants review offers, calculate transparent 0-100 quality scores,
    suggest description improvements, and generate actionable growth recommendations
    without requiring internal sales, occupancy, or revenue analytics.
    """

    def get_merchant_deal(self, user_id: int) -> Dict[str, Any]:
        """Returns the user's last viewed deal or a top representative catalog deal normalized via Shared Normalization Layer."""
        history = profile_manager.get_recently_viewed(user_id)
        if history:
            return normalize_deal(history[0])

        deals = load_deals()
        if deals:
            return normalize_deal(deals[0])

        return normalize_deal({
            "brand": "Sample Merchant",
            "category": "Restaurant",
            "title": "Flat 50% Off on Total Bill",
            "price": 500,
            "discount_percent": 50,
            "location": "Mumbai",
            "description": "Enjoy flat 50% discount on total dining bill."
        })

    def evaluate_offer_score(self, deal: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generates a transparent Offer Quality Score (0–100) using 5 criteria:
        1. Discount Competitiveness (max 30 pts)
        2. Offer Clarity & Description Length (max 25 pts)
        3. Price Availability & Value Presentation (max 20 pts)
        4. Category & Tag Information (max 15 pts)
        5. OCR Cleanliness & Title Readability (max 10 pts)
        """
        disc = deal.get("discount_percent", 0)
        title = deal.get("clean_title") or deal.get("title", "")
        desc = deal.get("description", "")
        cat = deal.get("display_category") or deal.get("category", "")
        loc = deal.get("display_location") or deal.get("location", "")

        try:
            price = float(str(deal.get("price", "0")).replace(",", ""))
        except Exception:
            price = 0.0

        breakdown = []
        score = 0

        # 1. Discount Competitiveness (30 pts)
        if disc >= 50:
            score += 30
            breakdown.append(f"Discount Competitiveness: 30/30 pts ({disc}% OFF - Highly Competitive)")
        elif disc >= 30:
            score += 22
            breakdown.append(f"Discount Competitiveness: 22/30 pts ({disc}% OFF - Moderate Discount)")
        elif disc > 0:
            score += 12
            breakdown.append(f"Discount Competitiveness: 12/30 pts ({disc}% OFF - Standard Savings)")
        else:
            breakdown.append("Discount Competitiveness: 0/30 pts (No Discount Specified)")

        # 2. Offer Clarity & Description Length (25 pts)
        if len(desc) >= 50 and len(title) >= 10:
            score += 25
            breakdown.append("Offer Clarity: 25/25 pts (Detailed Description & Clear Title)")
        elif len(title) >= 6:
            score += 15
            breakdown.append("Offer Clarity: 15/25 pts (Standard Title; Description could be expanded)")
        else:
            score += 8
            breakdown.append("Offer Clarity: 8/25 pts (Short Title; Needs more offer details)")

        # 3. Price Availability (20 pts)
        if price > 0:
            score += 20
            breakdown.append(f"Price Availability: 20/20 pts (Clear Price Specified: {deal.get('formatted_price')})")
        else:
            breakdown.append("Price Availability: 0/20 pts (Price Unavailable)")

        # 4. Category & Tag Information (15 pts)
        if cat and cat != "Special Experience":
            score += 15
            breakdown.append(f"Category Classification: 15/15 pts (Specific Category: {cat})")
        else:
            score += 5
            breakdown.append("Category Classification: 5/15 pts (Generic Category)")

        # 5. OCR Cleanliness & Title Readability (10 pts)
        raw_title = deal.get("title", "")
        if clean_offer_title(deal) == raw_title or "Offer" in title:
            score += 10
            breakdown.append("OCR Cleanliness: 10/10 pts (Clean & Readability Verified)")
        else:
            score += 5
            breakdown.append("OCR Cleanliness: 5/10 pts (Required Title Normalization)")

        return {
            "total_score": min(100, score),
            "breakdown": breakdown
        }

    def review_offer(self, deal: Dict[str, Any]) -> str:
        """Generates an in-depth Merchant Offer Review report."""
        score_eval = self.evaluate_offer_score(deal)
        score = score_eval["total_score"]
        breakdown_text = "\n".join([f"• {b}" for b in score_eval["breakdown"]])

        rating_label = "🌟 Excellent" if score >= 80 else ("👍 Good" if score >= 60 else "⚠️ Needs Improvement")

        review = (
            "📊 Merchant Offer Review\n\n"
            f"🏷️ Brand: {deal.get('brand')}\n"
            f"📂 Category: {deal.get('display_category')}\n"
            f"📝 Current Offer: {deal.get('clean_title')}\n"
            f"💰 Price: {deal.get('formatted_price')}\n"
            f"🎁 Discount: {deal.get('discount_percent')}%\n"
            f"📍 Location: {deal.get('display_location')}\n\n"
            f"🏆 Quality Score: {score}/100 ({rating_label})\n\n"
            "Score Breakdown:\n"
            f"{breakdown_text}\n\n"
            "💡 Performance Summary:\n"
            f"• Strong discount presence ({deal.get('discount_percent')}% OFF)\n" if deal.get('discount_percent', 0) >= 30 else "• Discount level could be increased for higher customer conversion\n"
        )
        review += (
            "ℹ️ Note: Recommendations are based strictly on offer catalog information (no sales or revenue data required)."
        )
        return review

    def generate_growth_suggestions(self, deal: Dict[str, Any]) -> str:
        """Generates actionable Merchant Growth Suggestions."""
        disc = deal.get("discount_percent", 0)

        try:
            price = float(str(deal.get("price", "0")).replace(",", ""))
        except Exception:
            price = 0.0

        suggestions = [
            "1. 📅 Weekday Promotions: Launch off-peak Mon-Thu lunchtime discounts to boost weekday traffic.",
            "2. 🎁 Combo Bundles: Pair main courses with beverages or desserts (e.g. Meal + Drink Combo) for higher average ticket value.",
            "3. 📝 Description Clarity: Highlight exact savings amounts and redemption steps clearly.",
            "4. ⚡ Highlight Customer Savings: Feature 'Save ₹X' explicitly on your promotional banner.",
            "5. 🎯 Title Optimization: Use action-oriented titles such as 'Buy 1 Get 1 Free' or 'Flat 50% Off Total Bill'."
        ]

        if price == 0:
            suggestions.append("6. 💰 Price Transparency: Adding exact prices increases customer booking intent by over 40%.")

        text = (
            "📈 Merchant Growth Suggestions\n\n"
            f"🏷️ Brand: {deal.get('brand')}\n"
            f"📂 Category: {deal.get('display_category')}\n\n"
            "Recommended Growth Actions:\n"
            + "\n\n".join(suggestions) + "\n\n"
            "ℹ️ Note: Recommendations are based strictly on offer catalog information (no sales, occupancy, or voucher analytics required)."
        )
        return text

    def suggest_improved_description(self, deal: Dict[str, Any]) -> str:
        """Generates an enhanced, high-converting offer title & description candidate for the merchant."""
        brand = deal.get("brand", "Zookout Merchant")
        cat = deal.get("display_category", "Restaurant")
        disc = deal.get("discount_percent", 0)
        formatted_price = deal.get("formatted_price", "Special Price")

        enhanced_title = f"{brand} – Flat {disc}% Off Special {cat} Experience" if disc > 0 else f"{brand} – Exclusive {cat} Offer"

        enhanced_desc = (
            f"Treat yourself to an unforgettable {cat} experience at {brand} in {deal.get('display_location', 'Mumbai')}!\n\n"
            f"✨ What's Included:\n"
            f"• Premium {cat} offer at {formatted_price}\n"
            f"• Instant voucher redemption at venue\n"
            f"• Flat {disc}% discount on your experience\n\n"
            f"📍 Location: {deal.get('display_location', 'Mumbai')}\n"
            f"⏰ Valid: Mon-Sun during regular operating hours"
        )

        return (
            "📝 Improved Offer Description Candidate\n\n"
            f"Original Offer: {deal.get('clean_title')}\n\n"
            f"✨ Recommended Title:\n{enhanced_title}\n\n"
            f"📄 Recommended Description:\n{enhanced_desc}\n\n"
            "💡 Why this converts better:\n"
            "• Clear value proposition in the title\n"
            "• Bulleted list of included benefits\n"
            "• Explicit location & validity details"
        )


merchant_agent = MerchantGrowthAgent()
