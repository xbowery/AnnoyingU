# AnnoyingU

## What does AnnoyingU do?
AnnoyingU Bot allows you to specify words that you want to call people out on, whether is it on group chats or private chats with your friends. Easily make memes of your friends whenever they speak of the special word and make your conversations more fun-filled with AnnoyingU!

## Inspiration
Ever get frustrated when your friend makes a typo error and they never seem to realise you can’t understand what they are saying? Or maybe you have a friend who incessantly swears every 10 seconds while you are having a conversation. It’s pretty annoying isn’t it? Maybe it’s time for us to annoy them back…

## What it does
AnnoyingU is simple to use. Tell AnnoyingU a list of words you want the bot to call people out on whenever it's being used. AnnoyingU will politely remind you and your friends whenever someone has used the “special word”. Send memes to embarrass your friends through the bot’s commands and make your conversations more memorable or… annoying….. So what are you waiting for? Use AnnoyingU now!

## How we built it
We built the bot using the Python Telegram package. We also used the nltk, better_profanity packages for our message handlers to filter out typing errors and use of profanities. We also linked the bot to MongoDB to store chat information such as chat timestamps and settings.

## Challenges we ran into
We had to find multiple suitable libraries that are able to handle spelling checks, especially to cater for modern English language use including colloquial words.

We also took a while to figure out how to store the states of the telegram bot, as well as how to send generated pictures.

## Accomplishments that we are proud of
Making a fully functional bot within 24 hours which is very customisable for users and is able to keep track of the chat history.

## What's next for AnnoyingU
We hope to improve the accuracy of the message filtering function so that we do not unnecessarily annoy users.
