import main
import helper
import consts
import pandas as pd
import ols_pairs_trading
import logging
import tests
import universe
import alpaca_trade_api
import json
import backtester
lookback=20
NY='America/New_York'

symbols = ('FCAU','HMC','MSFT')
symbols2 = ('FCAU','HMC')
start_day='2019-05-17T11:02:35.532756347-04:00Z'
end_day='2019-06-14T11:02:35.532756347-04:00Z'
start_day=pd.Timestamp(2019,5,18,9,30)
end_day = pd.Timestamp(2019,7,16)

experiment_start_day = pd.Timestamp(year=2019,month=6,day=1,tz=NY)
experiment_end_day = pd.Timestamp(year=2019,month=7,day=1,tz=NY)
#prices = helper.get_prices_with_start_end(symbols, end_dt=end_day, start_dt=start_day)
#another = helper.get_prices_with_start_end(symbols, start_day, end_day)
#tests.test_coint(('FCAU','HMC'))

#tests.test_pairs()
#prices = helper.prices_up_to_yesterday('AAPL')
weights, delta = ols_pairs_trading.get_portfolio_weights(consts.pairs)

BacktesterAPI = backtester.BacktestEngine(current_time = start_day, start_date = start_day, end_date = end_day, symbols_involved = symbols, alpaca_api = consts.api)


barset = BacktesterAPI.get_barset(symbols2,"day",200, experiment_start_day,experiment_end_day)
df = barset.df

logging.basicConfig(filename='app.log', level=logging.INFO)

weights, delta = ols_pairs_trading.get_portfolio_weights(consts.pairs,set_status=False)
print(delta)
