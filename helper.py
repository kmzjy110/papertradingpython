import consts
import pandas as pd
import time
import logging

def get_current_portfolio_weights():
    share_counts = get_current_portfolio_positions()
    if share_counts is None:
        return pd.DataFrame()
    cum_prices = current_prices([c[0] for c in share_counts.columns])

    prices = pd.DataFrame()
    for column in cum_prices.columns:
        prices.loc[:, column[0]] = [cum_prices.loc[:, column[0]].loc[:, 'close'][0]]
    current_weights = share_counts *prices / consts.api.get_account().equity
    return current_weights

def get_current_portfolio_positions():
    positions = consts.api.list_positions()
    if not positions:
        return None
    symbols = pd.Index([p.symbol for p in positions])
    quantities = [p.qty for p in positions]
    share_counts = pd.Series(
        index=symbols,
        data=quantities
    )
    return share_counts

def current_prices(symbols):
    now = pd.Timestamp.now(consts.NY)
    if not consts.api.get_clock().is_open:
        market_close = now.replace(hour=15, minute=59,second=0,microsecond=0)
        if now >= market_close:
            start = now.replace(hour=15, minute=00,second=0,microsecond=0).isoformat()[:19]+'Z'
            end = market_close.isoformat()[:19]+'Z'
            df = consts.api.get_barset(symbols,'minute',limit=60,start=start,end=end).df
            df_dropped = df.dropna()
            return df_dropped.tail(1)
        else:
            return prices_up_to_yesterday(symbols, lookback=1).dropna().tail(1)
    else:
        return consts.api.get_barset(symbols,'minute',limit=20,start=now-pd.Timedelta('5 minutes'),end=now).df.dropna().tail(1)

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
        else:
            barset.update(get_barset(symbols[i:i + 200]))
        i += 200

    return barset.df


def get_prices_with_lookback(symbols, end_dt, lookback=consts.lookback):
    start_dt = end_dt - pd.Timedelta(str(lookback)+' days')
    return get_prices_with_start_end(symbols, end_dt=end_dt, start_dt=start_dt)


def get_share_numbers(total_dollar, weights):
    #df = pd.DataFrame(columns=consts.columns)
    #df.loc[0] = weights
    dollar_values = weights*total_dollar
    prices = current_prices(consts.columns)
    numshares = pd.DataFrame()
    for column in prices.columns:
        numshares.loc[:,column[0]] = [prices.loc[:,column[0]].loc[:,'close'][0]]
    numshares= dollar_values/numshares
    return numshares