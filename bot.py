"""
Hanif Printing Services Telegram Bot - Advanced Version
Multi-language: English, Oromo, Amharic
Features: Persistent keyboard, inline language selector, detailed service requests
"""

import logging
import html
from datetime import datetime
from typing import Dict, Any, Optional

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
# CONFIGURATION
# ============================================================
BOT_TOKEN = "8611579366:AAFlOhOEHfobmLdgAgOsuDhZ57hiN5vK1ao"
ADMIN_CHAT_ID = 7594935459

# Logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# Conversation states
AWAITING_DESCRIPTION = 1

# ============================================================
# LANGUAGE DATA
# ============================================================
LANGUAGES = {
    "en": "English",
    "om": "Oromo",
    "am": "አማርኛ",
}

TEXTS: Dict[str, Dict[str, str]] = {
    "en": {
        "welcome": "👋 Welcome to <b>Hanif Printing Services</b>!\n\n"
                   "Please select your language first.",
        "start_menu": "Please choose a service:",
        "help": "📌 <b>How to use this bot:</b>\n\n"
                "• Tap any button to select a service\n"
                "• Describe your requirements clearly\n"
                "• Our team will contact you within 24 hours\n\n"
                "Use /start to return to the main menu.",
        "contact_info": "📞 <b>Phone:</b> +251 962 444 622\n"
                        "📍 <b>Address:</b> Harar, Ethiopia\n"
                        "⏰ <b>Working hours:</b> Mon – Sat, 12:00 AM – 12:00 PM",
        "service_question": "📝 <b>{service}</b>\n\n"
                            "Please describe your requirements in detail.\n"
                            "Examples:\n"
                            "• Colors, size, quantity, material\n"
                            "• Text/content, style preferences\n"
                            "• Any reference images or ideas",
        "thanks": "✅ Thank you! Your request for <b>{service}</b> has been received.\n\n"
                  "Our team will contact you shortly (within 24 hours).",
        "invalid": "❓ Please use the buttons below to select a valid service.",
        "cancelled": "Operation cancelled. Use the menu or /start to begin again.",
        "error": "An error occurred. Please try again or contact us directly.",
    },
    "om": {
        "welcome": "👋 Baga nagaan dhuftan <b>Hanif Printing Services</b>!\n\n"
                   "Dura afaan filadhaa.",
        "start_menu": "Seervisa filadhaa:",
        "help": "📌 <b>Akkaataa botii kana itti fayyadamuu qabdu:</b>\n\n"
                "• Seervisa filachuuf button tuqi\n"
                "• Barbaachisaa kee bal’inaan ibsi\n"
                "• Garaa 24 sa’aatiin isin qunnamuu dandeenya",
        "contact_info": "📞 <b>Bilbila:</b> +251 962 444 622\n"
                        "📍 <b>Teessoo:</b> Finfinnee, Itoophiyaa\n"
                        "⏰ <b>Yeroo hojii:</b> Wiixata – Sanbata, 9:00 – 18:00",
        "service_question": "📝 <b>{service}</b>\n\n"
                            "Barbaachisaa kee bal’inaan ibsi.\n"
                            "Fakkeenya:\n"
                            "• Kolora, hammamtaa, baay’ina, meeshaa\n"
                            "• Barruu, akkataa barbaaddu",
        "thanks": "✅ Galatoomi! Gaaffiin kee <b>{service}</b> fudhatameera.\n\n"
                  "Gareen keenya yeroo gabaabaa keessatti isin qunnama.",
        "invalid": "❓ Seervisa sirrii ta’e filachuuf button garaa gadii fayyadami.",
        "cancelled": "Hojiin dhaabbateera. Menu ykn /start fayyadami.",
        "error": "Dogoggorri uumameera. Mee irra deebi’ii yaali ykn bilbilii.",
    },
    "am": {
        "welcome": "👋 እንኳን ደህና መጡ <b>ሃኒፍ ማተሚያ አገልግሎት</b>!\n\n"
                   "መጀመሪያ ቋንቋ ይምረጡ።",
        "start_menu": "አገልግሎት ይምረጡ፡",
        "help": "📌 <b>ይህን ቦት እንዴት እንጠቀማለን፡</b>\n\n"
                "• አገልግሎት ለመምረጥ ቁልፍ ተጫን\n"
                "• ፍላጎትህን በዝርዝር ግለጽ\n"
                "• ቡድናችን በ24 ሰዓት ውስጥ ያገናኝሃል",
        "contact_info": "📞 <b>ስልክ:</b> +251 962 444 622\n"
                        "📍 <b>አድራሻ:</b> አዲስ አበባ፣ ኢትዮጵያ\n"
                        "⏰ <b>የስራ ሰዓት:</b> ሰኞ – ቅዳሜ፣ 9:00 – 18:00",
        "service_question": "📝 <b>{service}</b>\n\n"
                            "የሚፈልጉትን በዝርዝር ይግለጹ።\n"
                            "ለምሳሌ፡\n"
                            "• ቀለም፣ መጠን፣ ብዛት፣ ቁሳቁስ\n"
                            "• ጽሑፍ፣ ዲዛይን ዘይቤ",
        "thanks": "✅ እናመሰግናለን! ለ<b>{service}</b> ጥያቄዎ ተቀብለናል።\n\n"
                  "ቡድናችን በቅርቡ (24 ሰዓት ውስጥ) ያገናኝዎታል።",
        "invalid": "❓ እባክዎ ከታች ባሉት ቁልፎች ትክክለኛ አገልግሎት ይምረጡ።",
        "cancelled": "ስራው ተሰርዟል። ሜኑ ወይም /start ተጠቀሙ።",
        "error": "ስህተት ተከስቷል። እባክዎ እንደገና ይሞክሩ ወይም ቀጥታ ይደውሉ።",
    },
}

VALID_SERVICES = {
    "en": ["Banner Design", "Logo Design", "Website Design", "Video Editing"],
    "om": ["Banner Design", "Logo Design", "Website Design", "Video Editing"],
    "am": ["ቤንር ዲዛይን", "ሎጎ ዲዛይን", "ድር ጣቢያ ዲዛይን", "ቪዲዮ ኤዲቲንግ"],  # Improved translation
}

SERVICE_TRANSLATION = {
    "ቤንር ዲዛይን": "Banner Design",
    "ሎጎ ዲዛይን": "Logo Design",
    "ድር ጣቢያ ዲዛይን": "Website Design",
    "ቪዲዮ ኤዲቲንግ": "Video Editing",
}


def get_lang(context: ContextTypes.DEFAULT_TYPE) -> str:
    return context.user_data.get("lang", "en")


def _(key: str, lang: str) -> str:
    """Safe text getter with fallback"""
    return TEXTS.get(lang, TEXTS["en"]).get(key, TEXTS["en"].get(key, key))


# ============================================================
# KEYBOARDS
# ============================================================
def get_main_menu(lang: str) -> ReplyKeyboardMarkup:
    services = VALID_SERVICES.get(lang, VALID_SERVICES["en"])

    if lang == "am":
        keyboard = [
            [services[0], services[1]],
            [services[2], services[3]],
            ["📞 ስልክ", "ℹ️ እርዳታ"],
        ]
    else:
        keyboard = [
            [services[0], services[1]],
            [services[2], services[3]],
            ["📞 Contact", "ℹ️ Help"],
        ]

    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, is_persistent=True)


def get_language_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton("🇬🇧 English", callback_data="lang:en")],
        [InlineKeyboardButton("🇪🇹 Oromo", callback_data="lang:om")],
        [InlineKeyboardButton("🇪🇹 አማርኛ", callback_data="lang:am")],
    ]
    return InlineKeyboardMarkup(keyboard)


# ============================================================
# HANDLERS
# ============================================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    lang = get_lang(context)

    if "lang" not in context.user_data:
        await update.message.reply_text(
            TEXTS["en"]["welcome"],
            parse_mode="HTML",
            reply_markup=get_language_keyboard(),
        )
        return

    await update.message.reply_text(
        _("start_menu", lang),
        reply_markup=get_main_menu(lang),
    )
    logger.info(f"User {user.id} started bot (lang={lang})")


async def choose_language(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    lang_code = query.data.split(":")[1]
    context.user_data["lang"] = lang_code
    lang = lang_code

    await query.edit_message_text(
        text=_( "welcome", lang) if lang != "en" else TEXTS["en"]["welcome"],
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


async def service_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text.strip()
    user = update.effective_user
    lang = get_lang(context)

    # Handle special buttons
    if text in ["📞 Contact", "📞 ስልክ"]:
        await contact_command(update, context)
        return ConversationHandler.END

    if text in ["ℹ️ Help", "ℹ️ እርዳታ"]:
        await help_command(update, context)
        return ConversationHandler.END

    valid_services = VALID_SERVICES.get(lang, VALID_SERVICES["en"])
    if text not in valid_services:
        await update.message.reply_text(
            _("invalid", lang),
            reply_markup=get_main_menu(lang),
        )
        return ConversationHandler.END

    context.user_data["selected_service"] = text

    # Translate service name to English for admin
    service_eng = SERVICE_TRANSLATION.get(text, text)

    question = _("service_question", lang).format(service=text)
    await update.message.reply_text(question, parse_mode="HTML")

    return AWAITING_DESCRIPTION


async def receive_description(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    description = update.message.text
    user = update.effective_user
    lang = get_lang(context)
    service = context.user_data.get("selected_service", "Unknown Service")
    service_eng = SERVICE_TRANSLATION.get(service, service)

    # Thank user
    await update.message.reply_text(
        _("thanks", lang).format(service=service),
        parse_mode="HTML",
        reply_markup=get_main_menu(lang),
    )

    # Notify admin
    user_link = f"https://t.me/{user.username}" if user.username else f"tg://user?id={user.id}"

    admin_message = (
        f"🔔 <b>New Service Request</b>\n\n"
        f"👤 <b>Name:</b> {html.escape(user.full_name)}\n"
        f"🔗 <b>Username:</b> @{user.username or 'N/A'}\n"
        f"🆔 <b>User ID:</b> <code>{user.id}</code>\n"
        f"🌍 <b>Language:</b> {LANGUAGES.get(lang, lang)}\n"
        f"🛠 <b>Service:</b> {html.escape(service_eng)}\n"
        f"📝 <b>Description:</b>\n"
        f"<code>{html.escape(description)}</code>\n\n"
        f"⏰ <b>Time:</b> {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}\n"
        f"💬 <b>Link:</b> {user_link}"
    )

    try:
        await context.bot.send_message(
            chat_id=ADMIN_CHAT_ID,
            text=admin_message,
            parse_mode="HTML",
        )

        # Optional: Send user profile photo
        photos = await user.get_profile_photos(limit=1)
        if photos and photos.photos:
            await context.bot.send_photo(
                chat_id=ADMIN_CHAT_ID,
                photo=photos.photos[0][-1].file_id,
                caption=f"Profile photo of {user.full_name}",
            )
    except Exception as e:
        logger.error(f"Failed to notify admin: {e}")
        await update.message.reply_text(
            "⚠️ Request received, but we couldn't notify the team properly. "
            "Please call +251962444622 directly.",
            reply_markup=get_main_menu(lang),
        )

    context.user_data.clear()
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    lang = get_lang(context)
    await update.message.reply_text(
        _("cancelled", lang),
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
        except:
            pass


# ============================================================
# MAIN
# ============================================================
def main() -> None:
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[
            MessageHandler(
                filters.TEXT & \~filters.COMMAND,
                service_selected,
            ),
        ],
        states={
            AWAITING_DESCRIPTION: [
                MessageHandler(
                    filters.TEXT & \~filters.COMMAND,
                    receive_description,
                ),
            ],
        },
        fallbacks=[
            CommandHandler("cancel", cancel),
            CommandHandler("start", start),
        ],
        allow_reentry=True,
    )

    # Add handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("contact", contact_command))
    app.add_handler(conv_handler)
    app.add_handler(CallbackQueryHandler(choose_language, pattern=r"^lang:"))
    app.add_error_handler(error_handler)

    logger.info("🚀 Hanif Printing Services Bot is running (Advanced Version)...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
