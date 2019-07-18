import logging
import json

import alpaca_trade_api
import pandas as pd

import backtesthelper
import consts
import ols_pairs_trading
import csv
import helper

lookback = 20
NY = 'America/New_York'

symbols = ('NFLX', 'HMC', 'MSFT')
symbols2 = ('FCAU', 'HMC')
start_day = '2019-05-17T11:02:35.532756347-04:00Z'
end_day = '2019-06-14T11:02:35.532756347-04:00Z'
start_day = pd.Timestamp(2019, 5, 18, 9, 30)
end_day = pd.Timestamp(2019, 7, 16)

current_time = pd.Timestamp(2019,5,21)
experiment_start_day = pd.Timestamp(year=2019, month=6, day=1, tz=NY)
experiment_end_day = pd.Timestamp(year=2019, month=7, day=1, tz=NY)
# prices = helper.get_prices_with_start_end(symbols, end_dt=end_day, start_dt=start_day)
# another = helper.get_prices_with_start_end(symbols, start_day, end_day)
# tests.test_coint(('FCAU','HMC'))

# tests.test_pairs()
# prices = helper.prices_up_to_yesterday('AAPL')

#positions = consts.api.list_positions()

weights, delta, zscores = ols_pairs_trading.get_portfolio_weights(consts.pairs)

account = consts.api.get_account()
positions = consts.api.list_positions()

#orders = consts.api.list_orders(status="all",limit=50, after = pd.Timestamp(2019,7,12))

#positions1 = consts.api.list_positions()


#assets = []
#for symbol in symbols:
#    assets.append(consts.api.get_asset(symbol))
#print(type('NFLX')==str)


BacktesterAPI = backtesthelper.BacktestAPI(current_time=current_time, start_date=start_day, end_date=end_day,
                                           symbols_involved=symbols, alpaca_api=consts.api)
#df = BacktesterAPI.get_barset('NFLX','day',200,start_day,end_day).df
#orders = BacktesterAPI.list_orders()



print("a")



positions = BacktesterAPI.list_positions()
BacktesterAPI.submit_order('NFLX',1,'buy','market','day')
logging.basicConfig(filename='app.log', level=logging.INFO)

weights, delta = ols_pairs_trading.get_portfolio_weights(consts.pairs, set_status=False)
print(delta)
