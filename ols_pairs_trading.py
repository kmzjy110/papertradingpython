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
        current_prices = helper.current_prices(symbol_pairs)
        x_current= current_prices.loc[:, x].loc[:, 'close']
        y_current = current_prices.loc[:, y].loc[:, 'close']
        try:
            hedge = get_hedge_ratio(y_current,x_current)
        except ValueError as e:
            logging.error(e)
            return
        target_weights = helper.get_current_portfolio_weights()
        spreads = get_spreads((x,y), hedge, lookback)
        zscore = (spreads[-1] - spreads.mean()) / spreads.std()

        if (consts.inShort.get(symbol_pairs) and zscore<0.0 )or (consts.inLong.get(symbol_pairs) and zscore >0.0):
            target_weights.loc[x]=0
            target_weights.loc[y] = 0
            logging.log("Exiting positions of "+ symbol_pairs[0] + " and "+ symbol_pairs[1])
            consts.inLong[symbol_pairs]=False
            consts.inShort[symbol_pairs] = False
            return target_weights
        if not consts.inLong.get(symbol_pairs) and zscore < -1:
            y_target_shares = 1
            x_target_shares = -hedge
            consts.inLong[symbol_pairs] = True
            consts.inShort[symbol_pairs] = False
        if not consts.inShort.get(symbol_pairs) and zscore >1:
            y_target_shares = -1
            x_target_shares = hedge
            consts.inLong[symbol_pairs] = False
            consts.inShort[symbol_pairs] = True
        x_target_pct, y_target_pct = get_holding_percentage(x_target_shares,y_target_shares,x_current,y_current)
        target_weights.loc[x] = x_target_pct * (1.0/len(symbol_pairs))
        target_weights.loc[y] = y_target_pct * (1.0/len(symbol_pairs))
        return target_weights
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

def get_holding_percentage(xShares, yShares, xPrice, yPrice):
    xdol = xShares * xPrice;
    ydol = yShares * yPrice;
    total = abs(xdol) + abs(ydol)
    return (xdol/total), (ydol/total)