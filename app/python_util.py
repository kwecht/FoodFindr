#!/usr/bin/env python

"""
python_util.py
########################################################################
#
#        Kevin Wecht                22 January 2015
#
#    Insight Data Science Project:
#        Food Finder
#
########################################################################
#
#    python_util.py
#        - Contains functions for parsing and manipulating information
#          passed through the web front-end.
#
#    FUNCTIONS
#        FFscore_from_group - calculates FoodFindr score from a 
#            pandas dataframe of scored sentences, grouped by restaurant.
#
########################################################################
"""

__author__      = "Kevin Wecht"

########################################################################

import pymysql as db
import numpy as np
import sql_cfg
import pandas as pd
from flask import render_template
import string

########################################################################


def FFscore_from_group(group):
    """
    Returns bayesian estimate of rating as the FoodFindr score from a 
    pandas dataframe of scored sentences, grouped by restaurant.

    Assumes a Dirichlet prior whose distribution is taken from
    all FoodFindr scored sentences in the database. The strength
    of the prior is set in the first line of the function. For more
    info: http://masanjin.net/blog/how-to-rank-products-based-on-user-input
    """

    # prior distribution manually entered from the distribution
    #    of scores across all sentences
    prior_strength = 10.
    prior = np.array([16711,10247,17443,51856,50386])
    prior = prior_strength*prior/prior.sum()

    # Value of a vote for each category.
    value = np.arange(1,6)

    # Make 5-element array of votes
    votes = np.zeros(5)
    if len(group)!=0:
        for star,nvotes in zip(group['rating'].values,group['nrating'].values):
            votes[star-1] = nvotes

    # Calculate final score as weighted average of votes,
    #    regularized by the prior
    posterior = prior + votes
    temp_score = value*posterior
    final_score = temp_score.sum() / posterior.sum()

    return final_score


def rawavg_from_group(group):
    """
    Calculates raw average of ratings (without Bayesian Dirichlet prior)
    from a grouped pandas dataframe as grouped in query_term
    """

    value = np.arange(1,6)
    votes = np.zeros(5)
    for star,nvotes in zip(group['rating'].values,group['nrating'].values):
        votes[star-1] = nvotes

    return (value*votes).sum() / votes.sum()


def query_term(string):
    """
    Queries text of review database for a given string.

    Returns a list of dictionaries containing information about
    each restaurant.

    Query_term and query_business 
    """

    # Start engine to connect to mysql
    con = db.connect(host=sql_cfg.database['host'], db=sql_cfg.database['name'],
                     user=sql_cfg.database['user'], passwd=sql_cfg.database['passwd'],
                      use_unicode=True, charset="utf8")
    cur = con.cursor()

    # Perform query.
    # Returns business name and number of reviews for each business
    cmd = """
          SELECT rest.business_name, rest.business_stars, 
                 COUNT(sent.FF_score) as FF_count, sent.FF_score, 
                 rest.business_id, sent.content, rest.city
          FROM Restaurant_mexican as rest, Review_mexican as rev, sentences_scored_400 as sent
          WHERE rest.business_id=rev.business_id AND
                rev.review_id=sent.review_id AND
                sent.content LIKE '%{}%'
          GROUP BY rest.business_id, sent.FF_score
          ORDER BY rest.business_id, sent.FF_score;
          """.format(string)

    cur.execute(cmd)
    output = cur.fetchall()
    cur.close()
    con.close()

    # Return empty list if no restaurants found
    outlist = [v for v in output if v[2]!=0]
    if outlist==[]: return outlist

    # Calculate FoodFindr score and raw (unregularized) average for each restaurant
    df = pd.DataFrame(outlist,columns=['name','yelp','nrating','rating','ID','content','city'])
    grouped = df.groupby('ID')
    ffscore = grouped.apply(FFscore_from_group)
    ffavg = grouped.apply(rawavg_from_group)
    newdf = grouped['yelp','content','name','city'].last()
    newdf['ffscore'] = np.round(ffscore.values,decimals=2)
    newdf['ffavg'] = np.round(ffavg.values,decimals=2)
    newdf['ffround'] = np.round(newdf['ffscore']*2.)/2.0

    # Limit results to topN FoodFindr scores
    nreturn = 10
    newdf = newdf.sort('ffscore',ascending=False).iloc[0:nreturn,:]
    newdf['rank'] = np.arange(nreturn)+1
    newdf = newdf.reset_index()

    # Turn into list of restaurant information dictionaries
    outdicts = newdf.T.to_dict().values()

    # Return list of 
    return outdicts



def query_business(busID,query_term):
    """
    Queries text of reviews for a given business ID.

    Returns list of dictionaries with score information 
    for popular terms (food, service, atmosphere, drinks)
    hard-coded in the first line of the function.

    query_business and query_term share many similar 
    components. They should either be combined into a single
    function or their shared components should be combined
    into single functions. This is work to be done in the
    future when cleaning up the code. (kjw, 2/11/15)
    """

    # List of popular terms to query. Make this a function in the future.
    popular_terms = [{query_term:[query_term]},
                     {'food':['food']},
                     {'service':['service','waiter','waitress']},
                     {'atmosphere':['atmosphere','decor','environment']},
                     {'drinks':['drinks','alcohol','margarita','tequila','beer','wine']}]


    # Start engine to connect to mysql
    con = db.connect(host=sql_cfg.database['host'], db=sql_cfg.database['name'],
                     user=sql_cfg.database['user'], passwd=sql_cfg.database['passwd'],
                      use_unicode=True, charset="utf8")
    cur = con.cursor()

    # Perform query for each popular term. Return a dictionary of 
    #     terms : scores
    scores = {}

    # Make one query for each category in the popular_terms
    for category in popular_terms:

        terms = category.values()[0]

        # Build sub-string to insert into the SQL query
        like_list = ["sent.content LIKE '%{}%'".format(t) for t in terms]
        like_string = ' OR '.join(like_list)

        # Returns business name and number of reviews for each business
        cmd = """
        SELECT rest.business_name, rest.business_stars, 
               COUNT(sent.FF_score) as FF_count, sent.FF_score, 
               rest.business_id, sent.content
        FROM Restaurant_mexican as rest,
            Review_mexican as rev,
            sentences_scored_400 as sent
        WHERE rest.business_id=rev.business_id AND
            rev.review_id=sent.review_id AND 
            rest.business_id='{0}' AND 
            ({1})
        GROUP BY sent.FF_score
        ORDER BY sent.FF_score;
        """.format(busID,like_string)

        cur.execute(cmd)
        output = cur.fetchall()

        #print cmd
        #print output

        # Calculate FoodFindr score and row (unregularized) average
        outlist = [v for v in output if v[2]!=0]
        if outlist==[]:
            scores[category.keys()[0]] = {'ffavg': 0.0, 'ffround': 0.0, 'name': u'', 
                                          'yelp': 0.0, 'content': u'', 'ffscore': 0.0}
            scores[category.keys()[0]]['ffscore'] = FFscore_from_group([])
            scores[category.keys()[0]]['ffscore'] = np.round(scores[category.keys()[0]]['ffscore'],decimals=2)
            scores[category.keys()[0]]['ffavg'] = np.round(scores[category.keys()[0]]['ffscore'],decimals=2)
            scores[category.keys()[0]]['ffround'] = np.round(scores[category.keys()[0]]['ffscore']*2.)/2.0
            continue

        df = pd.DataFrame(outlist,columns=['name','yelp','nrating','rating','ID','content'])
        grouped = df.groupby('ID')
        ffscore = grouped.apply(FFscore_from_group)
        ffavg = grouped.apply(rawavg_from_group)
        newdf = grouped['yelp','content','name'].last()
        newdf['ffscore'] = np.round(ffscore,decimals=2)
        newdf['ffavg'] = np.round(ffavg,decimals=2)
        newdf['ffround'] = np.round(newdf['ffscore']*2.)/2.0

        # Place into dictionary of results
        scores[category.keys()[0]] = newdf.T.to_dict().values()[0]


    cur.close()
    con.close()

    return scores


def handle_input(input_term):
    """
    handle_input prints an error message if the input term is not 
    a reasonable search request.

    Current flags include:
       empty term
       terms with non-alphabetic values (except apostraphe)
       terms with a "select" and "from" in the search
    """

    error_string = ''
    if input_term=='':
        error_string = 'INPUT ERROR: please enter a non-blank search term.'
    if all((l in string.ascii_lowercase+"'"+string.whitespace) for l in input_term)==False:
        error_string = 'INPUT ERROR: please remove punctuation and numbers. Remove extra spaces. Apostrophes OK.'
    if ((('select' in input_term) & ('from' in input_term)) | 
       (('drop' in input_term) & ('table' in input_term))):
        error_string = 'INPUT ERROR: Do not enter SQL-like input.'

    return error_string

