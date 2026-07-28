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
from v2.search.search_engine import search_deals, normalize_deal, get_nearby_locations, get_deal_comparison
from v2.ai.intent import detect_intent
from v2.ai.memory import memory_manager
from v2.ai.profile import profile_manager
from v2.ai.savings import savings_agent
from v2.ai.merchant import merchant_agent
from v2.ai.content_creator import content_creator_agent
from v2.ai.analytics import analytics_engine
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


def generate_no_deals_response(intent: dict) -> str:
    """
    AI Deal Concierge Dataset-Aware 'No Deals Found' Response Engine.
    Explains requested search criteria, suggests nearby alternative locations, and provides active catalog suggestions.
    """
    query = intent.get("query") or "your request"
    cat = intent.get("category")
    loc = intent.get("location") or intent.get("area") or intent.get("city")
    max_p = intent.get("max_price")

    criteria = []
    if cat:
        criteria.append(f"Category: {cat.title()}")
    if loc:
        criteria.append(f"Location: {loc.title()}")
    if max_p:
        criteria.append(f"Max Budget: ₹{int(max_p)}")

    crit_text = f" ({', '.join(criteria)})" if criteria else ""

    nearby = get_nearby_locations(loc) if loc else ["Andheri", "Bandra", "Juhu"]
    nearby_text = f"Try nearby locations: {', '.join(nearby)}"

    return (
        f"🔍 No Deals Found for \"{query}\"{crit_text}\n\n"
        f"We currently don't have active catalog deals matching your exact search criteria in {loc or 'this area'}.\n\n"
        f"💡 {nearby_text}\n\n"
        "📊 Active Catalog Overview:\n"
        "• Locations Available: Mumbai (Andheri, Bandra, Juhu, Powai, Thane, Borivali, Dadar, Worli, Lower Parel, Malad)\n"
        "• Categories Available: Restaurant, Salon, Spa, Hotel, Cafe, Entertainment\n"
        "• Price Range: ₹9 – ₹999\n\n"
        "💡 Try exploring available catalog searches:\n"
        "• \"Restaurants in Bandra\"\n"
        "• \"Spa deals in Andheri\"\n"
        "• \"Buffet under ₹500\"\n"
        "• \"Show Opportunities\""
    )


def build_concierge_reasons(deal: dict, intent: dict) -> str:
    """Generates AI Concierge multi-constraint reasoning bullets."""
    reasons = []

    cat = deal.get("display_category") or deal.get("category")
    if cat:
        reasons.append(f"Top-rated {cat} experience matching your request.")

    loc = deal.get("display_location") or deal.get("location")
    req_loc = intent.get("area") or intent.get("location")
    if req_loc and loc and req_loc.lower() in loc.lower():
        reasons.append(f"Located right in your requested area ({req_loc}).")
    elif loc:
        reasons.append(f"Conveniently located in {loc}.")

    max_p = intent.get("max_price")
    try:
        p = float(str(deal.get("price", "0")).replace(",", ""))
        if max_p and p > 0 and p <= max_p:
            reasons.append(f"Fits within your budget of ₹{int(max_p)} (Price: {deal.get('formatted_price')}).")
        elif p > 0:
            reasons.append(f"Great value offer priced at {deal.get('formatted_price')}.")
    except Exception:
        pass

    disc = deal.get("discount_percent", 0)
    if disc and disc > 0:
        reasons.append(f"High savings offer with {disc}% OFF.")

    occ = intent.get("occasion")
    if occ:
        reasons.append(f"Perfect atmosphere for a {occ}.")

    dt = intent.get("date") or intent.get("time_filter")
    if dt:
        reasons.append(f"Available for your requested {dt} timing.")

    if not reasons:
        reasons.append("Top verified offer recommended for your criteria.")

    return "\n".join([f"• {r}" for r in reasons])


def get_suggested_next_actions(intent: dict) -> str:
    """Generates dynamic interactive next action suggestions."""
    actions = []
    cat = intent.get("category") or "deal"
    loc = intent.get("area") or intent.get("location") or "Mumbai"

    actions.append(f"• Type \"Plan a {cat} in {loc}\" for a full itinerary")
    actions.append(f"• Type \"Compare {cat}s in {loc}\" for side-by-side comparison")
    actions.append("• Type \"My Savings\" or \"Show Opportunities\" to surface top savings")
    actions.append("• Type \"Business Dashboard\" or \"Category Analytics\" for business intelligence")

    return "\n".join(actions)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id if update.effective_user else update.effective_chat.id
    memory_manager.clear_context(user_id)
    first_name = update.effective_user.first_name if update.effective_user else "there"

    await update.message.reply_text(
        f"👋 Hello {first_name}!\n\n"
        "I'm Zookout AI Deal Concierge, your AI assistant for discovering local deals, dining, spas, salons, and activities across India!\n\n"
        "🛒 AI Concierge Features:\n"
        "• Multi-turn Deal Concierge (\"I want dinner\")\n"
        "• Romantic dinner in Andheri under ₹2000\n"
        "• Plan a romantic evening in Andheri under ₹3000\n"
        "• Compare restaurants in Mumbai\n"
        "• My Savings | Show Opportunities\n\n"
        "🏪 For Merchants & Content Creators:\n"
        "• Create Instagram Post | Create Facebook Post\n"
        "• Merchant Dashboard | Offer Health\n\n"
        "📊 For Business Intelligence & Analytics:\n"
        "• Business Dashboard | Catalog Summary | Category Analytics | Location Analytics"
    )


async def help_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 Zookout AI Deal Concierge Features\n\n"
        "Available Customer Commands:\n"
        "💰 Customer Savings Profile (`My Savings`)\n"
        "🔥 Opportunity Detection (`Show Opportunities`)\n"
        "🔍 Multi-Turn Deal Concierge (`I want dinner`)\n"
        "🗓️ AI Experience Planner (`Plan a romantic evening in Andheri under ₹3000`)\n"
        "📊 Deal Comparison (`Compare restaurants in Mumbai`)\n\n"
        "🏪 Merchant & AI Content Creator Commands:\n"
        "📸 `Create Instagram Post` | 📘 `Create Facebook Post` | 💬 `Create WhatsApp Promotion` | 📊 `Merchant Dashboard`\n\n"
        "📊 Business Intelligence & Analytics Commands:\n"
        "📊 `Business Dashboard` | 📑 `Catalog Summary` | 📂 `Category Analytics` | 🏷️ `Brand Analytics` | 📍 `Location Analytics` | 🎁 `Discount Analytics` | 💰 `Price Analytics` | 🩺 `Catalog Health` | 📈 `Business Insights` | 🛠️ `What should we improve?`"
    )


async def merchant_review_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id if update.effective_user else update.effective_chat.id
    deal = merchant_agent.get_merchant_deal(user_id)
    review_text = merchant_agent.review_offer(deal)
    await update.message.reply_text(review_text)


async def merchant_score_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id if update.effective_user else update.effective_chat.id
    deal = merchant_agent.get_merchant_deal(user_id)
    score_text = merchant_agent.format_offer_score(deal)
    await update.message.reply_text(score_text)


async def merchant_growth_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id if update.effective_user else update.effective_chat.id
    deal = merchant_agent.get_merchant_deal(user_id)
    growth_text = merchant_agent.generate_growth_suggestions(deal)
    await update.message.reply_text(growth_text)


async def merchant_improve_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id if update.effective_user else update.effective_chat.id
    deal = merchant_agent.get_merchant_deal(user_id)
    improved_text = merchant_agent.suggest_improved_description(deal)
    await update.message.reply_text(improved_text)


async def merchant_dashboard_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id if update.effective_user else update.effective_chat.id
    dash_text = merchant_agent.merchant_dashboard(user_id)
    await update.message.reply_text(dash_text)


async def merchant_health_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id if update.effective_user else update.effective_chat.id
    health_text = merchant_agent.offer_health(user_id)
    await update.message.reply_text(health_text)


async def merchant_compare_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id if update.effective_user else update.effective_chat.id
    comp_text = merchant_agent.compare_offers(user_id)
    await update.message.reply_text(comp_text)


async def merchant_promote_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id if update.effective_user else update.effective_chat.id
    prom_text = merchant_agent.promote_offer(user_id)
    await update.message.reply_text(prom_text)


async def merchant_help_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = merchant_agent.merchant_help()
    await update.message.reply_text(help_text)


async def savings_profile_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id if update.effective_user else update.effective_chat.id
    summary = savings_agent.get_savings_profile_summary(user_id)
    await update.message.reply_text(summary)


async def opportunities_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id if update.effective_user else update.effective_chat.id
    opps = savings_agent.detect_opportunities(user_id, limit=4)

    if not opps:
        await update.message.reply_text(
            "🔥 Customer Savings Agent:\n\n"
            "No new unnotified deal opportunities found right now based on your current preferences.\n\n"
            "Try searching for deals or saving favourites to help me detect personalized opportunities for you!"
        )
        return

    await update.message.reply_text(f"🔥 Customer Savings Opportunities ({len(opps)} items):\n")

    for raw_deal in opps:
        deal = normalize_deal(raw_deal)
        deal_id = deal.get("id")
        savings_agent.mark_notified(user_id, deal_id)
        profile_manager.add_recently_viewed(user_id, deal)

        reasons_list = raw_deal.get("opportunity_reasons", [])
        reasons_text = "\n".join([f"• {r}" for r in reasons_list]) if reasons_list else "• Popular recommendation"

        reply = (
            f"🔥 Deal Opportunity\n\n"
            f"🏷️ Brand: {deal.get('brand')}\n"
            f"📂 Category: {deal.get('display_category')}\n"
            f"📝 Offer: {deal.get('clean_title')}\n"
            f"💰 Price: {deal.get('formatted_price')}\n"
            f"🎁 Discount: {deal.get('discount_percent')}%\n"
            f"📍 Location: {deal.get('display_location')}\n\n"
            "Why this opportunity:\n"
            f"{reasons_text}"
        )
        keyboard = build_deal_keyboard(deal)
        await update.message.reply_text(reply, reply_markup=keyboard, disable_web_page_preview=True)


async def why_this_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id if update.effective_user else update.effective_chat.id
    history = profile_manager.get_recently_viewed(user_id)

    if not history:
        await update.message.reply_text(
            "💡 Why you see recommendations:\n\n"
            "Zookout AI matches deals based on your favourite categories, budget range, preferred areas, and search activity.\n\n"
            "Try searching for deals first!"
        )
        return

    last_deal = normalize_deal(history[0])
    reasons = savings_agent.explain_recommendation(user_id, last_deal)

    reply = (
        f"💡 Why you saw this recommendation:\n\n"
        f"🏷️ Brand: {last_deal.get('brand')}\n"
        f"📝 Offer: {last_deal.get('clean_title')}\n\n"
        "Matching Criteria:\n"
        f"{reasons}"
    )
    await update.message.reply_text(reply)


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
                selected_deal = normalize_deal(candidate_deals[0])
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
                    raw_selected = min(valid_priced, key=lambda x: float(str(x.get("price", "999999")).replace(",", "")), default=candidate_deals[0])
                    selected_deal = normalize_deal(raw_selected)
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
            f"🏷️ Brand: {deal.get('brand')}\n"
            f"📂 Category: {deal.get('display_category')}\n"
            f"📝 Offer: {deal.get('clean_title')}\n"
            f"💰 Price: {deal.get('formatted_price')}\n"
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
        no_deals_msg = generate_no_deals_response(intent)
        await update.message.reply_text(no_deals_msg)
        return

    memory_manager.mark_completed(user_id)
    USER_SEARCH_CACHE[user_id] = results
    best_match = normalize_deal(results[0])
    other_matches = [normalize_deal(d) for d in results[1:4]]

    for d in results[:4]:
        profile_manager.add_recently_viewed(user_id, d)

    occ_title = intent.get("occasion") or "Special Occasion"
    reasons_text = build_concierge_reasons(best_match, intent)
    suggested_actions = get_suggested_next_actions(intent)

    best_reply = (
        f"❤️ Occasion Detected: {occ_title}\n\n"
        "⭐ Best Match\n\n"
        f"🏷️ Brand: {best_match.get('brand')}\n"
        f"📂 Category: {best_match.get('display_category')}\n"
        f"📝 Offer: {best_match.get('clean_title')}\n"
        f"💰 Estimated Price: {best_match.get('formatted_price')}\n"
        f"🎁 Discount: {best_match.get('discount_percent')}%\n"
        f"📍 Location: {best_match.get('display_location')}\n\n"
        "📝 Reasoning:\n"
        f"{reasons_text}\n\n"
        "💡 Suggested Next Actions:\n"
        f"{suggested_actions}"
    )
    best_keyboard = build_deal_keyboard(best_match)
    await update.message.reply_text(best_reply, reply_markup=best_keyboard, disable_web_page_preview=True)

    if other_matches:
        await update.message.reply_text("━━━━━━━━━━━━━━━━━━\n\n🎯 Other Occasion Recommendations:")
        for deal in other_matches:
            reply = (
                f"🏷️ Brand: {deal.get('brand')}\n"
                f"📂 Category: {deal.get('display_category')}\n"
                f"📝 Offer: {deal.get('clean_title')}\n"
                f"💰 Price: {deal.get('formatted_price')}\n"
                f"🎁 Discount: {deal.get('discount_percent')}%\n"
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

    results = get_deal_comparison(intent)
    if not results:
        no_deals_msg = generate_no_deals_response(intent)
        await update.message.reply_text(no_deals_msg)
        return

    memory_manager.mark_completed(user_id)
    reply = "📊 Deal Comparison Table\n\n"
    for i, item in enumerate(results, 1):
        reply += (
            f"{i}. 🏷️ Brand: {item['brand']}\n"
            f"   💰 Price: {item['price']}\n"
            f"   🎁 Discount: {item['discount']} (Savings: {item['savings']})\n"
            f"   {item['rating']} | 🏆 {item['recommendation']}\n\n"
        )

    await update.message.reply_text(reply, disable_web_page_preview=True)


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
        no_deals_msg = generate_no_deals_response(p_intent)
        await update.message.reply_text(no_deals_msg)
        return

    USER_SEARCH_CACHE[user_id] = results
    best_match = normalize_deal(results[0])

    for d in results[:4]:
        profile_manager.add_recently_viewed(user_id, d)

    p_reasons = profile_manager.get_personalization_reasons(user_id, best_match)
    reasons_text = ""
    for r in p_reasons:
        reasons_text += f"• {r}\n"

    suggested_actions = get_suggested_next_actions(p_intent)

    best_reply = (
        "🌟 Personalized Best Match\n\n"
        f"🏷️ Brand: {best_match.get('brand')}\n"
        f"📂 Category: {best_match.get('display_category')}\n"
        f"📝 Offer: {best_match.get('clean_title')}\n"
        f"💰 Estimated Price: {best_match.get('formatted_price')}\n"
        f"🎁 Discount: {best_match.get('discount_percent')}%\n"
        f"📍 Location: {best_match.get('display_location')}\n\n"
        "📝 Reasoning:\n"
        f"{reasons_text}\n"
        "💡 Suggested Next Actions:\n"
        f"{suggested_actions}"
    )
    best_keyboard = build_deal_keyboard(best_match)
    await update.message.reply_text(best_reply, reply_markup=best_keyboard, disable_web_page_preview=True)

    other_matches = [normalize_deal(d) for d in results[1:4]]
    if other_matches:
        await update.message.reply_text("━━━━━━━━━━━━━━━━━━\n\n🎯 Other Personalized Recommendations:")
        for deal in other_matches:
            reply = (
                f"🏷️ Brand: {deal.get('brand')}\n"
                f"📂 Category: {deal.get('display_category')}\n"
                f"📝 Offer: {deal.get('clean_title')}\n"
                f"💰 Price: {deal.get('formatted_price')}\n"
                f"🎁 Discount: {deal.get('discount_percent')}%\n"
                f"📍 Location: {deal.get('display_location')}\n"
            )
            keyboard = build_deal_keyboard(deal)
            await update.message.reply_text(reply, reply_markup=keyboard, disable_web_page_preview=True)

    if len(results) > 4:
        p_keyboard = build_pagination_keyboard(offset=4)
        await update.message.reply_text(f"Showing deals 1-{min(4, len(results))} of {len(results)}. Click below for more!", reply_markup=p_keyboard)


async def profile_preferences_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
    for raw_deal in history:
        deal = normalize_deal(raw_deal)
        title = deal.get("clean_title")
        reply = (
            f"🏷️ Brand: {deal.get('brand')}\n"
            f"📂 Category: {deal.get('display_category')}\n"
            f"📝 Offer: {title}\n"
            f"💰 Price: {deal.get('formatted_price')}\n"
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

    for raw_deal in favs:
        deal = normalize_deal(raw_deal)
        title = deal.get("clean_title")
        reply = (
            f"🏷️ Brand: {deal.get('brand')}\n"
            f"📂 Category: {deal.get('display_category')}\n"
            f"📝 Offer: {title}\n"
            f"💰 Price: {deal.get('formatted_price')}\n"
            f"🎁 Discount: {deal.get('discount_percent')}%\n"
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
        "• Business Dashboard\n"
        "• Category Analytics\n"
        "• Create Instagram Post\n"
        "• My Savings\n"
        "• Show Opportunities\n"
        "• Romantic dinner in Andheri under ₹2000"
    )


async def search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_id = update.effective_user.id if update.effective_user else update.effective_chat.id
        message = update.message.text.strip()

        # Step 1: Detect intent from message
        raw_intent = detect_intent(message)

        # Milestone 15 Business Intelligence & Analytics Interception
        if raw_intent.get("is_merchant") and raw_intent["type"].startswith("analytics_"):
            if raw_intent["type"] == "analytics_dashboard":
                await update.message.reply_text(analytics_engine.generate_business_dashboard())
                return
            if raw_intent["type"] == "analytics_summary":
                await update.message.reply_text(analytics_engine.generate_catalog_summary())
                return
            if raw_intent["type"] == "analytics_category":
                await update.message.reply_text(analytics_engine.generate_category_analytics())
                return
            if raw_intent["type"] == "analytics_brand":
                await update.message.reply_text(analytics_engine.generate_brand_analytics())
                return
            if raw_intent["type"] == "analytics_location":
                await update.message.reply_text(analytics_engine.generate_location_analytics())
                return
            if raw_intent["type"] == "analytics_discount":
                await update.message.reply_text(analytics_engine.generate_discount_analytics())
                return
            if raw_intent["type"] == "analytics_price":
                await update.message.reply_text(analytics_engine.generate_price_analytics())
                return
            if raw_intent["type"] == "analytics_health":
                await update.message.reply_text(analytics_engine.generate_catalog_health())
                return
            if raw_intent["type"] == "analytics_distribution":
                await update.message.reply_text(analytics_engine.generate_offer_distribution())
                return
            if raw_intent["type"] == "analytics_insights":
                await update.message.reply_text(analytics_engine.generate_business_insights())
                return
            if raw_intent["type"] == "analytics_improvements":
                await update.message.reply_text(analytics_engine.generate_improvement_suggestions())
                return
            if raw_intent["type"] == "analytics_help":
                await update.message.reply_text(analytics_engine.generate_business_help())
                return

        # Milestone 14 AI Content Creator Interception
        if raw_intent.get("is_merchant") and raw_intent["type"].startswith("content_"):
            deal = content_creator_agent.get_deal(user_id)
            if raw_intent["type"] == "content_instagram":
                await update.message.reply_text(content_creator_agent.generate_instagram_post(deal))
                return
            if raw_intent["type"] == "content_facebook":
                await update.message.reply_text(content_creator_agent.generate_facebook_post(deal))
                return
            if raw_intent["type"] == "content_whatsapp":
                await update.message.reply_text(content_creator_agent.generate_whatsapp_promo(deal))
                return
            if raw_intent["type"] == "content_sms":
                await update.message.reply_text(content_creator_agent.generate_sms_campaign(deal))
                return
            if raw_intent["type"] == "content_push":
                await update.message.reply_text(content_creator_agent.generate_push_notification(deal))
                return
            if raw_intent["type"] == "content_caption":
                await update.message.reply_text(content_creator_agent.generate_promotional_captions(deal))
                return
            if raw_intent["type"] == "content_hashtags":
                await update.message.reply_text(content_creator_agent.generate_hashtags(deal))
                return
            if raw_intent["type"] == "content_festival":
                await update.message.reply_text(content_creator_agent.generate_festival_promotions(deal))
                return
            if raw_intent["type"] == "content_weekend":
                await update.message.reply_text(content_creator_agent.generate_weekend_promotion(deal))
                return
            if raw_intent["type"] == "content_birthday":
                await update.message.reply_text(content_creator_agent.generate_birthday_promotion(deal))
                return
            if raw_intent["type"] == "content_email":
                await update.message.reply_text(content_creator_agent.generate_email_campaign(deal))
                return
            if raw_intent["type"] == "content_help":
                await update.message.reply_text(content_creator_agent.generate_marketing_help(deal))
                return

        # Milestone 13 Merchant Router Interception
        if raw_intent.get("is_merchant") or raw_intent["type"].startswith("merchant_"):
            if raw_intent["type"] == "merchant_review":
                await merchant_review_handler(update, context)
                return
            if raw_intent["type"] == "merchant_score":
                await merchant_score_handler(update, context)
                return
            if raw_intent["type"] == "merchant_growth":
                await merchant_growth_handler(update, context)
                return
            if raw_intent["type"] in ["merchant_improve", "merchant_improve_help"]:
                await merchant_improve_handler(update, context)
                return
            if raw_intent["type"] == "merchant_dashboard":
                await merchant_dashboard_handler(update, context)
                return
            if raw_intent["type"] == "merchant_health":
                await merchant_health_handler(update, context)
                return
            if raw_intent["type"] == "merchant_compare":
                await merchant_compare_handler(update, context)
                return
            if raw_intent["type"] == "merchant_promote":
                await merchant_promote_handler(update, context)
                return
            if raw_intent["type"] in ["merchant_get_customers", "merchant_help"]:
                await merchant_help_handler(update, context)
                return

        # Customer Priority Router
        if raw_intent["type"] == "greeting":
            await start(update, context)
            return

        if raw_intent["type"] == "savings":
            await savings_profile_handler(update, context)
            return

        if raw_intent["type"] == "opportunities":
            await opportunities_handler(update, context)
            return

        if raw_intent["type"] == "why_this":
            await why_this_handler(update, context)
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
            next_batch = [normalize_deal(d) for d in cached_deals[offset : offset + 4]]
            for deal in next_batch:
                profile_manager.add_recently_viewed(user_id, deal)
                title = deal.get("clean_title")
                reply = (
                    f"🏷️ Brand: {deal.get('brand')}\n"
                    f"📂 Category: {deal.get('display_category')}\n"
                    f"📝 Offer: {title}\n"
                    f"💰 Price: {deal.get('formatted_price')}\n"
                    f"🎁 Discount: {deal.get('discount_percent')}%\n"
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

        # Check if user sent a continuation modifier without an active search context
        is_modifier_query = any(w in message.lower() for w in [
            "cheaper", "lower price", "higher discount", "best discount", "only buffet"
        ])
        if is_modifier_query and not memory_manager.is_session_active(user_id):
            await update.message.reply_text(
                "There is no active search to continue. Please start a new search (e.g. 'Restaurants in Bandra' or 'I want dinner')."
            )
            return

        # Context-Aware Concierge & Multi-Turn Processing
        intent = memory_manager.update_context(user_id, raw_intent)
        if intent["type"] == "search":
            profile_manager.update_profile_from_intent(user_id, intent)

        # Multi-Turn Concierge Prompt Resolution Check
        cat = intent.get("category")
        loc = intent.get("location") or intent.get("area") or intent.get("city")
        price = intent.get("max_price")
        occ = intent.get("occasion")

        # Check if generic partial request missing fields
        is_generic_query = len(message.split()) <= 4 and (not loc or not price)

        if is_generic_query and cat and not loc:
            memory_manager.set_pending_field(user_id, "location")
            await update.message.reply_text("Which location are you looking for?")
            return

        if is_generic_query and cat and loc and not price:
            memory_manager.set_pending_field(user_id, "budget")
            await update.message.reply_text("What's your budget?")
            return

        if is_generic_query and cat and loc and price and not occ and cat in ["restaurant", "spa"]:
            memory_manager.set_pending_field(user_id, "occasion")
            await update.message.reply_text("Is this for a romantic dinner, family outing, business meeting, or casual meal?")
            return

        logger.info(f"User ID: {user_id} | Message: {message} | Merged Intent: {intent}")

        results = search_deals(intent)

        if not results:
            no_deals_msg = generate_no_deals_response(intent)
            await update.message.reply_text(no_deals_msg)
            return

        memory_manager.mark_completed(user_id)
        USER_SEARCH_CACHE[user_id] = results

        best_match = normalize_deal(results[0])
        other_matches = [normalize_deal(d) for d in results[1:4]]

        for d in results[:4]:
            profile_manager.add_recently_viewed(user_id, d)

        reasons_text = build_concierge_reasons(best_match, intent)
        suggested_actions = get_suggested_next_actions(intent)

        best_reply = (
            "⭐ Best Match\n\n"
            f"🏷️ Brand: {best_match.get('brand')}\n"
            f"📂 Category: {best_match.get('display_category')}\n"
            f"📝 Offer: {best_match.get('clean_title')}\n"
            f"💰 Estimated Price: {best_match.get('formatted_price')}\n"
            f"🎁 Discount: {best_match.get('discount_percent')}%\n"
            f"📍 Location: {best_match.get('display_location')}\n\n"
            "📝 Reasoning:\n"
            f"{reasons_text}\n\n"
            "💡 Suggested Next Actions:\n"
            f"{suggested_actions}"
        )
        best_keyboard = build_deal_keyboard(best_match)
        await update.message.reply_text(best_reply, reply_markup=best_keyboard, disable_web_page_preview=True)

        if other_matches:
            await update.message.reply_text("━━━━━━━━━━━━━━━━━━\n\n🎯 Other Top Recommendations:")

            for deal in other_matches:
                reply = (
                    f"🏷️ Brand: {deal.get('brand')}\n"
                    f"📂 Category: {deal.get('display_category')}\n"
                    f"📝 Offer: {deal.get('clean_title')}\n"
                    f"💰 Price: {deal.get('formatted_price')}\n"
                    f"🎁 Discount: {deal.get('discount_percent')}%\n"
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
    app.add_handler(CommandHandler("savings", savings_profile_handler))
    app.add_handler(CommandHandler("opportunities", opportunities_handler))
    app.add_handler(CommandHandler("review_offer", merchant_review_handler))
    app.add_handler(CommandHandler("offer_score", merchant_score_handler))
    app.add_handler(CommandHandler("growth", merchant_growth_handler))
    app.add_handler(CommandHandler("improve_desc", merchant_improve_handler))
    app.add_handler(CommandHandler("merchant_dashboard", merchant_dashboard_handler))
    app.add_handler(CommandHandler("offer_health", merchant_health_handler))
    app.add_handler(CommandHandler("compare_offers", merchant_compare_handler))
    app.add_handler(CommandHandler("promote", merchant_promote_handler))
    app.add_handler(CommandHandler("merchant_help", merchant_help_handler))
    app.add_handler(CommandHandler("business_dashboard", lambda u, c: u.message.reply_text(analytics_engine.generate_business_dashboard())))
    app.add_handler(CommandHandler("catalog_summary", lambda u, c: u.message.reply_text(analytics_engine.generate_catalog_summary())))
    app.add_handler(CommandHandler("category_analytics", lambda u, c: u.message.reply_text(analytics_engine.generate_category_analytics())))
    app.add_handler(CommandHandler("brand_analytics", lambda u, c: u.message.reply_text(analytics_engine.generate_brand_analytics())))
    app.add_handler(CommandHandler("location_analytics", lambda u, c: u.message.reply_text(analytics_engine.generate_location_analytics())))
    app.add_handler(CommandHandler("discount_analytics", lambda u, c: u.message.reply_text(analytics_engine.generate_discount_analytics())))
    app.add_handler(CommandHandler("price_analytics", lambda u, c: u.message.reply_text(analytics_engine.generate_price_analytics())))
    app.add_handler(CommandHandler("catalog_health", lambda u, c: u.message.reply_text(analytics_engine.generate_catalog_health())))
    app.add_handler(CommandHandler("distribution", lambda u, c: u.message.reply_text(analytics_engine.generate_offer_distribution())))
    app.add_handler(CommandHandler("business_insights", lambda u, c: u.message.reply_text(analytics_engine.generate_business_insights())))
    app.add_handler(CommandHandler("catalog_improvements", lambda u, c: u.message.reply_text(analytics_engine.generate_improvement_suggestions())))
    app.add_handler(CommandHandler("business_help", lambda u, c: u.message.reply_text(analytics_engine.generate_business_help())))
    app.add_handler(CommandHandler("favourites", favourites_handler))
    app.add_handler(CommandHandler("clear_favourites", clear_favourites_handler))
    app.add_handler(CommandHandler("history", recently_viewed_handler))
    app.add_handler(CommandHandler("profile", profile_preferences_handler))
    app.add_handler(CommandHandler("reset_profile", reset_profile_handler))
    app.add_handler(CallbackQueryHandler(handle_callback_query))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, search))
    app.add_error_handler(error_handler)

    print("[OK] Zookout AI Bot is running with AI Deal Concierge & Multi-Turn Conversations...")
    app.run_polling()


if __name__ == "__main__":
    main()