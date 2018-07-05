#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jul  5 19:47:54 2018

@author: Sofei1
"""

import datetime

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import sklearn

from pandas_datareader import data

from core.portfolio import MarketIntradayPortfolio
from core.strategy import ForecastingStrategy


if __name__ == "__main__":
    start_test = datetime.datetime(2017,1,1)
    end_period = datetime.datetime(2017,12,31)

    # Obtain the bars for SPY ETF which tracks the S&P500 index
    bars = data.DataReader("SPY", "yahoo", start_test, end_period)

    # Create the S&P500 forecasting strategy
    snpf = ForecastingStrategy("^GSPC", bars)
    signals = snpf.generate_signals()

    # Create the portfolio based on the forecaster
    portfolio = MarketIntradayPortfolio("SPY", bars, signals, initial_capital=100000.0)
    returns = portfolio.backtest_portfolio()

    # Plot results
    fig = plt.figure()
    fig.patch.set_facecolor('white')

    # Plot the price of the SPY ETF
    ax1 = fig.add_subplot(211,  ylabel='SPY ETF price in $')
    bars['Close'].plot(ax=ax1, color='r', lw=2.)

    # Plot the equity curve
    ax2 = fig.add_subplot(212, ylabel='Portfolio value in $')
    returns['total'].plot(ax=ax2, lw=2.)

    plt.show()
