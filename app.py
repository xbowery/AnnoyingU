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
import os

from dotenv import load_dotenv
import requests as re
from better_profanity import profanity
from nltk.util import ngrams
from nltk.corpus import words
from nltk.metrics.distance import (
    edit_distance,
    jaccard_distance,
    )
import matplotlib.pyplot as plt
from wordcloud import WordCloud, STOPWORDS

# nltk.download('words') #run this in the first run 
correct_spellings = words.words() 
typos = []

from pymongo import MongoClient

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

logger = logging.getLogger(__name__)

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

    if 'rick' in update.message.text.lower():
        update.message.reply_video('https://c.tenor.com/x8v1oNUOmg4AAAAC/rickroll-roll.gif')

    list_words = update.message.text.split()
    count = 0 
    for word in list_words:
        if word not in correct_spellings:
            count += 1
            candidates = [(jaccard_distance(set(ngrams(word, 2)), set(ngrams(w, 2))),w) for w in correct_spellings if w[0]==word[0]]
            if len(candidates) != 0:
                correction = sorted(candidates)[0] #gets most similar word based on jaccard distance
                typos.append((correction[0], word)) #adds jaccard score and original typo into list 
    
    context.chat_data["typos"] = typos #saves typos and scores into list 
    
    if count > 0: #if there are errors
        update.message.reply_text(f"Your reply contained {str(count)} typo errors! Are you even trying?")
    
    if len(typos) > 10: #triggered when more than 10 errors, replies with worst jaccard score (i.e. 1)
        typos.sort(key=lambda x:x[1])
        worst_spelt = typos[-1][1]
        update.message.reply_text(f"Someone made more than 10 typos today... Your worstly spelt word is {worst_spelt}")
        
    
    


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

    dp.add_handler(MessageHandler(Filters.text, vulgarity_check))

    unknown_handler = MessageHandler(Filters.command, unknown)
    dp.add_handler(unknown_handler)

    updater.start_polling()
    updater.idle()


if __name__ == "__main__":
    main()
