import logging
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

from config import BOT_TOKEN
from v2.search.search_engine import search_deals
from v2.ai.intent import detect_intent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Welcome to Zookout AI!\n\n"
        "I can help you discover amazing local deals and experiences.\n\n"
        "Examples:\n"
        "🍽 Restaurant in Mumbai\n"
        "💆 Spa under ₹1000\n"
        "💇 Salon in Andheri\n"
        "☕ Cafe below ₹500\n"
        "🍺 Pub in Bandra\n"
        "🏨 Hotel in Mumbai\n"
        "🎟 Adventure activities"
    )


async def search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        message = update.message.text.strip()
        intent = detect_intent(message)

        print("Message:", message)
        print("Intent:", intent)

        if intent["type"] == "greeting":
            await update.message.reply_text(
                "👋 Hello! Welcome to Zookout AI.\n\n"
                "How can I help you find deals today?"
            )
            return

        if intent["type"] == "help":
            await update.message.reply_text(
                "🤖 I can help you find amazing deals & answer questions about Zookout.\n\n"
                "Examples:\n"
                "🍽 Restaurant in Mumbai\n"
                "💆 Spa under ₹1000\n"
                "💇 Salon in Andheri\n"
                "🍺 Pub in Bandra"
            )
            return

        if intent["type"] == "thanks":
            await update.message.reply_text("😊 You're welcome! Happy to help.")
            return

        if intent["type"] == "bye":
            await update.message.reply_text("👋 Goodbye! Have a wonderful day.")
            return

        if intent["type"] == "out_of_scope":
            await update.message.reply_text(
                "I'm designed to help with Zookout experiences, bookings, vouchers, and local deals. I can't reliably answer unrelated questions."
            )
            return

        if intent["type"] == "faq":
            await update.message.reply_text(intent["faq_answer"])
            return

        results = search_deals(intent)

        if not results:
            fallback_intent = dict(intent)
            fallback_intent["max_price"] = None
            fallback_intent["min_price"] = None
            fallback_intent["location"] = None

            fallback_results = search_deals(fallback_intent)

            if fallback_results:
                reply = "I couldn't find an exact match.\n\nHere are the closest matching options:\n\n"
                for deal in fallback_results[:5]:
                    title = deal.get('title', 'No Title')
                    if len(title) > 80:
                        title = title[:77] + "..."

                    reply += (
                        f"🏷️ Brand: {deal.get('brand', 'N/A')}\n"
                        f"📂 Category: {deal.get('category', 'N/A')}\n"
                        f"📝 {title}\n"
                        f"💰 Price: ₹{deal.get('price', 'N/A')}\n"
                        f"🎁 Discount: {deal.get('discount_percent', 0)}%\n"
                        f"📍 Location: {deal.get('location', 'N/A')}\n"
                        f"🔗 {deal.get('website', '')}\n"
                        "────────────────────────\n\n"
                    )
                await update.message.reply_text(reply, disable_web_page_preview=True)
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

        reply = "🎯 Top Matching Deals\n\n"

        for deal in results[:5]:
            title = deal.get('title', 'No Title')
            if len(title) > 80:
                title = title[:77] + "..."

            reply += (
                f"🏷️ Brand: {deal.get('brand', 'N/A')}\n"
                f"📂 Category: {deal.get('category', 'N/A')}\n"
                f"📝 {title}\n"
                f"💰 Price: ₹{deal.get('price', 'N/A')}\n"
                f"🎁 Discount: {deal.get('discount_percent', 0)}%\n"
                f"📍 Location: {deal.get('location', 'N/A')}\n"
                f"🔗 {deal.get('website', '')}\n"
                "────────────────────────\n\n"
            )

        await update.message.reply_text(reply, disable_web_page_preview=True)

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
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, search))
    app.add_error_handler(error_handler)

    print("[OK] Zookout AI Bot is running...")
    app.run_polling()


if __name__ == "__main__":
    main()