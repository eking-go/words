#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
'''

import sys
import os
import argparse
import yaml
import nltk
from nltk.corpus import stopwords, wordnet
from nltk.stem import WordNetLemmatizer
from dictionary_client import DictionaryClient
from prompt_toolkit.shortcuts import (message_dialog,
                                      checkboxlist_dialog,
                                      radiolist_dialog)


__author__ = 'Nikolay Gatilov'
__copyright__ = 'Nikolay Gatilov'
__license__ = 'GPL'
__version__ = '0.4.2021091010'
__maintainer__ = 'Nikolay Gatilov'
__email__ = 'eking.work@gmail.com'


def nltk_init() -> None:
    nltk.download('stopwords')
    nltk.download('punkt')
    nltk.download('wordnet')


# ----------------------------------------------------------------------------
# Working with set of words

def get_cleaned_words_list(filename: str) -> list:
    raw_words_list = get_words(filename)
    rwlws = remove_stopwords(raw_words_list)
    clear(rwlws)
    return rwlws


def get_words(filename: str) -> list:
    words = []
    try:
        with open(filename, 'r') as gwf:
            gw = gwf.read()
    except Exception as e:
        print(e)
        return []
    sentences = nltk.sent_tokenize(gw)
    for sentence in sentences:
        words.extend(nltk.word_tokenize(sentence))
    return list(map(lambda s: s.lower(), words))


def remove_stopwords(words: list) -> list:
    stop_words = set(stopwords.words("english"))
    without_stop_words = []
    for word in words:
        if word not in stop_words:
            without_stop_words.append(word)
    return without_stop_words


def clear(words: list) -> None:
    ss = set('\'"[]{},.?/\\')
    suffixes = set(["'ve", "'re", "'s", "'nt", "n't", "'d", "'ll"])
    s = ss | suffixes
    for word in words.copy():
        if (word in s) or (not word.isalpha()):
            words.remove(word)


def get_dict_lemmatized(words_list: list) -> dict:
    lemmatizer = WordNetLemmatizer()
    lrw = {}
    for word in words_list:
        main_form = lemmatizer.lemmatize(word, wordnet.VERB)
        if main_form not in lrw.keys():
            lrw[main_form] = {}
            lrw[main_form]['count'] = 1
            lrw[main_form]['forms'] = list()
            lrw[main_form]['forms'].append(word)
        else:
            lrw[main_form]['count'] = lrw[main_form]['count'] + 1
            lrw[main_form]['forms'].append(word)
            lrw[main_form]['forms'] = list(set(lrw[main_form]['forms']))
    return lrw


def translate(words_lmtzd: dict) -> None:
    try:
        dc = DictionaryClient()
        for wrd in words_lmtzd.keys():
            dfn = dc.define(wrd).content
            if dfn is not None:
                words_lmtzd[wrd]['def'] = dfn[0]['definition'].split('\n')[1:]
        dc.disconnect()
    except:
        pass


def exclude_known_words(wrds_lmtzd: dict, known_words: list) -> None:
    for knwd in known_words:
        wrds_lmtzd.pop(knwd, None)


def convert_for_sort_and_remove_redundancy(first_form: dict) -> dict:
    result_form = {}
    for w in first_form.keys():
        if first_form[w]['count'] not in result_form.keys():
            result_form[first_form[w]['count']] = []
        result_form[first_form[w]['count']].append(w)
        first_form[w].pop('count')
        if w in first_form[w]['forms']:
            first_form[w]['forms'].remove(w)
        if first_form[w]['forms'] == []:
            first_form[w].pop('forms')
    return result_form


def add_new_known_words(kw_list: list, c_lwd_l: dict) -> None:
    sorted_u_w = []
    for i in sorted(c_lwd_l.keys(), reverse=True):
        sorted_u_w.extend(sorted(c_lwd_l[i]))
    while len(sorted_u_w) > 0:
        val_l = list(map(lambda a: (a, a), sorted_u_w[:10]))
        sorted_u_w = sorted_u_w[10:]
        results_array = checkboxlist_dialog(title='Select already known words',
                                            values=val_l).run()
        if results_array is None:
            break
        kw_list.extend(results_array)


# ----------------------------------------------------------------------------
# Working with configuration

def get_config_file() -> str:
    current_folder = os.getcwd()
    if sys.platform.startswith('win'):
        folder = os.getenv('USERPROFILE', current_folder)
    else:
        home_folder = os.getenv('HOME', current_folder)
        folder = os.getenv('XDG_CONFIG_HOME', home_folder)
    prog_name = os.path.basename(sys.argv[0])
    if prog_name.endswith('.py'):
        prog_name = prog_name[:-3]
    return os.path.join(folder, '.' + prog_name + '.yaml')


def load_config(filename: str) -> dict:
    try:
        with open(filename, 'r') as lcf:
            result = yaml.load(lcf, Loader=yaml.SafeLoader)
        if isinstance(result, dict):
            return result
        print('Incorrect format of %s' % filename)
    except Exception as e:
        print(e)
    return {}


def save_config(filename: str, config_dict: dict) -> None:
    with open(filename, 'w') as scf:
        yaml.dump(config_dict,
                  scf,
                  default_flow_style=False,
                  allow_unicode=True)


def load_kw(filename: str) -> list:
    config = load_config(filename)
    if 'KnownWords' in config.keys():
        return config['KnownWords']
    return []


def save_kw(filename: str, kwl: list) -> None:
    config = load_config(filename)
    config['KnownWords'] = sorted(kwl)
    save_config(args.config_file, config)


# ============================================================================

if __name__ == "__main__":  # main
    parser = argparse.ArgumentParser(description=__doc__,
                                     epilog='version: %s' % __version__)
    parser.add_argument('txtfile',
                        help='File with text')
    parser.add_argument('--config-file',
                        dest='config_file',
                        default=get_config_file(),
                        help=('Config file (also with already known words), '
                              'default - %(default)s'))
    args = parser.parse_args()
    # download data files for NLTK
    nltk_init()
    # load config and known words
    kwlist = load_kw(args.config_file)
    # working with text file
    abs_file_name = os.path.abspath(args.txtfile)
    uw_file_name = abs_file_name + '.words'
    wswl = get_cleaned_words_list(abs_file_name)
    lwd = get_dict_lemmatized(wswl)
    num_total_w = len(lwd)
    exclude_known_words(lwd, kwlist)
    translate(lwd)
    num_unknown_w = len(lwd)
    # Message with statistics
    message_dialog(title='Statistics for file: %s' % abs_file_name,
                   text=('Total number of words: {ntw}\n'
                         'Unknown words:         {uw} ({uwp}%)'
                         ).format(ntw=num_total_w,
                                  uw=num_unknown_w,
                                  uwp=int(num_unknown_w*100.0/num_total_w))
                   ).run()
    # Dialog
    val = [(1, 'Nothing save, exit'),
           (2, ('Add to config {}\n    '
                'already known words from text and save unknown words'
                ).format(args.config_file)),
           (3, 'Only save unknown words in file\n    %s' % uw_file_name)
           ]
    bd_result = radiolist_dialog(title='What do you want now?',
                                 values=val,).run()
    if bd_result == 1:
        sys.exit()
    c_lwd = convert_for_sort_and_remove_redundancy(lwd)
    if bd_result == 2:
        add_new_known_words(kwlist, c_lwd)
        exclude_known_words(lwd, kwlist)
        save_kw(args.config_file, kwlist)
    with open(uw_file_name, 'w') as rf:
        yaml.dump(lwd, rf, default_flow_style=False, allow_unicode=True)
