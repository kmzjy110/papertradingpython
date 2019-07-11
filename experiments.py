import test
import helper
import consts
import pandas as pd
lookback=20
NY='America/New_York'
symbol_pair = 'AAPL'
now = consts.api.get_clock().timestamp
print(now)
end_dt = now - pd.Timedelta(str(lookback) + ' days') + pd.Timedelta(str(20) + ' days')
prices = helper.get_prices(symbol_pair, end_dt, lookback=lookback).loc[:,'AAPL']
print(prices)
print(helper.current_prices('AAPL'))