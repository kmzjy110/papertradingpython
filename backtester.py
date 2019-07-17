import alpaca_trade_api
import pandas as pd
import json
import consts
import uuid
import csv
import logging

class Backtester:

    def __init__(self, start_date, end_date, api, list_assets):
        self.start_date = start_date
        self.end_date = end_date
        self.api = api
        self.list_assets = list_assets

    def do_backtest(self):
        pass


# functionalities: read-write backtesting results and displaying it
# class BacktestResultsReader
class BacktestEngine:
    def __init__(self, current_time, start_date, end_date, symbols_involved, alpaca_api, max_lookback=consts.lookback,
                 timeframe='day'):
        self.current_time = current_time
        self.start_date = start_date
        self.end_date = end_date
        self.symbols_involved = symbols_involved
        self.timeframe = timeframe
        start = ((start_date - pd.Timedelta(str(max_lookback) + ' days')).replace(second=0, microsecond=0).isoformat()[
                 :consts.iso_format_string_adjust]) + 'Z';
        end = (end_date.replace(second=0, microsecond=0).isoformat()[:consts.iso_format_string_adjust]) + 'Z'
        self.aggregate_prices = alpaca_api.get_barset(symbols_involved, timeframe, limit=1000, start=start, end=end)
        self.aggregate_assets = {}
        for symbol in symbols_involved:
            self.aggregate_assets[symbol] = alpaca_api.get_asset(symbol)
        self.order_columns = ['id', 'client_order_id', 'created_at', 'updated_at', 'submitted_at', 'filled_at', 'expired_at', 'canceled_at', 'failed_at', 'asset_id', 'symbol', 'asset_class', 'qty', 'filled_qty', 'filled_avg_price', 'order_type', 'type', 'side', 'time_in_force', 'limit_price', 'stop_price', 'status']
        self.position_columns = ['asset_class', 'asset_id', 'avg_entry_price', 'change_today', 'cost_basis', 'current_price', 'exchange', 'lastday_price', 'market_value', 'qty', 'side', 'symbol', 'unrealized_intraday_pl', 'unrealized_intraday_plpc', 'unrealized_pl', 'unrealized_plpc'];

    def get_clock(self):
        clock_raw = {"timestamp": self.current_time.isoformat() + 'Z', "is_open": self.check_is_open(self.current_time),
                     "next_open": self.get_next_open(self.current_time),
                     "next_close": self.get_next_close(self.current_time)}
        return alpaca_trade_api.rest.Clock(clock_raw)

    def get_next_open(self, timestamp):
        if self.check_is_open(timestamp):
            timestamp = timestamp + pd.Timedelta("1 day")

        if timestamp.dayofweek > 4:
            timestamp = timestamp + pd.Timedelta(str(7 - timestamp.dayofweek) + " days")

        return timestamp.replace(hour=9, minute=30, second=0, microsecond=0)

    def get_next_close(self, timestamp):
        if self.check_is_open(timestamp):
            return timestamp.replace(hour=16, minute=0, second=0, microsecond=0)

        return self.get_next_open(timestamp).replace(hour=16, minute=0, second=0, microsecond=0)

    def check_is_open(self, timestamp):
        if timestamp.dayofweek >= 5:
            return False
        if timestamp.hour < 9 or timestamp.hour > 16:
            return False
        if timestamp.hour == 9 and timestamp.minute < 30:
            return False
        return True

    def get_barset(self, symbols, timeframe, limit, start, end):
        if type(symbols)==str:
            return alpaca_trade_api.rest.BarSet({symbols:self.get_bar(symbols,timeframe,limit,start,end)})
        barset_dict = {}
        for symbol in symbols:
            symbol_bars = self.get_bar(symbol,timeframe,limit,start,end)
            barset_dict[symbol] = symbol_bars
        return alpaca_trade_api.rest.BarSet(barset_dict)
        pass
    def get_bar(self, symbol, timeframe,limit,start,end):
        bars = self.aggregate_prices[symbol]
        symbol_bars = [{
            't': int(Bar.t.value / 1e9),
            'o': Bar.o,
            'h': Bar.h,
            'l': Bar.l,
            'c': Bar.c,
            'v': Bar.v
        }
            for Bar in bars if
            pd.Timestamp(start, tz=consts.NY) <= Bar.t <= pd.Timestamp(end, tz=consts.NY)]
        return symbol_bars
    def list_positions(self):

        positions = []
        with open("backtest_positions.csv", mode='r') as csv_file:
            csv_reader = csv.DictReader(csv_file)
            for row in csv_reader:
                positions.append(alpaca_trade_api.rest.Position(row))
        return positions
        pass

    def list_orders(self):
        #TODO: time
        orders = []
        with open("backtest_orders.csv", mode='r') as csv_file:
            csv_reader = csv.DictReader(csv_file)
            for row in csv_reader:
                orders.append(alpaca_trade_api.rest.Order(row))
        return orders


    def submit_order(self, symbol, qty, side, type, time_in_force, limit_price = None, stop_price = None, extended_hours=False):  # write to excel, modify positions too

        #TODO: simulate full submit_order to include limit
        #TODO: INDEX CHECKING FOR PRICES BARSET
        #TODO: UPDATE POSITIONS
        #TODO: keep track of all positions of backtest
        order = {}
        order["id"] =str(uuid.uuid4())
        order["client_order_id"] = str(uuid.uuid4())
        order["created_at"] = self.current_time.isoformat()+'Z'
        order["updated_at"] = self.current_time.isoformat()+'Z'
        order["submitted_at"] = self.current_time.isoformat()+'Z'
        order["filled_at"] = self.current_time.isoformat()+'Z'
        order["expired_at"]=None
        order["canceled_at"]=None
        order["failed_at"]=None
        order["asset_id"] = self.aggregate_assets[symbol].id
        order["symbol"]=symbol
        order["asset_class"]=self.aggregate_assets[symbol].__getattr__("class")
        order["qty"] = qty
        order["filled_qty"] = qty
        order["filled_avg_price"]= str(self.aggregate_prices.df[symbol].loc[self.current_time].loc['close'])#maybe try averaging all 4 prices?
        order["order_type"] = type
        order["type"]=type
        order["side"]=side
        order["time_in_force"] = time_in_force
        order["limit_price"]=limit_price
        order["stop_price"]=stop_price
        order["status"]="filled"

        try:
            with open("backtest_orders.csv", "w") as csvfile:
                writer = csv.DictWriter(csvfile,fieldnames=self.order_columns)
                writer.writerow(order)
        except IOError:
            logging.error('I/O Error')
        pass


    def get_account(self): #https://docs.alpaca.markets/margin-and-shorting/
        pass




    def get_asset(self):
        pass
