import matplotlib.pyplot as plt
import statsmodels.api as sm
from statsmodels.tsa.stattools import coint,adfuller
import helper
import universe
from scipy.stats import jarque_bera
import ols_pairs_trading
import consts
import alpaca_trade_api
import pandas as pd
def get_actual_universe():
    actual_universe =[]
    for symbol in universe.Universe:
        try:
            asset = consts.api.get_asset(symbol)
        except alpaca_trade_api.rest.APIError as e:
            continue
        if asset.easy_to_borrow and asset.status == "active":
            actual_universe.append(symbol)

def gen_coint_from_sp500():
    #actual_universe = get_actual_universe()
    prices_up_to_yday = helper.prices_up_to_yesterday(universe.Universe, lookback=consts.lookback).dropna(axis=1)
    for x in universe.Universe:
        try:
            x_up_to_yday = prices_up_to_yday.loc[:, x].loc[:, 'close']
        except KeyError as e:
            #print("keyError:" + str(e))
            continue
        for y in universe.Universe:
            if(x is not y):
                try:
                    y_up_to_yday = prices_up_to_yday.loc[:, y].loc[:, 'close']
                except KeyError as e:
                    #print("keyError:" + str(e))
                    continue

                if len(prices_up_to_yday)!=0:
                    score, pvalue, _ = coint(x_up_to_yday, y_up_to_yday)

                    if pvalue<0.01:
                        new_X = sm.add_constant(x_up_to_yday)
                        model = sm.OLS(y_up_to_yday, new_X).fit()
                        A = model.params[0]
                        B = model.params[1]
                        spread = y_up_to_yday-B*x_up_to_yday
                        adfuller_pval = adfuller(spread)[1]
                        _, jarque_bera_pval = jarque_bera(spread)

                        if (adfuller_pval < 0.01) and (jarque_bera_pval>0.1):
                            spreads=ols_pairs_trading.get_spreads((x,y),model.params[1],lookback=consts.lookback,prices = prices_up_to_yday)
                            current_prices = helper.current_prices((x, y))
                            if len(current_prices)==0:
                                continue
                            x_current = current_prices.loc[:, x].loc[:, 'close'][-1]
                            y_current = current_prices.loc[:, y].loc[:, 'close'][-1]
                            diff= y_current-B*x_current
                            zscore = (diff - spreads.mean()) / spreads.std()
                            if(zscore>1) or (zscore<-1):
                                print("x:" + x + " y:" + y + " coint pval:" + str(pvalue))
                                print("x:" + x + " y:" + y + " adfuller pval (<0.05 means stationary):" + str(adfuller_pval) + " jarque_bera pval(>0.05 means normal):" + str(jarque_bera_pval))
                                print("last z-score: " + str(zscore) )
                                print("\n\n\n")
                                #plot_pair_and_spreads(x_up_to_yday, y_up_to_yday,model.params[1], model.params[0],x_symbol=x,y_symbol=y)



def test_coint(symbol_pair):
    prices_up_to_yday = helper.prices_up_to_yesterday(symbol_pair, lookback=consts.lookback).dropna()
    x_up_to_yday = prices_up_to_yday.loc[:, symbol_pair[0]].loc[:, 'close']
    y_up_to_yday = prices_up_to_yday.loc[:, symbol_pair[1]].loc[:, 'close']
    do_coint_with_price_data(x_up_to_yday,y_up_to_yday ,x=symbol_pair[0],y=symbol_pair[1])

def check_for_stationarity(X, cutoff=0.01):
    # H_0 in adfuller is unit root exists (non-stationary)
    # We must observe significant p-value to convince ourselves that the series is stationary
    pvalue = adfuller(X)[1]
    if pvalue < cutoff:
        print ('p-value = ' + str(pvalue) + ' The series is likely stationary.')
        return True
    else:
        print ('p-value = ' + str(pvalue) + ' The series is likely non-stationary.')
        return False
def plot_pair_and_spreads(X,Y,B,A, x_symbol='X', y_symbol='Y'):
    plt.plot(Y)
    plt.plot(X)
    plt.plot(A + B * X)
    spread = Y-B*X
    plt.plot(spread)
    #plt.plot(A)
    plt.legend([x_symbol
                   , y_symbol, 'reg', 'spread'])
    plt.show()
    plt.hist(spread)
    plt.show()

def do_coint_with_price_data(X,Y, x='X',y='Y'):
    score, pvalue, _ = coint(X, Y)
    print("x:" + x + " y:" + y + " coint pval:" + str(pvalue))

    new_X = sm.add_constant(X)
    model = sm.OLS(Y, new_X).fit()
    plot_pair_and_spreads(X,Y,model.params[1],model.params[0],x_symbol=x,y_symbol=y)
    spread = Y - model.params[1] * X
    adfuller_pval = adfuller(spread)[1]
    _, jarque_bera_pval = jarque_bera(spread)
    print("x:" + x + " y:" + y + " adfuller pval (<0.05 means stationary):" + str(
        adfuller_pval) + " jarque_bera pval(>0.05 means normal):" + str(jarque_bera_pval))

def do_coint(symbol_pair, start_day, end_day):
    prices = helper.get_prices_with_start_end(symbol_pair, end_dt=end_day, start_dt=start_day).dropna()
    X = prices.loc[:, symbol_pair[0]].loc[:, 'close']
    Y = prices.loc[:, symbol_pair[1]].loc[:, 'close']
    do_coint_with_price_data(X,Y,x=symbol_pair[0],y=symbol_pair[1])


def test_pairs():
    for pair in consts.pairs:
        test_coint(pair) #TODO:out of sample tests

