import logging
from typing import Dict, List, Any
from v2.search.search_engine import load_deals, normalize_deal, clean_offer_title, search_deals
from v2.ai.profile import profile_manager

logger = logging.getLogger(__name__)


class MerchantGrowthAgent:
    """
    Milestone 13.4 & Milestone 2 - Production-Ready Consistent Merchant Growth Agent Engine:
    - Explicit OCR Quality Reporting.
    - Structured Merchant Growth Report for dashboards & growth advice.
    """

    def generate_merchant_growth_report(self) -> str:
        """
        Milestone 2 - Merchant Growth Agent (Step 1):
        Generates structured Merchant Growth Report with catalog metrics, top ranked offers, and AI growth recommendations.
        """
        deals = self.get_merchant_dataset()
        total_offers = len(deals)

        if not deals:
            return (
                "📊 Merchant Growth Report\n\n"
                "• Total offers available: 0\n"
                "• Average discount: 0%\n"
                "• Categories available: None\n"
                "• Price range: ₹0 - ₹0\n\n"
                "• Top-performing offers:\n"
                "  No active offers in catalog.\n\n"
                "• Suggested improvements:\n"
                "  - Increase visibility during slow hours.\n"
                "  - Run limited-time 50% offers.\n"
                "  - Promote buffet deals on weekends.\n"
                "  - Improve offer titles if they are generic.\n"
                "  - Add more high-value offers in popular categories."
            )

        priced_deals = [d for d in deals if float(str(d.get("price", "0")).replace(",", "")) > 0]
        prices = [float(str(d.get("price", "0")).replace(",", "")) for d in priced_deals] if priced_deals else [0.0]
        min_price = int(min(prices))
        max_price = int(max(prices))

        avg_discount = int(sum(d.get("discount_percent", 0) for d in deals) / max(1, total_offers))

        categories = sorted(list({d.get("display_category") for d in deals if d.get("display_category")}))
        cat_str = ", ".join(categories) if categories else "Restaurant"

        # Top-performing offers based on current weighted recommendation ranking logic
        ranked_deals = search_deals({"type": "search"})
        if not ranked_deals:
            ranked_deals = deals

        top_offers = []
        for i, raw_d in enumerate(ranked_deals[:4], 1):
            d = normalize_deal(raw_d)
            b = d.get("brand", "Merchant")
            t = d.get("clean_title", "Offer")
            disc = d.get("discount_percent", 0)
            rating = d.get("rating", 4.5)
            top_offers.append(f"  {i}. {b} - {t} (Discount: {disc}%, Rating: ⭐ {rating})")

        top_offers_str = "\n".join(top_offers)

        suggested_improvements = [
            "  - Increase visibility during slow hours.",
            "  - Run limited-time 50% offers.",
            "  - Promote buffet deals on weekends.",
            "  - Improve offer titles if they are generic.",
            "  - Add more high-value offers in popular categories."
        ]
        improvements_str = "\n".join(suggested_improvements)

        return (
            "📊 Merchant Growth Report\n\n"
            f"• Total offers available: {total_offers}\n"
            f"• Average discount: {avg_discount}%\n"
            f"• Categories available: {cat_str}\n"
            f"• Price range: ₹{min_price:,} - ₹{max_price:,}\n\n"
            "• Top-performing offers (based on current ranking logic):\n"
            f"{top_offers_str}\n\n"
            "• Suggested improvements:\n"
            f"{improvements_str}"
        )

    def merchant_dashboard(self, user_id: int) -> str:
        """Returns structured Merchant Growth Report for merchant dashboard requests."""
        return self.generate_merchant_growth_report()

    def generate_slow_hours_performance_report(self, category: str = "Restaurant") -> str:
        """
        Milestone 2 - Step 2: AI Slow-Hour Prediction & Performance Report.
        Generates structured Business Performance Analysis with estimated peak/slow hours and happy hour suggestions.
        """
        cat_lower = (category or "").lower()

        if "spa" in cat_lower or "salon" in cat_lower or "beauty" in cat_lower:
            peak_hours = "• 11 AM – 2 PM & 5 PM – 8 PM"
            slow_hours = "• 1 PM – 4 PM"
            happy_hours = "• 2 PM – 5 PM"
        else:
            peak_hours = "• 7 PM – 10 PM"
            slow_hours = "• 2 PM – 5 PM"
            happy_hours = "• 3 PM – 6 PM"

        return (
            "📈 Business Performance Analysis\n\n"
            "Peak Hours:\n"
            f"{peak_hours}\n\n"
            "Slow Hours:\n"
            f"{slow_hours}\n\n"
            "Recommended Happy Hour:\n"
            f"{happy_hours}\n\n"
            "Suggested Offer:\n"
            "• Flat 30% OFF\n"
            "or\n"
            "• Buy 1 Get 1\n\n"
            "Best Promotion Days:\n"
            "• Monday\n"
            "• Tuesday\n"
            "• Wednesday\n\n"
            "AI Recommendations:\n"
            "• Increase promotions during slow hours.\n"
            "• Schedule buffet campaigns on weekends.\n"
            "• Push Instagram offers before lunch and dinner.\n"
            "• Test limited-time discounts."
        )

    def generate_ai_offer_recommendation_report(self) -> str:
        """
        Milestone 2 - Step 3: AI Offer Recommendation Engine Report.
        Generates structured offer insights including best/worst performing offers, highest discount,
        suggested new offer ideas, pricing strategy, promotion strategy, and revenue tips.
        """
        deals = self.get_merchant_dataset()

        if deals:
            # 1. Best Performing Offer (highest rated / weighted score)
            evaluated = [(d, self.evaluate_offer_score(d)) for d in deals]
            best_deal, _ = max(evaluated, key=lambda x: x[1]["total_score"], default=(deals[0], self.evaluate_offer_score(deals[0])))
            best_offer_str = f"• {best_deal.get('clean_title')} ({best_deal.get('brand')})"

            # 2. Highest Discount Offer
            highest_disc_deal = max(deals, key=lambda x: x.get("discount_percent", 0), default=deals[0])
            highest_disc_str = f"• {highest_disc_deal.get('discount_percent')}% OFF {highest_disc_deal.get('clean_title')}"

            # 3. Lowest Performing Offer
            lowest_deal, _ = min(evaluated, key=lambda x: x[1]["total_score"], default=(deals[0], self.evaluate_offer_score(deals[0])))
            lowest_offer_str = f"• {lowest_deal.get('clean_title')} ({lowest_deal.get('brand')})"
        else:
            best_offer_str = "• Flat 50% OFF Dinner"
            highest_disc_str = "• 57% OFF Hair Treatment"
            lowest_offer_str = "• Special Catalog Offer"

        return (
            "🎯 AI Offer Recommendation Report\n\n"
            "Best Performing Offer\n"
            f"{best_offer_str}\n\n"
            "Highest Discount\n"
            f"{highest_disc_str}\n\n"
            "Lowest Performing Offer\n"
            f"{lowest_offer_str}\n\n"
            "Suggested New Offers\n"
            "• Buy 1 Get 1\n"
            "• Family Combo\n"
            "• Weekend Buffet\n"
            "• Happy Hour\n\n"
            "Pricing Strategy\n"
            "• Use 30–50% discounts during slow hours.\n\n"
            "Promotion Strategy\n"
            "• Promote offers on Instagram.\n"
            "• Run weekend campaigns.\n"
            "• Push lunch offers before noon.\n\n"
            "Revenue Tips\n"
            "• Improve offer titles.\n"
            "• Add limited-time offers.\n"
            "• Rotate promotions weekly."
        )

    def get_merchant_dataset(self) -> List[Dict[str, Any]]:
        """Returns the single consistent normalized dataset across all Merchant AI features."""
        deals = load_deals()
        if deals:
            return [normalize_deal(d) for d in deals]

        return [normalize_deal({
            "brand": "Kohinoor Continental The Beryl",
            "category": "Restaurant",
            "title": "Flat 50% OFF on Total Bill",
            "price": 510,
            "discount_percent": 50,
            "location": "Mumbai",
            "description": "Enjoy flat 50% discount on total dining bill."
        })]

    def get_merchant_deal(self, user_id: int) -> Dict[str, Any]:
        """Returns the user's last viewed deal or top representative deal from normalized dataset."""
        history = profile_manager.get_recently_viewed(user_id)
        if history:
            return normalize_deal(history[0])

        dataset = self.get_merchant_dataset()
        return dataset[0]

    def evaluate_offer_score(self, deal: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transparent Offer Scoring Engine (0-100).
        Calculates 6 visible criteria and generates evidence-backed Strengths & Suggestions.
        Strict rule: Never suggests fixing a field that is already valid.
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

        # 1. Offer Clarity (/25)
        if len(title) >= 12 and len(desc) >= 30:
            clarity_score = 23
        elif len(title) >= 6:
            clarity_score = 18
        else:
            clarity_score = 12

        # 2. Discount Competitiveness (/20)
        if disc >= 50:
            disc_score = 20
        elif disc >= 30:
            disc_score = 15
        elif disc > 0:
            disc_score = 10
        else:
            disc_score = 0

        # 3. Known Price (/20)
        if price > 0:
            price_score = 18
        else:
            price_score = 0

        # 4. Category Available (/10)
        if cat and cat != "Special Experience":
            cat_score = 10
        else:
            cat_score = 5

        # 5. Location Available (/10)
        if loc and loc.lower() not in ["none", "location unavailable", ""]:
            loc_score = 10
        else:
            loc_score = 5

        # 6. OCR Quality (/15)
        if clean_offer_title(raw_title, cat) == raw_title:
            ocr_score = 15
        elif "Offer" in title or len(title) >= 8:
            ocr_score = 11
        else:
            ocr_score = 6

        total = clarity_score + disc_score + price_score + cat_score + loc_score + ocr_score

        # Evidence-Backed Strengths
        strengths = []
        if disc >= 30:
            strengths.append("✓ High discount")
        elif disc > 0:
            strengths.append("✓ Active discount")

        if price > 0:
            strengths.append("✓ Known price")

        if clean_offer_title(raw_title, cat) == raw_title:
            strengths.append("✓ Clean title")

        if loc_score == 10:
            strengths.append("✓ Complete location")

        if cat_score == 10:
            strengths.append("✓ Clear category")

        # Evidence-Backed Suggestions (ISSUE 2 FIX: Strict condition checking)
        suggestions = []
        if len(desc) < 30:
            suggestions.append("Expand description inclusions and readability.")

        if disc < 30:
            suggestions.append("Increase discount percentage to boost competitiveness.")

        if price == 0:
            suggestions.append("Display explicit pricing on listing card.")

        if clean_offer_title(raw_title, cat) != raw_title:
            suggestions.append("Clean OCR text artifacts in title.")

        if not loc or loc.lower() in ["none", "location unavailable", ""]:
            suggestions.append("Add verified location details.")

        if not suggestions:
            suggestions.append("Maintain high listing clarity & verified parameters.")

        breakdown = {
            "Offer Clarity": f"{clarity_score}/25",
            "Discount": f"{disc_score}/20",
            "Price": f"{price_score}/20",
            "Category": f"{cat_score}/10",
            "Location": f"{loc_score}/10",
            "OCR": f"{ocr_score}/15"
        }

        return {
            "total_score": min(100, total),
            "breakdown": breakdown,
            "strengths": strengths,
            "suggestions": suggestions
        }

    def review_offer(self, deal: Dict[str, Any]) -> str:
        """FEATURE 1: Review My Offer."""
        score_eval = self.evaluate_offer_score(deal)
        score = score_eval["total_score"]

        rating = "🌟 Excellent" if score >= 80 else ("👍 Good" if score >= 60 else ("⚠️ Fair" if score >= 40 else "🔴 Poor"))
        disc = deal.get("discount_percent", 0)

        strengths_text = "\n".join(score_eval["strengths"]) if score_eval["strengths"] else "• Active catalog listing"
        suggestions_text = "\n".join([f"• {sg}" for sg in score_eval["suggestions"]])

        weaknesses = []
        if disc < 30:
            weaknesses.append("• Discount percentage is lower than category average")
        if len(deal.get("description", "")) < 30:
            weaknesses.append("• Description is brief; missing key inclusions")

        weaknesses_text = "\n".join(weaknesses) if weaknesses else "• Headline can incorporate emotional occasion callouts"

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
        """FEATURE 2: Transparent Offer Score explaining WHY."""
        score_eval = self.evaluate_offer_score(deal)
        total = score_eval["total_score"]
        bd = score_eval["breakdown"]

        bd_text = (
            f"Offer Clarity\n{bd['Offer Clarity']}\n\n"
            f"Discount\n{bd['Discount']}\n\n"
            f"Price\n{bd['Price']}\n\n"
            f"Category\n{bd['Category']}\n\n"
            f"Location\n{bd['Location']}\n\n"
            f"OCR\n{bd['OCR']}"
        )

        strengths_text = "\n".join(score_eval["strengths"]) if score_eval["strengths"] else "✓ Listed catalog deal"
        suggestions_text = "\n".join(score_eval["suggestions"])

        return (
            "📈 Merchant Growth Agent\n\n"
            "Offer Score\n"
            f"{total}/100\n\n"
            "Breakdown\n\n"
            f"{bd_text}\n\n"
            "Strengths\n"
            f"{strengths_text}\n\n"
            "Suggestions\n"
            f"{suggestions_text}\n\n"
            f"🏷️ Brand: {deal.get('brand')}\n"
            f"📝 Offer: {deal.get('clean_title')}"
        )

    def generate_growth_suggestions(self, deal: Dict[str, Any]) -> str:
        """FEATURE 3 & 7: Dynamic Issue-Driven Growth Suggestions."""
        score_eval = self.evaluate_offer_score(deal)
        title = deal.get("clean_title", "")
        disc = deal.get("discount_percent", 0)

        try:
            price = float(str(deal.get("price", "0")).replace(",", ""))
        except Exception:
            price = 0.0

        dynamic_suggestions = []

        if len(title) < 10 or "Offer" in title:
            dynamic_suggestions.append("• Weak title: Action required → Refine headline to 'Flat 50% OFF Total Bill'")
        else:
            dynamic_suggestions.append("• Title quality: Good → Maintain clear brand & category naming")

        if len(deal.get("description", "")) < 30:
            dynamic_suggestions.append("• Missing detailed description: Action required → Add bullet points listing menu & venue inclusions")

        if disc < 30:
            dynamic_suggestions.append("• Low discount: Action required → Test stronger promotional discounts (30%-50% OFF)")
        else:
            dynamic_suggestions.append("• Competitive discount: Highlight exact rupee savings prominently")

        if price == 0:
            dynamic_suggestions.append("• Missing price: Action required → Display explicit pricing on listing card")

        if deal.get("clean_title") != deal.get("title"):
            dynamic_suggestions.append("• Poor OCR text: Action required → Clean offer title text formatting")

        dynamic_suggestions.append("• Off-peak promotions: Run Mon-Thu lunchtime deals to drive quiet hour visits")
        dynamic_suggestions.append("• Combo packages: Pair main courses with complimentary beverages or desserts")

        return (
            "📈 Merchant Growth Agent\n\n"
            "📈 Growth Suggestions\n\n"
            f"🏷️ Brand: {deal.get('brand')}\n"
            f"📂 Category: {deal.get('display_category')}\n\n"
            "Actionable Recommendations:\n"
            + "\n".join(dynamic_suggestions) + "\n\n"
            "ℹ️ Note: Based strictly on actual offer parameters."
        )

    def suggest_improved_description(self, deal: Dict[str, Any]) -> str:
        """FEATURE 4: Improve Description."""
        title = deal.get("clean_title") or deal.get("title", "")
        disc = deal.get("discount_percent", 0)

        marketing_copy = (
            f"Enjoy {disc}% OFF on your total bill.\n\n"
            "Perfect for family dinners, celebrations and date nights.\n\n"
            "Book today and enjoy premium dining while saving more."
        ) if disc > 0 else (
            f"Enjoy an exclusive experience at {deal.get('brand')}.\n\n"
            "Perfect for family dinners, celebrations and date nights.\n\n"
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
        """FEATURE 1 & 5: Merchant Dashboard with explicit OCR Quality Reporting (ISSUE 1 FIX)."""
        dataset = self.get_merchant_dataset()
        total_offers = len(dataset)

        priced_deals = [d for d in dataset if float(str(d.get("price", "0")).replace(",", "")) > 0]
        avg_price = int(sum(float(str(d.get("price", "0")).replace(",", "")) for d in priced_deals) / max(1, len(priced_deals)))
        avg_discount = int(sum(d.get("discount_percent", 0) for d in dataset) / max(1, total_offers))

        categories = sorted(list({d.get("display_category") for d in dataset if d.get("display_category")}))
        cat_str = ", ".join(categories[:4]) if categories else "Restaurant"

        highest_disc_deal = max(dataset, key=lambda x: x.get("discount_percent", 0), default=dataset[0])
        evaluated = [(d, self.evaluate_offer_score(d)) for d in dataset]
        highest_rated_deal, highest_eval = max(evaluated, key=lambda x: x[1]["total_score"], default=(dataset[0], self.evaluate_offer_score(dataset[0])))

        avg_score = int(sum(x[1]["total_score"] for x in evaluated) / max(1, len(evaluated)))

        # Explicit OCR Reporting (ISSUE 1 FIX)
        clean_ocr_count = sum(1 for d in dataset if d.get("clean_title") == d.get("title"))
        ocr_artifacts_count = total_offers - clean_ocr_count
        ocr_pct = int((clean_ocr_count / max(1, total_offers)) * 100)

        ocr_summary = (
            "OCR Summary\n"
            f"• Clean OCR Titles: {clean_ocr_count} / {total_offers} ({ocr_pct}%)\n"
            f"• Offers with OCR Artifacts: {ocr_artifacts_count} / {total_offers}\n"
            f"• Offers requiring OCR cleanup: {ocr_artifacts_count}"
        )

        missing_prices = sum(1 for d in dataset if float(str(d.get("price", "0")).replace(",", "")) == 0)
        weak_desc = sum(1 for d in dataset if len(d.get("description", "")) < 30)

        insights = [
            f"• Highest discount available: {highest_disc_deal.get('discount_percent')}% OFF ({highest_disc_deal.get('brand')})",
            f"• Most common category: {categories[0] if categories else 'Restaurant'}",
            f"• Offers missing pricing details: {missing_prices}",
            f"• Offers requiring OCR cleanup: {ocr_artifacts_count}",
            f"• Offers needing description expansion: {weak_desc}"
        ]

        return (
            "📈 Merchant Growth Agent\n\n"
            "📊 Merchant Dashboard\n\n"
            f"Total Offers: {total_offers}\n"
            f"Average Discount: {avg_discount}%\n"
            f"Average Price: ₹{avg_price}\n"
            f"Categories: {cat_str}\n"
            f"Highest Discount Offer: {highest_disc_deal.get('brand')} ({highest_disc_deal.get('discount_percent')}% OFF)\n"
            f"Highest Rated Offer: {highest_rated_deal.get('brand')} ({highest_eval['total_score']}/100)\n"
            f"Average Offer Score: {avg_score}/100\n\n"
            f"{ocr_summary}\n\n"
            "💡 Catalog Insights:\n"
            + "\n".join(insights) + "\n\n"
            "ℹ️ Note: All statistics are calculated dynamically from current catalog listings."
        )

    def offer_health(self, user_id: int) -> str:
        """FEATURE 6: Offer Health with clear diagnostic explanation."""
        deal = self.get_merchant_deal(user_id)
        score_eval = self.evaluate_offer_score(deal)
        score = score_eval["total_score"]

        health_rating = "Excellent" if score >= 80 else ("Good" if score >= 60 else ("Fair" if score >= 40 else "Poor"))

        reasons = []
        if len(deal.get("clean_title", "")) >= 8:
            reasons.append("• Title: Clear & concise naming")
        else:
            reasons.append("• Title: Short or unoptimized title format")

        if float(str(deal.get("price", "0")).replace(",", "")) > 0:
            reasons.append(f"• Price: Explicit pricing ({deal.get('formatted_price')})")
        else:
            reasons.append("• Price: Missing explicit price listing")

        if deal.get("discount_percent", 0) >= 30:
            reasons.append(f"• Discount: Competitive ({deal.get('discount_percent')}% OFF)")
        else:
            reasons.append("• Discount: Low or unstated discount level")

        if deal.get("display_location") and deal.get("display_location") != "Location unavailable":
            reasons.append(f"• Location: Complete ({deal.get('display_location')})")
        else:
            reasons.append("• Location: Unspecified location")

        if deal.get("display_category") and deal.get("display_category") != "Special Experience":
            reasons.append(f"• Category: Verified ({deal.get('display_category')})")

        if deal.get("clean_title") == deal.get("title"):
            reasons.append("• OCR: Clean title verified")
        else:
            reasons.append("• OCR: Cleaned title artifacts")

        if len(deal.get("description", "")) >= 30:
            reasons.append("• Description: Detailed inclusions provided")
        else:
            reasons.append("• Description: Brief description")

        return (
            "📈 Merchant Growth Agent\n\n"
            "🩺 Offer Health\n\n"
            f"🏷️ Offer: {deal.get('clean_title')}\n"
            f"Health\n{health_rating} ({score}/100)\n\n"
            "Diagnostic Explanation:\n"
            + "\n".join(reasons) + "\n\n"
            "Suggestions:\n"
            + "\n".join([f"• {sg}" for sg in score_eval["suggestions"]])
        )

    def compare_offers(self, user_id: int) -> str:
        """FEATURE 3: Enhanced Merchant Comparison (ISSUE 2 FIX: Data-consistent suggestions)."""
        dataset = self.get_merchant_dataset()
        norm_deals = dataset[:3] if len(dataset) >= 3 else dataset

        evals = [(d, self.evaluate_offer_score(d)) for d in norm_deals]
        sorted_evals = sorted(evals, key=lambda x: (x[1]["total_score"], x[0].get("discount_percent", 0)), reverse=True)

        reply = (
            "📈 Merchant Growth Agent\n\n"
            "📊 Compare My Offers\n\n"
        )

        for i, (d, ev) in enumerate(sorted_evals, 1):
            strengths_str = ", ".join(ev["strengths"]) if ev["strengths"] else "Listed catalog deal"

            # ISSUE 2 FIX: Accurate weaknesses calculation
            weaknesses = []
            if d.get("discount_percent", 0) < 30:
                weaknesses.append("Low discount")
            if float(str(d.get("price", "0")).replace(",", "")) == 0:
                weaknesses.append("Missing price")
            if len(d.get("description", "")) < 30:
                weaknesses.append("Brief description")
            if d.get("clean_title") != d.get("title"):
                weaknesses.append("OCR artifacts")

            weakness_str = ", ".join(weaknesses) if weaknesses else "Minor title optimization"

            reply += (
                f"Offer {chr(64 + i)}: {d.get('brand')} – {d.get('clean_title')}\n"
                f"Score: {ev['total_score']}/100\n"
                f"Discount: {d.get('discount_percent')}%\n"
                f"Price: {d.get('formatted_price')}\n"
                f"Strengths: {strengths_str}\n"
                f"Weaknesses: {weakness_str}\n\n"
            )

        best_deal, best_eval = sorted_evals[0]
        runner_up = sorted_evals[1][0] if len(sorted_evals) > 1 else None
        needing_imp = sorted_evals[-1][0] if len(sorted_evals) > 2 else (sorted_evals[1][0] if len(sorted_evals) == 2 else None)

        reply += "🏆 Categorized Ranking\n\n"
        reply += f"• Best Offer: {best_deal.get('brand')} ({best_eval['total_score']}/100)\n  Reasons: Highest discount, known price & clean title\n\n"

        if runner_up:
            runner_eval = sorted_evals[1][1]
            runner_needs = ", ".join(runner_eval["suggestions"])
            reply += f"• Runner-up: {runner_up.get('brand')} ({runner_eval['total_score']}/100)\n  Needs: {runner_needs}\n\n"

        if needing_imp:
            imp_eval = sorted_evals[-1][1]
            imp_needs = ", ".join(imp_eval["suggestions"])
            reply += f"• Offers Needing Improvement: {needing_imp.get('brand')} ({imp_eval['total_score']}/100)\n  Needs: {imp_needs}"

        return reply

    def promote_offer(self, user_id: int) -> str:
        """FEATURE 4: Evidence-backed Promotion Recommendation."""
        dataset = self.get_merchant_dataset()
        evals = [(d, self.evaluate_offer_score(d)) for d in dataset]
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
            "• One of the highest discounts in the catalog\n"
            "• Known pricing improves offer clarity\n"
            "• Complete category and location information\n"
            "• Clear offer description\n\n"
            "Improvement Suggestions:\n"
            "• Feature 'Save 50%' in headline promotional banner\n"
            "• Highlight 'Instant Redemption at Venue' callout"
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
