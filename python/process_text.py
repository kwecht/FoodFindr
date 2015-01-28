#!/usr/bin/env python

"""
process_text.py
########################################################################
#
#        Kevin Wecht                22 January 2015
#
#    Insight Data Science Project:
#        Food Finder
#
########################################################################
#
#    process_text.py
#        - processes text for many applications
#        - splits individual reviews into sentences
#
#    EXAMPLE
#        $ python initialize.py
#
########################################################################
"""

__author__      = "Kevin Wecht"

########################################################################

import pandas as pd
import numpy as np
import random
import nltk
import external.potts_tokenizer as ptk

########################################################################


#def add_training_label(sentences,review_data):
#    """
#    Adds column to pandas dataframe of sentences that holds hand-labeled 
#    values for classification (sentiment from 1-5 stars).
#
#    sentences  - pandas dataframe returned by reviews_to_sentences
#
#    returns same pandas dataframe with an extra column. All values of 
#        the new column are np.nan (NULL) except those selected
#        for hand labeling, which contain 0.
#    """
#
#    sentences['hand_label'] = np.nan
#
#    # select restaurants to be included in the training set
#    random.seed(1234)
#    busids = random.sample(review_data.business_id,20)
#    revids = review_data['review_id'][review_data.business_id.isin(busids)]
#    sentences['hand_label'][sentences.review_id.isin(revids)] = 0
#
#    return sentences



def reviews_to_sentences(append_string=''):
    """
    Divide reviews into individual sentences. 

    Save as pandas dataframe and save as a mysql table.

    append_string - Default = ''
                    Otherwise, adds the append_string
                    to the filename and table name
                    saved during this function.
    """

    # Restore all reviews from file
    reviews = pd.read_pickle('../data/pandas/review'+append_string+'.pkl')

    # Split reviews into sentences
    sentences = []
    total_count = 0
    for rev_id in reviews.review_id:
        thisreview = reviews[reviews.review_id==rev_id]
        sents = nltk.sent_tokenize(thisreview.text.values[0]) # nltk sentence tokenize
        thissent_count = 0
        for sent in sents:
            sentid = str(thissent_count).zfill(5)
            thisseries = pd.Series([thisreview.review_id.values[0],sentid,sent,thisreview.stars.values[0]])
            sentences.append(thisseries)
            thissent_count += 1
            total_count += 1
    
    # Convert to dataframe and save sentences dataframe to file
    dataframe = pd.concat(sentences,axis=1).T
    dataframe.columns = ['review_id','sentence_id','text','stars']

    # Save pandas dataframe to file
    dataframe.to_pickle('../data/pandas/sentences'+append_string+'.pkl')
    #result = sqlfuncs.make_sentence_db(sentences)

    return True

def text2pos(string):
    """
    Convert text input to part of speech tags.
    """
    pos_tags = []

    # Split string into sentences and operate on each sentence
    sentences = nltk.sent_tokenize(string)
    for sentence in sentences:
        tokens = nltk.word_tokenize(sentence)
        tokens = [x.lower() for x in tokens]
        pos_tags.extend(nltk.pos_tag(tokens))

    return pos_tags


def pos2lemmas(pos_tags):
    """
    Return list of word, pos-tags in which each word has been lemmatized.
    pos_tags is a list of word, pos-tag pairs returned by text2pos.
    """

    from nltk.corpus import wordnet as wn

    # Lemmatizer to use
    wnl = nltk.stem.WordNetLemmatizer()

    # mapping of PennTreebank part of speech tags to input for lemmatizer
    pos_mapper = {'NN':wn.NOUN,'VB':wn.VERB,'JJ':wn.ADJ,'RB':wn.ADV}

    lemmas = []
    pos    = []
    for pair in pos_tags:

        # Include pos tags when lemmatizing nouns, verbs, adjectives, and adverbs
        if pair[1][0:2] in pos_mapper.keys():
            thispos = pos_mapper[pair[1][0:2]]
            thislemma = wnl.lemmatize(pair[0],thispos)
        else:
            thispos = pair[1]
            thislemma = wnl.lemmatize(pair[0])
        lemmas.append(thislemma)
        pos.append(thispos)

    return (lemmas, pos)


def handle_negation(lemmas,pos):
    """
    If "not" or "n't" occurs immediately before a verb or adjective,
    replace the verb or adjective with not_verb or not_adjective
    """

    from nltk.corpus import wordnet as wn

    # Prepend "not_" to words following "not" or "n't"
    not_index = []
    for ii in range(1,len(lemmas)):
        if (lemmas[ii-1].lower() in ["not","n't"]) & (pos[ii] in [wn.VERB,wn.ADJ]):
            lemmas[ii] = 'not_' + lemmas[ii]
            not_index.append(ii-1)
    
    # Remove instances of "not" and "n't"
    lemmas = [value for index,value in enumerate(lemmas) if index not in not_index]
    pos    = [value for index,value in enumerate(pos) if index not in not_index]

    return lemmas,pos


def addNgrams(lemmas,pos,N_gram,N_return=20,min_occur=3):
    """
    Adds N_return most common N-grams to the lemmas already created.
    N-grams must occur at least min_occur times.

    lemmas - list of lemmas as returned by pos2lemmas or handle_negation
    pos - list of parts of speech as returned by pos2lemmas or handle_negation
    N_gram - integer (2 or 3 currently supported). return N-grams
    N_return - Return N_return most common N-grams
    min_occur - Filter out N-grams that occur less than min_occur times
    """

    import pdb

    from nltk.collocations import BigramCollocationFinder, TrigramCollocationFinder
    from nltk.metrics import BigramAssocMeasures, TrigramAssocMeasures

    # Determine whether finding bi or tri grams
    if N_gram==2: 
        finder = BigramCollocationFinder.from_words(lemmas)
        test   = BigramAssocMeasures.chi_sq
    if N_gram==3: 
        finder = TrigramCollocationFinder.from_words(lemmas)
        test   = TrigramAssocMeasures.chi_sq

    # Find N-grams
    finder.apply_freq_filter(min_occur)
    try:
        ngrams = finder.nbest(test,N_return)
    except:
        ngrams = []

    # Add N grams to list of lemmas, replacing the adjacent terms that form the N grams
    for gram in ngrams:
        lemmas.append('_'.join(gram))
        pos.append(str(N_gram)+'gram')

    return lemmas, pos


def remove_pos(lemmas,pos,keep=[]):
    """
    Remove lemmas with parts of speech in the list remove.
    
    lemmas - list of lemmas as returned by pos2lemmas, 
             handle_negation, or addNgrams
    pos - list of parts of speech as returned by pos2lemmas, 
          handle_negation, or addNgrams
    keep - list of parts of speech to keep from the list of lemmas
    """

    temp = [(l,p) for l,p in zip(lemmas,pos) if p in keep]
    if len(temp)!=0: 
        new_lemmas, new_pos = zip(*temp)
    else:
        new_lemmas = lemmas
        new_pos = pos
    return new_lemmas, new_pos

def remove_punctuation(lemmas,pos):
    """
    Return lemma and pos lists with all items removed that contain 
    punctuation (other than an apostraphe and underscore).
    """

    import string
    import re

    table = string.maketrans("","")
    punct = string.punctuation
    keep = ["'","_"]
    for k in keep:
        punct = punct.replace(k,'')

    regex = re.compile('[%s]' % re.escape(punct))
    newlemmas = [regex.sub('',l) for l in lemmas]

    # Remove empty strings
    try:
        temp = [(l,p) for l,p in zip(newlemmas,pos) if l!=""]
        newlemmas, newpos = zip(*temp)
        newlemmas = list(newlemmas)
        newpos = list(newpos)
    except:
        nostrings_here = True
        newlemmas = []
        newpos = []

    return newlemmas, newpos


def remove_duplicate_grams(lemmas,pos):
    """
    Remove Ngrams that are also part of identified (N+1)grams
    For example, bigrams of "fried rice" will be removed if 
        "chicken fried rice" is in the list of lemmas.

    This function is not written (1/25/2015)
    """

    return None


def text2lemmas(string):
    """
    Converts a string of text into a list of lemmas extracted from the text.
    """
    from nltk.corpus import wordnet as wn

    # Array to hold lemmas for output
    lemmas = []

    # Calculate pos_tag for each word in the string
    pos_tags = text2pos(string)

    # Lemmatize each word in the string
    lemmas, pos = pos2lemmas(pos_tags)

    # Remove lemmas with punctuation
    lemmas, pos = remove_punctuation(lemmas,pos)

    # Negation handling
    #   If "not" or "n't" occurs immediately before a verb or adjective,
    #   replace the verb or adjective with not_verb or not_adjective
    lemmas,pos = handle_negation(lemmas,pos)

    # N-gram identification
    lemmas, pos = addNgrams(lemmas,pos,2)   # bigrams
    lemmas, pos = addNgrams(lemmas,pos,3)   # trigrams
    # lemmas, pos = remove_duplicate_grams(lemmas, pos). obsolete 1/25/2015

    # Remove parts of speech that are not noun, verb, adjective, adverb, or Ngram
    lemmas, pos = remove_pos(lemmas,pos,keep=[wn.NOUN,wn.VERB,wn.ADJ,wn.ADV,'2gram','3gram'])

    return lemmas







#def word_count(lemmas,append_string=''):
#    """
#    Count frequency of words in a list of lemmas.
#    """
#    import sentiment
#
#    sentences = pd.read_pickle('../data/pandas/sentences'+append_string+'.pkl')
#
#    bags = []
#    for nstar in sentences.stars.unique():
#        print "processing stars = {}".format(nstar)
#        thisdata = sentences[sentences['stars']==nstar]
#        thisbag = sentiment.get_bag(thisdata)  # only keeps nouns, adjectives, verbs
#        thisbag.name = str(int(nstar))
#        bags.append( thisbag )
#    
#    dataframe = pd.concat(bags,axis=1)
#    dataframe.to_pickle('../data/pandas/word_count'+append_string+'.pkl')
#
#    return True
#
#
#def trim_word_count(words,how='',freq_threshold=0.0002,N=None):
#    """
#    Trims the bag of words prodoced by word_count().
#    Used to select meaningful words that will be passed to 
#    a classifier to determine how many stars a given 
#    piece of text should have (entire review or single sentence).
#
#    words  - a pandas dataframe produced by word_count()
#    how    - string indicating the way in which to trim the words
#             {'unique'|'frequency'}
#             unique    - keep the N most unique words in each category
#                         where unique is defined as the ratio of
#                         frequency-in-category : frequency-out-of-category
#             frequency - keep all words that occur in the corpus with
#                         frequency >= freq_threshold.
#    N      - if how='unique': keep N most unique words in each category
#    freq_threshold - keep all words that occur in the corpus
#                     with frequency >= freq_threshold
#    """
#
#    # Only keep words that occur above a threshold frequency
#    total = words.sum(1)
#    overallfreq = total / total.sum()
#    words = words[overallfreq>freq_threshold]
#
#    # Only keep words that are unique to a given category
#    if how=='unique':
#        
#        # Find all words that are unique to each category
#        keepwords = []
#        for col in words:
#            relfreq = words[col].div(words.sum(1),axis='index')
#            relfreq.order(ascending=False,inplace=True)
#            keepwords.extend(relfreq.index[0:N])
#
#        # Trim words dataframe for those words
#        if len(set(keepwords))==len(keepwords):
#            print "Warning in process_text.trim_word_count"
#            print "   Some words are important for more than one category."
#        words = words.loc[keepwords]
#        words.drop_duplicates(inplace=True)
#
#    return words
