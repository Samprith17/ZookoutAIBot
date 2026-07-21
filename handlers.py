import html
import logging
import re
from typing import Dict, List, Optional

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from search import engine, search_deals

logger = logging.getLogger(__name__)

GREETINGS = {"hi", "hello", "hey", "good morning", "good evening"}
THANKS = {"thanks", "thank you", "thankyou"}
GOODBYES = {"bye", "goodbye", "see you", "take care"}
NOISE_PATTERNS = [
    r"\bbuy\b",
    r"\bvoucher\b",
    r"\bvisit\b",
    r"\bshow\b",
    r"\bpay\b",
    r"\benjoy\b",
    r"\bnow\b",
    r"\bworth\b",
]

SEARCH_PROMPTS = (
    "Restaurant",
    "Salon",
    "Spa",
    "Cafe",
    "Hotel",
    "Waterpark",
    "Entertainment",
)


class DealFormatter:
    DIVIDER = "━━━━━━━━━━━━━━━━━━"

    @staticmethod
    def normalize_text(text: str) -> str:
        return re.sub(r"\s+", " ", (text or "").strip())

    @classmethod
    def format_deal(cls, deal: Dict[str, object], index: int, total: int) -> str:
        brand = cls.normalize_text(str(deal.get("brand", "Unknown")))
        category = cls.normalize_text(str(deal.get("category", "")))
        title = cls.normalize_text(str(deal.get("title", "Deal")))
        description = cls.normalize_text(str(deal.get("description", "")))
        price = deal.get("price", 0)
        original_price = deal.get("original_price", 0)
        raw_discount = deal.get("discount_percent", deal.get("discount", ""))
        if isinstance(raw_discount, (int, float)):
            discount = f"{int(raw_discount)}%" if raw_discount else ""
        else:
            discount = cls.normalize_text(str(raw_discount))
        location = cls.normalize_text(str(deal.get("location", "")))
        website = cls.normalize_text(str(deal.get("website", "")))

        lines = [
            cls.DIVIDER,
            f"Deal {index} of {total}",
            "",
            "🏢 Brand",
            html.escape(brand),
        ]

        if category:
            lines.extend(["", "📂 Category", html.escape(category)])

        lines.extend(["", "🎁 Offer", html.escape(title)])

        if price:
            lines.extend(["", f"💰 Price: ₹{price}"])
            if original_price and original_price != price:
                lines.append(f"🧾 Was: ₹{original_price}")
        else:
            lines.extend(["", "💰 Price", "Contact merchant"])

        if discount:
            lines.extend(["", "🎉 Discount", html.escape(discount)])

        if location:
            lines.extend(["", "📍 Location", html.escape(location)])

        if website:
            lines.extend(["", "🔗 Website", html.escape(website)])

        if description:
            lines.extend(["", "📝 Description", html.escape(description)])

        lines.append(cls.DIVIDER)

        return "\n".join(lines)

    @staticmethod
    def build_keyboard(index: int, total: int, website: str) -> InlineKeyboardMarkup:
        row: List[InlineKeyboardButton] = [InlineKeyboardButton("❤️ Save", callback_data=f"save:{index}")]
        if website:
            row.append(InlineKeyboardButton("🌐 Open Website", url=website))

        buttons: List[List[InlineKeyboardButton]] = [row]

        nav_buttons: List[InlineKeyboardButton] = []
        if index > 0:
            nav_buttons.append(InlineKeyboardButton("⬅ Previous", callback_data=f"nav:{index - 1}"))
        if index < total - 1:
            nav_buttons.append(InlineKeyboardButton("➡ Next", callback_data=f"nav:{index + 1}"))
        if nav_buttons:
            buttons.append(nav_buttons)

        buttons.append([InlineKeyboardButton("🏠 Home", callback_data="home")])
        return InlineKeyboardMarkup(buttons)

    @classmethod
    def build_session(cls, results: List[Dict[str, object]], index: int) -> Dict[str, object]:
        deal = results[index]
        return {
            "text": cls.format_deal(deal, index + 1, len(results)),
            "markup": cls.build_keyboard(index, len(results), str(deal.get("website", ""))),
        }

    @staticmethod
    def no_match_text() -> str:
        return (
            "❌ Sorry!\n\n"
            "No matching deals found.\n\n"
            "Try searching:\n"
            "Restaurant\n"
            "Salon\n"
            "Spa\n"
            "Cafe\n"
            "Hotel"
        )

    @staticmethod
    def home_text() -> str:
        return (
            "👋 Welcome to Zookout AI.\n\n"
            "Type any search query to find the best deals.\n\n"
            "Popular searches:\n"
            "Restaurant\n"
            "Salon\n"
            "Spa\n"
            "Cafe\n"
            "Hotel"
        )


def _normalize_query(query: str) -> str:
    return re.sub(r"\s+", " ", query.strip().lower())


def _get_intent(query: str) -> str | None:
    normalized = _normalize_query(query)
    if normalized in GREETINGS:
        return "greeting"
    if normalized in THANKS:
        return "thanks"
    if normalized in GOODBYES:
        return "goodbye"
    return None


def _search_intent(query: str) -> str:
    intent = engine.detect_intent(query)
    return intent or "Unknown"


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is None or update.message.text is None:
        logger.info("Ignored non-text update: %s", update)
        return

    query = update.message.text.strip()
    if not query:
        logger.info(
            "Ignored empty text message from chat %s",
            update.effective_chat.id if update.effective_chat else None,
        )
        return

    chat_id = update.effective_chat.id if update.effective_chat else None
    user_id = update.effective_user.id if update.effective_user else None
    logger.info("User Query: chat=%s user=%s query=%s", chat_id, user_id, query)

    intent = _get_intent(query)
    if intent == "greeting":
        await update.message.reply_text(DealFormatter.home_text())
        logger.info("Bot Reply: greeting chat=%s user=%s", chat_id, user_id)
        return

    if intent == "thanks":
        await update.message.reply_text("😊 You're welcome!\n\nNeed another deal?")
        logger.info("Bot Reply: thanks chat=%s user=%s", chat_id, user_id)
        return

    if intent == "goodbye":
        await update.message.reply_text("👋 Have a great day!\n\nCome back anytime.")
        logger.info("Bot Reply: goodbye chat=%s user=%s", chat_id, user_id)
        return

    results = search_deals(query)
    search_category = _search_intent(query)
    logger.info("Search Category: chat=%s user=%s category=%s", chat_id, user_id, search_category)

    if not results:
        await update.message.reply_text(DealFormatter.no_match_text())
        logger.info("Bot Reply: no result chat=%s user=%s", chat_id, user_id)
        return

    context.user_data["search_session"] = {
        "query": query,
        "results": results,
        "current_index": 0,
    }

    session = DealFormatter.build_session(results, 0)
    try:
        await update.message.reply_text(
            session["text"],
            disable_web_page_preview=True,
            reply_markup=session["markup"],
        )
        logger.info(
            "Bot Reply: deals chat=%s user=%s count=%s",
            chat_id,
            user_id,
            len(results),
        )
    except Exception:
        logger.exception("Failed to send reply to chat=%s user=%s", chat_id, user_id)
        await update.message.reply_text("⚠️ Sorry, I could not send the response.")


async def handle_callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query is None or query.data is None:
        return

    data = query.data
    session = context.user_data.get("search_session")
    if data == "home":
        context.user_data.pop("search_session", None)
        await query.edit_message_text(DealFormatter.home_text())
        await query.answer()
        return

    if not session or "results" not in session:
        await query.answer("Session expired. Please search again.", show_alert=True)
        return

    results = session["results"]
    if data.startswith("nav:"):
        try:
            new_index = int(data.split(":", 1)[1])
        except ValueError:
            await query.answer("Invalid navigation command.", show_alert=True)
            return

        if new_index < 0 or new_index >= len(results):
            await query.answer("No more cards.", show_alert=True)
            return

        session["current_index"] = new_index
        session_text = DealFormatter.build_session(results, new_index)
        await query.edit_message_text(
            session_text["text"],
            disable_web_page_preview=True,
            reply_markup=session_text["markup"],
        )
        await query.answer()
        return

    if data.startswith("save:"):
        try:
            deal_index = int(data.split(":", 1)[1])
        except ValueError:
            await query.answer("Could not save deal.", show_alert=True)
            return

        if deal_index < 0 or deal_index >= len(results):
            await query.answer("Could not save deal.", show_alert=True)
            return

        saved = context.user_data.setdefault("saved_deals", [])
        deal_to_save = results[deal_index]
        if deal_to_save not in saved:
            saved.append(deal_to_save)
        await query.answer("Deal saved. Use /start to search again.")
        return

    await query.answer("Unknown action.", show_alert=True)
