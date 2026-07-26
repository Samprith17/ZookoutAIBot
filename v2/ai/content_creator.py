import logging
from typing import Dict, List, Any
from v2.search.search_engine import normalize_deal
from v2.ai.merchant import merchant_agent

logger = logging.getLogger(__name__)


class ContentCreatorAgent:
    """
    Milestone 14 - AI Content Creator for Merchants:
    Generates professional, platform-specific marketing content for Instagram, Facebook,
    WhatsApp, SMS, Push Notifications, Promotional Captions, Hashtags, Festival Promotions,
    Weekend & Birthday Promotions, Email Campaigns, and Marketing Help.
    Strict Rule: Uses strictly normalized catalog offer data (never invents fake discounts, coupon codes, or analytics).
    """

    def get_deal(self, user_id: int) -> Dict[str, Any]:
        """Retrieves normalized merchant deal."""
        return merchant_agent.get_merchant_deal(user_id)

    def generate_instagram_post(self, deal: Dict[str, Any]) -> str:
        """FEATURE 1: Instagram Post Generator."""
        brand = deal.get("brand", "Zookout Merchant")
        title = deal.get("clean_title", "Special Offer")
        price = deal.get("formatted_price", "Price unavailable")
        disc = deal.get("discount_percent", 0)
        loc = deal.get("display_location", "Mumbai")
        cat = deal.get("display_category", "Experience")

        hashtags = self.generate_hashtags(deal).split("\n\n")[-1]

        disc_str = f"({disc}% OFF)" if disc > 0 else ""

        return (
            "📸 Instagram Post Generator\n\n"
            f"✨ Special Offer at {brand}!\n\n"
            f"Enjoy {title} for just {price} {disc_str}.\n\n"
            "Treat yourself to a fantastic experience with top-tier service.\n\n"
            "👉 Book your appointment today on Zookout!\n\n"
            f"📍 {loc}\n\n"
            f"{hashtags}"
        )

    def generate_facebook_post(self, deal: Dict[str, Any]) -> str:
        """FEATURE 2: Facebook Promotion Generator."""
        brand = deal.get("brand", "Zookout Merchant")
        title = deal.get("clean_title", "Special Offer")
        price = deal.get("formatted_price", "Price unavailable")
        disc = deal.get("discount_percent", 0)
        loc = deal.get("display_location", "Mumbai")
        cat = deal.get("display_category", "Experience")

        disc_str = f"SAVE {disc}% OFF" if disc > 0 else "SPECIAL OFFER"

        return (
            "📘 Facebook Promotion\n\n"
            f"🔥 EXCLUSIVE PROMOTION: {disc_str} AT {brand.upper()}!\n\n"
            f"Looking for a great {cat} experience in {loc}? We have an exciting deal for you!\n\n"
            f"📌 Offer Details:\n"
            f"• Offer: {title}\n"
            f"• Special Price: {price}\n"
            f"• Discount: {disc}% OFF\n"
            f"• Location: {loc}\n\n"
            "✨ Benefits:\n"
            "• Premium quality service\n"
            "• Instant venue redemption\n"
            "• Best value pricing guaranteed\n\n"
            "👉 How to Book:\n"
            "Click the link below or book instantly via Zookout!"
        )

    def generate_whatsapp_promo(self, deal: Dict[str, Any]) -> str:
        """FEATURE 3: WhatsApp Promotion Generator."""
        brand = deal.get("brand", "Zookout Merchant")
        title = deal.get("clean_title", "Special Offer")
        price = deal.get("formatted_price", "Price unavailable")
        disc = deal.get("discount_percent", 0)

        disc_str = f"Flat {disc}% OFF on " if disc > 0 else ""

        return (
            "💬 WhatsApp Promotion\n\n"
            f"🔥 Limited Time Offer at {brand}!\n\n"
            f"{disc_str}{title}.\n\n"
            f"💰 Only {price}.\n\n"
            "📍 Location: Mumbai\n\n"
            "📲 Book now directly via Zookout!"
        )

    def generate_sms_campaign(self, deal: Dict[str, Any]) -> str:
        """FEATURE 4: SMS Campaign (Strictly <= 160 Characters)."""
        brand = deal.get("brand", "Zookout Merchant")
        title = deal.get("clean_title", "Special Offer")
        price = deal.get("formatted_price", "Price unavailable")
        disc = deal.get("discount_percent", 0)

        sms_body = f"Special Deal at {brand}! {title} at {price} ({disc}% OFF). Book today on Zookout!"

        if len(sms_body) > 160:
            sms_body = f"{brand}: {title} at {price} ({disc}% OFF). Book now on Zookout!"[:160]

        return (
            "📱 SMS Campaign (160 Characters Max)\n\n"
            f"{sms_body}\n\n"
            f"📊 Character Count: {len(sms_body)}/160"
        )

    def generate_push_notification(self, deal: Dict[str, Any]) -> str:
        """FEATURE 5: Push Notification (Strictly < 80 Characters)."""
        brand = deal.get("brand", "Zookout Merchant")
        disc = deal.get("discount_percent", 0)

        if disc > 0:
            push_text = f"{disc}% OFF at {brand}! Book today on Zookout."
        else:
            push_text = f"Special Deal at {brand}! Book today on Zookout."

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
        title = deal.get("clean_title", "Special Offer")
        price = deal.get("formatted_price", "Price unavailable")
        disc = deal.get("discount_percent", 0)

        prof = f"Discover premium quality with {title} at {brand}. Available for {price} ({disc}% OFF). Reserve your booking via Zookout."
        friend = f"Hey there! Treat yourself to {title} at {brand} for just {price}! Save {disc}% OFF when you book today on Zookout 🎉"
        lux = f"Indulge in an exquisite experience. {brand} presents {title} at an exclusive offer of {price}. Elevate your day with Zookout."

        return (
            "✍️ Promotional Caption Styles\n\n"
            f"👔 Professional Style:\n{prof}\n\n"
            f"😊 Friendly Style:\n{friend}\n\n"
            f"👑 Luxury Style:\n{lux}"
        )

    def generate_hashtags(self, deal: Dict[str, Any]) -> str:
        """FEATURE 7: Hashtag Generator (10-15 Relevant Hashtags)."""
        brand = deal.get("brand", "Merchant").replace(" ", "").replace("&", "")
        cat = deal.get("display_category", "Deals").replace(" ", "")
        loc = deal.get("display_location", "Mumbai").replace(" ", "")

        hashtags = [
            f"#{cat}", f"#{cat}Deals", f"#{loc}Deals", f"#{loc}Food" if cat == "Restaurant" else f"#{loc}Life",
            f"#{brand}", f"#{cat}Offer", "#LocalDeals", f"#{loc}Shopping", "#BestOffers",
            "#ZookoutDeals", "#WeekendVibes", "#SpecialOffer", f"#{loc}Events", "#DiscountsIndia"
        ]

        tag_str = " ".join(hashtags[:14])

        return (
            "🏷️ Relevant Hashtags Generator\n\n"
            f"{tag_str}\n\n"
            "ℹ️ Note: 14 curated hashtags based on category, brand, and location."
        )

    def generate_festival_promotions(self, deal: Dict[str, Any]) -> str:
        """FEATURE 8: Festival Promotion Generator (Themed copy, no fake discounts)."""
        brand = deal.get("brand", "Zookout Merchant")
        title = deal.get("clean_title", "Special Offer")
        price = deal.get("formatted_price", "Price unavailable")
        disc = deal.get("discount_percent", 0)

        diwali = f"🪔 Diwali Celebration at {brand}! Enjoy {title} for {price} ({disc}% OFF). Light up your festivities with Zookout!"
        ny = f"🎆 New Year Special! Ring in the New Year with {title} at {brand} for just {price}. Book on Zookout!"
        vday = f"❤️ Valentine's Day Special! Celebrate love at {brand} with {title} at {price} ({disc}% OFF)."

        return (
            "🎉 Festival Campaign Generator\n\n"
            f"🪔 Diwali Campaign:\n{diwali}\n\n"
            f"🎆 New Year Campaign:\n{ny}\n\n"
            f"❤️ Valentine's Day Campaign:\n{vday}"
        )

    def generate_weekend_promotion(self, deal: Dict[str, Any]) -> str:
        """FEATURE 9: Weekend Promotion Generator."""
        brand = deal.get("brand", "Zookout Merchant")
        title = deal.get("clean_title", "Special Offer")
        price = deal.get("formatted_price", "Price unavailable")
        disc = deal.get("discount_percent", 0)

        return (
            "🥳 Weekend Promotion Generator\n\n"
            f"🌟 Make Your Weekend Unforgettable at {brand}!\n\n"
            f"Enjoy {title} for just {price} ({disc}% OFF) this weekend.\n\n"
            "Unwind, relax, and make the most of your days off.\n\n"
            "📲 Reserve your weekend slot on Zookout today!"
        )

    def generate_birthday_promotion(self, deal: Dict[str, Any]) -> str:
        """FEATURE 10: Birthday Promotion Generator."""
        brand = deal.get("brand", "Zookout Merchant")
        title = deal.get("clean_title", "Special Offer")
        price = deal.get("formatted_price", "Price unavailable")
        disc = deal.get("discount_percent", 0)

        return (
            "🎂 Birthday Promotion Generator\n\n"
            f"🎉 Celebrate Your Special Day at {brand}!\n\n"
            f"Treat yourself and your loved ones to {title} for just {price} ({disc}% OFF).\n\n"
            "Make birthday memories extra special with premium service.\n\n"
            "📲 Book your birthday celebration package on Zookout!"
        )

    def generate_email_campaign(self, deal: Dict[str, Any]) -> str:
        """FEATURE 11: Email Campaign Generator."""
        brand = deal.get("brand", "Zookout Merchant")
        title = deal.get("clean_title", "Special Offer")
        price = deal.get("formatted_price", "Price unavailable")
        disc = deal.get("discount_percent", 0)
        cat = deal.get("display_category", "Experience")

        subject = f"Exclusive Offer: {disc}% OFF on {title} at {brand}!"
        preview = f"Enjoy {title} for just {price}. Book your slot today on Zookout."
        body = (
            f"Dear Customer,\n\n"
            f"We are excited to share an exclusive {cat} offer at {brand}!\n\n"
            f"📌 Offer Details:\n"
            f"• Offer: {title}\n"
            f"• Special Price: {price} ({disc}% OFF)\n"
            f"• Location: {deal.get('display_location', 'Mumbai')}\n\n"
            "Take advantage of this limited-time catalog promotion and enjoy top-tier service.\n\n"
            "Warm regards,\n"
            f"{brand} Team"
        )
        cta = "👉 Click Here to Book on Zookout"

        return (
            "📧 Email Campaign Generator\n\n"
            f"📌 Subject Line:\n{subject}\n\n"
            f"👀 Preview Text:\n{preview}\n\n"
            f"📄 Email Body:\n{body}\n\n"
            f"🔗 Call-to-Action:\n{cta}"
        )

    def generate_marketing_help(self, deal: Dict[str, Any]) -> str:
        """FEATURE 12: Marketing Help."""
        cat = deal.get("display_category", "Experience")
        disc = deal.get("discount_percent", 0)

        return (
            "💡 Merchant Marketing Help Guide\n\n"
            "How to Effectively Promote Your Offer:\n\n"
            "1. 📸 Instagram & Visual Platforms:\n"
            f"• Best for {cat} offers. Post high-quality photos highlighting the {disc}% OFF savings.\n\n"
            "2. 💬 WhatsApp & Direct Messaging:\n"
            "• Share short, direct promotional messages with clear pricing for repeat customers.\n\n"
            "3. ⏰ Timing & Frequency:\n"
            "• Post weekend promotions on Thursday & Friday evenings to drive weekend bookings.\n\n"
            "4. 🎯 Target Audience Engagement:\n"
            "• Emphasize occasion themes like Family Dinners, Date Nights, or Birthdays in your captions.\n\n"
            "ℹ️ Note: Advice is based strictly on available catalog parameters."
        )


content_creator_agent = ContentCreatorAgent()
