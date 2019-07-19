import json
import logging
import pandas as pd
import statsmodels.api as sm
import consts
import helper
import os
# return stock-weight pairs that sum to one
#TODO:REFACTOR INTO A CLASS
class OLSPairsTradingAlgo:
    def __init__(self, symbol_pairs, symbols,lookback, set_status, status_file_name, api):
        self.symbol_pairs = symbol_pairs
        self.lookback = lookback
        self.set_status=set_status
        self.status_file_name = status_file_name
        self.api=api
        self.symbols = symbols
        self.initiate_strategy_status(checkfile=False)

        self.helper = helper.Helper(self.api,self.symbols,lookback, self.get_current_strategy_status())


    def get_portfolio_weights(self):
        target_weights = self.helper.get_current_portfolio_weights()
        delta = False
        current_zscores = {}
        strategy_status = self.get_current_strategy_status() #todo: move set status to somewhere else (refactor with trading?)
        for (x, y) in self.symbol_pairs:
    
            query_string = x + ' ' + y
            current_prices = self.helper.current_prices((x, y))
            x_current = current_prices.loc[:, x].loc[:, 'close']
            y_current = current_prices.loc[:, y].loc[:, 'close']
            prices_up_to_yday = self.helper.prices_up_to_yesterday((x, y), lookback=self.lookback).dropna()
            x_up_to_yday = prices_up_to_yday.loc[:, x].loc[:, 'close']
            y_up_to_yday = prices_up_to_yday.loc[:, y].loc[:, 'close']
            try:
                hedge = self.get_hedge_ratio(y_up_to_yday, x_up_to_yday)
                if hedge < 0:
                    logging.error("hedge less than 0!!")
                    raise Exception("hedge less than 0!!")
            except ValueError as e:
                logging.error(e)
                return
            spreads = self.get_spreads((x, y), hedge, prices=prices_up_to_yday) #todo: write spreads to a file??
    
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
                target_weights.loc[:, x] = [0]
                target_weights.loc[:, y] = [0]
                delta = True
            if not strategy_status[query_string]['inLong'] == 'True' and zscore < -1:
                y_target_shares = 1
                x_target_shares = -hedge
                strategy_status[query_string]['inShort'] = 'False'
                strategy_status[query_string]['inLong'] = 'True'
    
                x_target_pct, y_target_pct = self.get_holding_percentage(x_target_shares, y_target_shares, x_current, y_current)
                x_target_weight = x_target_pct * (1.0 / len(self.symbol_pairs))
                y_target_weight = y_target_pct * (1.0 / len(self.symbol_pairs))
    
                target_weights[x] = x_target_weight.values
                target_weights[y] = y_target_weight.values
                delta = True
            if not strategy_status[query_string]['inShort'] == 'True' and zscore > 1:
                y_target_shares = -1
                x_target_shares = hedge
                strategy_status[query_string]['inShort'] = 'True'
                strategy_status[query_string]['inLong'] = 'False'
    
                x_target_pct, y_target_pct = self.get_holding_percentage(x_target_shares, y_target_shares, x_current, y_current)
                x_target_weight = x_target_pct * (1.0 / len(self.symbol_pairs))
                y_target_weight = y_target_pct * (1.0 / len(self.symbol_pairs))
    
                target_weights[x] = x_target_weight.values
                target_weights[y] = y_target_weight.values
                delta = True
    
        if self.set_status and delta:
            self.set_current_strategy_status(strategy_status)
        return target_weights, delta, current_zscores
    
    
    def get_spreads(self, symbol_pair, hedge, prices=None):
        #TODO:URGENT FIX:SPREAD DATES INCONSISTENCY
        if prices is None:
            prices = self.helper.prices_up_to_yesterday(symbol_pair, lookback=self.lookback)
        x_price = prices.loc[:, symbol_pair[0]].loc[:, 'close']
        y_price = prices.loc[:, symbol_pair[1]].loc[:, 'close']
        spreads = y_price - hedge * x_price
        consts.spreads[symbol_pair] = spreads
        return spreads

    """ if symbol_pair in consts.spreads.keys():
                old_spreads = consts.spreads[symbol_pair]
                latest_price = self.helper.current_prices(symbol_pair)
                if old_spreads.tail(1).index.date != latest_price.tail(1).index.date:
                    x_price = latest_price.loc[:, symbol_pair[0]].loc[:, 'close']
                    y_price = latest_price.loc[:, symbol_pair[1]].loc[:, 'close']
                    new_spread = y_price - hedge * x_price
                    new_spreads = old_spreads[1:].append(new_spread)
                    consts.spreads[symbol_pair] = new_spreads
                    return new_spreads
                else:
                    return old_spreads
            else:"""
    
    
    # OLS:Y=A+BX
    def get_hedge_ratio(self,Y, X, add_const=True):
        if add_const:
            new_X = sm.add_constant(X)
            model = sm.OLS(Y, new_X).fit()
    
            return model.params[1]
        model = sm.OLS(Y, X).fit()
        return model.params.values
    
    
    def get_holding_percentage(self, xShares, yShares, xPrice, yPrice):
        xdol = xShares * xPrice
        ydol = yShares * yPrice
        total = abs(xdol) + abs(ydol)
        return (xdol / total), (ydol / total)
    
    
    def build_orders(self,cash=5000):
        weights, delta, _ = self.get_portfolio_weights()
        print(_)
        if not delta:
            print("no delta")
            return []
        target_num_shares = self.helper.get_share_numbers(cash,
                                                     weights)  # BECAUSE ONLY PASSING IN 5000, TARGET NUMBER OF SHARES MUST BE PROPORTIONAL
        cur_positions = self.helper.get_current_portfolio_positions()
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
    def trade(self, orders, wait=0):
        self.helper.trade(orders, wait)

    def set_current_strategy_status(self,data):
        with open(self.status_file_name, 'w+') as outfile:
            json.dump(data, outfile)

    def initiate_strategy_status(self, checkfile=True):
        if checkfile:
            if os.path.isfile(self.status_file_name):
                return
        status={}
        for pair in self.symbol_pairs:
            query_string = pair[0]+' '+pair[1]
            status[query_string]={}
            status[query_string]["inShort"]="False"
            status[query_string]["inLong"] = "False"
        status["REMAINING_CASH"] = 0
        self.set_current_strategy_status(status)

    def get_current_strategy_status(self):
        with open(self.status_file_name) as file:
            data = json.load(file)
            return data
