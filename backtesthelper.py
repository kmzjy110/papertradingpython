import csv
import logging

class BacktestHelper:

    def __init__(self, current_time, start_date, end_date):
        self.start_date = start_date
        self.end_date = end_date
        self.current_time = current_time
        self.order_columns = ['id', 'client_order_id', 'created_at', 'updated_at', 'submitted_at', 'filled_at',
                              'expired_at', 'canceled_at', 'failed_at', 'asset_id', 'symbol', 'asset_class', 'qty',
                              'filled_qty', 'filled_avg_price', 'order_type', 'type', 'side', 'time_in_force',
                              'limit_price', 'stop_price', 'status']
        self.position_columns = ['asset_class', 'asset_id', 'avg_entry_price', 'change_today', 'cost_basis',
                                 'current_price', 'exchange', 'lastday_price', 'market_value', 'qty', 'side', 'symbol',
                                 'unrealized_intraday_pl', 'unrealized_intraday_plpc', 'unrealized_pl',
                                 'unrealized_plpc']
        self.position_columns_with_time = ['time'] + [c for c in self.position_columns]
        self.account_columns= ['id', 'status', 'currency', 'buying_power', 'regt_buying_power', 'daytrading_buying_power', 'cash', 'portfolio_value', 'pattern_day_trader', 'trading_blocked', 'transfers_blocked', 'account_blocked', 'created_at', 'trade_suspended_by_user', 'multiplier', 'shorting_enabled', 'equity', 'last_equity', 'long_market_value', 'short_market_value', 'initial_margin', 'maintenance_margin', 'last_maintenance_margin', 'sma', 'daytrade_count']
        self.account_columns_with_time = ['time'] + [c for c in self.account_columns]
        #TODO:CREATE FILES IF THEY DONT EXIST
        #TODO: ALLOW CUSTOM FILE NAMES
        #TODO:INITIATE ACCOUNT



    def update_position(self, position_raw):
        positions_raw = self.read_positions_raw()
        for i in range(len(positions_raw)):
            if positions_raw[i]["symbol"] == position_raw["symbol"]:
                positions_raw[i] = position_raw
                break
        try:
            with open("backtest_positions.csv", "w") as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=self.position_columns)
                writer.writeheader()
                for pos in positions_raw:
                    writer.writerow(pos)
        except IOError:
            logging.error("I/O Error:" + "backtest_positions.csv")
            return False
        return True

    def append_to_cur_position(self, position_raw):
        return self.append_row_to_csv("backtest_positions.csv", position_raw, self.position_columns)

    def append_to_position_hist(self, position_raw):
        position_raw["time"] = self.current_time
        return self.append_row_to_csv("backtest_positions_hist.csv", position_raw, self.position_columns_with_time)

    def append_row_to_csv(self, filename, raw_data, fieldnames):
        try:
            with open(filename, "a") as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writerow(raw_data)
        except IOError:
            logging.error('I/O Error:' + filename)
            return False
        return True

    def read_from_csv(self, filename):
        raw_data = []
        try:
            with open(filename, mode='r') as csv_file:
                csv_reader = csv.DictReader(csv_file)
                for row in csv_reader:
                    raw_data.append(row)
        except IOError:
            logging.error('I/O Error:' + filename)
        return raw_data

    def write_order(self, order_raw):
        return self.append_row_to_csv("backtest_orders.csv", order_raw, self.order_columns)

    def read_positions_raw(self):
        return self.read_from_csv("backtest_positions.csv")

    def del_position(self, symbol):
        positions_raw = self.read_positions_raw()
        for i in range(len(positions_raw)):
            if positions_raw[i]["symbol"] == symbol:
                positions_raw[i] = None
                break
        try:
            with open("backtest_positions.csv", "w") as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=self.position_columns)
                writer.writeheader()
                for pos in positions_raw:
                    if pos is not None:
                        writer.writerow(pos)
        except IOError:
            logging.error("I/O Error:" + "backtest_positions.csv")

    def read_account_raw(self):
        return self.read_from_csv("account.csv")[0]

    def update_account(self, transaction_cash=0):
        account = self.read_account_raw()
        positions = self.read_positions_raw()
        account["cash"] = float(account["cash"])+transaction_cash
        account["multiplier"] = self.get_account_buying_power_factor(account["cash"])
        sum_shorts = sum([float(p["market_value"]) for p in positions if p["side"]=="short"])
        sum_longs = sum([float(p["market_value"]) for p in positions if p["side"]=="long"])
        account["long_market_value"] = sum_longs
        account["short_market_value"] = sum_shorts
        account["last_equity"] = account["equity"]
        account["equity"] = account["cash"] + account["long_market_value"] + account["short_market_value"]
        account["portfolio_value"] = account["equity"]
        account["initial_margin"] = (sum_longs + abs(sum_shorts)) *0.5
        account["buying_power"] = (account["equity"] - account["initial_margin"]) * account["multiplier"]
        account["regt_buying_power"] = account["buying_power"]
        account["last_maintenance_margin"] = account["maintenance_margin"]
        account["maintenance_margin"] = self.get_maintenance_margin(positions)
        self.write_account_data(account)
        self.append_account_hist(account)

    def write_account_data(self, account):
        try:
            with open("backtest_account.csv", "w") as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=self.account_columns)
                writer.writeheader()
                writer.writerow(account)
        except IOError:
            logging.error("I/O Error:" + "backtest_positions.csv")
            return False
        return True

    def append_account_hist(self, account):
        account["time"] = self.current_time
        return self.append_row_to_csv("backtest_account_his", account, self.account_columns_with_time)

    def get_account_buying_power_factor(self, cash):
        if cash<2000:
            return 1
        else:
            return 2

    def get_maintenance_margin(self, positions):
        maintenance_margin = 0
        for position in positions:
            margin_per_share=0
            if position["side"]=="short":
                if float(position["current_price"])< 5:
                    margin_per_share= max(float(position["current_price"]),2.5)
                else:
                    margin_per_share = max(float(position["current_price"])*0.3, 5)
            else:
                if float(position["current_price"])< 2.5:
                    margin_per_share = float(position["current_price"])
                else:
                    margin_per_share = float(position["current_price"])*0.3
            maintenance_margin = margin_per_share * abs(float(position["qty"]))
        return maintenance_margin