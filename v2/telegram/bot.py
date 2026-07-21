from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

from v2.search.search_engine import search_deals
from v2.ai.intent import detect_intent

# Replace with your NEW BotFather token
BOT_TOKEN = "8911959946:AAEsf-9H31eAYbSMAfvlrOF0x9uTQMNGc-c"


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Welcome to Zookout AI!\n\n"
        "I can help you discover amazing deals.\n\n"
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
        print("✅ Greeting detected")
        await update.message.reply_text(
            "👋 Hello! Welcome to Zookout AI.\n\n"
            "How can I help you today?"
        )
        return

    # Help
    if intent["type"] == "help":
        await update.message.reply_text(
            "🤖 I can help you find amazing deals.\n\n"
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

    # Search deals
    results = search_deals(intent)

    if not results:
        await update.message.reply_text(
            "❌ No matching deals found.\n\n"
            "Try:\n"
            "• Restaurant in Mumbai\n"
            "• Spa under ₹1000\n"
            "• Cafe in Bandra"
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
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, search)
    )

    print("✅ Zookout AI Bot is running...")
    app.run_polling()


if __name__ == "__main__":
    main()