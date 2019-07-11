import alpaca_trade_api as tradeapi
import pandas as pd
import time
import logging

NY='America/New_York'

now = pd.Timestamp.now(NY)
end_dt = now
if now.time() >= pd.Timestamp('09:30', tz=NY).time():
    print(pd.Timedelta(now.strftime('%H:%M:%S')) )
    end_dt = now - pd.Timedelta(now.strftime('%H:%M:%S')) - pd.Timedelta('1 minute')
print(end_dt)