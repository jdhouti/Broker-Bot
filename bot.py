#!/usr/bin/env python
# -*- coding: utf-8 -*- 

# This is the testing bot. Everything included in this file has not yet been released.
# Currently undergoing active development and testing.

from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackQueryHandler
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ParseMode
import logging, requests, json, random, boto3
import portfolio
import database_lookup as database

TOKEN = "TOKEN"

# Logging to find and squish bugs
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)


# This is where all of the bot commands lie
def start(bot, update):
    """Send a message when the command /start is issued and creates database entry."""
    update.message.reply_text('This bot is your new personal broker 😎\nType /help to get started.', quote=False)

    # when the /start command is run, script checks if user has a database entry.
    if not database.existance(update.message.from_user.__dict__['id']):
        database.table.put_item(
            Item={
                'user': update.message.from_user.__dict__['id'],
                'portfolios': {}
            }
        )


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


def price(bot, update, args):
    """Send a message with the stock price of the ticker."""
    try:
        raw_data = requests.get(f'https://api.iextrading.com/1.0/stock/{args[0]}/quote')
        data = json.loads(raw_data.text)

        price = "$" + '{:20,.2f}'.format(data['latestPrice'])
        company = data['companyName']
        volume = "$" + '{:20,.2f}'.format(data['avgTotalVolume'])
        mktcap = "$" + '{:20,.2f}'.format(data['marketCap'])
        
        string = (f'<b>{company} ({args[0].upper()}</b>)'
                    f'\n😎 Price: {price.replace(" ", "")}'
                    f'\n💰 Volume: {volume.replace(" ", "")}'
                    f'\n🌡️ Market Cap: {mktcap.replace(" ", "")}')
        update.message.reply_text(string, quote=False, parse_mode=ParseMode.HTML)

        return None

    except json.decoder.JSONDecodeError:
        update.message.reply_text(f'{args[0].upper()} isn\'t a valid ticker 😔', quote=False)
        return None


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


def portfolios(bot, update):
    """Returns all portfolio information when the /portfolios command is issued."""

    portfolios = portfolio.view_all(update.message.from_user.__dict__['id'])
    if len(portfolios) == 0:
        update.message.reply_text(
            f'You don\'t have any portfolios 😢\n'
            f'You can create one using <b>/create (name)</b>',
            parse_mode=ParseMode.HTML
        )
        return False

    keyboard = []

    # Create the markup keyboard from the list of portfolio names
    for i in portfolios.keys():
        keyboard.append([InlineKeyboardButton(i, callback_data=i)])

    reply_markup = InlineKeyboardMarkup(keyboard)

    # Ask the user which portfolio he would like to use
    update.message.reply_text(
        '<b>Select which portfolio you want to review:</b>', 
        reply_markup=reply_markup,
        parse_mode=ParseMode.HTML)
    return True


def create(bot, update, args):
    """Creates a portfolio for the user when the /create command is issued."""

    user_id = update.message.from_user.__dict__['id']
    args[0] = args[0].title()

    if portfolio.create(user_id, args[0]):
        update.message.reply_text(f'Your portfolio, {args[0].title()} was created!', quote=False)
    else:
        update.message.reply_text(f'You already have a portfolio called {args[0].title()}.')

    return None


def delete(bot, update, args):
    """Deletes a portfolio from the database"""

    user_id = update.message.from_user.__dict__['id']
    args[0] = args[0].title()

    if portfolio.delete(user_id, args[0]):
        update.message.reply_text(f'Your portfolio, {args[0].title()} was deleted!')
    else:
        update.message.reply_text(f'You don\'t have a portfolio called {args[0].title()}!')
    
    return None


def button(bot, update):
    """Handles the behavior of the inline buttons."""

    # Retrieve the information on which button was pressed
    query = update.callback_query
    user_id = query['message']['chat']['id']

    # Find which portfolio the user selected based on the returned query
    this_portfolio = portfolio.view(user_id, query.data)
    text = f"<b>{query.data}</b>\nValue: ${this_portfolio['value']}"

    bot.edit_message_text(text=text,
                          chat_id=query.message.chat_id,
                          message_id=query.message.message_id,
                          parse_mode=ParseMode.HTML)

    return True


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
    dp.add_handler(CommandHandler("delete", delete, pass_args=True))
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
