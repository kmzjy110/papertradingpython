import csv
import logging
import uuid

class BacktestHelper:

    def __init__(self, current_time, start_date, end_date, initial_cash, aggregate_prices, timeframe='day'):
        self.start_date = start_date
        self.end_date = end_date
        self.current_time = current_time
        self.timeframe=timeframe
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
        #TODO: ALLOW CUSTOM FILE NAMES
        self.backtest_orders_filename = "backtest_orders.csv"
        self.backtest_positions_filename = "backtest_positions.csv"
        self.backtest_positions_hist_filename = "backtest_positions_hist.csv"
        self.backtest_account_filename = "backtest_account.csv"
        self.backtest_account_hist_filename = "backtest_account_hist.csv"

        self.init_files(self.backtest_orders_filename, self.order_columns)
        self.init_files(self.backtest_positions_filename, self.position_columns)
        self.init_files(self.backtest_positions_hist_filename, self.position_columns_with_time)
        self.init_files(self.backtest_account_filename, self.account_columns)
        self.init_files(self.backtest_account_hist_filename, self.account_columns_with_time)

        self.initiate_account(initial_cash)
        self.aggregate_prices_df = aggregate_prices.df


    def initiate_account(self, cash):
        account={}
        account["id"]=str(uuid.uuid4())
        account["status"]="ACTIVE"
        account["currency"] = "USD"
        account["cash"] = cash
        account["buying_power"] = account["cash"] * self.get_account_buying_power_factor(cash)
        account["regt_buying_power"] = account["buying_power"]
        account["daytrading_buying_power"] = 0
        account["portfolio_value"] = cash
        account["pattern_day_trader"]=False
        account["trading_blocked"]=False
        account["transfers_blocked"]=False
        account["account_blocked"] = False
        account["created_at"] = self.current_time.isoformat()+'Z'
        account["trade_suspended_by_user"] = False
        account["multiplier"] = self.get_account_buying_power_factor(cash)
        account["shorting_enabled"]=True
        account["equity"] = cash
        account["last_equity"] = cash
        account["long_market_value"]=0
        account["short_market_value"] = 0
        account["initial_margin"]=0
        account["maintenance_margin"]=0
        account["last_maintenance_margin"]=0
        account["sma"]=0
        account["daytrade_count"]=0

        self.write_account_data(account)
        account["time"]=self.current_time
        self.write_to_csv(self.backtest_account_hist_filename, account, self.account_columns_with_time)


    def init_files(self, filename, columns):
        try:
            with open(filename, "w+") as csvfile:
                writer = csv.DictWriter(csvfile,fieldnames=columns)
                writer.writeheader()
        except IOError:
            logging.error("I/O Error:"+filename)

    def write_to_csv(self, filename, data, fieldnames):
        try:
            with open(filename, "w+") as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                if not data: #TODO:FIX DATA
                    return True
                if type(data) is dict:
                    writer.writerow(data)
                else:
                    for row in data:
                        if row is not None:
                            writer.writerow(row)
        except IOError:
            logging.error("I/O Error:" + self.backtest_positions_filename)
            return False
        return True

    def update_position(self, position_raw):
        positions_raw = self.read_positions_raw()
        for i in range(len(positions_raw)):
            if positions_raw[i]["symbol"] == position_raw["symbol"]:
                positions_raw[i] = position_raw
                break
        return self.write_to_csv(self.backtest_positions_filename,positions_raw, self.position_columns)


    def append_to_cur_position(self, position_raw):
        return self.append_row_to_csv(self.backtest_positions_filename, position_raw, self.position_columns)

    def append_to_position_hist(self, position_raw):
        position_raw["time"] = self.current_time
        return self.append_row_to_csv(self.backtest_positions_hist_filename, position_raw, self.position_columns_with_time)

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
        return self.append_row_to_csv(self.backtest_orders_filename, order_raw, self.order_columns)

    def read_positions_raw(self):
        return self.read_from_csv(self.backtest_positions_filename)

    def del_position(self, symbol):
        positions_raw = self.read_positions_raw()
        for i in range(len(positions_raw)):
            if positions_raw[i]["symbol"] == symbol:
                positions_raw.remove(positions_raw[i])
                break
        return self.write_to_csv(self.backtest_positions_filename, positions_raw, self.position_columns)

    def read_account_raw(self):
        return self.read_from_csv(self.backtest_account_filename)[0]

    def update_positions(self): #TODO:TEST
        positions = self.read_positions_raw()
        for position in positions:
            current_price = self.aggregate_prices_df[position["symbol"]].loc[:self.current_time].iloc[-1].loc["close"]
            position["market_value"] = float(position["qty"])* current_price
            position["unrealized_pl"] = round(position["market_value"] - position["cost_basis"], 2)
            position["unrealized_plpc"] = round(position["unrealized_pl"] / abs(position["cost_basis"]), 2) #TODO:SAME CALCULATION AS IN API SUBMIT ORDER, CONSIDER REFACTORING
            position["lastday_price"]=position["current_price"]
            position["current_price"]=str(current_price)
        self.write_to_csv(self.backtest_positions_filename,positions, self.position_columns)








    def update_account(self, transaction_cash=0):
        account = self.read_account_raw()
        positions = self.read_positions_raw()

        sum_shorts = sum([float(p["market_value"]) for p in positions if p["side"] == "short"])
        sum_longs = sum([float(p["market_value"]) for p in positions if p["side"] == "long"])

        account["cash"] = round(float(account["cash"])+transaction_cash,2)
        account["multiplier"] = self.get_account_buying_power_factor(account["cash"])
        account["long_market_value"] = sum_longs
        account["short_market_value"] = sum_shorts
        account["last_equity"] = account["equity"]
        account["equity"] = round(account["cash"] + account["long_market_value"] + account["short_market_value"],2)
        account["portfolio_value"] = account["equity"]
        account["initial_margin"] = round((sum_longs + abs(sum_shorts)) *0.5,2)
        account["buying_power"] = round((account["equity"] - account["initial_margin"]) * account["multiplier"],2)
        account["regt_buying_power"] = account["buying_power"]
        account["last_maintenance_margin"] = account["maintenance_margin"]
        account["maintenance_margin"] = round(self.get_maintenance_margin(positions),2)

        for key in account.keys():
            account[key] = str(account[key])
        self.write_to_account(account)

    def write_to_account(self, account):
        self.write_account_data(account)
        self.append_account_hist(account)

    def write_account_data(self, account):
        try:
            with open(self.backtest_account_filename, "w") as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=self.account_columns)
                writer.writeheader()
                writer.writerow(account)
        except IOError:
            logging.error("I/O Error:" + self.backtest_account_filename)
            return False
        return True

    def append_account_hist(self, account):
        account["time"] = self.current_time
        return self.append_row_to_csv(self.backtest_account_hist_filename, account, self.account_columns_with_time)

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