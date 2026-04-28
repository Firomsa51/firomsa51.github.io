"""
Telegram Bot for Hanif Printing Services (Advanced)
- Persistent keyboard + inline‑style service selection
- Collects user description for each service
- Notifies admin with full details
- Oromo language for contact info
"""

import logging
import html
from telegram import (
    Update,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    ConversationHandler,
    filters,
)

# ============================================================
# CONFIGURATION – REPLACE BOT TOKEN WITH A NEW ONE!
# ============================================================
BOT_TOKEN = "8611579366:AAFlOhOEHfobmLdgAgOsuDhZ57hiN5vK1ao"
ADMIN_CHAT_ID = 7594935459
# ============================================================

# Logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# Conversation states
AWAITING_DESCRIPTION = 1

# Buttons (full‑width, persistent)
MAIN_MENU = ReplyKeyboardMarkup(
    [
        ["Banner Design", "Logo Design"],
        ["Website Design", "Video Editing"],
        ["📞 Contact", "ℹ️ Help"],
    ],
    resize_keyboard=False,
    is_persistent=True,
)

VALID_SERVICES = {"Banner Design", "Logo Design", "Website Design", "Video Editing"}


def get_user_link(user) -> str:
    """Returns a clickable Telegram link for the user."""
    if user.username:
        return f"https://t.me/{user.username}"
    return f"tg://user?id={user.id}"


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send welcome message with persistent main menu."""
    user = update.effective_user
    welcome_text = (
        f"Welcome to Hanif Printing Services Bot 👋, {user.first_name}!\n\n"
        "Please choose a service from the menu below.\n\n"
        "📞 *Contact*: +251962444622\n"
        "📍 Addis Ababa, Ethiopia"
    )
    await update.message.reply_text(
        welcome_text,
        reply_markup=MAIN_MENU,
        parse_mode="Markdown",
    )
    logger.info(f"User {user.id} started the bot.")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send help message."""
    help_text = (
        "📌 *How to use this bot:*\n\n"
        "• Tap any button to select a service.\n"
        "• You will be asked to describe your requirements.\n"
        "• After you reply, our admin will be notified and will contact you.\n"
        "• Use /start to show the menu again.\n"
        "• Use /contact for our phone and address (Oromo)."
    )
    await update.message.reply_text(help_text, parse_mode="Markdown", reply_markup=MAIN_MENU)


async def contact(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send contact information in Oromo with a button to call."""
    contact_info = (
        "📞 *Lakkoofsa Bilbilaa:* +251962444622\n"
        "📍 *Teessoo:* Addis Ababa, Ethiopia\n"
        "⏰ *Sa'aatii Hojiitti:* Wiixata – Sanbata, 9:00 – 18:00"
    )
    # Send inline button to call (if client supports it)
    keyboard = [
        [InlineKeyboardButton("📞 Call us", url="tel:+251962444622")]
    ]
    await update.message.reply_text(
        contact_info,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def service_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """User selects a service; ask for description."""
    text = update.message.text
    user = update.effective_user

    if text == "📞 Contact":
        await contact(update, context)
        return ConversationHandler.END

    if text == "ℹ️ Help":
        await help_command(update, context)
        return ConversationHandler.END

    if text not in VALID_SERVICES:
        await update.message.reply_text(
            "❓ Please use the menu buttons to select a valid service.\n"
            "Type /help for assistance.",
            reply_markup=MAIN_MENU,
        )
        return ConversationHandler.END

    # Store selected service
    context.user_data["selected_service"] = text

    # Ask for description
    question = (
        f"📝 *{text} Request*\n\n"
        "Please describe what you need. Include:\n"
        "• Colors, size, text, style\n"
        "• Any reference or idea you have\n\n"
        "Send your description here 👇"
    )
    await update.message.reply_text(question, parse_mode="Markdown")
    return AWAITING_DESCRIPTION


async def receive_description(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """User sends description; notify admin and finish."""
    description = update.message.text
    user = update.effective_user
    service = context.user_data.get("selected_service", "Unknown service")

    # Confirm to user
    await update.message.reply_text(
        f"✅ Thank you! Your request for *{service}* has been received.\n\n"
        "Our team will contact you within 24 hours.\n"
        "Use the menu below to do more:",
        reply_markup=MAIN_MENU,
        parse_mode="Markdown",
    )

    # Prepare admin notification
    username_part = f"@{user.username}" if user.username else "No username"
    user_link = get_user_link(user)
    admin_message = (
        f"🔔 <b>New Service Request</b>\n\n"
        f"👤 <b>Name:</b> {html.escape(user.full_name)}\n"
        f"🔗 <b>Username:</b> {username_part}\n"
        f"🆔 <b>User ID:</b> <code>{user.id}</code>\n"
        f"🛠 <b>Service:</b> {html.escape(service)}\n"
        f"📝 <b>Description:</b>\n<code>{html.escape(description)}</code>\n\n"
        f"📅 <b>Time:</b> {update.message.date}\n"
        f"💬 <b>Message link:</b> {user_link}"
    )

    try:
        await context.bot.send_message(
            chat_id=ADMIN_CHAT_ID,
            text=admin_message,
            parse_mode="HTML",
        )
        logger.info(f"Admin notified for {service} from user {user.id}")
    except Exception as e:
        logger.error(f"Admin notification failed: {e}")
        await update.message.reply_text(
            "⚠️ Your request was saved, but we are having trouble notifying our team. "
            "Please call us directly at +251962444622.",
            reply_markup=MAIN_MENU,
        )

    context.user_data.clear()
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel the conversation."""
    await update.message.reply_text(
        "Operation cancelled. Use the menu or /start to begin again.",
        reply_markup=MAIN_MENU,
    )
    context.user_data.clear()
    return ConversationHandler.END


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log errors and notify user."""
    logger.error(msg="Exception:", exc_info=context.error)
    if update and update.effective_message:
        try:
            await update.effective_message.reply_text(
                "An error occurred. Our team has been alerted. Please try again.\n"
                "Use /start to refresh the menu.",
                reply_markup=MAIN_MENU,
            )
        except:
            pass  # avoid recursion on send error


def main() -> None:
    """Start the bot."""
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Conversation handler for service requests (from text buttons)
    conv_handler = ConversationHandler(
        entry_points=[
            MessageHandler(
                filters.TEXT & ~filters.COMMAND & ~filters.Regex(r"^/"), service_selected
            ),
        ],
        states={
            AWAITING_DESCRIPTION: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND, receive_description
                ),
            ],
        },
        fallbacks=[
            CommandHandler("cancel", cancel),
            CommandHandler("start", start),
        ],
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("contact", contact))
    app.add_handler(conv_handler)
    app.add_error_handler(error_handler)

    logger.info("Hanif Printing Bot is running with advanced menu and admin alerts...")
    app.run_polling()


if __name__ == "__main__":
    main()
