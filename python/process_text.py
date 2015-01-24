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

def reviews_to_sentences(review_data):
    """
    splits reviews into individual sentences.

    review_data  - pandas dataframe returned by initialize.read_yelp
    
    returns pandas dataframe with each row corresponding to a sentence
        and a new column for sentenceID within each review.
    """

    # Split reviews into sentences
    sentences = pd.DataFrame(columns=['review_id','sentence_id','text','stars'])
    total_count = 0
    for rev_id in reviews.review_id:
        thisreview = reviews[reviews.review_id==rev_id]
        sents = nltk.sent_tokenize(thisreview.text.values[0]) # nltk sentence tokenizer
        #temp = [sent.split('\n') for sent in sents]
        #sents = [item for sublist in temp for item in sublist]
        thissent_count = 0
        for sent in sents:
            sentid = str(thissent_count).zfill(5)
            sentences.loc[total_count] = [thisreview.review_id.values[0],sentid,sent,thisreview.stars.values[0]]
            thissent_count += 1
            total_count += 1

    return sentences



def add_training_label(sentences,review_data):
    """
    Adds column to pandas dataframe of sentences that holds hand-labeled 
    values for classification (sentiment from 1-5 stars).

    sentences  - pandas dataframe returned by reviews_to_sentences

    returns same pandas dataframe with an extra column. All values of 
        the new column are np.nan (NULL) except those selected
        for hand labeling, which contain 0.
    """

    sentences['hand_label'] = np.nan

    # select restaurants to be included in the training set
    random.seed(1234)
    busids = random.sample(review_data.business_id,20)
    revids = review_data['review_id'][review_data.business_id.isin(busids)]
    sentences['hand_label'][sentences.review_id.isin(revids)] = 0

    return sentences
