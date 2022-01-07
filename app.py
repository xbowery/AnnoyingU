#!/usr/bin/env python3

from telegram import (
    Bot,
    Update,
    ForceReply,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineQueryResultArticle,
    InputTextMessageContent,
)
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    ConversationHandler,
    CallbackContext,
    CallbackQueryHandler,
    InlineQueryHandler,
)
import logging
from db import settings

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

logger = logging.getLogger(__name__)

TOKEN = "5080624320:AAEEOUrjnItiTv-F_7VgsosKJbSi_cK13Nc"  # change
bot = Bot(TOKEN)


def unknown(update: Update, context: CallbackContext):
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Sorry, I didn't understand that command.",
    )


def start(update: Update, context: CallbackContext) -> None:
    user = update.effective_user
    update.message.reply_markdown_v2(
        fr"""Hi {user.mention_markdown_v2()}\!

Welcome to the **All In One**, *State of the art* mistake and profanity identifier\.

To get started, type /help""",
    )


def help(update: Update, context: CallbackContext):
    update.message.reply_markdown_v2(
        fr"""To see more **information** about our various services, type /info
To **toggle the settings**, type /settings
    """
    )


def info(update: Update, context: CallbackContext):
    pass


def settings(update: Update, context: CallbackContext):
    pass


def main():
    updater = Updater(TOKEN, use_context=True)

    # Get dispatcher to register handlers
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help))
    dp.add_handler(CommandHandler("info", info))
    dp.add_handler(CommandHandler("settings", settings))

    unknown_handler = MessageHandler(Filters.command, unknown)
    dp.add_handler(unknown_handler)

    updater.start_polling()
    updater.idle()


if __name__ == "__main__":
    main()
