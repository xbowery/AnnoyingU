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

from dotenv import load_dotenv
import os

load_dotenv()

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

logger = logging.getLogger(__name__)

TOKEN = os.environ.get("TOKEN")
bot = Bot(TOKEN)

fake_db = {"Spelling Hornets": True, "Profanity Alert": True}

reply_info_keyboard = [
    ["Spelling Hornets"],
    ["Profanity Alert"],
    ["Meme Generator"],
    ["End"],
]

reply_settings_keyboard = [["Spelling Hornets"], ["Profanity Alert"], ["End"]]

boolean_keyboard = [["On"], ["Off"], ["Cancel"]]

markup_info = ReplyKeyboardMarkup(reply_info_keyboard, one_time_keyboard=True)
markup_settings = ReplyKeyboardMarkup(reply_settings_keyboard, one_time_keyboard=True)
markup_boolean = ReplyKeyboardMarkup(boolean_keyboard, one_time_keyboard=True)

START_STATE, BOOL_STATE = range(2)


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


def help(update: Update, context: CallbackContext):
    update.message.reply_markdown_v2(
        fr"""To see more *information*, type /info

To *toggle the settings*, type /settings
    """
    )


def info(update: Update, context: CallbackContext):
    update.message.reply_markdown_v2(
        "Select one of these options:", reply_markup=markup_info
    )
    return START_STATE


def info_reply(update: Update, context: CallbackContext):
    msg = update.message.text

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
    return START_STATE


def settings(update: Update, context: CallbackContext):
    update.message.reply_text(
        "Choose which settings you would like to edit:", reply_markup=markup_settings
    )

    return START_STATE


def settings_reply(update: Update, context: CallbackContext):
    msg = update.message.text
    logger.info(msg)
    if msg in fake_db:
        update.message.reply_text(
            f"Settings for {msg}: {'ON' if fake_db[msg] else 'OFF'}.\nSelect the new settings:",
            reply_markup=markup_boolean,
        )
        context.chat_data["Settings_Option"] = msg
        return BOOL_STATE

    if msg == "End":
        update.message.reply_text("Bye", reply_markup=ReplyKeyboardRemove())
        return ConversationHandler.END

    update.message.reply_text(
        f"Sorry, such settings does not exist", reply_markup=markup_settings
    )
    return START_STATE


def change_settings(update: Update, context: CallbackContext):
    msg = update.message.text
    opt = context.chat_data["Settings_Option"]

    if msg not in ["On", "Off", "Back"]:
        update.message.reply_text(
            "Sorry. This is not a valid option", reply_markup=markup_settings
        )
        return START_STATE
    elif msg == "Back":
        update.message.reply_text(reply_markup=markup_settings)
        return START_STATE
    else:
        fake_db[opt] = True if msg == "On" else False

    update.message.reply_text(
        f"Settings for {opt}: {'ON' if fake_db[opt] else 'OFF'}",
        reply_markup=ReplyKeyboardRemove(),
    )
    return ConversationHandler.END


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
            START_STATE: [MessageHandler(Filters.text, info_reply)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    settings_handler = ConversationHandler(
        entry_points=[CommandHandler("settings", settings)],
        states={
            START_STATE: [MessageHandler(Filters.text, settings_reply)],
            BOOL_STATE: [MessageHandler(Filters.text, change_settings)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    dp.add_handler(CommandHandler("help", help))
    dp.add_handler(info_handler)
    dp.add_handler(settings_handler)

    unknown_handler = MessageHandler(Filters.command, unknown)
    dp.add_handler(unknown_handler)

    updater.start_polling()
    updater.idle()


if __name__ == "__main__":
    main()
