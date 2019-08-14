import matplotlib.pyplot as plt
import pandas as pd

import backtestapi
import backtesthelper
import consts
import ols_pairs_trading


class BacktestEngine:
    # for running the
    def __init__(self):
        self.start_date = pd.Timestamp(2019, 1, 1)
        self.end_date = pd.Timestamp(2019, 7, 16)
        # current_time = pd.Timestamp(2019, 5, 28)
        self.current_time = pd.Timestamp(2019, 1, 1)
        self.timeframe = 'day'
        self.cash = 5000

        self.backtest_orders_filename = "backtest_orders.csv"
        self.backtest_positions_filename = "backtest_positions.csv"
        self.backtest_positions_hist_filename = "backtest_positions_hist.csv"
        self.backtest_account_filename = "backtest_account.csv"
        self.backtest_account_hist_filename = "backtest_account_hist.csv"

        self.helper = None
        self.backtest_api = None
        self.algo = None
        max_lookback = consts.lookback
        start = (self.start_date.replace(second=0,
                                         microsecond=0).isoformat()[
                 :consts.iso_format_string_adjust]) + 'Z'
        # subtracted 3 more days to allow lastday price generalized to mondays

        end = ((self.end_date + pd.Timedelta("1 day")).replace(second=0, microsecond=0).isoformat()[
               :consts.iso_format_string_adjust]) + 'Z'
        self.spy_prices = consts.alpaca_api.get_barset('SPY', self.timeframe, limit=1000, start=start, end=end).df

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

        while self.current_time != self.end_date:
            print(self.current_time)
            orders = self.algo.build_orders(self.cash)
            self.algo.trade(orders)
            self.increment_time_and_update()

    def analyze_backtest(self):
        parse_dates = ['time']
        account_data = pd.read_csv(self.backtest_account_hist_filename, parse_dates=parse_dates)
        account_data.set_index('time', inplace=True)
        account_data = account_data.resample('D').last()

        orders_parsed_dates = ['submitted_at']
        orders = pd.read_csv(self.backtest_orders_filename, parse_dates=orders_parsed_dates)
        orders.set_index('submitted_at', inplace=True)

        positions = pd.read_csv(self.backtest_positions_hist_filename, parse_dates=parse_dates)

        positions.set_index('time', inplace=True)
        # self.calculate_beta(account_data)
        # self.calculate_turnover_rate(orders,account_data,30)
        # self.calc_position_concentration(positions,account_data)

        # self.calc_net_dollar_exposure(account_data)

        # self.calc_returns(account_data)
        # self.calc_max_drawdown(account_data)
        #self.calc_volatility(account_data, 30)
        self.calc_sharpe_ratio(account_data, 60)
        print('a')

    def calc_sharpe_ratio(self, account_data, rolling_window):
        account_data = account_data.portfolio_value
        account_data.index = account_data.index.tz_localize('America/New_York') #TODO:MOVE LOCALIZE
        spy_close = self.spy_prices.loc[:, 'SPY'].loc[:, 'close']

        joined_vals = pd.concat([account_data, spy_close], axis=1).dropna()
        account_data = joined_vals.loc[:, 'portfolio_value']
        rolling_returns = account_data.rolling(2).apply(lambda x: (x[1]-x[0])/x[0])
        rf = 0.025/365


        rolling_mean = rolling_returns.rolling(30).mean()[30:]

        rolling_std = rolling_returns.rolling(30).std()[30:]

        sharpe = (rolling_mean - rf) /rolling_std
        plt.plot(sharpe)



        spy_data = joined_vals.loc[:, 'close']

        spy_rolling_returns = spy_data.rolling(2).apply(lambda x: (x[1]-x[0])/x[0])

        spy_rolling_mean = spy_rolling_returns.rolling(30).mean()[30:]

        spy_rolling_std = spy_rolling_returns.rolling(30).std()[30:]
        spy_sharpe = (spy_rolling_mean-rf)/spy_rolling_std
        plt.plot(spy_sharpe)
        plt.legend(['portfolio rolling ' + str(rolling_window) + ' day sharpe','spy sharpe'])
        plt.show()
        print('a')

    def calc_volatility(self, account_data, rolling_window):
        account_data = account_data.portfolio_value
        account_data.index = account_data.index.tz_localize('America/New_York')

        spy_close = self.spy_prices.loc[:, 'SPY'].loc[:, 'close']

        joined_vals = pd.concat([account_data, spy_close], axis=1).dropna()
        account_data = joined_vals.loc[:, 'portfolio_value']
        spy_close = joined_vals.loc[:, 'close']
        std = account_data.rolling(rolling_window).std()
        spy_std = spy_close.rolling(rolling_window).std()
        std = std / self.cash
        spy_std = spy_std / spy_close[0]
        plt.plot(std)
        plt.plot(spy_std)
        plt.legend(['portfolio rolling ' + str(rolling_window) + ' day volatility', 'spy_std'])
        plt.show()
        return std

    def calc_max_drawdown(self, account_data):
        cum_returns = account_data.portfolio_value.diff()[1:].cumsum()

        cum_returns.index = cum_returns.index.tz_localize('America/New_York')
        current_date = self.start_date + pd.Timedelta("1 day")
        prev_high = 0
        spy_prev_high = 0
        drawdowns = pd.DataFrame()
        spy_drawdowns = pd.DataFrame()

        spy_close = self.spy_prices.loc[:, 'SPY'].loc[:, 'close']
        spy_cum_returns = spy_close.diff()[1:].cumsum()

        joined_vals = pd.concat([cum_returns, spy_cum_returns], axis=1).fillna(method='ffill')

        cum_returns = joined_vals.loc[:, 'portfolio_value']
        spy_cum_returns = joined_vals.loc[:, 'close']
        while current_date <= self.end_date:
            cur_cum_return = cum_returns[current_date:current_date][0]
            prev_high = max(prev_high, cur_cum_return)
            dd = cur_cum_return - prev_high
            drawdowns.loc[current_date, 'Drawdown'] = dd if dd < 0 else 0

            cur_spy_cum_return = spy_cum_returns[current_date:current_date][0]
            spy_prev_high = max(spy_prev_high, cur_spy_cum_return)
            spy_dd = cur_spy_cum_return - spy_prev_high
            spy_drawdowns.loc[current_date, 'Drawdown'] = spy_dd if spy_dd < 0 else 0

            current_date = current_date + pd.Timedelta("1 day")
        drawdowns = drawdowns / self.cash
        spy_drawdowns = spy_drawdowns / spy_close[0]
        plt.plot(drawdowns)
        plt.plot(spy_drawdowns)
        plt.legend(['drawdowns', 'spy_drawdowns'])
        plt.show()

    def calc_net_dollar_exposure(self, account_data):
        current_date = self.start_date
        net_dollar_exposure_df = pd.DataFrame()
        while current_date <= self.end_date:
            cur_account = account_data[current_date:current_date]
            exposure = cur_account.long_market_value - abs(cur_account.short_market_value)
            net_dollar_exposure_df = net_dollar_exposure_df.append(
                {'date': current_date, 'exposure': exposure}, ignore_index=True)
            current_date = current_date + pd.Timedelta("1 day")
        net_dollar_exposure_df.set_index('date', inplace=True)
        plt.plot(net_dollar_exposure_df)
        plt.legend(['net dollar exposure'])
        plt.show()
        return net_dollar_exposure_df

    def calc_position_concentration(self, positions, account_data):
        current_date = self.start_date
        position_concentration_df = pd.DataFrame()
        while current_date <= self.end_date:
            cur_pos = positions[current_date:current_date]
            cur_account = account_data[current_date:current_date]
            concentration = max(cur_pos.market_value) / cur_account.portfolio_value
            position_concentration_df = position_concentration_df.append(
                {'date': current_date, 'concentration': concentration}, ignore_index=True)
            current_date = current_date + pd.Timedelta("1 day")
        position_concentration_df.set_index('date', inplace=True)
        plt.plot(position_concentration_df)
        plt.legend(['max position concentrations'])
        plt.show()
        return position_concentration_df

    def calculate_turnover_rate(self, orders, account_data, rolling_window):
        prev_date = self.start_date
        current_date = self.start_date + pd.Timedelta(str(rolling_window) + "days")
        turnover_rates = pd.DataFrame()
        while current_date <= self.end_date:
            account_data_range = account_data[prev_date:current_date]
            avg_value = (account_data_range.iloc[0].portfolio_value + account_data_range.iloc[-1].portfolio_value) / 2
            cur_orders = orders[prev_date:current_date]
            buys = 0
            sells = 0
            turnover = 0
            for i in range(len(cur_orders)):
                order = cur_orders.iloc[i]
                if order.side == 'sell':
                    sells += order.filled_qty * order.filled_avg_price
                else:
                    buys += order.filled_qty * order.filled_avg_price
            if buys < sells:
                turnover = buys / avg_value
            else:
                turnover = sells / avg_value
            turnover_rates = turnover_rates.append({'date': current_date, 'turnover': turnover}, ignore_index=True)
            current_date = current_date + pd.Timedelta("1 day")
            prev_date = prev_date + pd.Timedelta("1 day")
        turnover_rates.set_index('date', inplace=True)
        plt.plot(turnover_rates)
        plt.legend(['portfolio rolling ' + str(rolling_window) + ' day turnover rates'])
        plt.show()
        return turnover_rates

    def calc_returns(self, account_data):
        spy_close = self.spy_prices.loc[:, 'SPY'].loc[:, 'close']
        norm_returns = account_data.portfolio_value / self.cash
        spy_norm_returns = spy_close / spy_close[0]
        plt.plot(norm_returns)
        plt.plot(spy_norm_returns)
        plt.legend(["portfolio value", "spy"])
        plt.show()

    def calculate_beta(self, account_data):
        mult_returns = account_data.portfolio_value.pct_change()[1:]
        mult_returns.index = mult_returns.index.tz_localize('America/New_York')

        spy_close = self.spy_prices.loc[:, 'SPY'].loc[:, 'close']
        spy_mult_returns = spy_close.pct_change()[1:]
        spy_mult_returns = spy_mult_returns.resample('D').last()
        joined_vals = pd.concat([mult_returns, spy_mult_returns], axis=1).dropna()

        spy_mult_returns = joined_vals.loc[:, 'close']

        covs = joined_vals.rolling(30).cov().reset_index().set_index('time')
        covs = covs.loc[(covs.level_1 == 'portfolio_value')][29:].loc[:, 'close']
        spy_vars = spy_mult_returns.rolling(30).var()[29:]
        rolling_betas = covs / spy_vars
        plt.plot(rolling_betas)
        plt.legend(['account beta'])
        plt.show()

    # calc sector exposure (rolling 63 day avg) TODO FEATURE
    # calc style exposure TODO FEATURE

    def test(self):

        orders = []
        orders.append({
            'symbol': 'AAPL',
            'qty': 5,
            'side': 'sell'
        })
        orders.append({
            'symbol': 'CRM',
            'qty': 10,
            'side': 'buy'
        })
        orders.append({
            'symbol': 'AAPL',
            'qty': 4,
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
        i = 0
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
        self.current_time = self.current_time + pd.Timedelta("1 " + self.timeframe)
        self.helper.current_time = self.current_time
        self.backtest_api.current_time = self.current_time
        self.helper.update_positions()
        self.helper.update_account(0)  # TODO:implement interest on short trades
