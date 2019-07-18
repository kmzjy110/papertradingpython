import alpaca_trade_api
import pandas as pd
import consts
import uuid
import csv

class BacktestAPI:
    def __init__(self, current_time, start_date, end_date, symbols_involved, alpaca_api, backtest_engine,
                 max_lookback=consts.lookback, timeframe='day'):
        self.current_time = current_time
        self.start_date = start_date
        self.end_date = end_date
        self.symbols_involved = symbols_involved
        self.timeframe = timeframe
        self.backtest_engine = backtest_engine
        start = ((start_date - pd.Timedelta(str(max_lookback + 3) + ' days')).replace(second=0,
                                                                                      microsecond=0).isoformat()[
                 :consts.iso_format_string_adjust]) + 'Z'
        # subtracted 3 more days to allow lastday price generalized to mondays

        end = (end_date.replace(second=0, microsecond=0).isoformat()[:consts.iso_format_string_adjust]) + 'Z'
        self.aggregate_prices = alpaca_api.get_barset(symbols_involved, timeframe, limit=1000, start=start, end=end)
        self.aggregate_assets = {}
        for symbol in symbols_involved:
            self.aggregate_assets[symbol] = alpaca_api.get_asset(symbol)


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
        if type(symbols) == str:
            return alpaca_trade_api.rest.BarSet({symbols: self.get_bar(symbols, timeframe, limit, start, end)})
        barset_dict = {}
        for symbol in symbols:
            symbol_bars = self.get_bar(symbol, timeframe, limit, start, end)
            barset_dict[symbol] = symbol_bars
        return alpaca_trade_api.rest.BarSet(barset_dict)
        pass

    def get_bar(self, symbol, timeframe, limit, start, end):
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
        positions_raw = self.backtest_engine.read_positions_raw()
        positions = []
        for raw in positions_raw:
            positions.append(alpaca_trade_api.rest.Position(raw))
        return positions

    def list_orders(self):
        # TODO: list orders between certain times
        orders = []
        with open("backtest_orders.csv", mode='r') as csv_file:
            csv_reader = csv.DictReader(csv_file)
            for row in csv_reader:
                orders.append(alpaca_trade_api.rest.Order(row))
        return orders

    def submit_order(self, symbol, qty, side, type, time_in_force, limit_price=None, stop_price=None,
                     extended_hours=False):

        # TODO: simulate full submit_order to include limit
        # TODO: INDEX CHECKING FOR PRICES BARSET

        order = {}
        order["id"] = str(uuid.uuid4())
        order["client_order_id"] = str(uuid.uuid4())
        order["created_at"] = self.current_time.isoformat() + 'Z'
        order["updated_at"] = self.current_time.isoformat() + 'Z'
        order["submitted_at"] = self.current_time.isoformat() + 'Z'
        order["filled_at"] = self.current_time.isoformat() + 'Z'
        order["expired_at"] = None
        order["canceled_at"] = None
        order["failed_at"] = None
        order["asset_id"] = self.aggregate_assets[symbol].id
        order["symbol"] = symbol
        order["asset_class"] = self.aggregate_assets[symbol].__getattr__("class")
        order["qty"] = str(qty)
        order["filled_qty"] = str(qty)
        order["filled_avg_price"] = str(
            self.aggregate_prices.df[symbol].loc[self.current_time].loc['close'])  # maybe try averaging all 4 prices?
        order["order_type"] = type
        order["type"] = type
        order["side"] = side
        order["time_in_force"] = time_in_force
        order["limit_price"] = limit_price
        order["stop_price"] = stop_price
        order["status"] = "filled"

        success = self.backtest_engine.write_order(order)
        if not success:
            return

        positions_raw = self.backtest_engine.read_positions_raw()
        cur_position = None
        for raw in positions_raw:
            if raw["symbol"] == symbol:
                cur_position = raw
        is_position_update = False
        closed_out = False
        cash_add=None
        if cur_position is not None:
            # TODO:somehow verify the calcs from actual API
            is_position_update = True
            most_recent_qty = int(order["qty"]) + int(cur_position["qty"])
            most_recent_price = float(order["filled_avg_price"])

            if most_recent_qty == 0:
                cash_add = (float(order["qty"])*float(order["filled_avg_price"]))-float(cur_position["cost_basis"])
                cur_position["avg_entry_price"] = -cash_add
                cur_position["unrealized_pl"] = cash_add
                cur_position["unrealized_plpc"] = cur_position["unrealized_pl"] / float(cur_position["cost_basis"])
                closed_out=True
            else:
                cur_position["avg_entry_price"] = (float(order["qty"]) * most_recent_price +
                                                  float(cur_position["qty"]) * float(cur_position["avg_entry_price"])) \
                                                  /most_recent_qty

            cur_position["qty"] = most_recent_qty

        else:
            cur_position = {}
            cur_position["asset_id"] = order["asset_id"]
            cur_position["symbol"] = order["symbol"]
            cur_position["exchange"] = self.aggregate_assets[symbol].exchange
            cur_position["asset_class"] = order["asset_class"]

            cur_position["avg_entry_price"] = order["filled_avg_price"]
            cur_position["qty"] = order["qty"]

        cur_position["current_price"] = order["filled_avg_price"]
        cur_position["lastday_price"] = self.aggregate_prices.df[symbol].loc[:self.current_time]["close"][-2]
        cur_position["market_value"] = float(cur_position["current_price"]) * float(cur_position["qty"])
        cur_position["cost_basis"] = float(cur_position["avg_entry_price"]) * float(cur_position["qty"])

        # TODO:FUTURE FEATURE INCLUDE INTRADAY STUFF
        cur_position["unrealized_intraday_pl"] = 0
        cur_position["unrealized_intraday_plpc"] = 0
        cur_position["change_today"] = 0

        if not closed_out:
            cur_position["unrealized_pl"] = cur_position["market_value"] - cur_position["cost_basis"]
            cur_position["unrealized_plpc"] = cur_position["unrealized_pl"] / cur_position["cost_basis"]
        else:
            self.backtest_engine.del_position_and_update_cash(cur_position["symbol"],cash_add)
            self.backtest_engine.append_to_position_all(cur_position)
            return

        if int(cur_position["qty"]) < 0:
            cur_position["side"] = "short"
        else:
            cur_position["side"] = "long"

        for key in cur_position.keys():
            cur_position[key] = str(cur_position[key])

        if is_position_update:
            self.backtest_engine.update_position(cur_position)
        if not is_position_update:
            self.backtest_engine.append_to_cur_position(cur_position)

        self.backtest_engine.append_to_position_all(cur_position)  # TODO:TEST all updating position methods and calculations ughhhhh

    def get_account(self):  # https://docs.alpaca.markets/margin-and-shorting/
        pass

    def get_asset(self, symbol):
        return self.alpaca_api.get_asset(symbol)