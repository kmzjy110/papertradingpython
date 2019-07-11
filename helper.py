import consts
import pandas as pd
import time
import logging

def get_current_portfolio_weights():
    positions = consts.api.list_positions()
    if not positions:
        return None
    symbols = pd.Index([p.symbol for p in positions])
    quantities = [p.qty for p in positions]
    share_counts = pd.Series(
        index= symbols,
        data = quantities
    )
    current_prices = pd.Series(index = symbols, data=[prices_up_to_yesterday(p.symbol, lookback=1).loc[:, p.symbol].loc[:, 'close'] for p in positions])
    current_weights = share_counts *current_prices / consts.api.get_account().equity
    return current_weights

def current_prices(symbols):
    now = pd.Timestamp.now(consts.NY);
    if not consts.api.get_clock().is_open:
        return prices_up_to_yesterday(symbols,1)
    else:
        return consts.api.get_barset(symbols,'minute',limit=5,start=now,end=now).df.dropna().head(1)

def prices_up_to_yesterday(symbols, lookback=consts.lookback):
    now = pd.Timestamp.now(consts.NY)
    end_dt = now
    if now.time()>=pd.Timestamp('09:30', tz=consts.NY).time():
        end_dt = now - pd.Timedelta(now.strftime('%H:%M:%S')) - pd.Timedelta('1 minute')
    return get_prices(symbols, end_dt, lookback)

def get_prices(symbols, end_dt, max_workers =5, lookback=consts.lookback):
    start_dt = end_dt - pd.Timedelta(str(lookback)+' days')
    start = start_dt.strftime('%Y-%m-%d')
    end = end_dt.strftime('%Y-%m-%d')

    barset = None
    i=0
    def get_barset(symbol):
        return consts.api.get_barset(symbols,'day',limit=lookback,start=start,end=end)

    while i<=len(symbols)-1:
        if barset is None:
            barset = get_barset(symbols[i:i+200])
        else:
            barset.update(get_barset(symbols[i:i+200]))
        i+=200
    return barset.df