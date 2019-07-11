import test

NY='America/New_York'

print(test.api.list_positions())
print(test.prices('AAPL'))
print(test.prices('AAPL').loc[:,'AAPL'].loc[:,'close'])