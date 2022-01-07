#!/usr/bin/env python3

from telegram import (
    Bot,
    Update,
    ForceReply,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
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
import os
from dotenv import load_dotenv
import requests as re
from better_profanity import profanity

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

logger = logging.getLogger(__name__)

reply_keyboard = [
    ["Spelling Hornets"],
    ["Profanity Alert"],
    ["Meme Generator"],
    ["End"],
]

markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)

INFO_STATE = 1

load_dotenv("./.env")
TOKEN = os.getenv("token")
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

Welcome to the *All In One*, _State of the art_ mistake and profanity identifier\.

To get started, type /help""",
    )

def vulgarity_check(update:Update, context:CallbackContext):
    profanity.load_censor_words()
    if profanity.contains_profanity(update.message.text) == True:
        update.message.reply_text("What a vulgar dude.")


def help(update: Update, context: CallbackContext):
    update.message.reply_markdown_v2(
        fr"""To see more *information*, type /info

To *toggle the settings*, type /settings
    """
    )


def info(update: Update, context: CallbackContext):
    update.message.reply_markdown_v2(
        "Select one of these options:", reply_markup=markup
    )
    return INFO_STATE


def info_reply(update: Update, context: CallbackContext):
    msg = update.message.text
    logger.info(msg)

    if msg == "Spelling Hornets":
        update.message.reply_markdown_v2(
            """*Spelling Hornets* is our best attempt to shame those who constantly makes spelling mistakes\.

We keep track of users' mistakes and constantly remind the entire group of your mistakes so that people can *laugh behind your backs*\.

We also generate a wordcloud and present them to everyone in a nice fancy manner to showcase the groups' mistakes in totality\.

Sponsored by the _type good English movement 2022_
"""
        )

    elif msg == "Profanity Alert":
        update.message.reply_markdown_v2(
            """*Profanity Alert* constantly reminds you of your vulgur nature in chats\.

We keep track of how long a group can last to maintain their purity before they start using profanities\.

Do not try to cheat the system, we have good ~if\-else statements~ advanced _AI_ to identify them to a high accuracy\.
"""
        )

    elif msg == "Meme Generator":
        update.message.reply_markdown_v2(
            """*Meme Generator* amplifies the fun by allowing anyone to create memes on the go\.

We also allow users to create memes of a pre\-defined template which links to their spelling errors\.
"""
        )

    elif msg == "End":
        update.message.reply_text(
            "Hope you gained some new knowledge!", reply_markup=ReplyKeyboardRemove()
        )
        return ConversationHandler.END

    else:
        update.message.reply_text("I don't understand you...")
    return INFO_STATE


def settings(update: Update, context: CallbackContext):
    pass


def cancel(update: Update, context: CallbackContext) -> int:
    """Cancels and ends the conversation."""
    user = update.message.from_user
    logger.info("User %s canceled the conversation.", user.first_name)
    update.message.reply_text(
        "Hope you learnt more about our services.", reply_markup=ReplyKeyboardRemove()
    )

    return ConversationHandler.END


def main():
    updater = Updater(TOKEN, use_context=True)

    # Get dispatcher to register handlers
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))

    info_handler = ConversationHandler(
        entry_points=[CommandHandler("info", info)],
        states={
            1: [MessageHandler(Filters.text, info_reply)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    dp.add_handler(info_handler)
    dp.add_handler(CommandHandler("help", help))
    dp.add_handler(CommandHandler("settings", settings))
    dp.add_handler(MessageHandler(Filters.text, vulgarity_check))

    unknown_handler = MessageHandler(Filters.command, unknown)
    dp.add_handler(unknown_handler)

    updater.start_polling()
    updater.idle()


if __name__ == "__main__":
    main()
