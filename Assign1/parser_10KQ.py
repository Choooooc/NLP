import re
import pandas as pd
from bs4 import BeautifulSoup
from nltk.stem import WordNetLemmatizer
from nltk.corpus import stopwords
def lemmatize_words(words):
    lemmatized_words = [WordNetLemmatizer().lemmatize(word, 'v') for word in words]
    return lemmatized_words

def parse_10KQ(raw_file, pos_dat):
    items = pos_dat.index.to_list()
    item_raw = ""
    for i in range(1, len(items)):
        item_raw += raw_file[pos_dat['start'].iloc[i-1]:pos_dat['start'].iloc[i]]
    item_raw += raw_file[pos_dat['start'].iloc[-1]:]
    return BeautifulSoup(item_raw, 'lxml')

def get_word_list(raw_file):
    # Regex to find <DOCUMENT> tags
    doc_start_pattern = re.compile(r'<DOCUMENT>')
    doc_end_pattern = re.compile(r'</DOCUMENT>')
    # Regex to find <TYPE> tag prceeding any characters, terminating at new line
    type_pattern = re.compile(r'<TYPE>[^\n]+')
    doc_start_is = [x.end() for x in doc_start_pattern.finditer(raw_file)]
    doc_end_is = [x.start() for x in doc_end_pattern.finditer(raw_file)]
    doc_types = [x[len('<TYPE>'):] for x in type_pattern.findall(raw_file)]
    document = {}
    # TODO: Fix re.compile
    regex_10k = re.compile(r'(>Item(\s|&#160;|&nbsp;)(1A|1B|7A|7|8)\.{0,1})|(ITEM\s(1A|1B|7A|7|8))')
    #regex_10q = re.compile(r'(>(Item|ITEM)(\s|&#160;|&nbsp;)(1A|1B|7A|7|8)\.{0,1})')
    regex_10q = re.compile(r'(>Item(\s|&#160;|&nbsp;)(1A|2|3|4|5))\.{0,1}|(ITEM\s(1A|2|3|4|5|))')
    # Create a loop to go through each section type and save only the 10-K section in the dictionary
    for doc_type, doc_start, doc_end in zip(doc_types, doc_start_is, doc_end_is):
        if doc_type == '10-K' or '10-Q':
            document[doc_type] = raw_file[doc_start:doc_end]
    if '10-K' in document:
        matches = regex_10k.finditer(document['10-K'])
        test_df = pd.DataFrame([(x.group(), x.start(), x.end()) for x in matches])
        if len(test_df)==0:
            return []
        test_df.columns = ['item', 'start', 'end']
        test_df['item'] = test_df.item.str.lower()
        test_df.replace('&#160;', ' ', regex=True, inplace=True)
        test_df.replace('&nbsp;', ' ', regex=True, inplace=True)
        test_df.replace(' ', '', regex=True, inplace=True)
        test_df.replace('\.', '', regex=True, inplace=True)
        test_df.replace('>', '', regex=True, inplace=True)
        pos_dat = test_df.sort_values('start', ascending=True).drop_duplicates(subset=['item'], keep='last')
        pos_dat.reset_index(drop=True)
        pos_dat.dropna(inplace=True)
        item_content = parse_10KQ(raw_file, pos_dat)
        file_clean = item_content.get_text("\n\n")
        word_pattern = re.compile('\w+')
        file_lemma = lemmatize_words(word_pattern.findall(file_clean))
        lemma_english_stopwords = lemmatize_words(stopwords.words('english'))
        file_lemmaR = [word for word in file_lemma if word not in lemma_english_stopwords]
        file_lemmaR = [x.lower() for x in file_lemmaR if re.match('[a-zA-Z]',x[0])]
    elif "10-Q" in document:
        matches = regex_10q.finditer(document["10-Q"])
        test_df = pd.DataFrame([(x.group(), x.start(), x.end()) for x in matches])
        if len(test_df)==0:
            return []
        test_df.columns = ['item', 'start', 'end']
        test_df['item'] = test_df.item.str.lower()
        test_df.replace('&#160;', ' ', regex=True, inplace=True)
        test_df.replace('&nbsp;', ' ', regex=True, inplace=True)
        test_df.replace(' ', '', regex=True, inplace=True)
        test_df.replace('\.', '', regex=True, inplace=True)
        test_df.replace('>', '', regex=True, inplace=True)
        #pos_dat = test_df.sort_values('start', ascending=True).drop_duplicates(subset=['item'], keep='last')
        pos_dat = test_df.copy().reset_index(drop=True)
        pos_dat.dropna(inplace=True)
        item_content = parse_10KQ(raw_file, pos_dat)
        file_clean = item_content.get_text("\n\n")
        word_pattern = re.compile('\w+')
        file_lemma = lemmatize_words(word_pattern.findall(file_clean))
        lemma_english_stopwords = lemmatize_words(stopwords.words('english'))
        file_lemmaR = [word for word in file_lemma if word not in lemma_english_stopwords]
        file_lemmaR = [x.lower() for x in file_lemmaR if re.match('[a-zA-Z]',x[0])]
    return file_lemmaR
