import logging
from typing import Dict, List, Any
from v2.search.search_engine import normalize_deal
from v2.ai.merchant import merchant_agent

logger = logging.getLogger(__name__)


class ContentCreatorAgent:
    """
    Milestone 14.2 - Production-Ready AI Content Creator Polish Engine:
    - Dedicated Facebook & Instagram NLU Routing (Never triggers Experience Planner).
    - Category-Aware Storytelling: Natural copy for Restaurant, Salon, Spa, Cafe, Hotel, Entertainment, Clinic, Fitness.
    - Smart CTA Engine: 'Reserve your table today', 'Book your appointment', 'Reserve your spa session', 'Book your stay', 'Grab your tickets', 'Visit us today'.
    - Embedded Real Hashtags: Appends 10-15 clean hashtags directly without generic notes.
    - Zero Generic Buzzwords: Removes 'Fantastic experience', 'Top-tier service', 'Exclusive offer', 'Book today'.
    """

    def get_deal(self, user_id: int) -> Dict[str, Any]:
        """Retrieves normalized merchant deal."""
        return merchant_agent.get_merchant_deal(user_id)

    def get_category_cta(self, category: str) -> str:
        """Returns smart category-specific call-to-action."""
        c = (category or "").lower()
        if any(k in c for k in ["restaurant", "dining", "buffet", "food"]):
            return "Reserve your table today"
        if any(k in c for k in ["salon", "hair", "beauty", "parlor"]):
            return "Book your appointment"
        if any(k in c for k in ["spa", "massage", "wellness"]):
            return "Reserve your spa session"
        if any(k in c for k in ["hotel", "resort", "stay"]):
            return "Book your stay"
        if any(k in c for k in ["entertainment", "gaming", "water park", "movie", "activity"]):
            return "Grab your tickets"
        if any(k in c for k in ["cafe", "coffee", "bakery"]):
            return "Visit us today"
        if any(k in c for k in ["clinic", "health"]):
            return "Schedule your consultation"
        if any(k in c for k in ["fitness", "gym"]):
            return "Start your fitness journey"
        return "Reserve your offer"

    def get_category_storytelling(self, category: str, brand: str, title: str, price: str, disc: int) -> str:
        """Generates natural category-aware storytelling copy."""
        c = (category or "").lower()
        price_text = f"for just {price} (Save {disc}% OFF)!" if disc > 0 else f"for just {price}."

        if any(k in c for k in ["restaurant", "dining", "buffet", "food"]):
            return (
                f"Gather your friends and family for an unforgettable {title} at {brand} {price_text}\n\n"
                "Savour fresh flavours, rich aromas, and a warm atmosphere. Perfect for weekend family dinners, celebrations, and date nights."
            )
        if any(k in c for k in ["salon", "hair", "beauty"]):
            return (
                f"Refresh your look with a professional makeover at {brand}!\n\n"
                f"Enjoy {title} {price_text} Step out with confidence, radiant style, and personalized hair & beauty care."
            )
        if any(k in c for k in ["spa", "massage", "wellness"]):
            return (
                f"Relax, recharge and unwind at {brand}.\n\n"
                f"Treat yourself to {title} {price_text} Melt away stress, restore your energy, and enjoy deep body relaxation."
            )
        if any(k in c for k in ["cafe", "coffee"]):
            return (
                f"Enjoy freshly brewed coffee and delicious bites at {brand}!\n\n"
                f"Try {title} {price_text} The perfect spot for brunch, casual meetups, and relaxing afternoon breaks."
            )
        if any(k in c for k in ["hotel", "resort", "stay"]):
            return (
                f"Plan your relaxing staycation at {brand}.\n\n"
                f"Experience {title} {price_text} Enjoy plush comfort, premium hospitality, and a serene weekend escape."
            )
        if any(k in c for k in ["entertainment", "gaming", "activity"]):
            return (
                f"Create unforgettable weekend memories at {brand}!\n\n"
                f"Enjoy {title} {price_text} Action-packed fun, exciting challenges, and great times for friends & family."
            )
        if any(k in c for k in ["clinic", "health"]):
            return (
                f"Prioritize your health & wellness with {brand}.\n\n"
                f"Schedule {title} {price_text} Receive professional consultation and personalized healthcare."
            )
        if any(k in c for k in ["fitness", "gym"]):
            return (
                f"Transform your fitness & energy at {brand}!\n\n"
                f"Start {title} {price_text} Modern training equipment, motivating atmosphere, and expert guidance."
            )

        return (
            f"Discover quality service at {brand}!\n\n"
            f"Enjoy {title} {price_text} Verified parameters and transparent pricing guaranteed."
        )

    def get_category_benefits(self, category: str) -> List[str]:
        """Returns natural category-specific benefit bullets."""
        c = (category or "").lower()
        if any(k in c for k in ["restaurant", "dining", "buffet", "food"]):
            return [
                "• Perfect for family dining, date nights & celebrations",
                "• Freshly prepared dishes with rich authentic flavours",
                "• Convenient venue reservation via Zookout"
            ]
        if any(k in c for k in ["salon", "hair", "beauty"]):
            return [
                "• Professional hair makeover & expert styling",
                "• Premium beauty products for long-lasting confidence",
                "• Personalized self-care treatment"
            ]
        if any(k in c for k in ["spa", "massage", "wellness"]):
            return [
                "• Deep stress relief & full body rejuvenation",
                "• Tranquil therapeutic atmosphere",
                "• Complete energy restoration"
            ]
        if any(k in c for k in ["hotel", "resort", "stay"]):
            return [
                "• Comfortable rooms & peaceful staycation vibe",
                "• Ideal weekend getaway near the city",
                "• Quality hospitality & relaxation"
            ]
        if any(k in c for k in ["entertainment", "gaming", "activity"]):
            return [
                "• Action-packed weekend fun for friends & group outings",
                "• Thrilling activities & memorable moments",
                "• Easy ticket booking via Zookout"
            ]
        if any(k in c for k in ["cafe", "coffee"]):
            return [
                "• Artisanal brewed coffee & fresh bakery treats",
                "• Cozy atmosphere for casual meetups & work sessions",
                "• Perfect midday coffee break"
            ]
        return [
            "• Verified quality service",
            "• Instant venue redemption",
            "• Transparent catalog pricing"
        ]

    def generate_hashtags(self, deal: Dict[str, Any]) -> str:
        """FEATURE 4: Embed Real Hashtags (Outputs 10-15 clean hashtags directly without generic notes)."""
        brand = deal.get("brand", "Merchant").replace(" ", "").replace("&", "").replace("-", "")
        cat = deal.get("display_category", "Deals").replace(" ", "")
        loc = deal.get("display_location", "Mumbai").replace(" ", "")

        tags = []
        c = cat.lower()

        if "restaurant" in c or "dining" in c:
            tags = [f"#{loc}Food", "#DinnerBuffet", "#WeekendDining", f"#{cat}Deals", "#Foodie", "#FamilyDinner", "#DateNight", f"#{brand}", f"#{loc}Restaurants", "#DiningOffers", "#BuffetLovers", "#ZookoutDeals"]
        elif "salon" in c or "beauty" in c:
            tags = [f"#{loc}Salon", "#HairCare", "#BeautyLook", "#HairTransformation", "#SelfCare", f"#{brand}", f"#{loc}Beauty", "#SalonOffers", "#HairStyling", "#ZookoutBeauty"]
        elif "spa" in c or "wellness" in c:
            tags = [f"#{loc}Spa", "#Wellness", "#MassageTherapy", "#StressRelief", "#Relaxation", f"#{brand}", "#SelfCareDay", f"#{loc}Wellness", "#SpaDeals", "#ZookoutSpa"]
        elif "hotel" in c or "stay" in c:
            tags = [f"#{loc}Hotels", "#Staycation", "#WeekendGetaway", "#LuxuryStay", "#TravelGram", f"#{brand}", f"#{loc}Tourism", "#HotelDeals", "#ZookoutHotels"]
        elif "cafe" in c or "coffee" in c:
            tags = [f"#{loc}Cafes", "#CoffeeLovers", "#BrunchVibes", "#CafeMeetup", "#CoffeeTime", f"#{brand}", f"#{loc}Foodie", "#FreshBrew", "#ZookoutCafes"]
        else:
            tags = [f"#{loc}Deals", f"#{cat}", f"#{brand}", "#LocalOffers", f"#{loc}Life", "#BestDeals", "#WeekendVibes", "#SpecialOffer", "#Zookout"]

        unique_tags = list(dict.fromkeys(tags))[:14]
        return " ".join(unique_tags)

    def generate_instagram_post(self, deal: Dict[str, Any]) -> str:
        """FEATURE 2: Instagram Post Generator (Category storytelling, natural CTAs, embedded real hashtags)."""
        brand = deal.get("brand", "Zookout Merchant")
        title = deal.get("clean_title", "Special Offer")
        price = deal.get("formatted_price", "Price unavailable")
        disc = deal.get("discount_percent", 0)
        loc = deal.get("display_location", "Mumbai")
        cat = deal.get("display_category", "Experience")

        cta = self.get_category_cta(cat)
        story = self.get_category_storytelling(cat, brand, title, price, disc)
        hashtags = self.generate_hashtags(deal)

        return (
            "📸 Instagram Post Generator\n\n"
            f"✨ {brand}\n\n"
            f"{story}\n\n"
            f"👉 {cta} on Zookout!\n\n"
            f"📍 {loc}\n\n"
            f"{hashtags}"
        )

    def generate_facebook_post(self, deal: Dict[str, Any]) -> str:
        """FEATURE 1: Facebook Promotion Generator (Longer post, benefits, customer-focused)."""
        brand = deal.get("brand", "Zookout Merchant")
        title = deal.get("clean_title", "Special Offer")
        price = deal.get("formatted_price", "Price unavailable")
        disc = deal.get("discount_percent", 0)
        loc = deal.get("display_location", "Mumbai")
        cat = deal.get("display_category", "Experience")

        cta = self.get_category_cta(cat)
        benefits = "\n".join(self.get_category_benefits(cat))

        if disc > 0:
            headline = f"🔥 SAVE {disc}% OFF AT {brand.upper()}!"
            price_detail = f"{price} (Flat {disc}% OFF)"
        else:
            headline = f"🌟 FEATURED {cat.upper()} EXPERIENCE AT {brand.upper()}!"
            price_detail = f"{price} (Affordable Quality)"

        return (
            "📘 Facebook Promotion\n\n"
            f"{headline}\n\n"
            f"Looking for a great {cat.lower()} experience in {loc}? {brand} presents a featured catalog offer:\n\n"
            f"📌 Offer Summary:\n"
            f"• Offer: {title}\n"
            f"• Price: {price_detail}\n"
            f"• Location: {loc}\n\n"
            f"✨ Highlights & Benefits:\n"
            f"{benefits}\n\n"
            f"👉 {cta} with Zookout!"
        )

    def generate_whatsapp_promo(self, deal: Dict[str, Any]) -> str:
        """FEATURE 6: WhatsApp Promotion (Short, shareable, clear CTA)."""
        brand = deal.get("brand", "Zookout Merchant")
        title = deal.get("clean_title", "Special Offer")
        price = deal.get("formatted_price", "Price unavailable")
        disc = deal.get("discount_percent", 0)
        cat = deal.get("display_category", "Experience")

        cta = self.get_category_cta(cat)

        if disc > 0:
            offer_line = f"Save {disc}% OFF on {title}."
        else:
            offer_line = f"Enjoy {title} for an affordable rate."

        return (
            "💬 WhatsApp Promotion\n\n"
            f"🔥 Special Deal at {brand}!\n\n"
            f"{offer_line}\n\n"
            f"💰 Price: {price}\n"
            f"📍 Location: {deal.get('display_location', 'Mumbai')}\n\n"
            f"📲 {cta} via Zookout!"
        )

    def generate_sms_campaign(self, deal: Dict[str, Any]) -> str:
        """FEATURE 6: SMS Campaign (Strictly <= 160 Characters)."""
        brand = deal.get("brand", "Zookout Merchant")
        title = deal.get("clean_title", "Special Offer")
        price = deal.get("formatted_price", "Price unavailable")
        disc = deal.get("discount_percent", 0)
        cat = deal.get("display_category", "Deal")

        cta = self.get_category_cta(cat)

        if disc > 0:
            sms_body = f"Special Offer at {brand}! {title} at {price} (Save {disc}%). {cta} on Zookout!"
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
        """FEATURE 6: Push Notification (Strictly < 80 Characters)."""
        brand = deal.get("brand", "Zookout Merchant")
        disc = deal.get("discount_percent", 0)
        cat = deal.get("display_category", "Deal")

        cta = self.get_category_cta(cat)

        if disc > 0:
            push_text = f"Save {disc}% OFF at {brand}! {cta} on Zookout."
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
        """FEATURE 6: Promotional Captions (Professional, Friendly, Luxury)."""
        brand = deal.get("brand", "Zookout Merchant")
        title = deal.get("clean_title", "Special Offer")
        price = deal.get("formatted_price", "Price unavailable")
        disc = deal.get("discount_percent", 0)
        cat = deal.get("display_category", "Experience")

        cta = self.get_category_cta(cat)

        disc_str = f"with a {disc}% savings" if disc > 0 else "at an accessible price"

        prof = f"Discover verified quality with {title} at {brand}. Available for {price} ({disc_str}). {cta} via Zookout."
        friend = f"Hey there! Ready for a great time? Enjoy {title} at {brand} for just {price}! {cta} on Zookout 🎉"
        lux = f"Indulge in a refined experience. {brand} presents {title} at {price}. Elevate your day with Zookout."

        return (
            "✍️ Promotional Caption Styles\n\n"
            f"👔 Professional Style:\n{prof}\n\n"
            f"😊 Friendly Style:\n{friend}\n\n"
            f"👑 Luxury Style:\n{lux}"
        )

    def generate_festival_promotions(self, deal: Dict[str, Any]) -> str:
        """FEATURE 8: Festival Promotions (Diwali, New Year, Valentine's Day)."""
        brand = deal.get("brand", "Zookout Merchant")
        title = deal.get("clean_title", "Special Offer")
        price = deal.get("formatted_price", "Price unavailable")
        disc = deal.get("discount_percent", 0)
        cat = deal.get("display_category", "Experience")

        cta = self.get_category_cta(cat)
        price_str = f"for {price} (Save {disc}% OFF)" if disc > 0 else f"for just {price}"

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
        """FEATURE 9: Weekend Promotion."""
        brand = deal.get("brand", "Zookout Merchant")
        title = deal.get("clean_title", "Special Offer")
        price = deal.get("formatted_price", "Price unavailable")
        disc = deal.get("discount_percent", 0)
        cat = deal.get("display_category", "Experience")

        cta = self.get_category_cta(cat)
        price_str = f"for just {price} (Save {disc}% OFF)" if disc > 0 else f"for {price}"

        return (
            "🥳 Weekend Promotion Generator\n\n"
            f"🌟 Make Your Weekend Memorable at {brand}!\n\n"
            f"Unwind and enjoy {title} {price_str} this weekend.\n\n"
            f"Perfect for family outings, friends meetups, and relaxed afternoons in {deal.get('display_location', 'Mumbai')}.\n\n"
            f"📲 {cta} on Zookout before weekend slots fill up!"
        )

    def generate_birthday_promotion(self, deal: Dict[str, Any]) -> str:
        """FEATURE 10: Birthday Promotion."""
        brand = deal.get("brand", "Zookout Merchant")
        title = deal.get("clean_title", "Special Offer")
        price = deal.get("formatted_price", "Price unavailable")
        disc = deal.get("discount_percent", 0)
        cat = deal.get("display_category", "Experience")

        cta = self.get_category_cta(cat)
        price_str = f"at {price} ({disc}% OFF)" if disc > 0 else f"at {price}"

        return (
            "🎂 Birthday Promotion Generator\n\n"
            f"🎉 Celebrate Your Birthday at {brand}!\n\n"
            f"Make your birthday extra special with {title} {price_str}.\n\n"
            "Enjoy personalized service and quality treatment on your big day.\n\n"
            f"📲 {cta} on Zookout today!"
        )

    def generate_email_campaign(self, deal: Dict[str, Any]) -> str:
        """FEATURE 8: Email Campaign (Subject, Preview, Greeting, Benefits, Details, CTA, Closing)."""
        brand = deal.get("brand", "Zookout Merchant")
        title = deal.get("clean_title", "Special Offer")
        price = deal.get("formatted_price", "Price unavailable")
        disc = deal.get("discount_percent", 0)
        cat = deal.get("display_category", "Experience")
        loc = deal.get("display_location", "Mumbai")

        cta = self.get_category_cta(cat)
        benefits = "\n".join(self.get_category_benefits(cat))

        if disc > 0:
            subject = f"Save {disc}% OFF on {title} at {brand}"
            disc_line = f"• Special Discount: Save {disc}% OFF\n"
        else:
            subject = f"Featured {cat} Package: {title} at {brand}"
            disc_line = ""

        preview = f"Discover {title} for just {price} at {brand}. {cta} on Zookout."

        body = (
            f"Dear Valued Guest,\n\n"
            f"We are delighted to introduce a featured {cat.lower()} package at {brand} in {loc}.\n\n"
            f"📌 Offer Details:\n"
            f"• Package: {title}\n"
            f"• Price: {price}\n"
            f"{disc_line}"
            f"• Location: {loc}\n\n"
            f"✨ Highlights & Customer Benefits:\n"
            f"{benefits}\n\n"
            f"Ready to enjoy this offer? Click the link below to finalize your booking.\n\n"
            f"👉 {cta} on Zookout\n\n"
            f"Warm regards,\n"
            f"{brand} Management Team"
        )

        return (
            "📧 Email Campaign Generator\n\n"
            f"📌 Subject Line:\n{subject}\n\n"
            f"👀 Preview Text:\n{preview}\n\n"
            f"📄 Email Content:\n{body}"
        )

    def generate_marketing_help(self, deal: Dict[str, Any]) -> str:
        """FEATURE 8: Category-Specific Marketing Help (Food photography, before/after reels, room tours)."""
        brand = deal.get("brand", "Zookout Merchant")
        cat = deal.get("display_category", "Experience")
        disc = deal.get("discount_percent", 0)
        loc = deal.get("display_location", "Mumbai")

        c = cat.lower()

        if "restaurant" in c:
            advice = [
                "• Food Photography: Share high-resolution photos of signature dishes and dining setups.",
                "• Weekend Campaigns: Announce weekend family dining deals on Thursday/Friday evenings.",
                "• Occasion Marketing: Highlight 'Family Dinner' & 'Date Night' themes in your social captions."
            ]
        elif "salon" in c:
            advice = [
                "• Before & After Photos: Post transformation reels showcasing hair makeovers & styling.",
                "• Transformation Reels: Share short video clips of client beauty & haircut reveals.",
                "• Self-Care Focus: Promote weekend pampering and hair treatment packages."
            ]
        elif "spa" in c:
            advice = [
                "• Relaxation Videos: Share peaceful video tours of spa rooms, candles, and therapy setups.",
                "• Stress-Relief Campaigns: Highlight weekend body relaxation and wellness rejuvenation.",
                "• Quiet Slot Promotions: Run weekday afternoon spa packages to fill off-peak hours."
            ]
        elif "hotel" in c:
            advice = [
                "• Room Showcase Tours: Share video walk-throughs of plush suites & hotel amenities.",
                "• Staycation Campaigns: Market 2-day weekend staycation packages to city residents.",
                "• Local Attraction Guides: Post local dining & sightseeing recommendations."
            ]
        elif "entertainment" in c:
            advice = [
                "• Experience Videos: Share action-packed video clips of gaming, bowling & fun activities.",
                "• Customer Testimonials: Feature happy group photos and energetic crowd reactions.",
                "• Group Discount Bundles: Promote 4-person family & friend weekend fun packages."
            ]
        elif "cafe" in c:
            advice = [
                "• Coffee & Brunch Reels: Post close-up videos of latte art, fresh bakery, and cozy seating.",
                "• Meetup Campaigns: Promote afternoon coffee & workspace meetups.",
                "• Daily Specials: Feature fresh daily bakery items on Instagram Stories."
            ]
        else:
            advice = [
                "• Visual Content Focus: Share clear photos and videos of your service experience.",
                "• Transparent Pricing: Highlight price & value clearly side-by-side in your posts.",
                "• Multi-Platform Sharing: Distribute campaigns across Instagram, Facebook & WhatsApp."
            ]

        if disc >= 40:
            advice.append(f"• High Discount Advantage: Your {disc}% OFF discount is a strong hook—feature it in bold banner headlines!")
        elif disc == 0:
            advice.append("• Value & Quality Focus: Since no discount percentage is listed, emphasize quality service and accessible pricing.")

        return (
            "💡 Merchant Marketing Help Guide\n\n"
            f"🏷️ Brand: {brand}\n"
            f"📂 Category: {cat} | 📍 Location: {loc}\n\n"
            "Category-Specific Promotion Strategies:\n"
            + "\n".join(advice) + "\n\n"
            "ℹ️ Note: Recommendations are generated specifically for your catalog listing parameters."
        )


content_creator_agent = ContentCreatorAgent()
