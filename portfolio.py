# Manages all portfolio functions to keep bot.py cleaner

import boto3
import database_lookup as database
db = boto3.resource('dynamodb')
pf = db.Table('portfolios')

def create(user_id, p_name):
    """This function will attempt to create a portfolio for the user.
    Will return True or False based on whether it was dable to do so."""

    ## Check if user already has a portfolio with the same name
    if database.existance(user_id):
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
    
    # Since the 'Item' is not in the potential dictionary, user was not created so do that here.
    else:
        pf.put_item(
            Item={
                'user': user_id,
                'portfolios': {
                    p_name: {
                        'tickers': {},
                        'value': 0
                    }
                }
            }
        )
        
    return True

def view_all(user_id):
    """Returns all portfolio names in a list for the given user."""
    if not database.existance(user_id):
        return None

    else:
        names = pf.get_item(
            Key={
                'user': user_id
            }
        )['Item']['portfolios'].keys()

        return list(names)

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