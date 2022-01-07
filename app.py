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
    chat,
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
import os
import random

from dotenv import load_dotenv
import requests as re
from better_profanity import profanity
from pymongo import MongoClient

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

logger = logging.getLogger(__name__)

ACCEPTABLE_SETTINGS = ["Spelling Hornets", "Profanity Alert"]

top_text = {}
bottom_text = {}

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

load_dotenv("./.env")
TOKEN = os.getenv("token")
USERNAME = os.getenv("username")
PASSWORD = os.getenv("password")
MONGOURL = os.getenv("mongourl")
bot = Bot(TOKEN)

client = MongoClient(MONGOURL)
db = client.annoyme

PROFANITY_USERDB = db["profanity_user"]
PROFANITY_TIMEDB = db["profanity_time"]
SPELLING_ERRORDB = db["spelling"]
SETTINGSDB = db["user_settings"]

# https://pymongo.readthedocs.io/en/stable/tutorial.html
# PROFANITY_USERDB.insert_one({"test": 123})
# PROFANITY_USERDB.findOne({})


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


def vulgarity_check(update: Update, context: CallbackContext):
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

    if chat_settings := SETTINGSDB.find_one({"chatid": update.message.chat_id}):
        pass
    else:
        chat_settings = {
            "chatid": update.message.chat_id,
            "Spelling Hornets": True,
            "Profanity Alert": True,
        }

    context.chat_data["chat_settings"] = chat_settings

    if msg in ACCEPTABLE_SETTINGS:
        update.message.reply_text(
            f"Settings for {msg}: {'ON' if chat_settings[msg] else 'OFF'}.\nSelect the new settings:",
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
    chat_settings = context.chat_data["chat_settings"]

    logger.info(chat_settings)

    if msg not in ["On", "Off", "Cancel"]:
        update.message.reply_text(
            "Sorry. This is not a valid option", reply_markup=markup_settings
        )
        return_state = START_STATE
    elif msg == "Cancel":
        update.message.reply_text(
            "Select the settings to edit:", reply_markup=markup_settings
        )
        return_state = START_STATE
    else:
        chat_settings[opt] = True if msg == "On" else False
        return_state = ConversationHandler.END

        update.message.reply_text(
            f"Settings for {opt}: {'ON' if chat_settings[opt] else 'OFF'}",
            reply_markup=ReplyKeyboardRemove(),
        )

    update_obj = {"$set": chat_settings}

    SETTINGSDB.update_one({"chatid": chat_settings["chatid"]}, update_obj, upsert=True)
    return return_state


def meme_generator(update: Update, context: CallbackContext):
    update.message.reply_text("Please enter the text for the top line:")

    return START_STATE


def message_filter(update: Update, context: CallbackContext):
    chat_id = update.effective_user.id
    text = update.message.text

    if text == "/cancel":
        update.message.reply_text(
            "Request Cancelled. Press /start to use the bot again!"
        )
        if chat_id in top_text:
            del top_text[chat_id]
        if chat_id in bottom_text:
            del bottom_text[chat_id]
        return ConversationHandler.END
    elif chat_id not in top_text:
        top_text[chat_id] = text
        update.message.reply_text("Please enter the text for the bottom line:")
        return START_STATE
    else:
        bottom_text[chat_id] = text

        data = re.get("https://api.imgflip.com/get_memes").json()["data"]["memes"]
        image_id = random.randint(0, len(data) - 1)
        URL = "https://api.imgflip.com/caption_image"

        params = {
            "username": USERNAME,
            "password": PASSWORD,
            "template_id": data[image_id]["id"],
            "text0": top_text[chat_id],
            "text1": bottom_text[chat_id],
        }

        response = re.request("POST", URL, params=params).json()
        url_image = response["data"]["url"]

        update.message.reply_photo(photo=url_image)

        del top_text[chat_id]
        del bottom_text[chat_id]

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

    meme_conv_handler = ConversationHandler(
        entry_points=[CommandHandler("memes", meme_generator)],
        states={
            1: [MessageHandler(Filters.text, message_filter)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        allow_reentry=True,
    )

    dp.add_handler(CommandHandler("help", help))

    dp.add_handler(info_handler)
    dp.add_handler(settings_handler)
    dp.add_handler(meme_conv_handler)

    dp.add_handler(MessageHandler(Filters.text, vulgarity_check))

    unknown_handler = MessageHandler(Filters.command, unknown)
    dp.add_handler(unknown_handler)

    updater.start_polling()
    updater.idle()


if __name__ == "__main__":
    main()
