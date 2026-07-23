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


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Welcome to Zookout AI!\n\n"
        "I can help you discover amazing local deals and experiences.\n\n"
        "Examples:\n"
        "🍽 Restaurant in Mumbai\n"
        "💆 Spa under ₹1000\n"
        "☕ Cafe in Bandra\n"
        "🏨 Hotel deals"
    )


async def search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message.text.strip()

    intent = detect_intent(message)

    print("Message:", message)
    print("Intent:", intent)

    # Greeting
    if intent["type"] == "greeting":
        print("[OK] Greeting detected")
        await update.message.reply_text(
            "👋 Hello! Welcome to Zookout AI.\n\n"
            "How can I help you find deals today?"
        )
        return

    # Help
    if intent["type"] == "help":
        await update.message.reply_text(
            "🤖 I can help you find amazing deals & answer questions about Zookout.\n\n"
            "Examples:\n"
            "🍽 Restaurant in Mumbai\n"
            "💆 Spa under ₹1000\n"
            "☕ Cafe in Bandra"
        )
        return

    # Thanks
    if intent["type"] == "thanks":
        await update.message.reply_text(
            "😊 You're welcome! Happy to help."
        )
        return

    # Goodbye
    if intent["type"] == "bye":
        await update.message.reply_text(
            "👋 Goodbye! Have a wonderful day."
        )
        return

    # Out of Scope
    if intent["type"] == "out_of_scope":
        await update.message.reply_text(
            "I'm designed to help with Zookout experiences, bookings, vouchers, and local deals. I can't reliably answer unrelated questions."
        )
        return

    # FAQ
    if intent["type"] == "faq":
        await update.message.reply_text(intent["faq_answer"])
        return

    # Search deals
    results = search_deals(intent)

    if not results:
        await update.message.reply_text(
            "I couldn't find an exact match.\n\n"
            "Try searching for:\n"
            "• Restaurant in Mumbai\n"
            "• Spa under ₹1000\n"
            "• Cafe in Bandra\n\n"
            "Would you like to see similar options?"
        )
        return

    reply = "🎯 Top Matching Deals\n\n"

    for deal in results[:5]:
        reply += (
            f"🏷️ Brand: {deal.get('brand', 'N/A')}\n"
            f"📂 Category: {deal.get('category', 'N/A')}\n"
            f"📝 {deal.get('title', 'No Title')}\n"
            f"💰 Price: ₹{deal.get('price', 'N/A')}\n"
            f"🎁 Discount: {deal.get('discount_percent', 0)}%\n"
            f"📍 Location: {deal.get('location', 'N/A')}\n"
            f"🔗 {deal.get('website', '')}\n"
            "────────────────────────\n\n"
        )

    await update.message.reply_text(reply)


def main():
    if not BOT_TOKEN:
        raise SystemExit("[ERROR] BOT_TOKEN is missing. Please set BOT_TOKEN in your environment or .env file.")

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, search)
    )

    print("[OK] Zookout AI Bot is running...")
    app.run_polling()


if __name__ == "__main__":
    main()