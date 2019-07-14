import helper
import logging
import consts
import pandas as pd
import numpy as np
import statsmodels.api as sm
import matplotlib.pyplot as plt
import tests
#return stock-weight pairs that sum to one

def get_portfolio_weights(symbol_pairs, lookback = consts.lookback):
    target_weights = helper.get_current_portfolio_weights()
    for (x,y) in symbol_pairs:
        current_prices = helper.current_prices((x,y))
        x_current = current_prices.loc[:, x].loc[:, 'close']
        y_current = current_prices.loc[:, y].loc[:, 'close']
        prices_up_to_yday = helper.prices_up_to_yesterday((x,y),lookback=lookback).dropna()
        x_up_to_yday = prices_up_to_yday.loc[:,x].loc[:,'close']
        y_up_to_yday = prices_up_to_yday.loc[:,y].loc[:,'close']
        try:
            hedge = get_hedge_ratio(y_up_to_yday,x_up_to_yday)
            if hedge < 0:
                logging.error("hedge less than 0!!")
                raise Exception("hedge less than 0!!")
        except ValueError as e:
            logging.error(e)
            return
        spreads = get_spreads((x,y), hedge, lookback=lookback)

        diff = y_current[-1] - hedge * x_current[-1]
        spread_mean = spreads.mean()
        spread_std = spreads.std()
        zscore = ( diff - spreads.mean()) / spreads.std()


        if(not x in target_weights) or (not y in target_weights):
            target_weights.loc[:,x] = [0]
            target_weights.loc[:,y] = [0]

        if (consts.ols_pairs_in_short.get((x,y)) and zscore < 0.0)or (consts.ols_pairs_in_long.get((x,y)) and zscore > 0.0):

            logging.log(0,"Exiting positions of "+ x + " and "+ y)
            consts.ols_pairs_in_long[(x,y)]=False
            consts.ols_pairs_in_short[(x,y)] = False
            x_target_weight=0
            y_target_weight=0
            target_weights[x] = x_target_weight.values
            target_weights[y] = y_target_weight.values

        if not consts.ols_pairs_in_long.get((x,y)) and zscore < -1:
            y_target_shares = 1
            x_target_shares = -hedge
            consts.ols_pairs_in_long[(x,y)] = True
            consts.ols_pairs_in_short[(x,y)] = False

            x_target_pct, y_target_pct = get_holding_percentage(x_target_shares, y_target_shares, x_current, y_current)
            x_target_weight = x_target_pct * (1.0 / len(symbol_pairs))
            y_target_weight = y_target_pct * (1.0 / len(symbol_pairs))

            target_weights[x] = x_target_weight.values
            target_weights[y] = y_target_weight.values

        if not consts.ols_pairs_in_short.get((x,y)) and zscore >1:
            y_target_shares = -1
            x_target_shares = hedge
            consts.ols_pairs_in_long[(x,y)] = False
            consts.ols_pairs_in_short[(x,y)] = True
            logging.log(0, "" + x + " target shares:" + str(x_target_shares) + "; " + y + " target shares:" + str(
                y_target_shares))

            x_target_pct, y_target_pct = get_holding_percentage(x_target_shares, y_target_shares, x_current, y_current)
            x_target_weight = x_target_pct * (1.0 / len(symbol_pairs))
            y_target_weight = y_target_pct * (1.0 / len(symbol_pairs))

            target_weights[x] = x_target_weight.values
            target_weights[y] = y_target_weight.values




    return target_weights
    pass


def get_spreads(symbol_pair, hedge, lookback = consts.lookback, prices=None):
    if symbol_pair in consts.spreads.keys():
        old_spreads = consts.spreads[symbol_pair]
        latest_price = helper.current_prices(symbol_pair)
        if old_spreads.tail(1).index.date !=latest_price.tail(1).index.date:
            x_price = latest_price.loc[:,symbol_pair[0]].loc[:,'close']
            y_price = latest_price.loc[:,symbol_pair[1]].loc[:,'close']
            new_spread = y_price-hedge*x_price
            new_spreads = old_spreads[1:].append(new_spread)
            consts.spreads[symbol_pair] = new_spreads
            return new_spreads
        else:
            return old_spreads
    else:
        if prices is None:
            prices = helper.prices_up_to_yesterday(symbol_pair,lookback=lookback)
        x_price = prices.loc[:, symbol_pair[0]].loc[:, 'close']
        y_price = prices.loc[:, symbol_pair[1]].loc[:, 'close']
        spreads = y_price - hedge * x_price
        """
                for i in range(len(prices)):
            index=-len(prices)+i
            spread = y_price[index] - hedge * x_price[index]
            spreads.append(spread)
        """

        consts.spreads[symbol_pair] = spreads
        return spreads
#OLS:Y=A+BX

def get_hedge_ratio(Y,X,add_const=True):
    if add_const:
        new_X=sm.add_constant(X)
        model = sm.OLS(Y,new_X).fit()

        return model.params[1]
    model = sm.OLS(Y,X).fit()
    return model.params.values
    pass

def get_holding_percentage(xShares, yShares, xPrice, yPrice):
    xdol = xShares * xPrice;
    ydol = yShares * yPrice;
    total = abs(xdol) + abs(ydol)
    return (xdol/total), (ydol/total)