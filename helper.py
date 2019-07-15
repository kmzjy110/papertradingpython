import consts
import pandas as pd
import time
import logging

def get_current_portfolio_weights():
    share_counts = get_current_portfolio_positions()
    if share_counts.empty:
        return pd.DataFrame()
    cum_prices = current_prices([c for c in share_counts.columns])

    prices = pd.DataFrame()
    for column in cum_prices.columns:
        prices.loc[:, column[0]] = [cum_prices.loc[:, column[0]].loc[:, 'close'][0]]
    current_weights = share_counts*prices/float(consts.api.get_account().equity)
    return current_weights

def get_current_portfolio_positions():
    positions = consts.api.list_positions()
    positions_df = pd.DataFrame()
    if not positions:
        return positions_df

    for position in positions:
        positions_df.loc[:,position.symbol] = [float(position.qty)]
    return positions_df


def current_prices(symbols):
    now = pd.Timestamp.now(consts.NY).replace(second=0,microsecond=0)
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
        end = now.isoformat()+'Z'
        start = (now-pd.Timedelta('20 minutes')).isoformat()+'Z'
        df = consts.api.get_barset(symbols,'1Min',limit=1,start=start,end=end)
        df = df.df
        return df.ffill().tail(1)

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

def trade(orders, wait = 100):
    sells = [o for o in orders if o['side'] == 'sell']
    for order in sells:
        try:
            logging.info(f'submit (sell):{order}')
            consts.api.submit_order(
                symbol=order['symbol'],
                qty=order['qty'],
                side='sell',
                type = 'market',
                time_in_force='day'
            )
        except Exception as e:
            logging.error(e)
    count = wait
    pending = consts.api.list_orders()
    while len(pending)>0:
        pending = consts.api.list_orders()
        if len(pending)==0:
            logging.info('all sell orders done')
            break
        logging.info(f'{len(pending)} sell orders pending...')
        time.sleep(1)
        count -=1

    buys = [o for o in orders if o['side']=='buy']
    for order in buys:
        try:
            logging.info(f'submit (buy):{order}')
            consts.api.submit_order(
                symbol=order['symbol'],
                qty=order['qty'],
                side='buy',
                type = 'market',
                time_in_force='day'
            )
        except Exception as e:
            logging.error(e)
    count = wait
    pending = consts.api.list_orders()
    while len(pending) > 0:
        pending = consts.api.list_orders()
        if len(pending) == 0:
            logging.info('all buy orders done')
            break
        logging.info(f'{len(pending)} buy orders pending...')
        time.sleep(1)
        count -= 1