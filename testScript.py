# This is the test script for functions and classes.
# Muy basic

import portfolio

my_portfolio = portfolio.Portfolio('julien', 'first')
my_portfolio2 = portfolio.Portfolio('vincent', 'second')
my_portfolio.add_share('gddy', 8)
my_portfolio.add_share('googl', 1000)

print(my_portfolio.get_value())
print(my_portfolio2.get_value())

print(my_portfolio2.__dict__)