#!/usr/bin/env python3
"""
Hanif Printing Services Telegram Bot - Advanced & Improved
Multi-language: English, Oromo, Amharic
Features: Persistent keyboard, inline language selector, file attachments, admin notifications
"""

import logging
import html
from datetime import datetime
from typing import Dict, Optional, Tuple

from telegram import (
    Update,
    ReplyKeyboardMarkup,
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
# CONFIGURATION (YOUR TOKEN & ADMIN ID)
# ============================================================
BOT_TOKEN = "8611579366:AAFlOhOEHfobmLdgAgOsuDhZ57hiN5vK1ao"
ADMIN_CHAT_ID = 7594935459

# Conversation states
AWAITING_DESCRIPTION = 1

# Timeout for conversation (seconds) – 10 minutes
CONVERSATION_TIMEOUT = 600

# Logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# ============================================================
# CONSTANTS & LANGUAGE DATA
# ============================================================
KEY_SELECTED_SERVICE = "selected_service"
KEY_LANG = "lang"

LANGUAGES = {
    "en": "English",
    "om": "Oromo",
    "am": "አማርኛ",
}

# Fully translated service names for each language
SERVICES = {
    "en": ["Banner Design", "Logo Design", "Website Design", "Video Editing"],
    "om": ["Banner Design (Afaan Oromo)", "Logo Design (Afaan Oromo)", "Website Design (Afaan Oromo)", "Video Editing (Afaan Oromo)"],
    "am": ["ቤንር ዲዛይን", "ሎጎ ዲዛይን", "ድር ጣቢያ ዲዛይን", "ቪዲዮ ኤዲቲንግ"],
}

# Map any service name back to English (for admin)
SERVICE_TO_ENGLISH = {
    # Amharic -> English
    "ቤንር ዲዛይን": "Banner Design",
    "ሎጎ ዲዛይን": "Logo Design",
    "ድር ጣቢያ ዲዛይን": "Website Design",
    "ቪዲዮ ኤዲቲንግ": "Video Editing",
    # Oromo (simple mapping)
    "Banner Design (Afaan Oromo)": "Banner Design",
    "Logo Design (Afaan Oromo)": "Logo Design",
    "Website Design (Afaan Oromo)": "Website Design",
    "Video Editing (Afaan Oromo)": "Video Editing",
    # English itself
    "Banner Design": "Banner Design",
    "Logo Design": "Logo Design",
    "Website Design": "Website Design",
    "Video Editing": "Video Editing",
}

TEXTS: Dict[str, Dict[str, str]] = {
    "en": {
        "welcome": "👋 Welcome to <b>Hanif Printing Services</b>!\n\n"
                   "Please select your language first.",
        "start_menu": "Please choose a service:",
        "help": "📌 <b>How to use this bot:</b>\n\n"
                "• Tap any button to select a service\n"
                "• Describe your requirements (text or send images/PDFs)\n"
                "• Our team will contact you within 24 hours\n\n"
                "Use /start to return to the main menu.",
        "contact_info": "📞 <b>Phone:</b> +251 962 444 622\n"
                        "📍 <b>Address:</b> Addis Ababa, Ethiopia\n"
                        "⏰ <b>Working hours:</b> Mon – Sat, 9:00 AM – 6:00 PM",
        "service_question": "📝 <b>{service}</b>\n\n"
                            "Please describe your requirements in detail.\n"
                            "You can also send images or PDF files.\n\n"
                            "Examples:\n"
                            "• Colors, size, quantity, material\n"
                            "• Text/content, style preferences\n"
                            "• Any reference images or ideas\n\n"
                            "🔴 To cancel, send /cancel or press the Cancel button below.",
        "thanks": "✅ Thank you! Your request for <b>{service}</b> has been received.\n\n"
                  "Our team will contact you shortly (within 24 hours).",
        "invalid": "❓ Please use the buttons below to select a valid service.",
        "cancelled": "Operation cancelled. Use the menu or /start to begin again.",
        "error": "An error occurred. Please try again or contact us directly.",
        "cancel_button": "❌ Cancel",
    },
    "om": {
        "welcome": "👋 Baga nagaan dhuftan <b>Hanif Printing Services</b>!\n\n"
                   "Dura afaan filadhaa.",
        "start_menu": "Seervisa filadhaa:",
        "help": "📌 <b>Akkaataa botii kana itti fayyadamuu qabdu:</b>\n\n"
                "• Seervisa filachuuf button tuqi\n"
                "• Barbaachisaa kee ibsi (barruu ykn fayloota ergi)\n"
                "• Garaa 24 sa'aatiin isin qunnamuu dandeenya",
        "contact_info": "📞 <b>Bilbila:</b> +251 962 444 622\n"
                        "📍 <b>Teessoo:</b> Finfinnee, Itoophiyaa\n"
                        "⏰ <b>Yeroo hojii:</b> Wiixata – Sanbata, 9:00 – 18:00",
        "service_question": "📝 <b>{service}</b>\n\n"
                            "Barbaachisaa kee bal'inaan ibsi.\n"
                            "Fayloota (sawiir ykn PDF) erguu ni dandeessu.\n\n"
                            "Fakkeenya:\n"
                            "• Kolora, hammamtaa, baay'ina, meeshaa\n"
                            "• Barruu, akkataa barbaaddu\n\n"
                            "🔴 Dhaabuuf /cancel ykn cancel button tuqi.",
        "thanks": "✅ Galatoomi! Gaaffiin kee <b>{service}</b> fudhatameera.\n\n"
                  "Gareen keenya yeroo gabaabaa keessatti isin qunnama.",
        "invalid": "❓ Seervisa sirrii ta'e filachuuf button jalaa fayyadami.",
        "cancelled": "Hojiin dhaabbateera. Menu ykn /start fayyadami.",
        "error": "Dogoggorri uumameera. Mee irra deebi'ii yaali ykn bilbilii.",
        "cancel_button": "❌ Dhaabi",
    },
    "am": {
        "welcome": "👋 እንኳን ደህና መጡ <b>ሃኒፍ ማተሚያ አገልግሎት</b>!\n\n"
                   "መጀመሪያ ቋንቋ ይምረጡ።",
        "start_menu": "አገልግሎት ይምረጡ፡",
        "help": "📌 <b>ይህን ቦት እንዴት እንጠቀማለን፡</b>\n\n"
                "• አገልግሎት ለመምረጥ ቁልፍ ተጫን\n"
                "• ፍላጎትህን በዝርዝር ግለጽ (ጽሑፍ ወይም ምስል/ፒዲኤፍ)\n"
                "• ቡድናችን በ24 ሰዓት ውስጥ ያገናኝሃል",
        "contact_info": "📞 <b>ስልክ:</b> +251 962 444 622\n"
                        "📍 <b>አድራሻ:</b> አዲስ አበባ፣ ኢትዮጵያ\n"
                        "⏰ <b>የስራ ሰዓት:</b> ሰኞ – ቅዳሜ፣ 9:00 – 18:00",
        "service_question": "📝 <b>{service}</b>\n\n"
                            "የሚፈልጉትን በዝርዝር ይግለጹ።\n"
                            "ምስሎችን ወይም ፒዲኤፍ መላክ ይችላሉ።\n\n"
                            "ለምሳሌ፡\n"
                            "• ቀለም፣ መጠን፣ ብዛት፣ ቁሳቁስ\n"
                            "• ጽሑፍ፣ ዲዛይን ዘይቤ\n\n"
                            "🔴 ለመሰረዝ /cancel ወይም የስረዛ ቁልፍ ይጫኑ።",
        "thanks": "✅ እናመሰግናለን! ለ<b>{service}</b> ጥያቄዎ ተቀብለናል።\n\n"
                  "ቡድናችን በቅርቡ (24 ሰዓት ውስጥ) ያገናኝዎታል።",
        "invalid": "❓ እባክዎ ከታች ባሉት ቁልፎች ትክክለኛ አገልግሎት ይምረጡ።",
        "cancelled": "ስራው ተሰርዟል። ሜኑ ወይም /start ተጠቀሙ።",
        "error": "ስህተት ተከስቷል። እባክዎ እንደገና ይሞክሩ ወይም ቀጥታ ይደውሉ።",
        "cancel_button": "❌ ሰርዝ",
    },
}


def get_lang(context: ContextTypes.DEFAULT_TYPE) -> str:
    return context.user_data.get(KEY_LANG, "en")


def _(key: str, lang: str) -> str:
    """Safe text getter with fallback to English."""
    return TEXTS.get(lang, TEXTS["en"]).get(key, TEXTS["en"].get(key, key))


# ============================================================
# KEYBOARDS
# ============================================================
def get_main_menu(lang: str) -> ReplyKeyboardMarkup:
    services = SERVICES.get(lang, SERVICES["en"])
    cancel_text = _("cancel_button", lang)

    if lang == "am":
        keyboard = [
            [services[0], services[1]],
            [services[2], services[3]],
            ["📞 ስልክ", "ℹ️ እርዳታ", cancel_text],
        ]
    else:
        keyboard = [
            [services[0], services[1]],
            [services[2], services[3]],
            ["📞 Contact", "ℹ️ Help", cancel_text],
        ]

    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, is_persistent=True)


def get_language_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton("🇬🇧 English", callback_data="lang:en")],
        [InlineKeyboardButton("🇪🇹 Oromo", callback_data="lang:om")],
        [InlineKeyboardButton("🇪🇹 አማርኛ", callback_data="lang:am")],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_cancel_keyboard(lang: str) -> ReplyKeyboardMarkup:
    """Keyboard shown during description input with only a cancel button."""
    cancel_text = _("cancel_button", lang)
    return ReplyKeyboardMarkup([[cancel_text]], resize_keyboard=True, one_time_keyboard=True)


# ============================================================
# HELPER FUNCTIONS
# ============================================================
async def notify_admin(
    context: ContextTypes.DEFAULT_TYPE,
    user,
    service_name: str,
    description: str,
    file_info: Optional[Tuple[str, str]] = None,
) -> None:
    """Send detailed service request to admin, optionally with a file."""
    lang_code = get_lang(context)
    lang_display = LANGUAGES.get(lang_code, lang_code)

    user_link = f"https://t.me/{user.username}" if user.username else f"tg://user?id={user.id}"
    service_eng = SERVICE_TO_ENGLISH.get(service_name, service_name)

    admin_message = (
        f"🔔 <b>New Service Request</b>\n\n"
        f"👤 <b>Name:</b> {html.escape(user.full_name)}\n"
        f"🔗 <b>Username:</b> @{user.username or 'N/A'}\n"
        f"🆔 <b>User ID:</b> <code>{user.id}</code>\n"
        f"🌍 <b>Language:</b> {lang_display}\n"
        f"🛠 <b>Service:</b> {html.escape(service_eng)}\n"
        f"📝 <b>Description:</b>\n"
        f"<code>{html.escape(description)}</code>\n\n"
        f"⏰ <b>Time:</b> {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}\n"
        f"💬 <b>Link:</b> {user_link}"
    )

    try:
        if file_info:
            file_type, file_id = file_info
            if file_type == "photo":
                await context.bot.send_photo(
                    chat_id=ADMIN_CHAT_ID,
                    photo=file_id,
                    caption=admin_message,
                    parse_mode="HTML",
                )
            elif file_type == "document":
                await context.bot.send_document(
                    chat_id=ADMIN_CHAT_ID,
                    document=file_id,
                    caption=admin_message,
                    parse_mode="HTML",
                )
        else:
            await context.bot.send_message(
                chat_id=ADMIN_CHAT_ID,
                text=admin_message,
                parse_mode="HTML",
            )

        # Send user profile picture if available
        photos = await user.get_profile_photos(limit=1)
        if photos and photos.photos:
            await context.bot.send_photo(
                chat_id=ADMIN_CHAT_ID,
                photo=photos.photos[0][-1].file_id,
                caption=f"Profile photo of {user.full_name}",
            )
    except Exception as e:
        logger.error(f"Failed to notify admin: {e}")
        raise


# ============================================================
# HANDLERS
# ============================================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Start command – clears any existing conversation and asks for language."""
    # Clear any stale conversation data
    context.user_data.clear()

    effective_message = update.effective_message
    if not effective_message:
        return

    # If language not chosen yet, show language selector
    if KEY_LANG not in context.user_data:
        await effective_message.reply_text(
            TEXTS["en"]["welcome"],
            parse_mode="HTML",
            reply_markup=get_language_keyboard(),
        )
        return

    lang = get_lang(context)
    await effective_message.reply_text(
        _("start_menu", lang),
        reply_markup=get_main_menu(lang),
    )
    logger.info(f"User {update.effective_user.id} opened start (lang={lang})")


async def choose_language(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Inline keyboard callback to set language."""
    query = update.callback_query
    await query.answer()

    lang_code = query.data.split(":")[1]
    context.user_data[KEY_LANG] = lang_code
    lang = lang_code

    await query.edit_message_text(
        text=_("welcome", lang),
        parse_mode="HTML",
        reply_markup=None,
    )

    await query.message.reply_text(
        _("start_menu", lang),
        reply_markup=get_main_menu(lang),
    )
    logger.info(f"User {update.effective_user.id} selected language: {lang}")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    lang = get_lang(context)
    await update.message.reply_text(
        _("help", lang),
        parse_mode="HTML",
        reply_markup=get_main_menu(lang),
    )


async def contact_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    lang = get_lang(context)
    await update.message.reply_text(
        _("contact_info", lang),
        parse_mode="HTML",
        reply_markup=get_main_menu(lang),
    )


async def handle_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel the current conversation and return to main menu."""
    lang = get_lang(context)
    await update.message.reply_text(
        _("cancelled", lang),
        reply_markup=get_main_menu(lang),
    )
    context.user_data.clear()
    return ConversationHandler.END


async def service_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Entry point: user picks a service (or special button)."""
    text = update.message.text.strip()
    lang = get_lang(context)
    cancel_text = _("cancel_button", lang)

    # Handle cancel button (if shown on main menu)
    if text == cancel_text:
        return await handle_cancel(update, context)

    # Handle special "Contact" and "Help"
    if text in ["📞 Contact", "📞 ስልክ"]:
        await contact_command(update, context)
        return ConversationHandler.END

    if text in ["ℹ️ Help", "ℹ️ እርዳታ"]:
        await help_command(update, context)
        return ConversationHandler.END

    valid_services = SERVICES.get(lang, SERVICES["en"])
    if text not in valid_services:
        await update.message.reply_text(
            _("invalid", lang),
            reply_markup=get_main_menu(lang),
        )
        return ConversationHandler.END

    # Store selected service
    context.user_data[KEY_SELECTED_SERVICE] = text

    question = _("service_question", lang).format(service=text)
    await update.message.reply_text(
        question,
        parse_mode="HTML",
        reply_markup=get_cancel_keyboard(lang),
    )
    return AWAITING_DESCRIPTION


async def receive_description(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    """Handle user's description (text, photo, or document)."""
    user = update.effective_user
    lang = get_lang(context)
    service = context.user_data.get(KEY_SELECTED_SERVICE, "Unknown Service")
    cancel_text = _("cancel_button", lang)

    # Check if user wants to cancel
    if update.message.text and update.message.text.strip() == cancel_text:
        return await handle_cancel(update, context)

    # Extract description text and optional file
    description = ""
    file_info = None

    if update.message.text:
        description = update.message.text.strip()
    elif update.message.photo:
        description = update.message.caption or "(No description provided)"
        file_info = ("photo", update.message.photo[-1].file_id)
    elif update.message.document:
        description = update.message.caption or "(No description provided)"
        file_info = ("document", update.message.document.file_id)
    else:
        await update.message.reply_text(
            _("error", lang),
            reply_markup=get_main_menu(lang),
        )
        return ConversationHandler.END

    if not description and not file_info:
        await update.message.reply_text(
            "Please provide a description or attach a file.",
            reply_markup=get_cancel_keyboard(lang),
        )
        return AWAITING_DESCRIPTION

    # Thank the user
    thanks_text = _("thanks", lang).format(service=service)
    await update.message.reply_text(
        thanks_text,
        parse_mode="HTML",
        reply_markup=get_main_menu(lang),
    )

    # Notify admin (with optional file)
    try:
        await notify_admin(context, user, service, description, file_info)
    except Exception as e:
        logger.error(f"Admin notification failed: {e}")
        await update.message.reply_text(
            "⚠️ Request received, but we had trouble notifying the team. "
            "Please call +251962444622 directly.",
            reply_markup=get_main_menu(lang),
        )

    context.user_data.clear()
    return ConversationHandler.END


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error("Exception while handling an update:", exc_info=context.error)
    if update and update.effective_message:
        lang = get_lang(context)
        try:
            await update.effective_message.reply_text(
                _("error", lang),
                reply_markup=get_main_menu(lang),
            )
        except Exception:
            pass


# ============================================================
# MAIN
# ============================================================
def main() -> None:
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[
            MessageHandler(
                filters.TEXT & ~filters.COMMAND,
                service_selected,
            ),
        ],
        states={
            AWAITING_DESCRIPTION: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    receive_description,
                ),
                MessageHandler(
                    filters.PHOTO | filters.DOCUMENT,
                    receive_description,
                ),
            ],
        },
        fallbacks=[
            CommandHandler("cancel", handle_cancel),
            CommandHandler("start", start),
            MessageHandler(filters.Regex("^(❌ Cancel|❌ Dhaabi|❌ ሰርዝ)$"), handle_cancel),
        ],
        allow_reentry=True,
        conversation_timeout=CONVERSATION_TIMEOUT,
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("contact", contact_command))
    app.add_handler(conv_handler)
    app.add_handler(CallbackQueryHandler(choose_language, pattern=r"^lang:"))
    app.add_error_handler(error_handler)

    logger.info("🚀 Hanif Printing Services Bot is running (Improved Version)...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
