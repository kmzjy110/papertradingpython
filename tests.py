import matplotlib.pyplot as plt
import statsmodels.api as sm
from statsmodels.tsa.stattools import coint,adfuller
import helper
import pandas as pd
from scipy.stats import jarque_bera
def test_coint(symbol_pair):
    prices_up_to_yday = helper.prices_up_to_yesterday(symbol_pair, lookback=200)
    x_up_to_yday = prices_up_to_yday.loc[:, symbol_pair[0]].loc[:, 'close']
    y_up_to_yday = prices_up_to_yday.loc[:, symbol_pair[1]].loc[:, 'close']
    do_coint_with_price_data(x_up_to_yday,y_up_to_yday)

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

def do_coint_with_price_data(X,Y):
    score, pvalue, _ = coint(X, Y)
    print("coint pvalue:" + str(pvalue))

    new_X = sm.add_constant(X)
    model = sm.OLS(Y, new_X).fit()
    plt.plot(Y)
    plt.plot(X)
    plt.plot(model.params[0] + model.params[1] * X)

    spread = Y - model.params[1] * X
    plt.plot(spread)
    plt.plot(spread - model.params[0])
    check_for_stationarity(spread, 0.1)
    plt.legend(['Y', 'X', 'reg', 'spread', 'spread-normalized'])
    plt.show()

    plt.hist(spread)
    plt.show()

    jb, pval = jarque_bera(spread)
    print("jarque bera pval of spread: " + str(pval))

def do_coint(symbol_pair, start_day, end_day):
    prices = helper.get_prices_with_start_end(symbol_pair, end_dt=end_day, start_dt=start_day)
    X = prices.loc[:, symbol_pair[0]].loc[:, 'close']
    Y = prices.loc[:, symbol_pair[1]].loc[:, 'close']
    do_coint_with_price_data(X,Y)

