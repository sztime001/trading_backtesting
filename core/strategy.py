import datetime
from abc import ABCMeta, abstractmethod

import numpy as np
import pandas as pd
from pandas_datareader import data, wb
from sklearn.discriminant_analysis import QuadraticDiscriminantAnalysis as QDA


class Strategy(object):
    __metaclass__ = ABCMeta

    @abstractmethod
    def generate_signals(self):
        raise NotImplementedError("Should implement generate_signals()!")

class MovingAverageCrossStrategy(Strategy):
    def __init__(self, symbol, bars, short_window=100, long_window=400):
        self.symbol = symbol
        self.bars = bars

        self.short_window = short_window
        self.long_window = long_window

    def generate_signals(self):
        signals = pd.DataFrame(index=self.bars.index)
        signals['signal'] = 0.0

        # Create the set of short and long simple moving averages over the
        # respective periods
        signals['short_mavg'] = self.bars['Close'].rolling(self.short_window).mean()
        signals['long_mavg'] = self.bars['Close'].rolling(self.long_window).mean()

        # Create a 'signal' (invested or not invested) when the short moving average crosses the long
        # moving average, but only for the period greater than the shortest moving average window
        signals['signal'][self.short_window:] = np.where(signals['short_mavg'][self.short_window:]
            > signals['long_mavg'][self.short_window:], 1.0, 0.0)

        # Take the difference of the signals in order to generate actual trading orders
        signals['positions'] = signals['signal'].diff()
        return signals

class ForecastingStrategy(Strategy):
    def __init__(self, symbol, bars):
        self.symbol = symbol
        self.bars = bars
        self.create_periods()
        self.fit_model()

    def create_periods(self):
        self.start_train = datetime.datetime(2001,1,10)
        self.start_test = datetime.datetime(2005,1,1)
        self.end_period = datetime.datetime(2005,12,31)

    def create_lagged_series(self, symbol, start_date, end_date, lags=5):
        # Obtain stock information from Yahoo Finance
        ts = data.DataReader(symbol, "yahoo", start_date-datetime.timedelta(days=365), end_date)

        # Create the new lagged DataFrame
        tslag = pd.DataFrame(index=ts.index)
        tslag["Today"] = ts["Adj Close"]
        tslag["Volume"] = ts["Volume"]

        # Create the shifted lag series of prior trading period close values
        for i in range(0,lags):
            tslag["Lag%s" % str(i+1)] = ts["Adj Close"].shift(i+1)

        # Create the returns DataFrame
        tsret = pd.DataFrame(index=tslag.index)
        tsret["Volume"] = tslag["Volume"]
        tsret["Today"] = tslag["Today"].pct_change()*100.0

        # If any of the values of percentage returns equal zero, set them to
        # a small number (stops issues with QDA model in scikit-learn)
        for i,x in enumerate(tsret["Today"]):
            if (abs(x) < 0.0001):
                tsret["Today"][i] = 0.0001

        # Create the lagged percentage returns columns
        for i in range(0,lags):
            tsret["Lag%s" % str(i+1)] = tslag["Lag%s" % str(i+1)].pct_change()*100.0

        # Create the "Direction" column (+1 or -1) indicating an up/down day
        tsret["Direction"] = np.sign(tsret["Today"])
        tsret = tsret[tsret.index >= start_date]

        return tsret

    def fit_model(self):
        # Create a lagged series of the S&P500 US stock market index
        snpret = self.create_lagged_series(self.symbol, self.start_train,
                                      self.end_period, lags=5)

        # Use the prior two days of returns as
        # predictor values, with direction as the response
        X = snpret[["Lag1","Lag2"]]
        y = snpret["Direction"]

        # Create training and test sets
        X_train = X[X.index < self.start_test]
        y_train = y[y.index < self.start_test]

        # Create the predicting factors for use
        # in direction forecasting
        self.predictors = X[X.index >= self.start_test]

        # Create the Quadratic Discriminant Analysis model
        # and the forecasting strategy
        self.model = QDA()
        self.model.fit(X_train, y_train)

    def generate_signals(self):
        signals = pd.DataFrame(index=self.bars.index)
        signals['signal'] = 0.0

        #print(len(signals))
        #print(len(self.model.predict(self.predictors)))
        # Predict the subsequent period with the QDA model
        signals['signal'] = self.model.predict(self.predictors)[1:]

        # Remove the first five signal entries to eliminate
        # NaN issues with the signals DataFrame
        signals['signal'][0:5] = 0.0
        signals['positions'] = signals['signal'].diff()

        return signals
