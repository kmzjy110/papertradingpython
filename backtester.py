import alpaca_trade_api
import pandas as pd
import consts
class Backtester:

    def __init__(self, start_date, end_date, api, list_assets):
        self.start_date = start_date
        self.end_date = end_date
        self.api = api
        self.list_assets = list_assets

    def do_backtest(self):
        pass


#functionalities: read-write backtesting results and displaying it
#class BacktestResultsReader
class BacktesterAPI:
    def __init__(self, current_time, start_date, end_date, symbols_involved, alpaca_api, max_lookback = consts.lookback, timeframe = 'day'):
        self.current_time = current_time
        self.start_date = start_date
        self.end_date = end_date
        self.symbols_involved = symbols_involved
        self.timeframe = timeframe
        start = ((start_date - pd.Timedelta(str(max_lookback) + ' days')).replace(second = 0, microsecond = 0).isoformat()[:consts.iso_format_string_adjust])+'Z';
        end = (end_date.replace(second=0, microsecond = 0).isoformat()[:consts.iso_format_string_adjust])+'Z'
        self.aggregate_prices = alpaca_api.get_barset(symbols_involved, timeframe, limit=1000, start=start,end=end )

    def get_clock(self):
        clock_raw = {"timestamp": self.current_time.isoformat() + 'Z', "is_open": self.check_is_open(self.current_time),
                     "next_open": self.get_next_open(self.current_time),
                     "next_close": self.get_next_close(self.current_time)}
        return alpaca_trade_api.rest.Clock(clock_raw)


    def get_next_open(self, timestamp):
        if self.check_is_open(timestamp):
            timestamp= timestamp + pd.Timedelta("1 day")

        if timestamp.dayofweek>4:
            timestamp= timestamp + pd.Timedelta(str(7-timestamp.dayofweek)+" days")

        return timestamp.replace(hour=9, minute=30, second=0, microsecond=0)

    def get_next_close(self, timestamp):
        if self.check_is_open(timestamp):
            return timestamp.replace(hour = 16, minute=0, second = 0, microsecond =0)

        return self.get_next_open(timestamp).replace(hour = 16, minute=0, second = 0, microsecond =0)

    def check_is_open(self, timestamp):
        if timestamp.dayofweek>=5:
            return False
        if timestamp.hour<9 or timestamp.hour >16:
            return False
        if timestamp.hour==9 and timestamp.minute<30:
            return False
        return True

    def get_barset(self, symbols, timeframe, limit, start, end):
        barset_dict = {}
        for symbol in symbols:
            bars = self.aggregate_prices[symbol]
            symbol_bars = [{
                't':int(Bar.t.value/1e9),
                'o':Bar.o,
                'h':Bar.h,
                'l':Bar.l,
                'c':Bar.c,
                'v':Bar.v
            }
                           for Bar in bars if
                           pd.Timestamp(start, tz=consts.NY) <= Bar.t <= pd.Timestamp(end, tz=consts.NY)]
            barset_dict[symbol] = symbol_bars
        return alpaca_trade_api.rest.BarSet(barset_dict)
        pass

    def list_positions(self):
        pass

    def get_account(self):
        pass


    def submit_order(self, symbol, qty, side, type, time_in_force): #write to excel
        pass

    def list_orders(self):
        return []

    def get_asset(self):
        pass

