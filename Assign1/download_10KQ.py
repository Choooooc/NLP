import nltk
import numpy as np
import pandas as pd
import pickle
import pprint
import project_helper
import project_tests
from tqdm import tqdm
from selenium import webdriver
from selenium.webdriver.edge.service import Service as EdgeService
from webdriver_manager.microsoft import EdgeChromiumDriverManager
from selenium.webdriver.common.by import By
from datetime import datetime
from selenium.webdriver import EdgeOptions
from parser_10KQ import get_word_list
from itertools import islice
from bs4 import BeautifulSoup
import requests
options = EdgeOptions()
options.add_argument("--headless")
options.add_argument("--window-size=%s" % "3840, 2160")

# headers for connecting to SEC
headers = {'Host': 'www.sec.gov', 'Connection': 'close',
           'Accept': 'application/json, text/javascript, */*; q=0.01',
           'X-Requested-With': 'XMLHttpRequest',
           'User-Agent': 'ruizhuoj@andrew.cmu.edu'
           }
endpoint = r"https://www.sec.gov/cgi-bin/browse-edgar"
base_url_sec = r"https://www.sec.gov"
sec_api = project_helper.SecAPI()
#break apart dictionaries
def chunks(data, SIZE=100):
    it = iter(data)
    for i in range(0, len(data), SIZE):
        yield {k:data[k] for k in islice(it, SIZE)}


### Get S&P500 CIKs
# Filter the sp500_constituents csv by removing companies that were out after 2017.
# Use the sp500_constituents permnos to filter sp500_data and get a dictionary of tickers and
# CIKs.
sp500_constituents = pd.read_csv("sp500_constituents.csv", dtype={"permno":int}, index_col=0)
sp500_constituents = sp500_constituents[(sp500_constituents["ending"] > "2017-01-01")]
sp500_data = pd.read_csv("sp500_w_addl_id_with_cik.csv",dtype={"cik":str, "permno":int})
sp500_data = sp500_data[["ticker", "permno", "cik"]].set_index("ticker")
sp500_data = sp500_data[sp500_data["permno"].isin(sp500_constituents["permno"])]
sp500_data.drop_duplicates(inplace=True)
sp500_data.dropna(inplace=True)
cik_lookup = sp500_data.to_dict()["cik"]
# download, parse and save 100 tickers at a time
counter = 0
for cik_lookup_s in chunks(cik_lookup, 10):
    counter += 1
    sec_data = {ticker: [] for ticker in cik_lookup_s}
    for ticker in cik_lookup_s:
        # define our parameters dictionary
        param_dict_10k = {'action': 'getcompany',
                          'CIK': cik_lookup_s[ticker],
                          'type': '10-k',
                          'dateb': '20220101',
                          'owner': 'exclude',
                          'start': '',
                          'output': '',
                          'count': '10'}
        # request the url, and then parse the response.
        response_10k = requests.get(url=endpoint, params=param_dict_10k, headers=headers)
        soup_10k = BeautifulSoup(response_10k.content, 'html.parser')
        doc_table_10k = soup_10k.find_all('table', class_='tableFile2')
        param_dict_10q = {'action': 'getcompany',
                          'CIK': cik_lookup_s[ticker],
                          'type': '10-Q',
                          'dateb': '20220101',
                          'owner': 'exclude',
                          'start': '',
                          'output': '',
                          'count': '20'}
        # request the url, and then parse the response.
        response_10q = requests.get(url=endpoint, params=param_dict_10q, headers=headers)
        soup_10q = BeautifulSoup(response_10q.content, 'html.parser')
        doc_table_10q = soup_10q.find_all('table', class_='tableFile2')
        # Get 10-Ks
        for row in doc_table_10k[0].find_all('tr'):
            # find all the columns
            cols = row.find_all('td')
            # if there are no columns move on to the next row.
            if len(cols) != 0:
                # grab the text
                filing_type = cols[0].text.strip()
                filing_date = cols[3].text.strip()
                if datetime.strptime(filing_date, '%Y-%m-%d').date() < datetime.strptime("2017", '%Y').date():
                    pass
                else:
                    filing_numb = cols[4].text.strip()
                    # find the links
                    filing_doc_href = cols[1].find('a', {'href': True, 'id': 'documentsbutton'})
                    filing_int_href = cols[1].find('a', {'href': True, 'id': 'interactiveDataBtn'})
                    filing_doc_link = base_url_sec + filing_doc_href['href']
                    sec_data[ticker].append((filing_doc_link, filing_type, filing_date))
        # Get 10-Qs
        for row in doc_table_10q[0].find_all('tr'):
            # find all the columns
            cols = row.find_all('td')
            # if there are no columns move on to the next row.
            if len(cols) != 0:
                # grab the text
                filing_type = cols[0].text.strip()
                filing_date = cols[3].text.strip()
                filing_numb = cols[4].text.strip()
                # find the links
                filing_doc_href = cols[1].find('a', {'href': True, 'id': 'documentsbutton'})
                filing_int_href = cols[1].find('a', {'href': True, 'id': 'interactiveDataBtn'})
                filing_doc_link = base_url_sec + filing_doc_href['href']
                sec_data[ticker].append((filing_doc_link, filing_type, filing_date))
        print(ticker, "request successful")

    fillings_by_ticker = {}
    browser = webdriver.Edge(service=EdgeService(EdgeChromiumDriverManager().install()))
    for ticker, data in sec_data.items():
        fillings_by_ticker[ticker] = {}
        for index_url, file_type, file_date in tqdm(data, desc='Downloading {} Fillings'.format(ticker),
                                                    unit='filling'):
            print(index_url, file_type, file_date)
            if (file_type == '10-K' or file_type == '10-Q'):
                file_url = index_url.replace('-index.htm', '.txt').replace('.txtl', '.txt')
                browser.get(file_url)
                raw_file = browser.find_element(By.TAG_NAME, "body").text
                file_lemmaR = get_word_list(raw_file)
                fillings_by_ticker[ticker][file_date] = file_lemmaR
    with open(r'E:\10KQ\fillings_by_ticker ' + str(counter), 'wb') as handle:
        pickle.dump(fillings_by_ticker, handle, protocol=pickle.HIGHEST_PROTOCOL)
        print("Batch", counter, "saved.")