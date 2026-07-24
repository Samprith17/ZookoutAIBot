import logging
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

from config import BOT_TOKEN
from v2.search.search_engine import search_deals
from v2.ai.intent import detect_intent
from v2.ai.memory import memory_manager
from v2.ai.profile import profile_manager
from v2.telegram.handlers import (
    USER_SEARCH_CACHE,
    get_favourites,
    build_deal_keyboard,
    build_pagination_keyboard,
    build_confirm_clear_keyboard,
    build_confirm_reset_profile_keyboard,
    handle_callback_query,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id if update.effective_user else update.effective_chat.id
    memory_manager.clear_context(user_id)
    first_name = update.effective_user.first_name if update.effective_user else "there"

    await update.message.reply_text(
        f"👋 Hello {first_name}!\n\n"
        "I'm Zookout AI.\n\n"
        "I can help you discover amazing offers on:\n\n"
        "🍽 Restaurants\n"
        "☕ Cafes\n"
        "💆 Spas\n"
        "💇 Salons\n"
        "🏨 Hotels\n"
        "🎯 Activities\n\n"
        "Try asking:\n"
        "• Recommend something\n"
        "• What should I do today?\n"
        "• Plan a romantic evening under ₹2000\n"
        "• Compare restaurants in Mumbai\n"
        "• My Preferences"
    )


async def help_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 Zookout AI Guide & Supported Features\n\n"
        "I can help you discover, compare, and book local deals across India!\n\n"
        "Available Features & Commands:\n"
        "🌟 Smart Personalization & Preference Learning (`Recommend something`, `My Preferences`)\n"
        "🗓️ AI Experience Planner (`Plan a romantic evening under ₹2000`)\n"
        "❤️ Smart Occasion & Mood Recommendations (`Romantic Evening`, `Relax today`)\n"
        "📊 AI Smart Deal Comparison (`Compare restaurants`)\n"
        "🍽️ Restaurant & Cafe Deals\n"
        "💆 Spa & Salon Offers\n"
        "🏨 Hotel & Resort Staycations\n"
        "❤️ My Favourites (`My Favourites`)\n"
        "📜 Search History (`Recently Viewed`)\n\n"
        "Try typing:\n"
        "• Recommend something\n"
        "• What should I do today?\n"
        "• Plan a romantic evening under ₹2000\n"
        "• Compare restaurants\n"
        "• Reset Preferences"
    )


async def planner_handler(update: Update, context: ContextTypes.DEFAULT_TYPE, raw_intent: dict):
    user_id = update.effective_user.id if update.effective_user else update.effective_chat.id
    intent = memory_manager.update_context(user_id, raw_intent)
    profile_manager.update_profile_from_intent(user_id, intent)

    user_query = (intent.get("query") or "").lower()
    max_price = intent.get("max_price")
    occasion = (intent.get("occasion") or "").lower()

    if "romantic" in occasion or "romantic" in user_query or "date" in user_query:
        exp_title = "Romantic Evening"
        steps = [
            ("☕ Coffee & Atmosphere", ["cafe", "spa"], 0.25),
            ("🌙 Fine Dining Experience", ["restaurant"], 0.50),
            ("🍰 Late Night Dessert & Lounge", ["cafe", "pub", "bar"], 0.25),
        ]
        fit_reason = "Selected for an intimate romantic evening combining relaxed coffee, high-discount fine dining, and late-night lounge desserts."

    elif "birthday" in occasion or "birthday" in user_query or "celebrate" in user_query:
        exp_title = "Birthday Celebration"
        steps = [
            ("🎉 Fun Activity & Entertainment", ["entertainment", "gaming", "water park"], 0.30),
            ("🍽️ Celebration Lunch", ["restaurant"], 0.30),
            ("☕ Birthday Cafe & Treats", ["cafe"], 0.15),
            ("🌙 Festive Birthday Dinner", ["restaurant"], 0.25),
        ]
        fit_reason = "Curated for a festive birthday celebration featuring thrilling group activities, lunch, cafe treats, and a grand dinner."

    elif "relax" in occasion or "relax" in user_query or "massage" in user_query or "wellness" in user_query:
        exp_title = "Relaxing Day"
        steps = [
            ("💆 Spa Therapy & Wellness", ["spa"], 0.50),
            ("☕ Relaxing Tea & Cafe", ["cafe"], 0.20),
            ("🌙 Peaceful Dinner", ["restaurant"], 0.30),
        ]
        fit_reason = "Tailored for complete body and mind rejuvenation with premium spa therapy, peaceful cafe beverages, and dinner."

    elif "friend" in occasion or "friend" in user_query or "friends" in user_query:
        exp_title = "Weekend with Friends"
        steps = [
            ("🎯 Group Activity & Hangout", ["gaming", "adventure", "entertainment"], 0.35),
            ("☕ Cafe & Chill", ["cafe"], 0.25),
            ("🍹 Evening Pub & Dinner", ["restaurant", "pub", "bar"], 0.40),
        ]
        fit_reason = "Designed for a lively group hangout with fun activities, casual cafe socializing, and evening pub dining."

    elif "family" in occasion or "family" in user_query or "kids" in user_query:
        exp_title = "Family Outing"
        steps = [
            ("👨‍👩‍👧‍👦 Family Fun & Entertainment", ["water park", "adventure", "gaming", "entertainment"], 0.40),
            ("☕ Midday Refreshments & Cafe", ["cafe", "restaurant"], 0.20),
            ("🍽️ Family Dinner", ["restaurant"], 0.40),
        ]
        fit_reason = "Balanced for family enjoyment with engaging activities, midday refreshments, and spacious family dining."

    elif "business" in occasion or "business" in user_query:
        exp_title = "Business Lunch"
        steps = [
            ("☕ Morning Coffee & Strategy", ["cafe"], 0.30),
            ("💼 Executive Business Lunch", ["restaurant"], 0.70),
        ]
        fit_reason = "Optimized for professional discussions in quiet, executive cafe and dining venues."

    elif "solo" in occasion or "solo" in user_query:
        exp_title = "Solo Day"
        steps = [
            ("☕ Quiet Cafe & Coffee", ["cafe"], 0.30),
            ("💆 Solo Spa & Relaxation", ["spa", "entertainment"], 0.45),
            ("🍽️ Solo Gourmet Dinner", ["restaurant"], 0.25),
        ]
        fit_reason = "Curated for a peaceful solo day featuring quiet reading cafes, personal spa wellness, and gourmet dining."

    else:
        exp_title = "Weekend Experience"
        steps = [
            ("🌅 Afternoon Activity & Cafe", ["spa", "cafe", "entertainment"], 0.40),
            ("🌙 Evening Dining", ["restaurant", "pub"], 0.60),
        ]
        fit_reason = "A well-rounded weekend experience combining daytime leisure and evening dining."

    itinerary_items = []
    total_cost = 0.0
    used_brands = set()

    for step_header, step_cats, weight in steps:
        step_max_price = (max_price * weight) if max_price else None

        selected_deal = None
        for cat in step_cats:
            step_intent = {
                "type": "search",
                "category": cat,
                "city": intent.get("city") or "Mumbai",
                "location": intent.get("location"),
                "area": intent.get("area"),
                "max_price": step_max_price,
            }
            candidate_deals = search_deals(step_intent)
            candidate_deals = [d for d in candidate_deals if d.get("brand") not in used_brands]

            if candidate_deals:
                selected_deal = candidate_deals[0]
                break

        if not selected_deal:
            for cat in step_cats:
                step_intent = {
                    "type": "search",
                    "category": cat,
                    "city": intent.get("city") or "Mumbai",
                    "location": intent.get("location"),
                    "area": intent.get("area"),
                    "max_price": None,
                }
                candidate_deals = search_deals(step_intent)
                candidate_deals = [d for d in candidate_deals if d.get("brand") not in used_brands]
                if candidate_deals:
                    valid_priced = [d for d in candidate_deals if float(str(d.get("price", "0")).replace(",", "")) > 0]
                    selected_deal = min(valid_priced, key=lambda x: float(str(x.get("price", "999999")).replace(",", "")), default=candidate_deals[0])
                    break

        if selected_deal:
            used_brands.add(selected_deal.get("brand"))
            try:
                deal_price = float(str(selected_deal.get("price", "0")).replace(",", ""))
            except Exception:
                deal_price = 0.0
            total_cost += deal_price
            itinerary_items.append((step_header, selected_deal))
            profile_manager.add_recently_viewed(user_id, selected_deal)

    reply = f"🗓️ AI Experience Itinerary: {exp_title}\n\n"

    for header, deal in itinerary_items:
        reply += (
            f"{header}\n"
            f"🏷️ Brand: {deal.get('brand', 'N/A')}\n"
            f"📂 Category: {deal.get('display_category', 'N/A')}\n"
            f"📝 Offer: {deal.get('clean_title')}\n"
            f"💰 Price: {deal.get('formatted_price', 'Price not available')}\n"
            f"📍 Location: {deal.get('display_location')}\n\n"
        )

    reply += "━━━━━━━━━━━━━━━━━━\n\n"
    reply += f"💡 Estimated Total: ₹{int(total_cost)}\n"

    if max_price:
        remaining = max(0, int(max_price - total_cost))
        reply += f"💰 Remaining Budget: ₹{remaining} (out of ₹{int(max_price)})\n"

    reply += f"\n📝 Why this plan fits:\n• {fit_reason}"

    await update.message.reply_text(reply, disable_web_page_preview=True)


async def occasion_handler(update: Update, context: ContextTypes.DEFAULT_TYPE, raw_intent: dict):
    user_id = update.effective_user.id if update.effective_user else update.effective_chat.id
    user_query = (raw_intent.get("query") or "").lower()

    if any(k in user_query for k in ["weekend", "outing", "plan", "relax", "itinerary"]):
        await planner_handler(update, context, raw_intent)
        return

    intent = memory_manager.update_context(user_id, raw_intent)
    profile_manager.update_profile_from_intent(user_id, intent)

    results = search_deals(intent)
    if not results:
        fallback_intent = dict(intent)
        fallback_intent["max_price"] = None
        fallback_intent["location"] = None
        results = search_deals(fallback_intent)

    if not results:
        await update.message.reply_text("I couldn't find deals matching that occasion right now. Try searching for a specific venue or location!")
        return

    USER_SEARCH_CACHE[user_id] = results
    best_match = results[0]
    other_matches = results[1:4]

    for d in results[:4]:
        profile_manager.add_recently_viewed(user_id, d)

    occ_title = intent.get("occasion") or "Special Occasion"
    reasons_text = ""
    for reason in best_match.get("reasons", []):
        reasons_text += f"• {reason}\n"

    best_reply = (
        f"❤️ Occasion Detected:\n{occ_title}\n\n"
        "⭐ Best Match\n\n"
        f"🏷️ Brand: {best_match.get('brand', 'N/A')}\n"
        f"📂 Category: {best_match.get('display_category', 'N/A')}\n"
        f"📝 Offer: {best_match.get('clean_title')}\n"
        f"💰 Price: {best_match.get('formatted_price', 'Price not available')}\n"
        f"🎁 Discount: {best_match.get('discount_percent', 0)}%\n"
        f"📍 Location: {best_match.get('display_location')}\n\n"
        "Why this recommendation?\n"
        f"{reasons_text}"
    )
    best_keyboard = build_deal_keyboard(best_match)
    await update.message.reply_text(best_reply, reply_markup=best_keyboard, disable_web_page_preview=True)

    if other_matches:
        await update.message.reply_text("━━━━━━━━━━━━━━━━━━\n\n🎯 Other Occasion Recommendations:")
        for deal in other_matches:
            reply = (
                f"🏷️ Brand: {deal.get('brand', 'N/A')}\n"
                f"📂 Category: {deal.get('display_category', 'N/A')}\n"
                f"📝 Offer: {deal.get('clean_title')}\n"
                f"💰 Price: {deal.get('formatted_price', 'Price not available')}\n"
                f"🎁 Discount: {deal.get('discount_percent', 0)}%\n"
                f"📍 Location: {deal.get('display_location')}\n"
            )
            keyboard = build_deal_keyboard(deal)
            await update.message.reply_text(reply, reply_markup=keyboard, disable_web_page_preview=True)

    if len(results) > 4:
        p_keyboard = build_pagination_keyboard(offset=4)
        await update.message.reply_text(
            f"Showing deals 1-{min(4, len(results))} of {len(results)}. Click below for more!",
            reply_markup=p_keyboard,
        )


async def compare_handler(update: Update, context: ContextTypes.DEFAULT_TYPE, raw_intent: dict):
    user_id = update.effective_user.id if update.effective_user else update.effective_chat.id
    intent = memory_manager.update_context(user_id, raw_intent)

    if not intent.get("category"):
        intent["category"] = "restaurant"

    results = search_deals(intent)
    if not results:
        fallback_intent = dict(intent)
        fallback_intent["max_price"] = None
        fallback_intent["location"] = None
        results = search_deals(fallback_intent)

    if not results:
        await update.message.reply_text("I couldn't find deals to compare right now. Try searching for a specific category or location!")
        return

    comp_deals = results[:5]
    for d in comp_deals:
        profile_manager.add_recently_viewed(user_id, d)

    USER_SEARCH_CACHE[user_id] = comp_deals

    reply = "📊 Deal Comparison\n\n"
    for i, deal in enumerate(comp_deals, 1):
        reply += (
            f"{i}. 🏷️ Brand: {deal.get('brand', 'N/A')}\n"
            f"📂 Category: {deal.get('display_category', 'N/A')}\n"
            f"📝 Offer: {deal.get('clean_title')}\n"
            f"💰 Price: {deal.get('formatted_price', 'Price not available')}\n"
            f"🎁 Discount: {deal.get('discount_percent', 0)}%\n"
            f"📍 Location: {deal.get('display_location')}\n\n"
        )

    best_overall = comp_deals[0]

    valid_prices = [d for d in comp_deals if float(str(d.get("price", "0")).replace(",", "")) > 0]
    cheapest = min(valid_prices, key=lambda x: float(str(x.get("price", "999999")).replace(",", "")), default=best_overall)

    highest_discount = max(comp_deals, key=lambda x: x.get("discount_percent", 0), default=best_overall)

    reply += "━━━━━━━━━━━━━━━━━━\n\n"
    reply += f"🏆 Best Overall\n{best_overall.get('brand')} – Highest overall recommendation score matching your category, location, and budget criteria.\n\n"
    reply += f"💰 Cheapest\n{cheapest.get('brand')} – Lowest payable price at {cheapest.get('formatted_price')} among all compared options.\n\n"
    reply += f"🎁 Highest Discount\n{highest_discount.get('brand')} – Maximum savings offer at {highest_discount.get('discount_percent', 0)}% OFF."

    best_keyboard = build_deal_keyboard(best_overall)
    await update.message.reply_text(reply, reply_markup=best_keyboard, disable_web_page_preview=True)


async def personalized_recommendations_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Adaptive Personalization Handler (Milestone 10).
    Uses learned recency-weighted preference profile and provides clear explanation bullets.
    """
    user_id = update.effective_user.id if update.effective_user else update.effective_chat.id
    p_intent = profile_manager.get_personalized_intent(user_id)

    if not p_intent:
        p_intent = {
            "type": "search",
            "category": "restaurant",
            "city": "Mumbai",
            "location": "Mumbai",
            "query": "Recommended Deals"
        }

    results = search_deals(p_intent)
    if not results:
        await update.message.reply_text("I couldn't find personalized deals right now. Try searching for a specific venue or category!")
        return

    USER_SEARCH_CACHE[user_id] = results
    best_match = results[0]

    for d in results[:4]:
        profile_manager.add_recently_viewed(user_id, d)

    p_reasons = profile_manager.get_personalization_reasons(user_id, best_match)
    reasons_text = ""
    for r in p_reasons:
        reasons_text += f"• {r}\n"

    best_reply = (
        "🌟 Personalized Best Match\n\n"
        f"🏷️ Brand: {best_match.get('brand', 'N/A')}\n"
        f"📂 Category: {best_match.get('display_category', 'N/A')}\n"
        f"📝 Offer: {best_match.get('clean_title')}\n"
        f"💰 Price: {best_match.get('formatted_price', 'Price not available')}\n"
        f"🎁 Discount: {best_match.get('discount_percent', 0)}%\n"
        f"📍 Location: {best_match.get('display_location')}\n\n"
        "Why this recommendation?\n"
        f"{reasons_text}"
    )
    best_keyboard = build_deal_keyboard(best_match)
    await update.message.reply_text(best_reply, reply_markup=best_keyboard, disable_web_page_preview=True)

    other_matches = results[1:4]
    if other_matches:
        await update.message.reply_text("━━━━━━━━━━━━━━━━━━\n\n🎯 Other Personalized Recommendations:")
        for deal in other_matches:
            reply = (
                f"🏷️ Brand: {deal.get('brand', 'N/A')}\n"
                f"📂 Category: {deal.get('display_category', 'N/A')}\n"
                f"📝 Offer: {deal.get('clean_title')}\n"
                f"💰 Price: {deal.get('formatted_price', 'Price not available')}\n"
                f"🎁 Discount: {deal.get('discount_percent', 0)}%\n"
                f"📍 Location: {deal.get('display_location')}\n"
            )
            keyboard = build_deal_keyboard(deal)
            await update.message.reply_text(reply, reply_markup=keyboard, disable_web_page_preview=True)

    if len(results) > 4:
        p_keyboard = build_pagination_keyboard(offset=4)
        await update.message.reply_text(f"Showing deals 1-{min(4, len(results))} of {len(results)}. Click below for more!", reply_markup=p_keyboard)


async def profile_preferences_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Displays User Preference Profile (Milestone 10).
    """
    user_id = update.effective_user.id if update.effective_user else update.effective_chat.id
    profile = profile_manager.get_profile(user_id)

    if profile["search_count"] == 0 and not profile["categories"]:
        await update.message.reply_text(
            "👤 Your preference profile is currently empty!\n\n"
            "Search for deals or save favourites, and I will automatically learn your preferences over time."
        )
        return

    top_cat = profile["categories"].most_common(1)[0][0] if profile["categories"] else "Not specified"
    top_loc = profile["locations"].most_common(1)[0][0] if profile["locations"] else "Mumbai"
    top_occ = profile["occasions"].most_common(1)[0][0] if profile["occasions"] else "Not specified"
    top_merch = profile["merchants"].most_common(1)[0][0] if profile["merchants"] else "Not specified"
    avg_b = int(sum(profile["budgets"]) / len(profile["budgets"])) if profile["budgets"] else None
    budget_str = f"Under ₹{avg_b}" if avg_b else "Not specified"

    reply = (
        "👤 Your Learned Preference Profile:\n\n"
        f"📂 Favorite Category: {top_cat}\n"
        f"📍 Favorite Location: {top_loc}\n"
        f"💰 Typical Budget: {budget_str}\n"
        f"❤️ Favorite Occasion: {top_occ}\n"
        f"🏷️ Favorite Brand: {top_merch}\n"
        f"📊 Total Activity Recorded: {profile['search_count']} searches"
    )
    await update.message.reply_text(reply)


async def reset_profile_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id if update.effective_user else update.effective_chat.id
    confirm_keyboard = build_confirm_reset_profile_keyboard()
    await update.message.reply_text(
        "⚠️ Are you sure you want to reset your preference profile and clear your search history?",
        reply_markup=confirm_keyboard,
    )


async def recently_viewed_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id if update.effective_user else update.effective_chat.id
    history = profile_manager.get_recently_viewed(user_id)

    if not history:
        await update.message.reply_text("📜 You haven't viewed any deals recently! Try searching for deals first.")
        return

    await update.message.reply_text(f"📜 Recently Viewed Deals ({len(history)} items):\n")
    for deal in history:
        title = deal.get("clean_title", deal.get("title", ""))
        reply = (
            f"🏷️ Brand: {deal.get('brand', 'N/A')}\n"
            f"📂 Category: {deal.get('display_category', 'N/A')}\n"
            f"📝 Offer: {title}\n"
            f"💰 Price: {deal.get('formatted_price', 'Price not available')}\n"
            f"📍 Location: {deal.get('display_location')}\n"
        )
        keyboard = build_deal_keyboard(deal)
        await update.message.reply_text(reply, reply_markup=keyboard, disable_web_page_preview=True)


async def favourites_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id if update.effective_user else update.effective_chat.id
    favs = get_favourites(user_id)

    if not favs:
        await update.message.reply_text(
            "❤️ You haven't saved any favourite deals yet!\n\n"
            "Click ❤️ Save on any deal recommendation to view it here anytime."
        )
        return

    await update.message.reply_text(f"❤️ Your Saved Favourites ({len(favs)} deals):\n")

    for deal in favs:
        title = deal.get("clean_title", deal.get("title", ""))
        reply = (
            f"🏷️ Brand: {deal.get('brand', 'N/A')}\n"
            f"📂 Category: {deal.get('display_category', 'N/A')}\n"
            f"📝 Offer: {title}\n"
            f"💰 Price: {deal.get('formatted_price', 'Price not available')}\n"
            f"🎁 Discount: {deal.get('discount_percent', 0)}%\n"
            f"📍 Location: {deal.get('display_location')}\n"
        )
        keyboard = build_deal_keyboard(deal, is_favourite=True)
        await update.message.reply_text(reply, reply_markup=keyboard, disable_web_page_preview=True)


async def clear_favourites_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id if update.effective_user else update.effective_chat.id
    favs = get_favourites(user_id)

    if not favs:
        await update.message.reply_text("You have no saved favourites to clear.")
        return

    confirm_keyboard = build_confirm_clear_keyboard()
    await update.message.reply_text(
        f"⚠️ Are you sure you want to delete all {len(favs)} saved favourites?",
        reply_markup=confirm_keyboard,
    )


async def fallback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 I'm not sure what you mean.\n\n"
        "You can ask me things like:\n"
        "• Recommend something\n"
        "• What should I do today?\n"
        "• Plan a romantic evening under ₹2000\n"
        "• My Preferences\n"
        "• Reset Preferences"
    )


async def search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_id = update.effective_user.id if update.effective_user else update.effective_chat.id
        message = update.message.text.strip()

        # Step 1: Detect intent from message
        raw_intent = detect_intent(message)

        # Milestone 10 Preference Learning Priority Router
        if raw_intent["type"] == "greeting":
            await start(update, context)
            return

        if raw_intent["type"] == "recent":
            await recently_viewed_handler(update, context)
            return

        if raw_intent["type"] == "favourites":
            await favourites_handler(update, context)
            return

        if raw_intent["type"] == "clear_favourites":
            await clear_favourites_handler(update, context)
            return

        if raw_intent["type"] == "profile":
            await profile_preferences_handler(update, context)
            return

        if raw_intent["type"] == "reset_profile":
            await reset_profile_handler(update, context)
            return

        if raw_intent["type"] == "help":
            await help_handler(update, context)
            return

        if raw_intent["type"] == "faq":
            await update.message.reply_text(raw_intent["faq_answer"])
            return

        if raw_intent["type"] == "thanks":
            await update.message.reply_text("😊 You're welcome! Happy to help.")
            return

        if raw_intent["type"] == "bye":
            memory_manager.clear_context(user_id)
            await update.message.reply_text("👋 Goodbye! Have a wonderful day.")
            return

        if raw_intent["type"] == "out_of_scope":
            await update.message.reply_text(
                "I'm designed to help with Zookout experiences, bookings, vouchers, and local deals. I can't reliably answer unrelated questions."
            )
            return

        if raw_intent["type"] == "planner":
            await planner_handler(update, context, raw_intent)
            return

        if raw_intent["type"] == "occasion":
            await occasion_handler(update, context, raw_intent)
            return

        if raw_intent["type"] == "compare":
            await compare_handler(update, context, raw_intent)
            return

        if raw_intent["type"] == "personalized":
            await personalized_recommendations_handler(update, context)
            return

        if raw_intent["type"] == "pagination":
            cached_deals = USER_SEARCH_CACHE.get(user_id, [])
            if not cached_deals:
                await personalized_recommendations_handler(update, context)
                return

            offset = 4
            next_batch = cached_deals[offset : offset + 4]
            for deal in next_batch:
                profile_manager.add_recently_viewed(user_id, deal)
                title = deal.get("clean_title", deal.get("title", ""))
                reply = (
                    f"🏷️ Brand: {deal.get('brand', 'N/A')}\n"
                    f"📂 Category: {deal.get('display_category', 'N/A')}\n"
                    f"📝 Offer: {title}\n"
                    f"💰 Price: {deal.get('formatted_price', 'Price not available')}\n"
                    f"🎁 Discount: {deal.get('discount_percent', 0)}%\n"
                    f"📍 Location: {deal.get('display_location')}\n"
                )
                keyboard = build_deal_keyboard(deal)
                await update.message.reply_text(reply, reply_markup=keyboard, disable_web_page_preview=True)

            if offset + 4 < len(cached_deals):
                p_keyboard = build_pagination_keyboard(offset + 4)
                await update.message.reply_text(
                    f"Showing deals 1-{min(offset + 4, len(cached_deals))} of {len(cached_deals)}. Click below for more!",
                    reply_markup=p_keyboard,
                )
            return

        if raw_intent["type"] == "fallback":
            await fallback_handler(update, context)
            return

        # Standard Context-Aware Search Processing with Preference Learning
        intent = memory_manager.update_context(user_id, raw_intent)
        if intent["type"] == "search":
            profile_manager.update_profile_from_intent(user_id, intent)

        print("User ID:", user_id)
        print("Message:", message)
        print("Merged Intent:", intent)

        results = search_deals(intent)

        if not results:
            fallback_intent = dict(intent)
            fallback_intent["max_price"] = None
            fallback_intent["min_price"] = None
            fallback_intent["location"] = None

            fallback_results = search_deals(fallback_intent)

            if fallback_results:
                USER_SEARCH_CACHE[user_id] = fallback_results
                await update.message.reply_text("I couldn't find an exact match for your budget/location criteria.\n\nHere are the closest matching options:\n")

                for deal in fallback_results[:4]:
                    profile_manager.add_recently_viewed(user_id, deal)
                    reply = (
                        f"🏷️ Brand: {deal.get('brand', 'N/A')}\n"
                        f"📂 Category: {deal.get('display_category', 'N/A')}\n"
                        f"📝 Offer: {deal.get('clean_title')}\n"
                        f"💰 Price: {deal.get('formatted_price', 'Price not available')}\n"
                        f"🎁 Discount: {deal.get('discount_percent', 0)}%\n"
                        f"📍 Location: {deal.get('display_location')}\n"
                    )
                    keyboard = build_deal_keyboard(deal)
                    await update.message.reply_text(reply, reply_markup=keyboard, disable_web_page_preview=True)

                if len(fallback_results) > 4:
                    p_keyboard = build_pagination_keyboard(offset=4)
                    await update.message.reply_text("Click below to view more recommendations:", reply_markup=p_keyboard)
            else:
                await update.message.reply_text(
                    "I couldn't find an exact match.\n\n"
                    "Try searching for:\n"
                    "• Recommend something\n"
                    "• What should I do today?\n"
                    "• Plan a romantic evening under ₹2000"
                )
            return

        USER_SEARCH_CACHE[user_id] = results

        best_match = results[0]
        other_matches = results[1:4]

        for d in results[:4]:
            profile_manager.add_recently_viewed(user_id, d)

        reasons_text = ""
        for reason in best_match.get("reasons", []):
            reasons_text += f"• {reason}\n"

        best_reply = (
            "⭐ Best Match\n\n"
            f"🏷️ Brand: {best_match.get('brand', 'N/A')}\n"
            f"📂 Category: {best_match.get('display_category', 'N/A')}\n"
            f"📝 Offer: {best_match.get('clean_title')}\n"
            f"💰 Price: {best_match.get('formatted_price', 'Price not available')}\n"
            f"🎁 Discount: {best_match.get('discount_percent', 0)}%\n"
            f"📍 Location: {best_match.get('display_location')}\n\n"
            "Why this recommendation?\n"
            f"{reasons_text}"
        )
        best_keyboard = build_deal_keyboard(best_match)
        await update.message.reply_text(best_reply, reply_markup=best_keyboard, disable_web_page_preview=True)

        if other_matches:
            await update.message.reply_text("━━━━━━━━━━━━━━━━━━\n\n🎯 Other Top Recommendations:")

            for deal in other_matches:
                reply = (
                    f"🏷️ Brand: {deal.get('brand', 'N/A')}\n"
                    f"📂 Category: {deal.get('display_category', 'N/A')}\n"
                    f"📝 Offer: {deal.get('clean_title')}\n"
                    f"💰 Price: {deal.get('formatted_price', 'Price not available')}\n"
                    f"🎁 Discount: {deal.get('discount_percent', 0)}%\n"
                    f"📍 Location: {deal.get('display_location')}\n"
                )
                keyboard = build_deal_keyboard(deal)
                await update.message.reply_text(reply, reply_markup=keyboard, disable_web_page_preview=True)

        if len(results) > 4:
            p_keyboard = build_pagination_keyboard(offset=4)
            await update.message.reply_text(
                f"Showing deals 1-{min(4, len(results))} of {len(results)}. Click below for more!",
                reply_markup=p_keyboard,
            )

    except Exception as e:
        logger.error(f"Error in search handler: {e}", exc_info=True)
        await update.message.reply_text(
            "Sorry, I encountered an issue processing your request. Please try again!"
        )


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error("Exception while handling an update:", exc_info=context.error)
    if isinstance(update, Update) and update.effective_message:
        await update.effective_message.reply_text(
            "Sorry, something went wrong while processing your request."
        )


def main():
    if not BOT_TOKEN:
        raise SystemExit("[ERROR] BOT_TOKEN is missing. Please set BOT_TOKEN in your environment or .env file.")

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_handler))
    app.add_handler(CommandHandler("favourites", favourites_handler))
    app.add_handler(CommandHandler("clear_favourites", clear_favourites_handler))
    app.add_handler(CommandHandler("history", recently_viewed_handler))
    app.add_handler(CommandHandler("profile", profile_preferences_handler))
    app.add_handler(CommandHandler("reset_profile", reset_profile_handler))
    app.add_handler(CallbackQueryHandler(handle_callback_query))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, search))
    app.add_error_handler(error_handler)

    print("[OK] Zookout AI Bot is running with Preference Learning Engine...")
    app.run_polling()


if __name__ == "__main__":
    main()