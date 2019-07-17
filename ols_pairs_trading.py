import json
import logging
import pandas as pd
import statsmodels.api as sm
import consts
import helper

# return stock-weight pairs that sum to one
def get_portfolio_weights(symbol_pairs, lookback=consts.lookback, set_status=False):
    target_weights = helper.get_current_portfolio_weights()
    delta = False
    current_zscores = {}
    strategy_status = get_current_strategy_status()
    for (x, y) in symbol_pairs:

        query_string = x + ' ' + y
        current_prices = helper.current_prices((x, y))
        x_current = current_prices.loc[:, x].loc[:, 'close']
        y_current = current_prices.loc[:, y].loc[:, 'close']
        prices_up_to_yday = helper.prices_up_to_yesterday((x, y), lookback=lookback).dropna()
        x_up_to_yday = prices_up_to_yday.loc[:, x].loc[:, 'close']
        y_up_to_yday = prices_up_to_yday.loc[:, y].loc[:, 'close']
        try:
            hedge = get_hedge_ratio(y_up_to_yday, x_up_to_yday)
            if hedge < 0:
                logging.error("hedge less than 0!!")
                raise Exception("hedge less than 0!!")
        except ValueError as e:
            logging.error(e)
            return
        spreads = get_spreads((x, y), hedge, lookback=lookback)

        diff = y_current[-1] - hedge * x_current[-1]
        zscore = (diff - spreads.mean()) / spreads.std()
        current_zscores[query_string] = zscore

        if (not x in target_weights) or (not y in target_weights):
            target_weights.loc[:, x] = [0]
            target_weights.loc[:, y] = [0]

        if ((strategy_status[query_string]['inShort'] == 'True') and zscore < 0.0) or (
                (strategy_status[query_string]['inLong'] == 'True') and zscore > 0.0):
            strategy_status[query_string]['inShort'] = 'False'
            strategy_status[query_string]['inLong'] = 'False'
            target_weights[x][0] = 0
            target_weights[y][0] = 0
            delta = True
        if not strategy_status[query_string]['inLong'] == 'True' and zscore < -1:
            y_target_shares = 1
            x_target_shares = -hedge
            strategy_status[query_string]['inShort'] = 'False'
            strategy_status[query_string]['inLong'] = 'True'

            x_target_pct, y_target_pct = get_holding_percentage(x_target_shares, y_target_shares, x_current, y_current)
            x_target_weight = x_target_pct * (1.0 / len(symbol_pairs))
            y_target_weight = y_target_pct * (1.0 / len(symbol_pairs))

            target_weights[x] = x_target_weight.values
            target_weights[y] = y_target_weight.values
            delta = True
        if not strategy_status[query_string]['inShort'] == 'True' and zscore > 1:
            y_target_shares = -1
            x_target_shares = hedge
            strategy_status[query_string]['inShort'] = 'True'
            strategy_status[query_string]['inLong'] = 'False'

            x_target_pct, y_target_pct = get_holding_percentage(x_target_shares, y_target_shares, x_current, y_current)
            x_target_weight = x_target_pct * (1.0 / len(symbol_pairs))
            y_target_weight = y_target_pct * (1.0 / len(symbol_pairs))

            target_weights[x] = x_target_weight.values
            target_weights[y] = y_target_weight.values
            delta = True

    if set_status and delta:
        set_current_strategy_status(strategy_status)
    return target_weights, delta, current_zscores


def get_spreads(symbol_pair, hedge, lookback=consts.lookback, prices=None):
    if symbol_pair in consts.spreads.keys():
        old_spreads = consts.spreads[symbol_pair]
        latest_price = helper.current_prices(symbol_pair)
        if old_spreads.tail(1).index.date != latest_price.tail(1).index.date:
            x_price = latest_price.loc[:, symbol_pair[0]].loc[:, 'close']
            y_price = latest_price.loc[:, symbol_pair[1]].loc[:, 'close']
            new_spread = y_price - hedge * x_price
            new_spreads = old_spreads[1:].append(new_spread)
            consts.spreads[symbol_pair] = new_spreads
            return new_spreads
        else:
            return old_spreads
    else:
        if prices is None:
            prices = helper.prices_up_to_yesterday(symbol_pair, lookback=lookback)
        x_price = prices.loc[:, symbol_pair[0]].loc[:, 'close']
        y_price = prices.loc[:, symbol_pair[1]].loc[:, 'close']
        spreads = y_price - hedge * x_price
        consts.spreads[symbol_pair] = spreads
        return spreads


# OLS:Y=A+BX
def get_hedge_ratio(Y, X, add_const=True):
    if add_const:
        new_X = sm.add_constant(X)
        model = sm.OLS(Y, new_X).fit()

        return model.params[1]
    model = sm.OLS(Y, X).fit()
    return model.params.values


def get_holding_percentage(xShares, yShares, xPrice, yPrice):
    xdol = xShares * xPrice;
    ydol = yShares * yPrice;
    total = abs(xdol) + abs(ydol)
    return (xdol / total), (ydol / total)


def build_orders(cash=5000):
    weights, delta, _ = get_portfolio_weights(consts.pairs)
    if not delta:
        return []
    target_num_shares = helper.get_share_numbers(cash,
                                                 weights)  # BECAUSE ONLY PASSING IN 5000, TARGET NUMBER OF SHARES MUST BE PROPORTIONAL
    cur_positions = helper.get_current_portfolio_positions()
    order_df = pd.DataFrame()
    orders = []
    for column in target_num_shares.columns:
        if column not in cur_positions.columns:
            order_df.loc[:, column] = [target_num_shares.loc[:, column][0]]
        else:
            order_df.loc[:, column] = [target_num_shares.loc[:, column][0] - cur_positions.loc[:, column][0]]

    for column in order_df.columns:
        rounded = round(order_df.loc[:, column].loc[0])
        if (rounded == 0) and ( order_df.loc[:, column].loc[0] >= 0.2):
            logging.error("rounded to 0!")
            raise Exception('rounded to 0!')
        order_df.loc[:, column].loc[0] = rounded

    for column in order_df.columns:
        num = order_df.loc[:, column][0]
        if num==0:
            continue
        if num < 0:
            orders.append({
                'symbol': column,
                'qty': -num,
                'side': 'sell'
            })
        else:
            orders.append({
                'symbol': column,
                'qty': num,
                'side': 'buy'
            })

    return orders


def set_current_strategy_status(data):
    with open('ols_pairs_trading.json', 'w+') as outfile:
        json.dump(data, outfile)


def get_current_strategy_status():
    with open('ols_pairs_trading.json') as file:
        data = json.load(file)
        return data
