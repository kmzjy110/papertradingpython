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

def main():
    done = None
    logging.info('started')
    while True:
        clock = api.get_clock()
        now = clock.timestamp
        if clock.is_open and done!= now.strftime('%Y-%m-%d'):

            done = now.strftime('%Y-%m-%d')
            logging.info(f'Done for {done}')
    pass

if __name__ == '__main__':
    main()

def prices(symbols):
    now = pd.Timestamp.now(NY)
    end_dt = now
    if now.time()>=pd.Timestamp('09:30', tz=NY).time():
        end_dt = now - pd.Timedelta(now.strftime('%H:%M:%S')) - pd.Timedelta('1 minute')
    return _get_prices(symbols,end_dt)

def _get_prices(symbols, end_dt, max_workers =5):

