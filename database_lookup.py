import boto3

db = boto3.resource('dynamodb')
table = db.Table('portfolios')

def existance(user_id):
    """Will check if a user_id is already in the database"""

    entry = table.get_item(
        Key={
            'user': user_id
        }
    )

    return 'Item' in entry

def portfolio_existance(user_id, name):
    """Will check if a portfolio name is already present in a user's entry."""

    entry = table.get_item(
        Key={
            'user': user_id
        }
    )

    return name in entry['Item']['portfolios'].keys()