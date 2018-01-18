#!/usr/bin/env python
# -*- coding: utf-8 -*- 

# This is the current bot code. This code HAS been pushed out and is currently live at @check_my_stock_bot on Telegram.
# If there are any issues with the code, please create an issue to the repository.

from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
import logging
# from alpha_vantage.timeseries import TimeSeries
import requests
import json
import random
import portfolio


TOKEN = "TOKEN"
# ts = TimeSeries(key='WXVDTULIQ8D8RY0C') 

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)


# Define a few command handlers. These usually take the two arguments bot and
# update. Error handlers also receive the raised TelegramError object in error.
def start(bot, update):
    """Send a message when the command /start is issued."""
    update.message.reply_text('This bot is your new personal broker 😎\nType /help to get started.', quote=False)


def help(bot, update):
    """Send a message when the command /help is issued."""
    formatted_string = ('I can manage and perform stock analysis and broker-like tasks.\n\n'
                        'Here are some commands that work for me:\n\n'
                        '/price <ticker> - find current stock price\n'
                        '/news <ticker> - latest news on company (top 5)')
    update.message.reply_text(formatted_string, quote=False)


def news(bot, update, args):
    """Sends news about a given ticker."""
    raw_data = requests.get(f'https://api.iextrading.com/1.0/stock/{args[0]}/news/last/5')
    data = json.loads(raw_data.text)

    # randomize the article that you want to pick
    art_num = random.randint(0, len(data))
    data = data[art_num]

    title = data['headline']
    summary = data['summary']
    link = data['url']
    source = data['source']
    date = data['datetime'][0:10]
    string = (f'\"**{title}**\" by {source}\n'
            f'Date: {date}\n\n'
            f'{summary}\n\n'
            f'{link}')

    update.message.reply_text(string, quote=False)
    return None


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
    except:
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

    # log all errors
    dp.add_error_handler(error)

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()
