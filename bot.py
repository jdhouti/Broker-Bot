#!/usr/bin/env python
# -*- coding: utf-8 -*- 

# This is the testing bot. Everything included in this file has not yet been released.
# Currently undergoing active development and testing.

from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackQueryHandler, ConversationHandler
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ParseMode
import logging, requests, json, random, boto3
import portfolio
import database_lookup as database

TOKEN = "TOKEN"

# Logging to find and squish bugs
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

ADD, INFO, DELETECONF, DELETEFINAL = range(4)

# This is where all of the bot commands lie
def start(bot, update):
    """Send a message when the command /start is issued and creates database entry."""
    update.message.reply_text('This bot is ready to be your new personal broker 😎\nType /help to get started.', quote=False)

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
                        '/portfolios - view all portfolios you\'ve created\n'
                        '/create (name) - creates a portfolio')
    update.message.reply_text(formatted_string, quote=False, parse_mode=ParseMode.HTML)


def price(bot, update, args):
    """Send a message with the stock price of the ticker."""
    if len(args) == 0:
        update.message.reply_text(u'Incorrect usage. Refer to /help.')
        return

    try:    # try collecting all of the data
        raw_data = requests.get(f'https://api.iextrading.com/1.0/stock/{args[0]}/quote')
        data = json.loads(raw_data.text)
        price = "$" + '{:20,.2f}'.format(data['latestPrice'])
        company = data['companyName']
        volume = "$" + '{:20,.2f}'.format(data['avgTotalVolume'])
        mktcap = "$" + '{:20,.2f}'.format(data['marketCap'])
    
    except json.decoder.JSONDecodeError:    # was unable to collect all data so ticker isn't valid
        update.message.reply_text(f'{args[0].upper()} isn\'t a valid ticker 😔', quote=False)
        return

    string = (f'<b>{company} ({args[0].upper()}</b>)'
                f'\n😎 Price: {price.replace(" ", "")}'
                f'\n💰 Volume: {volume.replace(" ", "")}'
                f'\n🌡️ Market Cap: {mktcap.replace(" ", "")}')

    keyboard = [
        [InlineKeyboardButton(u'Add to portfolio', callback_data=str(PRICE))]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    update.message.reply_text(string, quote=False, parse_mode=ParseMode.HTML, reply_markup=reply_markup)
    return ADD


def add(bot, update):
    query = update.callback_query

    bot.edit_message_text(
        text='Feature not yet available.',
        chat_id=query.message.chat_id,
        message_id=query.message.message_id,
    )


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
    user_id = update.message.from_user.__dict__['id']

    if not portfolio.get_keyboard(user_id):
        update.message.reply_text(u'You don\'t have any portfolios 😢\nUse /create (portfolio_name).')
        return

    # Ask the user which portfolio he would like to use
    update.message.reply_text(
        '<b>Select the portfolio you would like to review</b>', 
        reply_markup=portfolio.get_keyboard(user_id),
        parse_mode=ParseMode.HTML)
    return INFO


def create(bot, update, args):
    """Creates a portfolio for the user when the /create command is issued."""

    if len(args) == 0:
        update.message.reply_text(u'Incorrect usage. Refer to /help.')
        return

    user_id = update.message.from_user.__dict__['id']
    args[0] = args[0].title()

    if portfolio.create(user_id, args[0]):
        update.message.reply_text(f'Your portfolio, {args[0].title()} was created!', quote=False)
    else:
        update.message.reply_text(f'You already have a portfolio called {args[0].title()}.')

    return None

##
# this is the beginning of the deletion conversation
##
def delete(bot, update):
    """Starts the deletion of a portfolio from the database"""
    user_id = update.message.from_user.__dict__['id']
    if not portfolio.get_keyboard(user_id):
        update.message.reply_text(u'You don\'t have any portfolios 😢\nUse /create (portfolio_name).')
        return

    update.message.reply_text(
        '<b>Select the portfolio you would like to delete</b>',
        reply_markup=portfolio.get_keyboard(user_id),
        parse_mode=ParseMode.HTML
    )
    return DELETECONF


def delete_conf(bot, update):
    """Confirms if the user really wants to delete the portfolio."""
    query = update.callback_query
    portfolio.current = query.data

    keyboard = [
        [InlineKeyboardButton("Yes", callback_data="Yes"),
        InlineKeyboardButton("No", callback_data="No")]
    ]

    bot.edit_message_text(
        f"Are you sure you would like to <b>delete</b> {query.data}?",
        chat_id=query.message.chat_id,
        message_id=query.message.message_id,
        parse_mode=ParseMode.HTML
    )
    bot.edit_message_reply_markup(
        chat_id=query.message.chat_id,
        message_id=query.message.message_id,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return DELETEFINAL


def delete_final(bot, update):
    """Final step in the deletion process. Will either complete or abort the deletion process."""
    query = update.callback_query
    user_id = query['message']['chat']['id']

    if query.data == 'Yes' and portfolio.delete(user_id, portfolio.current):
        bot.edit_message_text(
            f'Ok. Your portfolio, {portfolio.current} was deleted.',
            chat_id=query.message.chat_id,
            message_id=query.message.message_id
        )
    else:
        bot.edit_message_text(
            'Ok. Aborted deletion process.',
            chat_id=query.message.chat_id,
            message_id=query.message.message_id
        )
    portfolio.current = ""
    return
##
# End of the deletion conversation
##

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
    dp.add_handler(CommandHandler("news", news, pass_args=True))
    dp.add_handler(CommandHandler("create", create, pass_args=True))
    
    portfolio_conv_handler = ConversationHandler(
        entry_points=[CommandHandler("portfolios", portfolios)],
        states={
        INFO: [CallbackQueryHandler(button)]
        },
        fallbacks=[CommandHandler("portfolios", portfolios)]
    )

    price_conv_handler = ConversationHandler(
        entry_points=[CommandHandler("price", price, pass_args=True)],
        states={
            ADD: [CallbackQueryHandler(add)]
        },
        fallbacks=[CommandHandler("price", price, pass_args=True)]
    )

    deletion_conv_handler = ConversationHandler(
        entry_points=[CommandHandler("delete", delete)],
        states={
            DELETECONF: [CallbackQueryHandler(delete_conf)],
            DELETEFINAL: [CallbackQueryHandler(delete_final)]
        },
        fallbacks=[CommandHandler("delete", delete)]
    )

    # log all errors
    dp.add_error_handler(error)

    # Start the Bot
    updater.dispatcher.add_handler(price_conv_handler)
    updater.dispatcher.add_handler(portfolio_conv_handler)
    updater.dispatcher.add_handler(deletion_conv_handler)
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()

if __name__ == '__main__':
    main()
