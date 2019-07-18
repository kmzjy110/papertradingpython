import csv
import logging


class BacktestEngine:

    def __init__(self, start_date, end_date, api, list_assets):
        self.start_date = start_date
        self.end_date = end_date
        self.api = api
        self.list_assets = list_assets
        self.order_columns = ['id', 'client_order_id', 'created_at', 'updated_at', 'submitted_at', 'filled_at',
                              'expired_at', 'canceled_at', 'failed_at', 'asset_id', 'symbol', 'asset_class', 'qty',
                              'filled_qty', 'filled_avg_price', 'order_type', 'type', 'side', 'time_in_force',
                              'limit_price', 'stop_price', 'status']
        self.position_columns = ['asset_class', 'asset_id', 'avg_entry_price', 'change_today', 'cost_basis',
                                 'current_price', 'exchange', 'lastday_price', 'market_value', 'qty', 'side', 'symbol',
                                 'unrealized_intraday_pl', 'unrealized_intraday_plpc', 'unrealized_pl',
                                 'unrealized_plpc']

    def do_backtest(self):
        #TODO:need to update position daily omg
        pass

    def read_positions_raw(self):
        positions_raw = []

        # TODO:check file creation
        with open("backtest_positions.csv", mode='r') as csv_file:
            csv_reader = csv.DictReader(csv_file)
            for row in csv_reader:
                positions_raw.append(row)
        return positions_raw

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

    def append_to_cur_position(self, position_raw):
        return self.append_row_to_csv("backtest_positions.csv", position_raw, self.position_columns)

    def append_to_position_all(self, position_raw):
        return self.append_row_to_csv("backtest_positions_all.csv", position_raw, self.position_columns)

    def append_row_to_csv(self, filename, raw_data, fieldnames):
        try:
            with open(filename, "a") as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writerow(raw_data)
            return True
        except IOError:
            logging.error('I/O Error:' + filename)
            return False

    def write_order(self, order_raw):
        return self.append_row_to_csv("backtest_orders.csv", order_raw, self.order_columns)

    def del_position_and_update_cash(self, symbol,cash_add):
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
                #TODO:UPDATE ACCOUNT CASH
        except IOError:
            logging.error("I/O Error:" + "backtest_positions.csv")
