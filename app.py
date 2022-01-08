#!/usr/bin/env python3

from telegram import (
    Bot,
    Update,
    ForceReply,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ParseMode,
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
import datetime
import time
import uuid

from dotenv import load_dotenv
from database import top_text, bottom_text, last_called, last_called_username
import requests as re
from better_profanity import profanity
from nltk import download
from nltk.util import ngrams
from nltk.corpus import words
from nltk.metrics.distance import (
    edit_distance,
    jaccard_distance,
)
import matplotlib.pyplot as plt
from wordcloud import WordCloud, STOPWORDS

download("words")  # run this in the first run
correct_spellings = words.words()
# typos = []

from pymongo import MongoClient

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

logger = logging.getLogger(__name__)

ACCEPTABLE_SETTINGS = [
    "Spelling Hornets",
    "Profanity Alert",
    "Custom Blacklist",
    "Custom Whitelist",
]
APPROVED_ADMIN_ROLES = ["administrator", "creator", "member"]

reply_info_keyboard = [
    ["Spelling Hornets"],
    ["Profanity Alert"],
    ["Meme Generator"],
    ["End"],
]

reply_settings_keyboard = [
    ["Spelling Hornets"],
    ["Profanity Alert"],
    ["Custom Blacklist"],
    ["Custom Whitelist"],
    ["End"],
]

boolean_keyboard = [["On"], ["Off"], ["Cancel"]]

markup_info = ReplyKeyboardMarkup(reply_info_keyboard, one_time_keyboard=True)
markup_settings = ReplyKeyboardMarkup(reply_settings_keyboard, one_time_keyboard=True)
markup_boolean = ReplyKeyboardMarkup(boolean_keyboard, one_time_keyboard=True)

FIRST_STATE, SECOND_STATE, THIRD_STATE = range(3)

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
SETTINGSDB = db["chat_settings"]

# https://pymongo.readthedocs.io/en/stable/tutorial.html
# PROFANITY_USERDB.insert_one({"test": 123})
# PROFANITY_USERDB.findOne({})


def unknown(update: Update, context: CallbackContext):
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Sorry, I didn't understand that command.",
    )


def init_settings(chat_id, context):

    if "chat_settings" in context.chat_data:
        return

    chat_settings = {
        "chatid": chat_id,
        "Spelling Hornets": True,
        "Profanity Alert": True,
        "wordlist": [],
        "whitelist": [],
    }

    context.chat_data["chat_settings"] = chat_settings
    SETTINGSDB.insert_one(chat_settings)


def start(update: Update, context: CallbackContext) -> None:
    user = update.effective_user
    update.message.reply_markdown_v2(
        fr"""Hi {user.mention_markdown_v2()}\!

Welcome to the *All In One*, _State of the art_ mistake and profanity identifier\.

To get started, type /help""",
    )

    init_settings(update.message.chat_id, context)


def message_check(update: Update, context: CallbackContext):
    if "chat_settings" not in context.chat_data:
        init_settings(update.message.chat_id, context)

    chat_settings = context.chat_data["chat_settings"]
    spell_on, profanity_on, blacklist, whitelist = (
        chat_settings["Spelling Hornets"],
        chat_settings["Profanity Alert"],
        chat_settings["wordlist"],
        chat_settings["whitelist"],
    )

    if not spell_on and not profanity_on:
        return

    msg = update.message.text
    user_id = str(update.effective_user.id)

    punc = """!()-[]{};:'"\,<>./?@#$%^&*_~"""
    text = msg.lower()
    for ele in text:
        if ele in punc:
            text = text.replace(ele, "")
    list_words = text.split()

    profanity.load_censor_words()
    profanity.add_censor_words(blacklist)

    if (
        profanity_on
        and all(t not in whitelist for t in list_words)
        and profanity.contains_profanity(msg)
    ):

        user_first_name = update.effective_user.first_name

        if user_first_name == None:
            user_first_name = " "
        user_last_name = update.effective_user.last_name
        if user_last_name == None:
            user_last_name = " "
        user_string = (
            user_first_name + " (*&%^) " + user_last_name + " (*&%^) " + user_id
        )

        datetime_now = datetime.datetime.now()

        if chat_time_storage := PROFANITY_TIMEDB.find_one(
            {"chatid": update.message.chat_id}
        ):
            datetime_last_called = chat_time_storage["datetime"]
            user_string_last_called = chat_time_storage["userstring"]

            firstname_last_called = user_string_last_called.split(" (*&%^) ")[0]
            lastname_last_called = user_string_last_called.split(" (*&%^) ")[1]
            userid_last_called = user_string_last_called.split(" (*&%^) ")[2]

            time_diff = str(datetime_now - datetime_last_called)

            word_list = [
                "a mind\-boggling",
                "an unbelievable",
                "a spectacular",
                "an exceptional",
                "a mind\-blowing",
                "an incredible",
                "an inconceivable span of",
                "an unimaginable",
                "an impressive",
                "a remarkable",
                "a grand total of",
                "a noteworthy",
                "a shocking span of",
                "a wondrous",
                "a peaceful span of",
                "a momentous",
                "an astonishing",
            ]

            if "day" in time_diff:
                break_list = time_diff.split(" day, ")
                num_days = int(break_list[0])
                num_hours = int((break_list[1]).split(":")[0])

                total_hours = 24 * num_days + num_hours

                word_input = str(total_hours) + " hours"

            elif "days" in time_diff:
                word_input = time_diff.split(", ")[0]

            else:
                break_list = time_diff.split(".")[0]
                num_hours = int(break_list.split(":")[0])
                num_minutes = int(break_list.split(":")[1])
                num_seconds = int(break_list.split(":")[2])

                if num_hours > 0:
                    word_input = str(num_hours) + " hours"
                elif num_minutes > 0:
                    word_input = str(num_minutes) + " minutes"
                else:
                    word_input = str(num_seconds) + " seconds"

            chat_time_storage["datetime"] = datetime_now
            chat_time_storage["userstring"] = user_string
            rand_num = random.randint(0, len(word_list) - 1)
            update.message.reply_markdown_v2(
                fr"""🎉 *RESET THE COUNTER\!\!\!* 🎉
            
It has been _{word_list[rand_num]}_ *{word_input}* since someone spewed a vulgarity here\!

Previous user to spew a vulgarity: [{firstname_last_called} {lastname_last_called}](tg://user?id={userid_last_called})"""
            )
        else:
            chat_time_storage = {
                "chatid": update.message.chat_id,
                "datetime": datetime_now,
                "userstring": user_string,
            }

        context.chat_data["chat_time_storage"] = chat_time_storage

        update_obj = {"$set": chat_time_storage}
        PROFANITY_TIMEDB.update_one(
            {"chatid": chat_time_storage["chatid"]}, update_obj, upsert=True
        )

    elif "rick" in update.message.text.lower():
        option = random.randint(0, 4)
        if option == 0:
            update.message.reply_video(
                "https://c.tenor.com/x8v1oNUOmg4AAAAC/rickroll-roll.gif"
            )
        elif option == 1:
            update.message.reply_text(
                "Here's a Spotify Code to help solve all your problems!\n\nDo scan it using the Spotify app on your phone!"
            )
            context.bot.send_photo(
                chat_id=update.effective_chat.id,
                photo="https://i.imgur.com/iI76wrG.jpg",
            )
        elif option == 2:
            new_list = []
            with open("lyrics.txt", "r+", encoding="utf-8") as file:
                new_list = file.readlines()
                for text in new_list:
                    words = text.split("%")
                    sentence = ""
                    for i in range(len(words)):
                        sentence += words[i] + "\n"
                    context.bot.send_message(
                        chat_id=update.effective_chat.id, text=sentence
                    )
                    time.sleep(1.5)
        elif option == 3:
            update.message.reply_text(
                "Here you go, champ! You earned this 😊\n\nbit.do/YeetYeet",
                disable_web_page_preview=True,
            )
        else:
            update.message.reply_text(
                "Hey rockstar, you earned this!\n\nhttps://tinyurl.com/hacknroll2k22",
                disable_web_page_preview=True,
            )

    elif spell_on:
        count = 0
        typos = []
        # if update.effective_user.id not in context.chat_data["typos"]:
        #     typos = []
        # else:
        #     typos = context.chat_data["typos"][update.effective_user.id]
        for word in list_words:
            if word.isalpha() == True and word not in correct_spellings:
                count += 1
                candidates = [
                    (jaccard_distance(set(ngrams(word, 2)), set(ngrams(w, 2))), w)
                    for w in correct_spellings
                    if w[0] == word[0]
                ]
                if len(candidates) != 0:
                    correction = sorted(candidates)[
                        0
                    ]  # gets most similar word based on jaccard distance
                    typos.append(
                        (correction[0], word)
                    )  # adds jaccard score and original typo into list

        context.chat_data["typos"] = {
            update.effective_user.id: typos
        }  # saves typos and scores into list

        if count == 1:  # if there are errors
            update.message.reply_text(
                f"Your reply contained {str(count)} typo error! Are you even trying?"
            )
        if count > 1:
            update.message.reply_text(
                f"Your reply contained {str(count)} typo errors! Are you even trying?"
            )
        if (
            len(typos) > 10
        ):  # triggered when more than 10 errors, replies with worst jaccard score (i.e. 1)
            typos.sort(key=lambda x: x[1])
            worst_spelt = context.chat_data["typos"][update.effective_user.id][0][1]
            update.message.reply_text(
                f"Someone made more than 10 typos today... Your worstly spelt word is {worst_spelt}"
            )


def plot_cloud(wordcloud):
    plt.figure(figsize=(40, 30))
    plt.imshow(wordcloud)
    plt.axis("off")
    filename = str(uuid.uuid4().hex) + ".png"
    plt.savefig(filename)
    return filename


def word_cloud(update: Update, context: CallbackContext):
    if not "typos" in context.chat_data:
        update.message.reply_text("All great! No Spelling erros.")
        return

    update.message.reply_text("Be patient! I am generating it now!")
    typos = context.chat_data["typos"]
    words = []
    for w in typos.values():
        for word in w:
            words.append(word[1])

    wordcloud = WordCloud(
        width=3000,
        height=2000,
        random_state=1,
        background_color="salmon",
        colormap="Pastel1",
        collocations=False,
    ).generate(" ".join(words))
    filename = plot_cloud(wordcloud)
    img = open(filename, "rb")
    update.message.reply_photo(img)

    os.remove(filename)


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
    return FIRST_STATE


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
    return FIRST_STATE


def settings(update: Update, context: CallbackContext):
    user_id = update.effective_user.id

    if user_id is not None:
        member = update.message.chat.get_member(user_id=user_id)
        if member.status in APPROVED_ADMIN_ROLES:
            update.message.reply_text(
                "Choose which settings you would like to edit:",
                reply_markup=markup_settings,
            )

            return FIRST_STATE

    update.message.reply_text(
        "Insufficient permissions to change settings. Please contact the administrator.",
        reply_markup=ReplyKeyboardRemove(),
    )
    return ConversationHandler.END


def settings_reply(update: Update, context: CallbackContext):
    msg = update.message.text

    if "chat_settings" not in context.chat_data:
        init_settings(update.message.chat_id, context)

    chat_settings = context.chat_data["chat_settings"]

    if msg in ACCEPTABLE_SETTINGS:
        context.chat_data["Settings_Option"] = msg

        if msg in ["Custom Blacklist", "Custom Whitelist"]:
            orig_words = (
                chat_settings["wordlist"]
                if msg == "Custom Blacklist"
                else chat_settings["whitelist"]
            )
            wordlist = ", ".join(orig_words)
            if wordlist == "":
                wordlist = "EMPTY"

            update.message.reply_text(
                f"Current {msg}: {wordlist}.\n\nPlease enter whether to keep and append to old list (KEEP) or replace (REP) followed by the words seperated by a comma.\n\nExample: KEEP, word1, word2.",
                reply_markup=ReplyKeyboardRemove(),
            )
            return THIRD_STATE

        update.message.reply_text(
            f"Settings for {msg}: {'ON' if chat_settings[msg] else 'OFF'}.\nSelect the new settings:",
            reply_markup=markup_boolean,
        )
        return SECOND_STATE

    if msg == "End":
        update.message.reply_text("Bye", reply_markup=ReplyKeyboardRemove())
        return ConversationHandler.END

    update.message.reply_text(
        f"Sorry, such settings does not exist", reply_markup=markup_settings
    )
    return FIRST_STATE


def change_settings(update: Update, context: CallbackContext):
    msg = update.message.text
    opt = context.chat_data["Settings_Option"]
    chat_settings = context.chat_data["chat_settings"]

    logger.info(chat_settings)

    if msg not in ["On", "Off", "Cancel"]:
        update.message.reply_text(
            "Sorry. This is not a valid option", reply_markup=markup_settings
        )
        return_state = FIRST_STATE
    elif msg == "Cancel":
        update.message.reply_text(
            "Select the settings to edit:", reply_markup=markup_settings
        )
        return_state = FIRST_STATE
    else:
        chat_settings[opt] = True if msg == "On" else False
        return_state = ConversationHandler.END

        update.message.reply_text(
            f"Settings for {opt}: {'ON' if chat_settings[opt] else 'OFF'}",
            reply_markup=ReplyKeyboardRemove(),
        )

    update_obj = {"$set": chat_settings}

    SETTINGSDB.update_one({"chatid": chat_settings["chatid"]}, update_obj, upsert=True)
    context.chat_data["chat_settings"] = chat_settings

    return return_state


def change_wordlist(update: Update, context: CallbackContext):
    msg = update.message.text
    chat_settings = context.chat_data["chat_settings"]
    prev_options = context.chat_data["Settings_Option"]

    try:
        new_list = [
            a.strip().lower() for a in msg.split(",") if a.strip() not in ["", " "]
        ]

        if new_list[0] in ["keep", "rep"]:
            final_list = list(set(new_list[1:]))
            if prev_options == "Custom Blacklist":
                if new_list[0] == "keep":
                    final_list = list(set(chat_settings["wordlist"] + new_list[1:]))
                    chat_settings["wordlist"] = final_list
                else:
                    chat_settings["wordlist"] = final_list
            else:
                if new_list[0] == "keep":
                    final_list = list(set(chat_settings["whitelist"] + new_list[1:]))
                    chat_settings["whitelist"] = final_list
                else:
                    chat_settings["whitelist"] = final_list

            update_obj = {"$set": chat_settings}

            SETTINGSDB.update_one(
                {"chatid": chat_settings["chatid"]},
                update_obj,
                upsert=True,
            )

            context.chat_data["chat_settings"] = chat_settings

            update.message.reply_text(
                f"{prev_options} successfully updated.\n\nNew {prev_options}: {', '.join(final_list) if len(final_list) > 0 else 'EMPTY!'}",
                reply_markup=ReplyKeyboardRemove(),
            )

            return ConversationHandler.END
    except:
        pass

    update.message.reply_text(
        f"The wordlist entered is malformed, please try again using /settings",
        reply_markup=ReplyKeyboardRemove(),
    )
    return ConversationHandler.END


def meme_generator(update: Update, context: CallbackContext):
    update.message.reply_text("Please enter the text for the top line:")

    return FIRST_STATE


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
        return FIRST_STATE
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

    for c in SETTINGSDB.find():
        del c["_id"]
        dp.chat_data[c["chatid"]]["chat_settings"] = c

    dp.add_handler(CommandHandler("start", start))

    info_handler = ConversationHandler(
        entry_points=[CommandHandler("info", info)],
        states={
            FIRST_STATE: [MessageHandler(Filters.text, info_reply)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    settings_handler = ConversationHandler(
        entry_points=[CommandHandler("settings", settings)],
        states={
            FIRST_STATE: [MessageHandler(Filters.text, settings_reply)],
            SECOND_STATE: [MessageHandler(Filters.text, change_settings)],
            THIRD_STATE: [MessageHandler(Filters.text, change_wordlist)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    meme_conv_handler = ConversationHandler(
        entry_points=[CommandHandler("memes", meme_generator)],
        states={
            FIRST_STATE: [MessageHandler(Filters.text, message_filter)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        allow_reentry=True,
    )

    dp.add_handler(CommandHandler("help", help))

    dp.add_handler(meme_conv_handler)
    dp.add_handler(info_handler)
    dp.add_handler(settings_handler)

    dp.add_handler(CommandHandler("word_cloud", word_cloud))
    dp.add_handler(MessageHandler(Filters.text, message_check))

    unknown_handler = MessageHandler(Filters.command, unknown)
    dp.add_handler(unknown_handler)

    updater.start_polling()
    updater.idle()


if __name__ == "__main__":
    main()
