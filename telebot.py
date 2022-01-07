from telegram import (
    Bot,
    Update,
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
from nltk import download
from nltk.corpus import words
from nltk.metrics.distance import (
    edit_distance,
    jaccard_distance,
)
from nltk.util import ngrams
import matplotlib.pyplot as plt
from wordcloud import WordCloud, STOPWORDS

import os
from dotenv import load_dotenv

load_dotenv("./.env")
TOKEN = os.getenv("token")
bot = Bot(TOKEN)

download("words")  # run this in the first run
correct_spellings = words.words()

typos = []


def plot_cloud(wordcloud):
    plt.figure(figsize=(40, 30))
    plt.imshow(wordcloud)
    plt.axis("off")
    plt.savefig("word_cloud.png")


def show(update: Update, context: CallbackContext):
    update.message.reply_text("hello")


def word_cloud(update: Update, context: CallbackContext):
    typos = context.chat_data["typos"]
    typo_words = []
    for typo in typos:
        typo_words.append(typo[1])

    # convo handler? maybe can ask what colour they want
    wordcloud = WordCloud(
        width=3000,
        height=2000,
        random_state=1,
        background_color="salmon",
        colormap="Pastel1",
        collocations=False,
    ).generate(" ".join(typo_words))
    plot_cloud(wordcloud)
    img = open("word_cloud.png", "rb")
    update.message.reply_photo(img)  ##dk how to send the file


def typo_msg(update: Update, context: CallbackContext):
    list_words = update.message.text.split()
    count = 0

    for word in list_words:
        if word not in correct_spellings:
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

    context.chat_data["typos"] = typos  # saves typos and scores into list

    if count > 0:  # if there are errors
        update.message.reply_text(
            f"Your reply contained {str(count)} typo errors! Are you even trying?"
        )

    if (
        len(typos) > 10
    ):  # triggered when more than 10 errors, replies with worst jaccard score (i.e. 1)
        typos.sort(key=lambda x: x[1])
        worst_spelt = typos[-1][1]
        update.message.reply_text(
            f"Someone made more than 10 typos today... Your worstly spelt word is {worst_spelt}"
        )


def main():
    updater = Updater(TOKEN, use_context=True)

    # Get dispatcher to register handlers
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("show", show))
    dp.add_handler(CommandHandler("word_cloud", word_cloud))
    dp.add_handler(MessageHandler(Filters.text, typo_msg))

    # dp.add_handler(InlineQueryHandler(inline_price))
    # dp.add_error_handler(error)

    updater.start_polling()
    updater.idle()


if __name__ == "__main__":
    main()
