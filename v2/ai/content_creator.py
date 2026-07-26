import logging
from typing import Dict, List, Any
from v2.search.search_engine import normalize_deal
from v2.ai.merchant import merchant_agent

logger = logging.getLogger(__name__)


class ContentCreatorAgent:
    """
    Milestone 14.1 - Production-Quality AI Marketing Intelligence Engine:
    - Conditional Discount Logic: Never promotes '0% OFF' or 'No Discount'. Highlights affordable pricing & quality when discount=0.
    - Category-Aware Marketing: Tailors copy, benefits, and occasions specifically for Restaurant, Salon, Spa, Hotel, Cafe, Entertainment, Clinic, Fitness.
    - Smart Category CTAs: Uses 'Reserve your table', 'Book your appointment', 'Plan your staycation', 'Grab your tickets'.
    - Real Hashtag Generator: Outputs 10–15 clean, relevant hashtags.
    - Platform-Specific Constraints: SMS <= 160 chars, Push < 80 chars, Email structured with subject/preview/body/closing.
    - Data Safety: Uses normalized catalog data only; never invents fake coupon codes, reviews, or analytics.
    """

    def get_deal(self, user_id: int) -> Dict[str, Any]:
        """Retrieves normalized merchant deal."""
        return merchant_agent.get_merchant_deal(user_id)

    def get_category_cta(self, category: str) -> str:
        """Returns smart category-specific call-to-action."""
        c = (category or "").lower()
        if any(k in c for k in ["restaurant", "dining", "buffet", "food"]):
            return "Reserve your table"
        if any(k in c for k in ["salon", "hair", "beauty", "parlor"]):
            return "Book your appointment"
        if any(k in c for k in ["spa", "massage", "wellness"]):
            return "Reserve your relaxation session"
        if any(k in c for k in ["hotel", "resort", "stay"]):
            return "Plan your staycation"
        if any(k in c for k in ["entertainment", "gaming", "water park", "movie", "activity"]):
            return "Grab your tickets"
        if any(k in c for k in ["cafe", "coffee", "bakery"]):
            return "Drop by today"
        if any(k in c for k in ["clinic", "health"]):
            return "Schedule your consultation"
        if any(k in c for k in ["fitness", "gym"]):
            return "Start your fitness journey"
        return "Book your offer"

    def get_category_benefits(self, category: str) -> List[str]:
        """Returns category-specific benefit bullets."""
        c = (category or "").lower()
        if any(k in c for k in ["restaurant", "dining", "buffet", "food"]):
            return [
                "• Perfect for family dinners & date nights",
                "• Freshly prepared gourmet dining experience",
                "• Instant venue reservation with Zookout"
            ]
        if any(k in c for k in ["salon", "hair", "beauty"]):
            return [
                "• Complete hair makeover & styling by experts",
                "• High-quality beauty products & personalized care",
                "• Boost your confidence with a fresh look"
            ]
        if any(k in c for k in ["spa", "massage", "wellness"]):
            return [
                "• Deep stress relief & full body rejuvenation",
                "• Tranquil ambience & professional therapy",
                "• Unwind your mind and restore energy"
            ]
        if any(k in c for k in ["hotel", "resort", "stay"]):
            return [
                "• Luxurious rooms & peaceful getaway ambiance",
                "• Ideal weekend escape close to the city",
                "• Comfort & top-tier hospitality guaranteed"
            ]
        if any(k in c for k in ["entertainment", "gaming", "activity"]):
            return [
                "• Action-packed weekend fun for friends & family",
                "• Thrilling activities & memorable experiences",
                "• Easy booking with zero hassle"
            ]
        if any(k in c for k in ["cafe", "coffee"]):
            return [
                "• Artisanal coffee & fresh bakery delights",
                "• Relaxing atmosphere for meetups & work sessions",
                "• Perfect midday coffee break"
            ]
        if any(k in c for k in ["clinic", "health"]):
            return [
                "• Professional medical consultation & care",
                "• Qualified health specialists",
                "• Comprehensive health assessment"
            ]
        if any(k in c for k in ["fitness", "gym"]):
            return [
                "• State-of-the-art gym equipment & trainers",
                "• Goal-driven workout routines & transformation",
                "• Energizing fitness environment"
            ]
        return [
            "• Verified quality service",
            "• Instant redemption at venue",
            "• Transparent catalog pricing"
        ]

    def generate_hashtags(self, deal: Dict[str, Any]) -> str:
        """FEATURE 7: Real Hashtag Generator (Outputs 10-15 clean, relevant hashtags)."""
        brand = deal.get("brand", "Merchant").replace(" ", "").replace("&", "").replace("-", "")
        cat = deal.get("display_category", "Deals").replace(" ", "")
        loc = deal.get("display_location", "Mumbai").replace(" ", "")
        title = deal.get("clean_title", "").replace(" ", "").replace("&", "")

        tags = []
        if cat.lower() in ["restaurant", "dining"]:
            tags = [f"#{loc}Food", "#Foodie", f"#{cat}Deals", "#WeekendDining", "#FamilyDinner", "#DateNight", f"#{brand}", f"#{loc}Restaurants", "#DiningOffers", "#BuffetLovers", "#MumbaiEats", "#ZookoutDeals"]
        elif cat.lower() in ["salon", "beauty"]:
            tags = [f"#{loc}Salon", "#HairCare", "#BeautyLook", "#HairTransformation", "#SelfCare", f"#{brand}", f"#{loc}Beauty", "#SalonOffers", "#HairStyling", "#Grooming", "#ZookoutBeauty"]
        elif cat.lower() in ["spa", "wellness"]:
            tags = [f"#{loc}Spa", "#Wellness", "#MassageTherapy", "#StressRelief", "#Relaxation", f"#{brand}", "#SelfCareDay", f"#{loc}Wellness", "#SpaDeals", "#Rejuvenation", "#ZookoutSpa"]
        elif cat.lower() in ["hotel", "resort"]:
            tags = [f"#{loc}Hotels", "#Staycation", "#WeekendGetaway", "#LuxuryStay", "#TravelGram", f"#{brand}", f"#{loc}Tourism", "#HotelDeals", "#VacationVibes", "#ZookoutHotels"]
        elif cat.lower() in ["cafe", "coffee"]:
            tags = [f"#{loc}Cafes", "#CoffeeLovers", "#BrunchVibes", "#CafeMeetup", "#CoffeeTime", f"#{brand}", f"#{loc}Foodie", "#FreshBrew", "#ZookoutCafes"]
        else:
            tags = [f"#{loc}Deals", f"#{cat}", f"#{brand}", "#LocalOffers", f"#{loc}Life", "#BestDeals", "#WeekendVibes", "#SpecialOffer", f"#{loc}Events", "#Zookout"]

        # Ensure 10-15 clean unique hashtags
        unique_tags = list(dict.fromkeys(tags))[:14]
        return " ".join(unique_tags)

    def generate_instagram_post(self, deal: Dict[str, Any]) -> str:
        """FEATURE 1: Instagram Post Generator (Storytelling, emojis, category CTA, real hashtags)."""
        brand = deal.get("brand", "Zookout Merchant")
        title = deal.get("clean_title", "Special Experience")
        price = deal.get("formatted_price", "Price unavailable")
        disc = deal.get("discount_percent", 0)
        loc = deal.get("display_location", "Mumbai")
        cat = deal.get("display_category", "Experience")

        cta = self.get_category_cta(cat)
        tags = self.generate_hashtags(deal)

        if disc > 0:
            price_text = f"for just {price} (Save {disc}% OFF)!"
        else:
            price_text = f"available for just {price}."

        return (
            "📸 Instagram Post Generator\n\n"
            f"✨ Refresh Your Day at {brand}!\n\n"
            f"Treat yourself to our featured {cat} experience: {title} {price_text}\n\n"
            f"Whether you're planning a weekend outing or a special celebration, {brand} offers top-tier quality and exceptional service in {loc}.\n\n"
            f"👉 {cta} on Zookout today!\n\n"
            f"📍 {loc}\n\n"
            f"{tags}"
        )

    def generate_facebook_post(self, deal: Dict[str, Any]) -> str:
        """FEATURE 2: Facebook Promotion (Longer post, benefits, customer-focused)."""
        brand = deal.get("brand", "Zookout Merchant")
        title = deal.get("clean_title", "Special Experience")
        price = deal.get("formatted_price", "Price unavailable")
        disc = deal.get("discount_percent", 0)
        loc = deal.get("display_location", "Mumbai")
        cat = deal.get("display_category", "Experience")

        cta = self.get_category_cta(cat)
        benefits = "\n".join(self.get_category_benefits(cat))

        if disc > 0:
            headline = f"🔥 EXCLUSIVE PROMOTION: SAVE {disc}% OFF AT {brand.upper()}!"
            price_detail = f"{price} ({disc}% OFF)"
        else:
            headline = f"🌟 FEATURED {cat.upper()} EXPERIENCE AT {brand.upper()}!"
            price_detail = f"{price} (Affordable Quality)"

        return (
            "📘 Facebook Promotion\n\n"
            f"{headline}\n\n"
            f"Looking for a great {cat.lower()} experience in {loc}? {brand} presents an exclusive catalog offer for you!\n\n"
            f"📌 Offer Summary:\n"
            f"• Offer: {title}\n"
            f"• Price: {price_detail}\n"
            f"• Location: {loc}\n\n"
            f"✨ Highlights & Benefits:\n"
            f"{benefits}\n\n"
            f"👉 {cta} with Zookout!"
        )

    def generate_whatsapp_promo(self, deal: Dict[str, Any]) -> str:
        """FEATURE 3: WhatsApp Promotion (Very short, shareable, clear CTA)."""
        brand = deal.get("brand", "Zookout Merchant")
        title = deal.get("clean_title", "Special Offer")
        price = deal.get("formatted_price", "Price unavailable")
        disc = deal.get("discount_percent", 0)
        cat = deal.get("display_category", "Experience")

        cta = self.get_category_cta(cat)

        if disc > 0:
            offer_line = f"Flat {disc}% OFF on {title}."
        else:
            offer_line = f"Enjoy {title} for an affordable rate."

        return (
            "💬 WhatsApp Promotion\n\n"
            f"🔥 Special Deal at {brand}!\n\n"
            f"{offer_line}\n\n"
            f"💰 Price: {price}\n"
            f"📍 Location: {deal.get('display_location', 'Mumbai')}\n\n"
            f"📲 {cta} directly via Zookout!"
        )

    def generate_sms_campaign(self, deal: Dict[str, Any]) -> str:
        """FEATURE 4: SMS Campaign (Strictly <= 160 Characters)."""
        brand = deal.get("brand", "Zookout Merchant")
        title = deal.get("clean_title", "Special Offer")
        price = deal.get("formatted_price", "Price unavailable")
        disc = deal.get("discount_percent", 0)
        cat = deal.get("display_category", "Deal")

        cta = self.get_category_cta(cat)

        if disc > 0:
            sms_body = f"Special Offer at {brand}! {title} at {price} ({disc}% OFF). {cta} on Zookout!"
        else:
            sms_body = f"Enjoy {title} at {brand} for just {price}. {cta} on Zookout!"

        if len(sms_body) > 160:
            sms_body = f"{brand}: {title} at {price}. {cta} on Zookout!"[:160]

        return (
            "📱 SMS Campaign (160 Characters Max)\n\n"
            f"{sms_body}\n\n"
            f"📊 Character Count: {len(sms_body)}/160"
        )

    def generate_push_notification(self, deal: Dict[str, Any]) -> str:
        """FEATURE 5: Push Notification (Strictly < 80 Characters)."""
        brand = deal.get("brand", "Zookout Merchant")
        disc = deal.get("discount_percent", 0)
        cat = deal.get("display_category", "Deal")

        cta = self.get_category_cta(cat)

        if disc > 0:
            push_text = f"{disc}% OFF at {brand}! {cta} on Zookout."
        else:
            push_text = f"Special deal at {brand}! {cta} on Zookout."

        if len(push_text) >= 80:
            push_text = push_text[:79]

        return (
            "🔔 Push Notification (< 80 Characters)\n\n"
            f"{push_text}\n\n"
            f"📊 Character Count: {len(push_text)}/80"
        )

    def generate_promotional_captions(self, deal: Dict[str, Any]) -> str:
        """FEATURE 6: Promotional Caption (Professional, Friendly, Luxury)."""
        brand = deal.get("brand", "Zookout Merchant")
        title = deal.get("clean_title", "Special Experience")
        price = deal.get("formatted_price", "Price unavailable")
        disc = deal.get("discount_percent", 0)
        cat = deal.get("display_category", "Experience")

        cta = self.get_category_cta(cat)

        disc_str = f"with a {disc}% savings" if disc > 0 else "at an accessible price"

        prof = f"Discover verified quality with {title} at {brand}. Available for {price} ({disc_str}). {cta} via Zookout."
        friend = f"Hey there! Ready for a great time? Enjoy {title} at {brand} for just {price}! {cta} today on Zookout 🎉"
        lux = f"Indulge in a refined experience. {brand} presents {title} at {price}. Elevate your moments with Zookout."

        return (
            "✍️ Promotional Caption Styles\n\n"
            f"👔 Professional Style:\n{prof}\n\n"
            f"😊 Friendly Style:\n{friend}\n\n"
            f"👑 Luxury Style:\n{lux}"
        )

    def generate_festival_promotions(self, deal: Dict[str, Any]) -> str:
        """FEATURE 8: Festival Promotion (Diwali, New Year, Valentine's Day - No fake discounts)."""
        brand = deal.get("brand", "Zookout Merchant")
        title = deal.get("clean_title", "Special Offer")
        price = deal.get("formatted_price", "Price unavailable")
        disc = deal.get("discount_percent", 0)
        cat = deal.get("display_category", "Experience")

        cta = self.get_category_cta(cat)

        price_str = f"for {price} ({disc}% OFF)" if disc > 0 else f"for just {price}"

        diwali = f"🪔 Diwali Celebration at {brand}! Light up your festive season with {title} {price_str}. {cta} on Zookout!"
        ny = f"🎆 New Year Special! Celebrate the New Year with {title} at {brand} {price_str}. {cta} on Zookout!"
        vday = f"❤️ Valentine's Day Special! Share memorable moments at {brand} with {title} {price_str}. {cta} on Zookout!"

        return (
            "🎉 Festival Campaign Generator\n\n"
            f"🪔 Diwali Campaign:\n{diwali}\n\n"
            f"🎆 New Year Campaign:\n{ny}\n\n"
            f"❤️ Valentine's Day Campaign:\n{vday}"
        )

    def generate_weekend_promotion(self, deal: Dict[str, Any]) -> str:
        """FEATURE 9: Weekend Promotion (Encourages weekend bookings)."""
        brand = deal.get("brand", "Zookout Merchant")
        title = deal.get("clean_title", "Special Offer")
        price = deal.get("formatted_price", "Price unavailable")
        disc = deal.get("discount_percent", 0)
        cat = deal.get("display_category", "Experience")

        cta = self.get_category_cta(cat)

        price_str = f"for just {price} ({disc}% OFF)" if disc > 0 else f"for {price}"

        return (
            "🥳 Weekend Promotion Generator\n\n"
            f"🌟 Make Your Weekend Unforgettable at {brand}!\n\n"
            f"Unwind and enjoy {title} {price_str} this weekend.\n\n"
            f"Perfect for family outings, friends meetups, and relaxed afternoons in {deal.get('display_location', 'Mumbai')}.\n\n"
            f"📲 {cta} on Zookout before weekend slots fill up!"
        )

    def generate_birthday_promotion(self, deal: Dict[str, Any]) -> str:
        """FEATURE 10: Birthday Promotion (Birthday celebration copy)."""
        brand = deal.get("brand", "Zookout Merchant")
        title = deal.get("clean_title", "Special Offer")
        price = deal.get("formatted_price", "Price unavailable")
        disc = deal.get("discount_percent", 0)
        cat = deal.get("display_category", "Experience")

        cta = self.get_category_cta(cat)

        price_str = f"at {price} ({disc}% OFF)" if disc > 0 else f"at {price}"

        return (
            "🎂 Birthday Promotion Generator\n\n"
            f"🎉 Celebrate Your Special Birthday at {brand}!\n\n"
            f"Make your birthday memories unforgettable with {title} {price_str}.\n\n"
            "Enjoy personalized care and premium service on your big day.\n\n"
            f"📲 {cta} on Zookout today!"
        )

    def generate_email_campaign(self, deal: Dict[str, Any]) -> str:
        """FEATURE 11: Email Campaign (Subject, Preview, Greeting, Benefits, Details, CTA, Closing)."""
        brand = deal.get("brand", "Zookout Merchant")
        title = deal.get("clean_title", "Special Offer")
        price = deal.get("formatted_price", "Price unavailable")
        disc = deal.get("discount_percent", 0)
        cat = deal.get("display_category", "Experience")
        loc = deal.get("display_location", "Mumbai")

        cta = self.get_category_cta(cat)
        benefits = "\n".join(self.get_category_benefits(cat))

        if disc > 0:
            subject = f"Exclusive {disc}% OFF Offer: {title} at {brand}"
            disc_line = f"• Special Discount: {disc}% OFF\n"
        else:
            subject = f"Featured {cat} Experience: {title} at {brand}"
            disc_line = ""

        preview = f"Discover {title} for just {price} at {brand}. {cta} on Zookout."

        body = (
            f"Dear Valued Guest,\n\n"
            f"We are delighted to introduce a featured {cat.lower()} offer at {brand} in {loc}.\n\n"
            f"📌 Offer Summary:\n"
            f"• Package: {title}\n"
            f"• Payable Price: {price}\n"
            f"{disc_line}"
            f"• Location: {loc}\n\n"
            f"✨ Why You'll Love This Experience:\n"
            f"{benefits}\n\n"
            f"Ready to enjoy this offer? Click the link below to complete your reservation.\n\n"
            f"👉 {cta} on Zookout\n\n"
            f"Warmest regards,\n"
            f"{brand} Management Team"
        )

        return (
            "📧 Email Campaign Generator\n\n"
            f"📌 Subject Line:\n{subject}\n\n"
            f"👀 Preview Text:\n{preview}\n\n"
            f"📄 Email Content:\n{body}"
        )

    def generate_marketing_help(self, deal: Dict[str, Any]) -> str:
        """FEATURE 12: Marketing Help (Category-specific advice using actual offer quality & parameters)."""
        brand = deal.get("brand", "Zookout Merchant")
        cat = deal.get("display_category", "Experience")
        disc = deal.get("discount_percent", 0)
        loc = deal.get("display_location", "Mumbai")

        c = cat.lower()

        if "restaurant" in c:
            advice = [
                "• Visual Content: Share high-resolution photos of signature dishes and dining ambiance.",
                "• Weekend Timing: Run weekend family meal promotions announced on Thursday/Friday.",
                "• Occasion Marketing: Highlight 'Family Dinner' & 'Date Night' themes in your social captions."
            ]
        elif "salon" in c:
            advice = [
                "• Before/After Content: Create short video reels showcasing hair & beauty transformations.",
                "• Self-Care Focus: Emphasize weekend pampering and festive glow promotions.",
                "• Visual Proof: Tag client transformations to build trust and appointment bookings."
            ]
        elif "spa" in c:
            advice = [
                "• Stress-Relief Focus: Highlight weekend relaxation, body rejuvenation, and tranquility.",
                "• Ambience Reels: Share peaceful videos of spa rooms and therapy setups.",
                "• Off-Peak Discounts: Promote weekday afternoon spa packages to fill quiet slots."
            ]
        elif "hotel" in c:
            advice = [
                "• Room Showcase: Share virtual room tours and scenic location views.",
                "• Weekend Staycations: Market 2-day weekend escapes for city residents.",
                "• Local Attraction Guides: Highlight nearby dining & leisure spots in your posts."
            ]
        else:
            advice = [
                "• Category-Targeted Messaging: Focus social posts on your core category strengths.",
                "• Clear Rupee Savings: Highlight payable price vs original list price side-by-side.",
                "• Multi-Channel Sharing: Post regularly across Instagram, WhatsApp, and Facebook."
            ]

        if disc >= 40:
            advice.append(f"• High Discount Advantage: Your {disc}% OFF discount is highly competitive—feature it prominently in headlines!")
        elif disc == 0:
            advice.append("• Value-Add Focus: Since no discount percentage is listed, emphasize premium service quality and affordable pricing.")

        return (
            "💡 Merchant Marketing Intelligence Guide\n\n"
            f"🏷️ Brand: {brand}\n"
            f"📂 Category: {cat} | 📍 Location: {loc}\n\n"
            "Category-Specific Promotion Strategies:\n"
            + "\n".join(advice) + "\n\n"
            "ℹ️ Note: Recommendations are generated specifically for your catalog listing parameters."
        )


content_creator_agent = ContentCreatorAgent()
