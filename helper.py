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
        return prices_up_to_yesterday(symbols, lookback=1)
    else:
        return consts.api.get_barset(symbols,'minute',limit=5,start=now,end=now).df.dropna().head(1)

def prices_up_to_yesterday(symbols, lookback=consts.lookback):
    now = pd.Timestamp.now(consts.NY)
    end_dt = now
    return get_prices_with_lookback(symbols, end_dt, lookback=lookback)


def get_prices_with_start_end(symbols, end_dt,start_dt):
    end_dt=pd.Timestamp(end_dt.year,end_dt.month,end_dt.day)
    start_dt=pd.Timestamp(start_dt.year,start_dt.month,start_dt.day)
    end_dt = end_dt.isoformat() +'Z'
    start_dt = start_dt.isoformat() +'Z'

    barset = None
    i = 0

    def get_barset(symbols):
        return consts.api.get_barset(symbols, timeframe='day', start=start_dt, end=end_dt)

    while i <= len(symbols) - 1:
        if barset is None:
            barset = get_barset(symbols[i:i + 200])
            df = barset.df
        else:
            barset.update(get_barset(symbols[i:i + 200]))
        i += 200
    return barset.df.dropna()


def get_prices_with_lookback(symbols, end_dt, lookback=consts.lookback):
    start_dt = end_dt - pd.Timedelta(str(lookback)+' days')
    return get_prices_with_start_end(symbols, end_dt=end_dt, start_dt=start_dt)