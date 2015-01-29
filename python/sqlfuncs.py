#!/usr/bin/env python

"""
sentiment.py
########################################################################
#
#        Kevin Wecht                22 January 2015
#
#    Insight Data Science Project:
#        Food Finder
#
########################################################################
#
#    sqlfuncs.py
#        - Handles all querying and writing to mysql database
#        - Querying of database based on user input through web app.
#	 - Initial creation of mysql database from pandas objects, 
#              called during initialize.py.
#	 - Querying of database and insertion of columns for sentiment scoring.
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
import pymysql as mdb

########################################################################

def query_term(string):
    """
    Queries text of review database for a given string.

    Returns the number of reviews for each restaurant that contain the string.

    Returns list of tuples that are:
    (business_id, n_reviews)
    """

    # Start engine to connect to mysql
    con = mdb.connect('localhost', 'root', '', 'yelp_sentiment_db', 
                      use_unicode=True, charset="utf8") #host, user, password, 
    cur = con.cursor()

    # Perform query.
    # Returns business name and number of reviews for each business
    cmd = """
          SELECT business.name, review.nrev
          FROM 
              (SELECT business_id, COUNT(review_id) AS nrev 
              FROM review_mexican 
              WHERE content LIKE '%{}%' 
              GROUP BY business_id 
              ORDER BY nrev) AS review 
            INNER JOIN
              (SELECT business_id, business_name as name
              FROM restaurant_mexican) AS business
            ON review.business_id=business.business_id
          ORDER BY review.nrev DESC;
          """.format(string)
    cur.execute(cmd)

    # Create list of tuples with query results
    output = []
    for row in cur:
        output.append(row)

    cur.close()
    con.close()

    return output



def pandas2sql(dataframe,tablename):
    """
    Save pandas dataframe to mysql database as a table.
    """

    # Restore pandas dataframe from file
    dataframe = pd.read_pickle('../data/pandas/sentences_lemmas_mexican.pkl')

    # score sentences in the dataframe.
    classes = classification.classify_sentences(model,dataframe)
    dataframe['FF_class'] = classes

    # Write sentences dataframe to file
    con = mdb.connect('localhost', 'root', '', 'yelp_sentiment_db', 
                      use_unicode=True, charset="utf8")
    dataframe.to_sql('scored_sentences',con,index=False,flavor='mysql')
    con.close()

    return True
