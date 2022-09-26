import pickle
import os
from parser_10KQ import get_word_list
import requests
directory = r'E:\10KQ'
filling_lem = {}
for filename in os.listdir(directory):
    f = os.path.join(directory, filename)
    if os.path.isfile(f):
        with open(f, 'rb') as handle:
            fillings_by_ticker = pickle.load(handle)
            for k, v in fillings_by_ticker.items():
                filling_lem[k] = {}
                for date in list(v.keys())[:20]:
                    filling_lem[k][date] = get_word_list(fillings_by_ticker[k][date])
                    print(k, "at", date, "finished")
        print(f, "finished")

with open(r'E:\10KQ', 'wb') as handle:
    pickle.dump(filling_lem, handle, protocol=pickle.HIGHEST_PROTOCOL)
    print("filling_lem saved.")