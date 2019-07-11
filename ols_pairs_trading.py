import helper
import logging
import consts
import pandas as pd
import numpy as np

#return stock-weight pairs that sum to one
def get_target_portfolio_weights():
    pass

def get_positions(symbol_pairs, lookback = consts.lookback):
    for x,y in symbol_pairs:
        x_close = helper.prices_up_to_yesterday(x,lookback).loc[:, x].loc[:, 'close']
        y_close = helper.prices_up_to_yesterday(y,lookback).loc[:, y].loc[:, 'close']
        try:
            hedge = get_hedge_ratio(y_close,x_close)
        except ValueError as e:
            logging.error(e)
            return
        target_weights = helper.get_current_portfolio_weights()
        spreads = get_spreads((x,y), hedge)
        zscore = (spreads[-1] - spreads.mean()) / spreads.std()
        
    pass

def get_spreads(symbol_pair, hedge, lookback = consts.lookback):
    if symbol_pair in consts.spreads.keys():
        old_spreads = consts.spreads[symbol_pair]
        latest_price = helper.current_prices(symbol_pair)
        x_price = latest_price.loc[:,symbol_pair[0]]
        y_price = latest_price.loc[:,symbol_pair[1]]
        new_spread = y_price-hedge*x_price;
        new_spreads = old_spreads[1:].append(new_spread)
        return new_spreads
    else:
        now = consts.api.get_clock().timestamp
        spreads = []
        for i in range(lookback):
            end_dt = now - pd.Timedelta(str(lookback) + ' days') + pd.Timedelta(str(i) + ' days')
            prices = helper.get_prices(symbol_pair,end_dt,lookback=lookback)
            x_price = prices.loc[:, symbol_pair[0]].loc[:,'close']
            y_price = prices.loc[:, symbol_pair[1]].loc[:,'close']
            hedge = get_hedge_ratio(y_price,x_price)
            spread = y_price[-1] - hedge * x_price[-1]
            spreads.append(spread)
        consts.spreads[symbol_pair] = np.array(spreads)
        return spreads
#OLS:Y=A+BX

def get_hedge_ratio(Y,X,add_const=True):

    pass