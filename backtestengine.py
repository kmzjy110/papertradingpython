import ols_pairs_trading
import consts
import backtestapi
import pandas as pd
import alpaca_trade_api as tradeapi
import backtesthelper
class BacktestEngine:
    #for running the
    def __init__(self):
        pass

    def do_backtest(self):
        #TODO:need to update position daily omg
        start_day = pd.Timestamp(2019, 5, 18)
        end_day = pd.Timestamp(2019, 7, 16)

        current_time = pd.Timestamp(2019, 5, 22)

        helper = backtesthelper.BacktestHelper(current_time,start_day,end_day,5000)
        backtest_api = backtestapi.BacktestAPI(current_time,start_day,end_day,consts.columns, consts.alpaca_api, helper)
        algo = ols_pairs_trading.OLSPairsTradingAlgo(consts.pairs, consts.columns, 200,True,"ols_pairs_backtest.json",backtest_api)
        orders = algo.build_orders(5000)
        algo.trade(orders)
