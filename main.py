import alpaca_trade_api as tradeapi
import pandas as pd
import time
import logging
#import statsmodels.api as sm
import ols_pairs_trading
import consts
import experiments

def main():
    done = None
    logging.info('started')
    while True:
        clock = consts.api.get_clock()
        now = clock.timestamp
        if clock.is_open and done!= now.strftime('%Y-%m-%d'):

            done = now.strftime('%Y-%m-%d')
            logging.info(f'Done for {done}')




if __name__ == '__main__':
    main()




