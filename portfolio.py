# This is the portfolio class.

import requests # to use to determine the value of the portfolio
import json

class Portfolio(object):
	def __init__(self, owner, name):
		self.owner = owner
		self.name = name 	# name of the portfolio
		self.shares = {} 	# this is a dictionary where the keys are the tickers, and the 
		self.value = 0

	def get_shares(self):
		"""Returns the stocks that are currently being tracked in the porfolio."""
		return self.shares


	def get_owner(self):
		""""Returns the telegram user that owns the portfolio."""
		return self.owner


	def get_value(self):
		"""Returns the value of the user's portfolio."""
		if len(self.shares) == 0:
			return 0

		tickers, value = '', 0
		for ticker in self.shares.keys():
			tickers += ticker + ','

		raw_data = requests.get(f'https://api.iextrading.com/1.0/stock/market/batch?symbols={tickers}&types=quote')
		data = json.loads(raw_data.text)

		for i in data:
			value += data[i]['quote']['close'] * self.shares[i]

		return value


	def add_share(self, stock, shares=0):
		"""Adds a number of shares to  the user's portfolio."""
		stock = stock.upper()

		if shares == 0:		# the amount of shares cannot be 0
			return False

		# checks if the stock is already in the portfolio
		if stock in list(self.shares.keys()):
			self.shares[stock] += shares
		else:
			self.shares[stock] = shares
		return True
	

	def remove_share(self, stock, shares=None):
		"""Removes a certain amount of shares from the user's portfolio."""
		stock = stock.upper()
		
		if stock in list(self.shares.keys()):
			if shares == None or shares >= self.shares[stock]:
				del self.shares[stock]
			else:
				self.shares[stock] -= shares
			return True
		else:
			return False


	def __str__(self):
		"""For database and testing purposes, this is a representation of the portfolio object."""
		return "{'user':self.owner, 'name':self.name, 'shares':self.shares, 'value':self.value}"