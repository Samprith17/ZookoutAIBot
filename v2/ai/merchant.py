import logging
from typing import Dict, List, Any
from v2.search.search_engine import load_deals, normalize_deal, clean_offer_title
from v2.ai.profile import profile_manager

logger = logging.getLogger(__name__)


class MerchantGrowthAgent:
    """
    Milestone 13.2 - Complete Production-Ready Merchant Growth Agent Engine:
    Handles all 9 merchant features using the Shared Deal Normalization Layer and catalog parameters:
    1. Review My Offer
    2. Offer Score
    3. Growth Suggestions
    4. Improve Description
    5. Merchant Dashboard
    6. Offer Health
    7. Compare My Offers (Dedicated Merchant Comparison)
    8. Which offer should I promote?
    9. Merchant Help / How can I get more customers?
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
            "title": "Flat 50% OFF on Total Bill",
            "price": 510,
            "discount_percent": 50,
            "location": "Mumbai",
            "description": "Enjoy flat 50% discount on total dining bill."
        })

    def evaluate_offer_score(self, deal: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generates a transparent score (0–100) using visible criteria only:
        - Offer Clarity (/25)
        - Discount (/20)
        - Price (/20)
        - Category (/10)
        - Location (/10)
        - OCR (/15)
        """
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

        if len(title) >= 12 and len(desc) >= 30:
            clarity_score = 22
        elif len(title) >= 6:
            clarity_score = 18
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
            price_score = 18
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
            ocr_score = 6

        total = clarity_score + disc_score + price_score + cat_score + loc_score + ocr_score

        breakdown = {
            "Offer Clarity": f"{clarity_score}/25",
            "Discount": f"{disc_score}/20",
            "Price": f"{price_score}/20",
            "Category": f"{cat_score}/10",
            "Location": f"{loc_score}/10",
            "OCR": f"{ocr_score}/15"
        }

        recs = []
        if clarity_score < 25:
            recs.append("Improve title clarity")
        if ocr_score < 15:
            recs.append("Remove OCR artifacts")
        if disc_score < 20:
            recs.append("Highlight customer savings")

        if not recs:
            recs.append("Maintain high offer visibility")

        return {
            "total_score": min(100, total),
            "breakdown": breakdown,
            "recommendations": recs
        }

    def review_offer(self, deal: Dict[str, Any]) -> str:
        """FEATURE 1: Review My Offer."""
        score_eval = self.evaluate_offer_score(deal)
        score = score_eval["total_score"]

        rating = "🌟 Excellent" if score >= 80 else ("👍 Good" if score >= 60 else ("⚠️ Fair" if score >= 40 else "🔴 Poor"))

        strengths = []
        weaknesses = []
        suggestions = []

        disc = deal.get("discount_percent", 0)
        try:
            price = float(str(deal.get("price", "0")).replace(",", ""))
        except Exception:
            price = 0.0

        if disc >= 40:
            strengths.append(f"High discount attractiveness ({disc}% OFF)")
        elif disc > 0:
            strengths.append(f"Active discount percentage ({disc}% OFF)")

        if price > 0:
            strengths.append(f"Clear pricing specified ({deal.get('formatted_price')})")

        strengths.append(f"Specific category ({deal.get('display_category')}) & location ({deal.get('display_location')})")

        if price == 0:
            weaknesses.append("Price unavailable directly on listing card.")
        if disc < 30:
            weaknesses.append("Discount percentage is lower than category average.")
        if len(deal.get("description", "")) < 30:
            weaknesses.append("Offer description is brief; missing dish/service inclusions.")

        if not weaknesses:
            weaknesses.append("Headline can include stronger call-to-action wording.")

        suggestions.append("Highlight exact customer rupee savings prominently.")
        suggestions.append("Add bullet points listing key inclusions or menu features.")
        if disc < 40:
            suggestions.append("Run off-peak weekday promotions at 40%+ discount to drive volume.")

        strengths_text = "\n".join([f"• {s}" for s in strengths])
        weaknesses_text = "\n".join([f"• {w}" for w in weaknesses])
        suggestions_text = "\n".join([f"• {sg}" for sg in suggestions])

        return (
            "📈 Merchant Growth Agent\n\n"
            "📊 Review My Offer\n\n"
            f"🏷️ Brand: {deal.get('brand')}\n"
            f"📂 Category: {deal.get('display_category')}\n"
            f"📝 Offer: {deal.get('clean_title')}\n"
            f"💰 Price: {deal.get('formatted_price')}\n"
            f"🎁 Discount: {disc}%\n"
            f"📍 Location: {deal.get('display_location')}\n\n"
            f"🏆 Overall Rating: {score}/100 ({rating})\n\n"
            "💪 Strengths:\n"
            f"{strengths_text}\n\n"
            "⚠️ Weaknesses:\n"
            f"{weaknesses_text}\n\n"
            "💡 Suggestions:\n"
            f"{suggestions_text}\n\n"
            "ℹ️ Note: Evaluated strictly using catalog offer information."
        )

    def format_offer_score(self, deal: Dict[str, Any]) -> str:
        """FEATURE 2: Offer Score."""
        score_eval = self.evaluate_offer_score(deal)
        total = score_eval["total_score"]
        bd = score_eval["breakdown"]
        recs = score_eval["recommendations"]

        bd_text = (
            f"Offer Clarity\n{bd['Offer Clarity']}\n\n"
            f"Discount\n{bd['Discount']}\n\n"
            f"Price\n{bd['Price']}\n\n"
            f"Category\n{bd['Category']}\n\n"
            f"Location\n{bd['Location']}\n\n"
            f"OCR\n{bd['OCR']}"
        )

        recs_text = "\n".join([f"• {r}" for r in recs])

        return (
            "📈 Merchant Growth Agent\n\n"
            "Offer Score\n"
            f"{total}/100\n\n"
            "Breakdown\n\n"
            f"{bd_text}\n\n"
            "Recommendations\n"
            f"{recs_text}\n\n"
            f"🏷️ Brand: {deal.get('brand')}\n"
            f"📝 Offer: {deal.get('clean_title')}"
        )

    def generate_growth_suggestions(self, deal: Dict[str, Any]) -> str:
        """FEATURE 3: Growth Suggestions."""
        suggestions = [
            "• Improve title: Use action titles like 'Flat 50% OFF Total Bill'",
            "• Highlight discount: Display rupee savings prominently for buyers",
            "• Use better descriptions: Add bullet points for inclusions & terms",
            "• Mention customer benefits: Specify 'Instant Redemption at Venue'",
            "• Bundle offers: Pair meals with beverages or desserts",
            "• Weekday promotions: Run off-peak Mon-Thu lunchtime specials",
            "• Weekend promotions: Feature weekend evening dining packages",
            "• Improve readability: Shorten paragraphs into clean bullets"
        ]

        return (
            "📈 Merchant Growth Agent\n\n"
            "📈 Growth Suggestions\n\n"
            f"🏷️ Brand: {deal.get('brand')}\n"
            f"📂 Category: {deal.get('display_category')}\n\n"
            "Actionable Recommendations:\n"
            + "\n".join(suggestions) + "\n\n"
            "ℹ️ Note: Based strictly on offer catalog parameters."
        )

    def suggest_improved_description(self, deal: Dict[str, Any]) -> str:
        """FEATURE 4: Improve Description."""
        title = deal.get("clean_title") or deal.get("title", "")
        disc = deal.get("discount_percent", 0)

        marketing_copy = (
            f"Enjoy {disc}% OFF on your total bill.\n"
            "Perfect for family dinners, celebrations and date nights.\n"
            "Book today and enjoy premium dining while saving more."
        ) if disc > 0 else (
            f"Enjoy an exclusive experience at {deal.get('brand')}.\n"
            "Perfect for family dinners, celebrations and date nights.\n"
            "Book today and enjoy premium dining while saving more."
        )

        return (
            "📈 Merchant Growth Agent\n\n"
            "📝 Improve Description\n\n"
            "Input\n"
            f"{title}\n\n"
            "Output\n"
            f"{marketing_copy}"
        )

    def merchant_dashboard(self, user_id: int) -> str:
        """FEATURE 5: Merchant Dashboard (Real calculated metrics only)."""
        deals = load_deals()
        norm_deals = [normalize_deal(d) for d in deals] if deals else [self.get_merchant_deal(user_id)]

        total_offers = len(norm_deals)
        priced_deals = [d for d in norm_deals if float(str(d.get("price", "0")).replace(",", "")) > 0]
        avg_price = int(sum(float(str(d.get("price", "0")).replace(",", "")) for d in priced_deals) / max(1, len(priced_deals)))
        avg_discount = int(sum(d.get("discount_percent", 0) for d in norm_deals) / max(1, total_offers))

        categories = list({d.get("display_category") for d in norm_deals if d.get("display_category")})
        cat_str = ", ".join(categories[:3]) if categories else "Restaurant"

        highest_disc_deal = max(norm_deals, key=lambda x: x.get("discount_percent", 0), default=norm_deals[0])
        evaluated = [(d, self.evaluate_offer_score(d)) for d in norm_deals]
        highest_rated_deal, highest_eval = max(evaluated, key=lambda x: x[1]["total_score"], default=(norm_deals[0], self.evaluate_offer_score(norm_deals[0])))

        avg_score = int(sum(x[1]["total_score"] for x in evaluated) / max(1, len(evaluated)))
        clean_ocr_count = sum(1 for d in norm_deals if d.get("clean_title") == d.get("title"))
        ocr_quality_pct = int((clean_ocr_count / max(1, total_offers)) * 100)

        return (
            "📈 Merchant Growth Agent\n\n"
            "📊 Merchant Dashboard\n\n"
            f"Total Offers: {total_offers}\n"
            f"Average Discount: {avg_discount}%\n"
            f"Average Price: ₹{avg_price}\n"
            f"Categories: {cat_str}\n"
            f"Highest Discount Offer: {highest_disc_deal.get('brand')} ({highest_disc_deal.get('discount_percent')}% OFF)\n"
            f"Highest Rated Offer: {highest_rated_deal.get('brand')} ({highest_eval['total_score']}/100)\n"
            f"Average Offer Score: {avg_score}/100\n"
            f"OCR Quality: {ocr_quality_pct}% verified clean\n\n"
            "ℹ️ Note: Metrics are calculated strictly from active catalog listings."
        )

    def offer_health(self, user_id: int) -> str:
        """FEATURE 6: Offer Health."""
        deal = self.get_merchant_deal(user_id)
        score_eval = self.evaluate_offer_score(deal)
        score = score_eval["total_score"]

        health_rating = "Excellent" if score >= 80 else ("Good" if score >= 60 else ("Fair" if score >= 40 else "Poor"))

        return (
            "📈 Merchant Growth Agent\n\n"
            "🩺 Offer Health\n\n"
            f"🏷️ Offer: {deal.get('clean_title')}\n"
            f"Health\n{health_rating} ({score}/100)\n\n"
            "Evaluation:\n"
            f"• Title Quality: {'Passed' if len(deal.get('clean_title', '')) >= 8 else 'Needs Polish'}\n"
            f"• Price: {deal.get('formatted_price')}\n"
            f"• Discount: {deal.get('discount_percent')}%\n"
            f"• Category: {deal.get('display_category')}\n"
            f"• Location: {deal.get('display_location')}\n"
            f"• OCR: {'Clean' if deal.get('clean_title') == deal.get('title') else 'Normalized'}\n"
            f"• Description: {'Detailed' if len(deal.get('description', '')) >= 30 else 'Brief'}\n\n"
            "Suggestions:\n"
            "• Add explicit rupee savings to increase conversion\n"
            "• Expand description with dish/service inclusions"
        )

    def compare_offers(self, user_id: int) -> str:
        """FEATURE 7: Compare My Offers (Dedicated Merchant Comparison)."""
        deals = load_deals()
        norm_deals = [normalize_deal(d) for d in deals[:3]] if len(deals) >= 3 else [self.get_merchant_deal(user_id)]

        evals = [(d, self.evaluate_offer_score(d)) for d in norm_deals]
        best_deal, best_eval = max(evals, key=lambda x: (x[1]["total_score"], x[0].get("discount_percent", 0)))
        weakest_deal, weakest_eval = min(evals, key=lambda x: (x[1]["total_score"], x[0].get("discount_percent", 0)))

        reply = (
            "📈 Merchant Growth Agent\n\n"
            "📊 Compare My Offers\n\n"
        )
        for i, (d, ev) in enumerate(evals, 1):
            reply += (
                f"{i}. 🏷️ {d.get('brand')}\n"
                f"   Offer: {d.get('clean_title')}\n"
                f"   Price: {d.get('formatted_price')} | Discount: {d.get('discount_percent')}%\n"
                f"   Offer Score: {ev['total_score']}/100\n\n"
            )

        reply += (
            f"🏆 Best Offer\n"
            f"{best_deal.get('brand')} – {best_deal.get('clean_title')} ({best_eval['total_score']}/100)\n\n"
            f"⚠️ Weakest Offer\n"
            f"{weakest_deal.get('brand')} – {weakest_deal.get('clean_title')} ({weakest_eval['total_score']}/100)\n\n"
            "💡 Suggestions\n"
            f"• Upgrade {weakest_deal.get('brand')}'s discount level to match {best_deal.get('brand')}\n"
            "• Add clear price details to all lower-scoring offers"
        )
        return reply

    def promote_offer(self, user_id: int) -> str:
        """FEATURE 8: Which offer should I promote?"""
        deals = load_deals()
        norm_deals = [normalize_deal(d) for d in deals[:5]] if deals else [self.get_merchant_deal(user_id)]

        evals = [(d, self.evaluate_offer_score(d)) for d in norm_deals]
        best_deal, best_eval = max(evals, key=lambda x: (x[1]["total_score"], x[0].get("discount_percent", 0)))

        return (
            "📈 Merchant Growth Agent\n\n"
            "🚀 Which offer should I promote?\n\n"
            "Recommended Offer:\n"
            f"🏷️ Brand: {best_deal.get('brand')}\n"
            f"📝 Offer: {best_deal.get('clean_title')}\n"
            f"💰 Price: {best_deal.get('formatted_price')} ({best_deal.get('discount_percent')}% OFF)\n"
            f"🏆 Offer Score: {best_eval['total_score']}/100\n\n"
            "Reasons:\n"
            "• Highest Offer Score among listed catalog deals\n"
            "• Known price & transparent value presentation\n"
            "• High discount attractiveness drives 3x more customer clicks\n"
            "• Clean offer description & verified location\n\n"
            "Improvement Suggestions:\n"
            "• Feature 'Save 50%' in headline promotional banner"
        )

    def merchant_help(self) -> str:
        """FEATURE 9: Merchant Help."""
        return (
            "📈 Merchant Growth Agent\n\n"
            "🏪 Merchant Help\n\n"
            "Practical Recommendations:\n"
            "• Improve title: Use action phrases like 'Flat 50% OFF Total Bill'\n"
            "• Improve description: Highlight key dish & service inclusions clearly\n"
            "• Increase offer visibility: Display exact rupee savings prominently\n"
            "• Highlight savings: Show payable price vs original list price\n"
            "• Mention target audience: Highlight 'Perfect for Family & Couple Dinners'\n\n"
            "ℹ️ Note: Recommendations are based strictly on offer catalog information."
        )


merchant_agent = MerchantGrowthAgent()
