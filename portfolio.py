# Manages all portfolio functions to keep bot.py cleaner

import boto3, requests, json
import database_lookup as database

db = boto3.resource('dynamodb')
pf = db.Table('portfolios')

def create(user_id, p_name):
    """This function will attempt to create a portfolio for the user.
    Will return True or False based on whether it was dable to do so."""

    ## Check if user already has a portfolio with the same name
    if database.portfolio_existance(user_id, p_name):
        return False
        
    # Otherwise we just update the list of all portfolios for that user here.
    else:
        pf.update_item(
            Key={
                'user': user_id
            },
            UpdateExpression=f"set portfolios.{p_name} = :r",
            ExpressionAttributeValues={
                ':r':{'tickers':{}, 'value':0}
            }
        )

    return True


def delete(user_id, p_name):
    # Check to see if the given database is actually inside the DB
    if not database.portfolio_existance(user_id, p_name):
        return False
    
    # If not, begin deletion...
    else:
        portfolios = view_all(user_id)
        del portfolios[p_name]

        pf.update_item(
            Key={
                'user': user_id
            },
            UpdateExpression=f"set portfolios = :r",
            ExpressionAttributeValues={
                ':r': portfolios
            }
        )

    return True


def update_values(user_id, p_name):
    """Will update the value of the portfolio."""

    portfolio_tickers = view(user_id)['tickers']
    total_value, ticker_strings = 0, ''

    for i in portfolio_tickers.keys():
        ticker_strings += i + ','

    raw_data = requests.get(f'https://api.iextrading.com/1.0/stock/market/batch?symbols={ticker_strings}&types=quote')
    data = json.loads(raw_data.text)

    prices =[]

    for i in data:
        prices.append(i['quote']['latestPrice'])

    for price, amount in zip(prices, ticker_strings.values()):
        total_value += price * amount

    # update the dictionary


def view_all(user_id):
    """Returns all portfolio names in a list for the given user."""

    portfolios = pf.get_item(
        Key={
            'user': user_id
        }
    )['Item']['portfolios']

    return portfolios

def view(user_id, p_name):
    """Returns the information of a specific portfolio. Returns a dictionary."""

    if not database.portfolio_existance(user_id, p_name):
        return None

    else:
        info = pf.get_item(
            Key={
                'user': user_id
            }
        )['Item']['portfolios'][p_name]

    return info # i am a dictionary