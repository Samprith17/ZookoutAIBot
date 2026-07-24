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
        "• Restaurant in Mumbai\n"
        "• Spa under ₹1000\n"
        "• Cafe in Bandra\n"
        "• Recommend something\n"
        "• Plan my Saturday"
    )


async def help_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 Zookout AI Guide & Supported Features\n\n"
        "I can help you discover, compare, and book local deals across India!\n\n"
        "Available Features & Commands:\n"
        "🍽️ Restaurant & Cafe Deals\n"
        "💆 Spa & Salon Offers\n"
        "🏨 Hotel & Resort Staycations\n"
        "🎯 Entertainment & Water Parks\n"
        "❤️ My Favourites (`My Favourites`)\n"
        "📜 Search History (`Recently Viewed`)\n"
        "🌟 Personal Recommendations (`Recommend something`)\n"
        "🗓️ AI Day Planner (`Plan my Saturday under ₹2000`)\n\n"
        "Try typing:\n"
        "• Restaurant in Mumbai\n"
        "• Spa under ₹1000\n"
        "• Cafe in Bandra\n"
        "• Recommend something\n"
        "• Plan my Saturday"
    )


async def planner_handler(update: Update, context: ContextTypes.DEFAULT_TYPE, intent: dict):
    user_id = update.effective_user.id if update.effective_user else update.effective_chat.id
    max_price = intent.get("max_price") or 3000

    dining_intent = {"type": "search", "category": "restaurant", "city": "Mumbai", "max_price": max_price / 2}
    spa_intent = {"type": "search", "category": "spa", "city": "Mumbai", "max_price": max_price / 2}

    dining_deals = search_deals(dining_intent)
    spa_deals = search_deals(spa_intent)

    reply = "🗓️ AI Day Planner Itinerary\n\n"
    total_cost = 0

    if spa_deals:
        spa = spa_deals[0]
        try:
            total_cost += float(str(spa.get("price", "0")).replace(",", ""))
        except Exception:
            pass
        reply += (
            "🌅 Morning / Relaxation Experience\n"
            f"🏷️ Brand: {spa.get('brand', 'N/A')}\n"
            f"📂 Category: {spa.get('display_category', 'Spa')}\n"
            f"📝 Offer: {spa.get('clean_title')}\n"
            f"💰 Price: {spa.get('formatted_price')}\n"
            f"📍 Location: {spa.get('display_location')}\n\n"
        )
        profile_manager.add_recently_viewed(user_id, spa)

    if dining_deals:
        dine = dining_deals[0]
        try:
            total_cost += float(str(dine.get("price", "0")).replace(",", ""))
        except Exception:
            pass
        reply += (
            "🌙 Evening / Dining Experience\n"
            f"🏷️ Brand: {dine.get('brand', 'N/A')}\n"
            f"📂 Category: {dine.get('display_category', 'Restaurant')}\n"
            f"📝 Offer: {dine.get('clean_title')}\n"
            f"💰 Price: {dine.get('formatted_price')}\n"
            f"📍 Location: {dine.get('display_location')}\n\n"
        )
        profile_manager.add_recently_viewed(user_id, dine)

    if total_cost > 0:
        reply += f"💡 Total Estimated Cost: ₹{int(total_cost)}"

    await update.message.reply_text(reply, disable_web_page_preview=True)


async def fallback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 I'm not sure what you mean.\n\n"
        "You can ask me things like:\n"
        "• Restaurant in Mumbai\n"
        "• Spa under ₹1000\n"
        "• Recommend something\n"
        "• Plan my Saturday"
    )


async def personalized_recommendations_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
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


async def profile_preferences_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id if update.effective_user else update.effective_chat.id
    profile = profile_manager.get_profile(user_id)

    if profile["search_count"] == 0 and not profile["categories"]:
        await update.message.reply_text(
            "👤 Your preference profile is currently empty!\n\n"
            "Search for deals or save favourites, and I will automatically learn your preferences over time."
        )
        return

    cats_str = ", ".join([f"{k} ({v})" for k, v in profile["categories"].most_common(3)]) or "None"
    locs_str = ", ".join([f"{k} ({v})" for k, v in profile["locations"].most_common(3)]) or "None"
    merch_str = ", ".join([f"{k} ({v})" for k, v in profile["merchants"].most_common(3)]) or "None"
    avg_b = int(sum(profile["budgets"]) / len(profile["budgets"])) if profile["budgets"] else None
    budget_str = f"Under ₹{avg_b}" if avg_b else "Not specified"

    reply = (
        "👤 Your Personal Preference Profile:\n\n"
        f"📂 Favourite Categories: {cats_str}\n"
        f"💰 Typical Budget: {budget_str}\n"
        f"📍 Preferred Locations: {locs_str}\n"
        f"🏷️ Favourite Merchants: {merch_str}\n"
        f"📊 Total Searches Recorded: {profile['search_count']}"
    )
    await update.message.reply_text(reply)


async def reset_profile_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id if update.effective_user else update.effective_chat.id
    confirm_keyboard = build_confirm_reset_profile_keyboard()
    await update.message.reply_text(
        "⚠️ Are you sure you want to reset your preference profile and clear your search history?",
        reply_markup=confirm_keyboard,
    )


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


async def search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_id = update.effective_user.id if update.effective_user else update.effective_chat.id
        message = update.message.text.strip()

        # Step 1: Detect intent from message
        raw_intent = detect_intent(message)

        # Milestone 6.3 Strict Priority Routing Hierarchy:
        # Priority 1: Commands & Greetings
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

        # Priority 3: Help
        if raw_intent["type"] == "help":
            await help_handler(update, context)
            return

        # Priority 4: General Questions / FAQ
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

        # Priority 5: Day Planner Intent
        if raw_intent["type"] == "planner":
            await planner_handler(update, context, raw_intent)
            return

        # Priority 6: Recommendation Intent (Explicit Only)
        if raw_intent["type"] == "personalized":
            await personalized_recommendations_handler(update, context)
            return

        # Priority 8: Fallback Intent
        if raw_intent["type"] == "fallback":
            await fallback_handler(update, context)
            return

        # Priority 7: Search Intent
        intent = memory_manager.update_context(user_id, raw_intent)
        if intent["type"] == "search":
            profile_manager.update_profile_from_intent(user_id, intent)

        print("User ID:", user_id)
        print("Message:", message)
        print("Merged Intent:", intent)

        # Search deals using Recommendation Engine
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
                    "• Restaurant in Mumbai\n"
                    "• Spa under ₹1000\n"
                    "• Salon in Andheri\n"
                    "• Cafe below ₹500"
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

    print("[OK] Zookout AI Bot is running with Prioritized Intent Router...")
    app.run_polling()


if __name__ == "__main__":
    main()