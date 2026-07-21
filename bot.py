import logging
from telegram import Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

from config import BOT_TOKEN
from handlers import handle_callback_query, handle_message

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logging.getLogger("telegram").setLevel(logging.WARNING)
logging.getLogger("telegram.ext").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Welcome to Zookout AI!\n\n"
        "I can help you find:\n"
        "🍽 Restaurants\n"
        "💆 Spas\n"
        "💇 Salons\n"
        "🏨 Hotels\n"
        "🎬 Entertainment\n\n"
        "Simply type what you're looking for.\n\n"
        "Examples:\n"
        "Restaurant\n"
        "Spa\n"
        "Salon\n"
        "Buffet\n"
        "Coffee\n"
        "Waterpark"
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 Zookout AI Help\n\n"
        "Type anything like:\n"
        "• Restaurant\n"
        "• Spa\n"
        "• Salon\n"
        "• Hotel\n"
        "• Buffet\n"
        "• Coffee\n"
        "• Waterpark\n\n"
        "I'll find matching Zookout deals for you."
    )


def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))

    # Search all user messages
    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            handle_message,
        )
    )
    app.add_handler(CallbackQueryHandler(handle_callback_query))

    async def unknown_update(update: Update, context: ContextTypes.DEFAULT_TYPE):
        logger.info("Unhandled update: %s", update)
        if update.message and update.message.text:
            await update.message.reply_text(
                "I only respond to text search queries. Please type something like 'Restaurant' or 'Spa'."
            )

    app.add_handler(MessageHandler(~filters.TEXT & filters.ALL, unknown_update))

    async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
        logging.error("Exception while handling update", exc_info=context.error)
        if hasattr(update, "message") and update.message:
            try:
                await update.message.reply_text(
                    "⚠️ Sorry, something went wrong. Please try again."
                )
            except Exception:
                pass

    app.add_error_handler(error_handler)

    if not BOT_TOKEN:
        logger.error("BOT_TOKEN is not configured. Bot cannot start.")
        return

    print("✅ Zookout AI Bot is running...")

    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()