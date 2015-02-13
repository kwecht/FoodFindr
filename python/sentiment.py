#!/usr/bin/env python

"""
sentiment.py
########################################################################
#
#        Kevin Wecht                21 January 2015
#
#    Insight Data Science Project:
#        Food Finder
#
########################################################################
#
#    sentiment.py
#        - builds sentiment dictionary for the lexicon
#        - contains functions to assist processing text for sentiment
#        - scores sentiment of given strings
#
#    EXAMPLE
#        
#
########################################################################
"""

__author__      = "Kevin Wecht"

########################################################################

import numpy as np
import pandas as pd
import scipy.sparse as sps
from nltk.stem import PorterStemmer
import external.potts_tokenizer as potts
import string
from sklearn.feature_extraction.text import TfidfVectorizer
import nltk
import collections

########################################################################


    # This code borrows very heavily, and often copies from:
    # http://www.cs.duke.edu/courses/spring14/compsci290/assignments/lab02.html


def stem_tokens(tokens,stemmer):
    """stems a list of tokens using the given stemmer.
    """
    stemmed = []
    for token in tokens:
        try:
            stemmed.append(str(stemmer.stem(token)))  # convert stem from unicode to str
        except:
            print "neglecting non-ascii character: ", token
    return stemmed


def tokenize(text):
    """takes raw text of review and prepares it for use in the sklearn.tfidf
        This consists of:
            1. tokenizing words with the potts sentiment tokenizer
            2. stemming english words using the Porter Stemmer
    """

    stemmer = PorterStemmer()
    tokens = potts.Tokenizer().tokenize(text)
    tokens = [t for t in tokens if (t not in string.punctuation) & (not any(char.isdigit() for char in t))]
    return stem_tokens(tokens, stemmer)


def get_bag(sentences,rawtext=False):
    """
    Returns pandas Series where the indices are lemmas and values are the 
    number of occurances of each distinct lemma in the text

    This is useful for making bag-of-words features of relative frequencies
    for classification.

    sentences - pandas dataframe of sentences as returned by 
                process_text.reviews_to_sentences
    rawtext   - accepts a string of text instead of a dataframe of sentences
    """

    # Tag each word with part of speech
    word_pos = []
    if rawtext==True:
        sentences = nltk.sent_tokenize(sentences)
        for sentence in sentences:
            result = nltk.pos_tag(nltk.word_tokenize(sentence))
            word_pos.extend(result)
    else:
        for sent in sentences.index:
            thissent = sentences.iloc[0]
            result = nltk.pos_tag(nltk.word_tokenize(sentences.loc[sent].text))
            word_pos.extend(result)

    # Count occurances of nouns, verbs, and adjectives
    # Filter for not punctuation
    count = collections.Counter(word_pos)
    count = {key: count[key] for key in count if key[1][0] in ['N','V','J']}
    count = {key: count[key] for key in count if key[0] not in string.punctuation}

    # Lemmatize the words in the counter
    lemmas = []
    for key,value in count.iteritems():
        pos = key[1][0].lower()
        if pos=='j': pos='a'
        output = nltk.stem.WordNetLemmatizer().lemmatize(key[0],pos=pos)
        lemmas.append((output,value))

    # Sum the number of occurances of each lemma
    final_count = {tup[0]: 0 for tup in lemmas}
    for row in lemmas:
        final_count[row[0]] += row[1]

    final_count = pd.Series(final_count,index=final_count.keys())
    #final_count.index.name = str(int(sentences.iloc[0].stars))
    
    return final_count



def make_bags(sentences):
    """
    Make bags of relative frequencies for bag-of-words features
    passed to a classification algorithm.

    Returns data in the form taking by the training algorithm

    sentences - pandas dataframe of sentences as returned by 
                process_text.reviews_to_sentences
    """

    # Split sentence data into N categories based on column of labels
    bags = []
    for nstar in sentences.stars.unique():
        print "processing stars = {}".format(nstar)
        thisdata = sentences[sentences['stars']==nstar]
        thisbag = get_bag(thisdata)
        thisbag.name = str(int(nstar))
        bags.append( thisbag )

    # bags is a list of pandas series. Concatenate them together in a dataframe
    dataframe = pd.concat(bags,axis=1)
    total = dataframe.sum(1)
    overallfreq = total / total.sum()

    # Threshold for filtering relative frequency of words
    threshold = 0.0002
    dataframe = dataframe[overallfreq>threshold]

    # Place relative frequencies into a format expected by the classifier


    return dataframe





