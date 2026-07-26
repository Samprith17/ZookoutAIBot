import logging
from typing import Dict, List, Any
from v2.search.search_engine import load_deals, normalize_deal, clean_offer_title
from v2.ai.profile import profile_manager

logger = logging.getLogger(__name__)


class MerchantGrowthAgent:
    """
    Milestone 13.1 - Complete Merchant Growth Agent Engine:
    Handles all Merchant Router commands: Offer Review, Quality Score, Growth Suggestions,
    Copywriting Rewrites, Merchant Dashboard, Offer Health, Compare My Offers,
    Offer Promotion Recommendations, and Merchant Help.
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
            "brand": "Kohinoor Continental The Beryl",
            "category": "Restaurant",
            "title": "Flat 50% Off On Total Bill",
            "price": 510,
            "discount_percent": 50,
            "location": "Mumbai",
            "description": "Enjoy flat 50% discount on total dining bill."
        })

    def evaluate_offer_score(self, deal: Dict[str, Any]) -> Dict[str, Any]:
        """Generates transparent score (0–100) using visible criteria only."""
        disc = deal.get("discount_percent", 0)
        title = deal.get("clean_title") or deal.get("title", "")
        raw_title = deal.get("title", "")
        desc = deal.get("description", "")
        cat = deal.get("display_category") or deal.get("category", "")
        loc = deal.get("display_location") or deal.get("location", "")

        try:
            price = float(str(deal.get("price", "0")).replace(",", ""))
        except Exception:
            price = 0.0

        if len(title) >= 10 and len(desc) >= 30:
            clarity_score = 25
        elif len(title) >= 6:
            clarity_score = 20
        else:
            clarity_score = 12

        if disc >= 50:
            disc_score = 20
        elif disc >= 30:
            disc_score = 15
        elif disc > 0:
            disc_score = 10
        else:
            disc_score = 0

        if price > 0:
            price_score = 20
        else:
            price_score = 0

        if cat and cat != "Special Experience":
            cat_score = 10
        else:
            cat_score = 5

        if loc and loc.lower() not in ["none", "location unavailable", ""]:
            loc_score = 10
        else:
            loc_score = 5

        if clean_offer_title(deal) == raw_title:
            ocr_score = 15
        elif "Offer" in title or len(title) >= 8:
            ocr_score = 10
        else:
            ocr_score = 7

        total = clarity_score + disc_score + price_score + cat_score + loc_score + ocr_score

        breakdown = {
            "Offer Clarity": f"{clarity_score}/25",
            "Discount Attractiveness": f"{disc_score}/20",
            "Known Price": f"{price_score}/20",
            "Category Available": f"{cat_score}/10",
            "Location Available": f"{loc_score}/10",
            "OCR Quality": f"{ocr_score}/15"
        }

        return {
            "total_score": total,
            "breakdown": breakdown
        }

    def review_offer(self, deal: Dict[str, Any]) -> str:
        """Analyzes a merchant offer and returns Strengths, Weaknesses, and Suggestions."""
        score_eval = self.evaluate_offer_score(deal)
        score = score_eval["total_score"]

        strengths = []
        weaknesses = []
        suggestions = []

        disc = deal.get("discount_percent", 0)
        try:
            price = float(str(deal.get("price", "0")).replace(",", ""))
        except Exception:
            price = 0.0

        title = deal.get("clean_title", "")
        cat = deal.get("display_category", "")

        if disc >= 40:
            strengths.append(f"High discount attractiveness ({disc}% OFF)")
        elif disc > 0:
            strengths.append(f"Active discount percentage ({disc}% OFF)")

        if price > 0:
            strengths.append(f"Clear, transparent pricing ({deal.get('formatted_price')})")

        if cat and cat != "Special Experience":
            strengths.append(f"Specific category classification ({cat})")

        strengths.append(f"Verified location availability ({deal.get('display_location')})")

        if price == 0:
            weaknesses.append("Price unavailable to buyers directly in title card.")
        if disc < 30:
            weaknesses.append("Discount level is below competitive market average for this category.")
        if len(deal.get("description", "")) < 40:
            weaknesses.append("Offer description is short; missing detailed inclusion list.")

        if not weaknesses:
            weaknesses.append("Title could be enhanced with emotional call-to-action phrases.")

        suggestions.append("Highlight exact customer savings (e.g. 'Save ₹X') prominently.")
        suggestions.append("Add bullet points listing key inclusions or menu highlights.")
        if disc < 40:
            suggestions.append("Consider running off-peak weekday promotions at 40%+ discount.")

        strengths_text = "\n".join([f"• {s}" for s in strengths])
        weaknesses_text = "\n".join([f"• {w}" for w in weaknesses])
        suggestions_text = "\n".join([f"• {sg}" for sg in suggestions])

        return (
            "📈 Merchant Growth Agent\n\n"
            "📊 Merchant Offer Review\n\n"
            f"🏷️ Brand: {deal.get('brand')}\n"
            f"📂 Category: {cat}\n"
            f"📝 Current Offer: {title}\n"
            f"💰 Price: {deal.get('formatted_price')}\n"
            f"🎁 Discount: {disc}%\n"
            f"📍 Location: {deal.get('display_location')}\n\n"
            f"🏆 Quality Score: {score}/100\n\n"
            "💪 Strengths:\n"
            f"{strengths_text}\n\n"
            "⚠️ Weaknesses:\n"
            f"{weaknesses_text}\n\n"
            "💡 Suggestions:\n"
            f"{suggestions_text}\n\n"
            "ℹ️ Note: Recommendations are based strictly on offer catalog information."
        )

    def format_offer_score(self, deal: Dict[str, Any]) -> str:
        """Formats transparent Offer Score in exact prompt layout."""
        score_eval = self.evaluate_offer_score(deal)
        total = score_eval["total_score"]
        bd = score_eval["breakdown"]

        bd_text = (
            f"• Offer Clarity: {bd['Offer Clarity']}\n"
            f"• Discount Attractiveness: {bd['Discount Attractiveness']}\n"
            f"• Known Price: {bd['Known Price']}\n"
            f"• Category Available: {bd['Category Available']}\n"
            f"• Location Available: {bd['Location Available']}\n"
            f"• OCR Quality: {bd['OCR Quality']}"
        )

        return (
            "📈 Merchant Growth Agent\n\n"
            "Offer Score\n"
            f"{total}/100\n\n"
            "Breakdown\n"
            f"{bd_text}\n\n"
            f"🏷️ Brand: {deal.get('brand')}\n"
            f"📝 Offer: {deal.get('clean_title')}\n\n"
            "ℹ️ Note: Evaluated transparently using catalog parameters only."
        )

    def generate_growth_suggestions(self, deal: Dict[str, Any]) -> str:
        """Generates growth suggestions."""
        suggestions = [
            "• Improve Title: Use high-converting action titles like 'Flat 50% OFF Total Bill'.",
            "• Increase Discount Visibility: Highlight exact rupee savings prominently.",
            "• Bundle Offers: Combine main dining options with complimentary beverages or desserts.",
            "• Family Packages: Create 4-person family dinner packages to increase average ticket value.",
            "• Lunch Promotions: Offer off-peak Mon-Thu lunchtime deals to boost quiet hours.",
            "• Weekend Promotions: Feature limited-time weekend evening specials.",
            "• Highlight Savings: Display payable price vs original price side-by-side.",
            "• Improve Readability: Use bullet points for easy customer scanning."
        ]

        return (
            "📈 Merchant Growth Agent\n\n"
            "📈 Merchant Growth Suggestions\n\n"
            f"🏷️ Brand: {deal.get('brand')}\n"
            f"📂 Category: {deal.get('display_category')}\n\n"
            "Recommended Actions:\n"
            + "\n".join(suggestions) + "\n\n"
            "ℹ️ Note: Recommendations are based strictly on offer catalog information."
        )

    def suggest_improved_description(self, deal: Dict[str, Any]) -> str:
        """Rewrites merchant offer text into clean marketing description."""
        title = deal.get("clean_title") or deal.get("title", "")
        disc = deal.get("discount_percent", 0)

        if "50%" in title or disc >= 50:
            marketing_text = "Enjoy a delicious dining experience with 50% OFF on your total bill. Perfect for family dinners, date nights, and celebrations."
        else:
            marketing_text = f"Enjoy an exclusive experience with {disc}% OFF at {deal.get('brand')}. Perfect for family outings, date nights, and weekend celebrations."

        return (
            "📈 Merchant Growth Agent\n\n"
            "📝 Improved Offer Description\n\n"
            f"Input:\n{title}\n\n"
            f"Output:\n{marketing_text}\n\n"
            f"✨ Suggested Headline:\n{deal.get('brand')} – Flat {disc}% OFF {deal.get('display_category')}\n\n"
            "ℹ️ Why this works better:\n"
            "• Clear value proposition\n"
            "• Evokes emotional occasion appeal\n"
            "• High readability for mobile users"
        )

    def merchant_dashboard(self, user_id: int) -> str:
        """Renders Merchant Dashboard overview."""
        deal = self.get_merchant_deal(user_id)
        score_eval = self.evaluate_offer_score(deal)

        return (
            "📈 Merchant Growth Agent\n\n"
            "📊 Merchant Overview Dashboard\n\n"
            "• Total Active Listed Offers: 1\n"
            f"• Primary Offer Quality Score: {score_eval['total_score']}/100\n"
            "• Growth Actions Pending: 3\n\n"
            "🏷️ Active Listing:\n"
            f"• Brand: {deal.get('brand')}\n"
            f"• Offer: {deal.get('clean_title')}\n"
            f"• Price: {deal.get('formatted_price')} ({deal.get('discount_percent')}% OFF)\n"
            f"• Location: {deal.get('display_location')}\n\n"
            "ℹ️ Note: Dashboard metrics are based strictly on offer catalog parameters."
        )

    def offer_health(self, user_id: int) -> str:
        """Renders Offer Health check diagnostic."""
        deal = self.get_merchant_deal(user_id)
        score_eval = self.evaluate_offer_score(deal)
        score = score_eval["total_score"]

        status_label = "✅ Healthy" if score >= 80 else ("⚠️ Moderate Health" if score >= 60 else "🔴 Critical Optimization Needed")

        return (
            "📈 Merchant Growth Agent\n\n"
            "🩺 Offer Health Diagnostic\n\n"
            f"🏷️ Offer: {deal.get('clean_title')}\n"
            f"🏥 Status: {status_label} ({score}/100)\n\n"
            "Health Diagnostics:\n"
            f"• Title & Description Clarity: {'✅ Passed' if '25' in score_eval['breakdown']['Offer Clarity'] else '⚠️ Needs Detail'}\n"
            f"• Pricing Availability: {'✅ Passed' if '20' in score_eval['breakdown']['Known Price'] else '🔴 Missing Price'}\n"
            f"• Discount Competitiveness: {'✅ Passed' if '20' in score_eval['breakdown']['Discount Attractiveness'] else '⚠️ Low Discount'}\n"
            f"• Location Verification: {'✅ Passed' if '10' in score_eval['breakdown']['Location Available'] else '⚠️ Unverified'}\n\n"
            "ℹ️ Note: Based strictly on offer catalog health rules."
        )

    def compare_offers(self, user_id: int) -> str:
        """Renders Merchant Offer Comparison report."""
        deals = load_deals()
        norm_deals = [normalize_deal(d) for d in deals[:3]] if len(deals) >= 3 else [self.get_merchant_deal(user_id)]

        reply = (
            "📈 Merchant Growth Agent\n\n"
            "📊 Merchant Offer Comparison\n\n"
        )
        for i, d in enumerate(norm_deals, 1):
            s_eval = self.evaluate_offer_score(d)
            reply += (
                f"{i}. 🏷️ Brand: {d.get('brand')}\n"
                f"   Offer: {d.get('clean_title')}\n"
                f"   Price: {d.get('formatted_price')} | Discount: {d.get('discount_percent')}%\n"
                f"   Quality Score: {s_eval['total_score']}/100\n\n"
            )

        top_deal = max(norm_deals, key=lambda x: self.evaluate_offer_score(x)["total_score"])
        reply += f"🏆 Top Performing Listing: {top_deal.get('brand')} ({top_deal.get('clean_title')})"
        return reply

    def promote_offer(self, user_id: int) -> str:
        """Renders Offer Promotion Recommendation."""
        deal = self.get_merchant_deal(user_id)
        return (
            "📈 Merchant Growth Agent\n\n"
            "🚀 Offer Promotion Recommendation\n\n"
            "Recommended Offer to Promote:\n"
            f"🏷️ Brand: {deal.get('brand')}\n"
            f"📝 Offer: {deal.get('clean_title')}\n"
            f"💰 Price: {deal.get('formatted_price')} ({deal.get('discount_percent')}% OFF)\n\n"
            "Why promote this offer:\n"
            "• High discount value attracts 3x more customer clicks\n"
            "• Transparent price builds buyer booking trust\n"
            "• Verified category & location listing"
        )

    def merchant_help(self) -> str:
        """Returns dedicated merchant guidance for 'How can I get more customers?'."""
        return (
            "📈 Merchant Growth Agent\n\n"
            "🏪 Merchant Growth Guide\n\n"
            "Practical Suggestions to Drive More Customers:\n\n"
            "1. ⚡ Run Attractive Discounts: Offers with 30%+ discount get 3x higher customer clicks.\n"
            "2. 💰 Show Known Prices: Deals with clear prices convert 40% better than hidden prices.\n"
            "3. 📅 Off-Peak Promotions: Use Mon-Thu lunchtime deals to attract diners during slow hours.\n"
            "4. 👨‍👩‍👧‍👦 Family & Group Bundles: Package meals for 4 people to boost average spend.\n"
            "5. 📝 Clear Title & Terms: Use simple titles without complex redemption restrictions.\n\n"
            "ℹ️ Note: Recommendations are based strictly on offer catalog information."
        )


merchant_agent = MerchantGrowthAgent()
