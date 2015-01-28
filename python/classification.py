#!/usr/bin/env python

"""
initialize.py
########################################################################
#
#        Kevin Wecht                26 January 2015
#
#    Insight Data Science Project:
#        Food Finder
#
########################################################################
#
#    classification.py
#        - Prepares data for insertion into a classification algorithm
#        - Trains and tests classifcation algorithms
#        - Makes predictions based on trained classification algorithms
#
#
########################################################################
"""

__author__      = "Kevin Wecht"

########################################################################

import pandas as pd
import pdb

########################################################################

def lemma_count(type_string='',by='stars',append_string='',save=False):
    """
    Count number of occurences of lemmas in a given group of reviews/sentences

    type_string = {'review'|'sentences'}  determines whether to look in
                  text of pandas dataframe of reviews or sentences
    by = 'stars'  determines which column of the incoming dataframe on 
         which to group for the counting. Default is 'stars'
    append_string = {''|'_mexican'|'_mexican_train'}  determines
                    which dataframe is counted.
    """

    from collections import Counter

    # Restore dataframe from file for counting lemmas
    dataframe = pd.read_pickle('../data/pandas/'+type_string+'_lemmas'+append_string+'.pkl')

    # Initialize list of Counter collections to hold lemma counts
    groups = dataframe[by].unique()
    counters = []

    # Count lemmas in each group
    for i,g in enumerate(groups):
        thiscounter = Counter()
        thisgroup = dataframe[dataframe[by]==g].lemmas
        for lemmas in thisgroup:
            thiscounter.update(lemmas)
        counters.append(thiscounter)

    # Convert lemma counts to pandas dataframe
    group_names = [str(group) for group in groups]
    newdata = pd.DataFrame(counters,index=group_names)

    if save==True:
        newdata.to_pickle('../data/pandas/'+type_string+'_lemmaCount'+append_string+'.pkl')

    return newdata


def build_lemma_list(lemmaCount,interrogate=False):
    """
    Write lemmas that will be used for modeling to file.
    Trim lemmas by a number of methods:
         1) threshold number of counts (N>10)
         2) keep 200 most unique lemmas in each star category

    Returns pandas dataframe of lemma counts for each lemma kept
    after building the trimmed list.

    interrogate - if True, prints diagnostics about the vocabulary
                  selection to screen. It uses extra memory and takes
                  time, so do not use after deployment.
    """

    if interrogate==True: original_lemmaCount = lemmaCount

    # 1) Trim by threshold
    N = 10
    lemmaCount = lemmaCount.loc[:,lemmaCount.max()>N]
    if interrogate==True: trimmed_lemmaCount = lemmaCount

    # 2) Trim by ratio of term frequency in group vs. out of group
    # Find all words that are unique to each group
    N = 200    # Keep N most unique words in each group
    wordmatch = {}
    keeplemmas = []
    for ind in lemmaCount.index:
        relfreq = lemmaCount.loc[ind,:].div(lemmaCount.sum(0),axis='index')
        relfreq.order(ascending=False,inplace=True)
        keeplemmas.extend(relfreq.index[0:N])
        wordmatch[str(ind)] = relfreq.index[0:N]

    if interrogate==True: full_lemmalist = keeplemmas


    # Trim lemmaCount dataframe for those lemmaCount
    keeplemmas = list(set(keeplemmas))
    lemmaCount = lemmaCount.loc[:,keeplemmas]
    #lemmaCount.drop_duplicates(inplace=True)



    # Investigate properties of the words that I pull out to use
    #     as representative of the vocabulary.
    # Turn off when running production code.
    if interrogate==True:
        result = interrogate_vocab(wordmatch,lemmaCount,
                                   full_lemmalist,original_lemmaCount,
                                   trimmed_lemmaCount,append_string='_mexican')


    # Save list of lemmas to use for training
    with open('../data/pandas/lemma_list.txt', 'w') as f:
        for s in keeplemmas:
            f.write(s.encode('unicode-escape'))
            f.write('\n')

    # Read list from file
    #with open(the_filename, 'r') as f:
    #    my_list = [line.decode('unicode-escape').rstrip(u'\n') for line in f]

    return lemmaCount



def anyinlist(mainlist,sublist):
    return any([s in mainlist for s in sublist])


def interrogate_vocab(wordmatch, lemmaCount, keeplemmas, 
                      original_lemmaCount, trimmed_lemmaCount,
                      append_string=''):
    """
    Prints statistics (and makes plots?) about the vocabulary 
    that I have selected to perform the classification. For example,
        - how many reviews/sentences does the vocab cover? for each group?
        -    follow-up: what's the expected number of key words in a given sentence?
        -        --> important to keep high or sentence will go unscored.
        - in which groups are the duplicates found?

    This function is to be called when compiling the vocabulary in build_lemma_list()
    """

    #---------------------------------------------------------------------------
    # What range of the vocabulary am I cutting out when I make the unique words?
    print "-"*60
    print "  Number of unique lemmas in each group"
    print "At start :   Total = ", len(original_lemmaCount.columns)
    print original_lemmaCount.count(1).sort_index(ascending=False)
    print ""
    print "After threshold N_Occurences :   Total = ", len(trimmed_lemmaCount.columns)
    print trimmed_lemmaCount.count(1).sort_index(ascending=False)
    print ""
    print "After Ratio filtering (final) :   Total = ", len(lemmaCount.columns)
    print lemmaCount.count(1).sort_index(ascending=False)
    print ""
    print ""

    #---------------------------------------------------------------------------
    # What fraction of the vocabulary am I cutting out when I make the unique words?
    print "-"*60
    print "  Number of total lemmas in each group"
    print "At start :   Total = ", original_lemmaCount.sum(1).sum()
    print original_lemmaCount.sum(1).sort_index(ascending=False)#.div(original_lemmaCount.sum(1))
    print ""
    print "After threshold N_Occurences :   Total = ", trimmed_lemmaCount.sum(1).sum()
    print trimmed_lemmaCount.sum(1).sort_index(ascending=False)#.div(original_lemmaCount.sum(1))
    print ""
    print "After Ratio filtering (final) :   Total = ", lemmaCount.sum(1).sum()
    print lemmaCount.sum(1).sort_index(ascending=False)#.div(original_lemmaCount.sum(1))
    print ""
    print ""


    #---------------------------------------------------------------------------
    # What fraction reviews/sentences am I losing with the given trimming?
    # read review and sentence pickle data
    import functools
    reviews = pd.read_pickle('../data/pandas/review_lemmas'+append_string+'.pkl')
    sentences = pd.read_pickle('../data/pandas/sentences_lemmas'+append_string+'.pkl')
    mykeeplemmas = list(set(keeplemmas))
    ntest = 1000
    wrappedfunc = functools.partial(anyinlist,mykeeplemmas)
    for star in range(1,6):
        rr = reviews[reviews['stars']==star].iloc[0:ntest,:]
        ss = sentences[sentences['stars']==star].iloc[0:ntest,:]
        print "Stars = ",star
        print "Approx. fraction of reviews with key terms: ", sum(rr.lemmas.map(wrappedfunc))/float(ntest)
        print "Approx. fraction of sentences with key terms: ", sum(ss.lemmas.map(wrappedfunc))/float(ntest)
        print ""
    print ""


    #---------------------------------------------------------------------------
    # In which categories the duplicate words exist?
    #     Mostly with star ratings of 2,1,3 in decreasing order (kjw, 1/27/2015)
    ndups = {}
    dups = [l for l in keeplemmas if keeplemmas.count(l)>1]
    for ind in trimmed_lemmaCount.index:
        templist = []
        for dup in list(set(dups)):
            if dup in wordmatch[str(ind)]:
                templist.append(dup)
        ndups[str(ind)] = templist

    print "-"*60
    print "Number of duplicates found in each category: "
    for ind in trimmed_lemmaCount.index:
        print "    ", ind, len(ndups[str(ind)])


    return True
