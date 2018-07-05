from abc import ABCMeta, abstractmethod
import pandas as pd

class Portfolio(object):
    __metaclass__ = ABCMeta

    @abstractmethod
    def generate_positions(self):
        raise NotImplementedError("Should implement generate_positions()!")

    @abstractmethod
    def backtest_portfolio(self):
        raise NotImplementedError("Should implement backtest_portfolio()!")

class MarketOnClosePortfolio(Portfolio):
    def __init__(self, symbol, bars, signals, initial_capital=100000.0):
        self.symbol = symbol
        self.bars = bars
        self.signals = signals
        self.initial_capital = float(initial_capital)
        self.positions = self.generate_positions()

    def generate_positions(self):
        positions = pd.DataFrame(index=self.signals.index).fillna(0.0)
        positions[self.symbol] = 100*self.signals['signal']   # This strategy buys 100 shares
        return positions

    def backtest_portfolio(self):
        portfolio = self.positions*self.bars['Close']
        pos_diff = self.positions.diff()

        portfolio['holdings'] = (self.positions.iloc[:,0]*self.bars['Close'])
        portfolio['cash'] = self.initial_capital - (pos_diff.iloc[:,0]*self.bars['Close']).cumsum()

        portfolio['total'] = portfolio['cash'] + portfolio['holdings']
        portfolio['returns'] = portfolio['total'].pct_change()
        return portfolio

class MarketIntradayPortfolio(Portfolio):

    def __init__(self, symbol, bars, signals, initial_capital=100000.0):
        self.symbol = symbol
        self.bars = bars
        self.signals = signals
        self.initial_capital = float(initial_capital)
        self.positions = self.generate_positions()

    def generate_positions(self):
        """Generate the positions DataFrame, based on the signals
        provided by the 'signals' DataFrame."""
        positions = pd.DataFrame(index=self.signals.index).fillna(0.0)

        # Long or short 500 shares of SPY based on
        # directional signal every day
        positions[self.symbol] = 500*self.signals['signal']
        return positions

    def backtest_portfolio(self):

        # Set the portfolio object to have the same time period
        # as the positions DataFrame
        portfolio = pd.DataFrame(index=self.positions.index)
        pos_diff = self.positions.diff()

        # Work out the intraday profit of the difference
        # in open and closing prices and then determine
        # the daily profit by longing if an up day is predicted
        # and shorting if a down day is predicted
        portfolio['price_diff'] = self.bars['Close']-self.bars['Open']
        portfolio['price_diff'][0:5] = 0.0
        portfolio['profit'] = self.positions[self.symbol] * portfolio['price_diff']

        # Generate the equity curve and percentage returns
        portfolio['total'] = self.initial_capital + portfolio['profit'].cumsum()
        portfolio['returns'] = portfolio['total'].pct_change()
        return portfolio