import alpaca_trade_api as tradeapi
import pandas as pd
import time
import logging

NY='America/New_York'
api = tradeapi.REST(
    key_id='PKBJHXRAN650UDI78H7B',
    secret_key='vofINwfP0XtMFRNcSzHs4qGBSkmMYqtOoKBPYMsZ',
    base_url='https://paper-api.alpaca.markets'
)
want_lookback=20
lookback=200
ols_pairs_in_long={}
ols_pairs_in_short={}
spreads={}

pairs = [('ALL','WLTW'), ('AAPL','TXN'), ('DG','WMT'),('NFLX','DISCK'), ('CRM','IBM'), ('WRK','PEP'),('MET','ABBV')]

#MET,ABBV and MET,LLY