#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jun 19 20:56:59 2018

@author: Sofei1
"""

import datetime

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from core.event import Event
from core.portfolio import MarketOnClosePortfolio
from core.strategy import MovingAverageCrossStrategy

def generate_signal_from_strategy(class_name, symbol, bars, **kwargs):
    return class_name(symbol, bars, **kwargs).generate_signals()

def create_portfolio(class_name, symbol, bars, signals, **kwargs):
    return class_name(symbol, bars, signals, **kwargs).backtest_portfolio()

if __name__ == "__main__":
    # Obtain daily bars of AAPL from Yahoo Finance for the period
    symbol = 'AAPL'
    bars = pd.read_csv('data/AAPL.csv')

    # Create a Moving Average Cross Strategy instance with a short moving
    # average window of 100 days and a long window of 200 days
    signals = generate_signal_from_strategy(MovingAverageCrossStrategy, symbol, bars, short_window=100, long_window=200)

    # Create a portfolio of AAPL, with $100,000 initial capital
    returns = create_portfolio(MarketOnClosePortfolio, symbol, bars, signals, initial_capital=100000)

    # Plot two charts to assess trades and equity curve
    fig = plt.figure()
    fig.patch.set_facecolor('white')     # Set the outer colour to white
    ax1 = fig.add_subplot(211,  ylabel='Price in $')

    # Plot the AAPL closing price overlaid with the moving averages
    bars['Close'].plot(ax=ax1, color='r', lw=2.)
    signals[['short_mavg', 'long_mavg']].plot(ax=ax1, lw=2.)

    # Plot the "buy" trades against AAPL
    ax1.plot(signals.ix[signals.positions == 1.0].index,
             signals.short_mavg[signals.positions == 1.0],
             '^', markersize=10, color='m')

    # Plot the "sell" trades against AAPL
    ax1.plot(signals.ix[signals.positions == -1.0].index,
             signals.short_mavg[signals.positions == -1.0],
             'v', markersize=10, color='k')

    # Plot the equity curve in dollars
    ax2 = fig.add_subplot(212, ylabel='Portfolio value in $')
    returns['total'].plot(ax=ax2, lw=2.)

    # Plot the "buy" and "sell" trades against the equity curve
    ax2.plot(returns.ix[signals.positions == 1.0].index,
             returns.total[signals.positions == 1.0],
             '^', markersize=10, color='m')
    ax2.plot(returns.ix[signals.positions == -1.0].index,
             returns.total[signals.positions == -1.0],
             'v', markersize=10, color='k')

    plt.show()
    print(returns.total.tail(10))
