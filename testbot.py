#!/usr/bin/env python
# -*- coding: utf-8 -*- 

# This is the testing bot. Everything included in this file has not yet been released.
# Currently undergoing active development and testing.

from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackQueryHandler
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ParseMode
from pymongo import MongoClient
import logging
import requests
import json
import random
import portfolio as p


TOKEN = "TOKEN"

# Logging to find and squish bugs
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)


# This is where all of the bot commands lie
def start(bot, update):
    """Send a message when the command /start is issued."""
    update.message.reply_text('This bot is your new personal broker 😎\nType /help to get started.', quote=False)


def help(bot, update):
    """Send a message when the command /help is issued."""
    formatted_string = ('I can manage and perform stock analysis and broker related tasks.\n\n'
                        'Here are some basic commands to get started:\n\n'
                        '/price (ticker) - find current stock price\n'
                        '/news (ticker) - latest news on company (top 5)\n\n'
                        '<b>Portfolio Settings</b>\n'
                        '/portfolios - view all portfolios you\'ve created'
                        '/create (name) - creates a portfolio')
    update.message.reply_text(formatted_string, quote=False, parse_mode=ParseMode.HTML)


def news(bot, update, args):
    """Sends news about a given ticker."""
    try:
        raw_data = requests.get(f'https://api.iextrading.com/1.0/stock/{args[0]}/news/last/5')
        data = json.loads(raw_data.text)

        # Randomize the article that is returned
        art_num = random.randint(0, len(data))
        data = data[art_num]

        title = data['headline']
        summary = data['summary']
        link = data['url']
        source = data['source']
        date = data['datetime'][0:10]
        text = (f'<b>{title}</b> by {source}\n'
                f'<i>Date: {date}</i>\n\n'
                f'{summary}\n\n'
                f'{link}')

        update.message.reply_text(text, quote=False, parse_mode=ParseMode.HTML)
        return True

    except json.decoder.JSONDecodeError:
        update.message.reply_text(f'{args[0]} isn\'t a valid ticker 😔', quote=False)
        return False


def delete(bot, update, args):
    """Deletes a portfolio from the database"""

    # Open db connection
    mgclient = MongoClient()
    db = mgclient.user_db           # Create database for user information
    portfolio_db = db.portfolios    # Create table for portfolio data




def create(bot, update, args):
    """Creates a portfolio for the user."""
    
    # Open db connection
    mgclient = MongoClient()
    db = mgclient.user_db           # Create database for user information
    portfolio_db = db.portfolios    # Create table for portfolio data

    username = update.message.from_user.__dict__['username']
    
    # Check if user already has a portfolio with the same name
    if db.portfolios.find_one({'owner':update.message.from_user.__dict__['id'], 'name':args[0].title()}):
        update.message.reply_text('You already have a portfolio with that name!')
        return False

    # Create the portfolio using user ID and portfolio name
    new_portfolio = p.Portfolio(update.message.from_user.__dict__['id'], args[0].title())

    # Insert the class into the mongodb database
    db.portfolios.insert(new_portfolio.__dict__)
    update.message.reply_text(f'@{username}, your portfolio was created!', quote=False)

    # Close db connection
    mgclient.close()
    return True


def button(bot, update):
    """Handles the behavior of the inline buttons."""

    # Open the database connection
    mgclient = MongoClient()
    db = mgclient.user_db           # Connect to database of user information
    portfolio_db = db.portfolios    # Connect to table of portfolio data

    # Retrieve the information on which button was pressed
    query = update.callback_query

    # Find which portfolio the user selected based on the returned query
    portfolio = portfolio_db.find_one({'owner':query.from_user['id'], 'name':query.data})
    text = f"<b>{query.data}</b>\nValue: ${portfolio['value']}"

    bot.edit_message_text(text=text,
                          chat_id=query.message.chat_id,
                          message_id=query.message.message_id,
                          parse_mode=ParseMode.HTML)

    # Close the database connection
    mgclient.close()
    return True


def portfolios(bot, update):
    """Returns all portfolio information."""

    # Open the database connection
    mgclient = MongoClient()
    db = mgclient.user_db           # Connect to database of user information
    portfolio_db = db.portfolios    # Connect to table of portfolio data

    portfolios, keyboard = [], []

    # Create a list of all of the portfolio names found under the user's id
    for i in db.portfolios.find({'owner':update.message.from_user.__dict__['id']}):
        portfolios.append(i['name'])

    # Check if user has a portfolio, if not, quit out of the function
    if len(portfolios) == 0:
        update.message.reply_text(
            'You do not have any portfolios.\nUse <b>/create (name)</b> to create one!',
            parse_mode=ParseMode.HTML)
        return False

    # Create the markup keyboard from the list of portfolio names
    for i in portfolios:
        keyboard.append([InlineKeyboardButton(i, callback_data=i)])

    reply_markup = InlineKeyboardMarkup(keyboard)

    # Ask the user which portfolio he would like to use
    update.message.reply_text(
        '<b>Select which portfolio you want to review:</b>', 
        reply_markup=reply_markup,
        parse_mode=ParseMode.HTML)

    # Close the database connection
    mgclient.close()
    return True


def price(bot, update, args):
    """Send a message with the stock price of the ticker."""
    try:
        raw_data = requests.get(f'https://api.iextrading.com/1.0/stock/{args[0]}/quote')
        data = json.loads(raw_data.text)

        price = data['latestPrice']
        company = data['companyName']
        volume = data['avgTotalVolume']
        mktcap = data['marketCap']
        string = (f'{company} ({args[0].upper()})'
                    f'\n😎 Price: {price}'
                    f'\n💰 Volume: {volume}'
                    f'\n🌡️ Market Cap: {mktcap}')
        update.message.reply_text(string, quote=False)
        return None
    except json.decoder.JSONDecodeError:
        update.message.reply_text(f'{args[0]} isn\'t a valid ticker 😔', quote=False)
        return None


def error(bot, update, error):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, error)


def main():
    """Start the bot."""
    # Create the EventHandler and pass it your bot's token.
    updater = Updater(TOKEN)

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    # on different commands - answer in Telegram
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help))
    dp.add_handler(CommandHandler("price", price, pass_args=True))
    dp.add_handler(CommandHandler("news", news, pass_args=True))
    dp.add_handler(CommandHandler("create", create, pass_args=True))
    dp.add_handler(CommandHandler("portfolios", portfolios))
    dp.add_handler(CallbackQueryHandler(button))

    # log all errors
    dp.add_error_handler(error)

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()
    mg.close()


if __name__ == '__main__':
    main()
