import ols_pairs_trading
import consts
import backtestapi
import pandas as pd
import alpaca_trade_api as alpaca_api
import backtesthelper
class BacktestEngine:
    #for running the
    def __init__(self):
        start_date = pd.Timestamp(2019, 5, 18)
        end_date = pd.Timestamp(2019, 7, 16)
        # current_time = pd.Timestamp(2019, 5, 28)
        self.current_time = pd.Timestamp(2019, 5, 26)
        self.timeframe = 'day'
        symbols_involved = consts.columns
        max_lookback = consts.lookback
        start = ((start_date - pd.Timedelta(str(max_lookback + 3) + ' days')).replace(second=0,
                                                                                      microsecond=0).isoformat()[
                 :consts.iso_format_string_adjust]) + 'Z'
        # subtracted 3 more days to allow lastday price generalized to mondays

        end = (end_date.replace(second=0, microsecond=0).isoformat()[:consts.iso_format_string_adjust]) + 'Z'
        aggregate_prices = consts.alpaca_api.get_barset(symbols_involved, self.timeframe, limit=1000, start=start, end=end)
        aggregate_assets = {}
        for symbol in symbols_involved:
            aggregate_assets[symbol] = consts.alpaca_api.get_asset(symbol)
        self.helper = backtesthelper.BacktestHelper(self.current_time, start_date, end_date, 5000, aggregate_prices)
        self.backtest_api = backtestapi.BacktestAPI(self.current_time, start_date, end_date, symbols_involved,
                                                    consts.alpaca_api, self.helper, aggregate_prices, aggregate_assets, timeframe=self.timeframe)
        pass

    def do_backtest(self):
        algo = ols_pairs_trading.OLSPairsTradingAlgo(consts.pairs, consts.columns, 200, True, "ols_pairs_backtest.json",self.backtest_api)
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
        for i in range(len(orders)):
            current_time = current_time + pd.Timedelta(str(i)+"days")
            self.helper.current_time=current_time
            self.backtest_api.current_time=current_time
            self.backtest_api.submit_order(
                symbol=orders[i]['symbol'],
                qty=orders[i]['qty'],
                side=orders[i]['side'],
                type='market',
                time_in_force='day'
            )

    def increment_time_and_update(self):
        self.current_time = self.current_time+ pd.Timedelta("1 " + self.timeframe)
        self.helper.current_time=self.current_time
        self.backtest_api.current_time = self.current_time
        self.helper.update_positions()
        self.helper.update_account(0)
