import helper
import logging
#return stock-weight pairs that sum to one
def get_target_portfolio_weights():
    pass

def get_positions(symbol_pairs, lookback = 20):
    for x,y in symbol_pairs:
        x_close = helper.prices(x).loc[:,x].loc[:,'close']
        y_close = helper.prices(y).loc[:, y].loc[:, 'close']
        try:
            hedge = get_hedge_ratio(y_close,x_close)
        except ValueError as e:
            logging.error(e)
            return
    pass



#OLS:Y=A+BX
def get_hedge_ratio(Y,X,add_const=True):

    pass