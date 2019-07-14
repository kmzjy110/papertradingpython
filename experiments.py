import main
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

#tests.test_pairs()

weights = ols_pairs_trading.get_portfolio_weights(consts.pairs)
#weights = [ 0.09676241, -0.15323759,  0.10637252, -0.14362748 , 0.08412611, -0.16587389,
#   0.,          0.        ]
#weights=[ 0.06450827, -0.1021584 ,  0.07098589, -0.09568077 , 0.05608408, -0.11058259,
#   0.    ,      0.  ,       -0.076328  , -0.09033867  ,0.08144351,  0.08522315]
num_shares = helper.get_share_numbers(5000, weights)
print(num_shares)