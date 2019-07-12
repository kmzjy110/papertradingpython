import test
import helper
import consts
import pandas as pd
import ols_pairs_trading
import tests
import universe
import alpaca_trade_api
lookback=20
NY='America/New_York'

symbols = ('FCAU','HMC')
start_day='2019-05-17T11:02:35.532756347-04:00Z'
end_day='2019-06-14T11:02:35.532756347-04:00Z'
start_day=pd.Timestamp(2019,5,17)
end_day = pd.Timestamp(2019,6,14)
#prices = helper.get_prices_with_start_end(symbols, end_dt=end_day, start_dt=start_day)
#another = helper.get_prices_with_start_end(symbols, start_day, end_day)
#tests.test_coint(('FCAU','HMC'))

tests.test_pairs()


#ols_pairs_trading.get_portfolio_weights([('FCAU','HMC')])