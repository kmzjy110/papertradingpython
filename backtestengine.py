import ols_pairs_trading
import consts
import backtestapi
import pandas as pd
import alpaca_trade_api as alpaca_api
import backtesthelper
import numpy as np
import matplotlib.pyplot as plt
class BacktestEngine:
    #for running the
    def __init__(self):
        self.start_date = pd.Timestamp(2019, 1, 1)
        self.end_date = pd.Timestamp(2019, 7, 16)
        # current_time = pd.Timestamp(2019, 5, 28)
        self.current_time = pd.Timestamp(2019, 1, 1)
        self.timeframe = 'day'
        self.cash=5000

        self.backtest_orders_filename = "backtest_orders.csv"
        self.backtest_positions_filename = "backtest_positions.csv"
        self.backtest_positions_hist_filename = "backtest_positions_hist.csv"
        self.backtest_account_filename = "backtest_account.csv"
        self.backtest_account_hist_filename = "backtest_account_hist.csv"

        self.helper=None
        self.backtest_api=None
        self.algo=None
        max_lookback = consts.lookback
        start = (self.start_date.replace(second=0,
                                                                                           microsecond=0).isoformat()[
                 :consts.iso_format_string_adjust]) + 'Z'
        # subtracted 3 more days to allow lastday price generalized to mondays

        end = ((self.end_date+pd.Timedelta("1 day")).replace(second=0, microsecond=0).isoformat()[:consts.iso_format_string_adjust]) + 'Z'
        self.spy_prices = aggregate_prices = consts.alpaca_api.get_barset('SPY', self.timeframe, limit=1000, start=start,end=end).df





        pass
    def do_backtest(self):
        symbols_involved = consts.columns
        max_lookback = consts.lookback
        start = ((self.start_date - pd.Timedelta(str(max_lookback + 3) + ' days')).replace(second=0,
                                                                                           microsecond=0).isoformat()[
                 :consts.iso_format_string_adjust]) + 'Z'
        # subtracted 3 more days to allow lastday price generalized to mondays

        end = (self.end_date.replace(second=0, microsecond=0).isoformat()[:consts.iso_format_string_adjust]) + 'Z'

        aggregate_prices = consts.alpaca_api.get_barset(symbols_involved, self.timeframe, limit=1000, start=start,
                                                        end=end)

        aggregate_assets = {}
        for symbol in symbols_involved:
            aggregate_assets[symbol] = consts.alpaca_api.get_asset(symbol)

        self.helper = backtesthelper.BacktestHelper(self.current_time, self.start_date, self.end_date, 5000,
                                                    aggregate_prices, timeframe='day', init_files=False,
                                                    backtest_orders_filename=self.backtest_orders_filename,
                                                    backtest_positions_filename=self.backtest_positions_filename,
                                                    backtest_positions_hist_filename=self.backtest_positions_hist_filename,
                                                    backtest_account_filename=self.backtest_account_filename,
                                                    backtest_account_hist_filename=self.backtest_account_hist_filename)
        self.backtest_api = backtestapi.BacktestAPI(self.current_time, self.start_date, self.end_date, symbols_involved,
                                                    consts.alpaca_api, self.helper, aggregate_prices, aggregate_assets,
                                                    timeframe=self.timeframe)

        self.algo = ols_pairs_trading.OLSPairsTradingAlgo(consts.pairs, consts.columns, 200, set_status=False,
                                                          status_file_name="ols_pairs_backtest.json",
                                                          api=self.backtest_api, recreate_strategy_file=False)



        while self.current_time!=self.end_date:
            print(self.current_time)
            orders=self.algo.build_orders(self.cash)
            self.algo.trade(orders)
            self.increment_time_and_update()

    def analyze_backtest(self):
        parse_dates=['time']
        account_data=pd.read_csv(self.backtest_account_hist_filename, parse_dates=parse_dates)
        account_data.set_index('time',inplace=True)
        account_data=account_data.resample('D').last()
        self.calculate_beta(account_data)

        orders_parsed_dates = ['submitted_at']
        orders = pd.read_csv(self.backtest_orders_filename, parse_dates=orders_parsed_dates)
        orders.set_index('submitted_at', inplace=True)
        print('a')


    def calculate_turnover_rate(self, orders, account_data):
        pass



    def calculate_beta(self, account_data):
        mult_returns = account_data.portfolio_value.pct_change()[1:]
        mult_returns.index = mult_returns.index.tz_localize('America/New_York')


        spy_close = self.spy_prices.loc[:, 'SPY'].loc[:, 'close']
        spy_mult_returns = spy_close.pct_change()[1:]
        spy_mult_returns = spy_mult_returns.resample('D').last()
        joined_vals = pd.concat([mult_returns, spy_mult_returns], axis=1).dropna()

        mult_returns = joined_vals.loc[:, 'portfolio_value']
        spy_mult_returns = joined_vals.loc[:, 'close']

        covs = joined_vals.rolling(30).cov().reset_index().set_index('time')
        covs = covs.loc[(covs.level_1 == 'portfolio_value')][29:].loc[:, 'close']
        spy_vars = spy_mult_returns.rolling(30).var()[29:]
        rolling_betas = covs / spy_vars
        plt.plot(rolling_betas)
        plt.show()

        norm_returns = account_data.portfolio_value/self.cash
        spy_norm_returns = spy_close/spy_close[0]
        plt.plot(norm_returns)
        plt.plot(spy_norm_returns)
        plt.legend(["portfolio value", "spy"])
        plt.show()





    #calc beta to SPY (6 month rolling beta)
    #calc sector exposure (rolling 63 day avg) TODO FEATURE
    #calc style exposure TODO FEATURE
    #calc rolling turnover rate (63day avg)
    #calc position concentration (The percentage of the algorithm's portfolio invested in its most-concentrated asset)
    #calc net dollar exposure (End-of-day net dollar exposure. A measure of the difference between the algorithm's long positions and short positions.)

    # calc return
    # common return vs specific return (hard to find data)
    #sharpe (6-month rolling)
    # calc max draw-down (The largest peak-to-trough drop in the portfolio's history.)
    #calc volatility (std of portfolio's returns)


    def test(self):

        orders=[]
        orders.append({
            'symbol':'AAPL',
            'qty':5,
            'side':'sell'
        })
        orders.append({
            'symbol':'CRM',
            'qty': 10,
            'side':'buy'
        })
        orders.append({
            'symbol':'AAPL',
            'qty':4,
            'side': 'buy'
        })
        orders.append({
            'symbol': 'AAPL',
            'qty': 1,
            'side': 'buy'
        })
        orders.append({
            'symbol': 'CRM',
            'qty': 10,
            'side': 'sell'
        })
        i=0
        self.backtest_api.submit_order(
            symbol=orders[i]['symbol'],
            qty=orders[i]['qty'],
            side=orders[i]['side'],
            type='market',
            time_in_force='day'
        )
        self.increment_time_and_update()
        print("0")
        """  for i in range(len(orders)):
            current_time = current_time + pd.Timedelta(str(i)+"days")
            self.helper.current_time=current_time
            self.backtest_api.current_time=current_time
            self.backtest_api.submit_order(
                symbol=orders[i]['symbol'],
                qty=orders[i]['qty'],
                side=orders[i]['side'],
                type='market',
                time_in_force='day'
            )"""

    def increment_time_and_update(self):
        self.current_time = self.current_time+ pd.Timedelta("1 " + self.timeframe)
        self.helper.current_time=self.current_time
        self.backtest_api.current_time = self.current_time
        self.helper.update_positions()
        self.helper.update_account(0)
