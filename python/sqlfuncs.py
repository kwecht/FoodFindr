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
    #dataframe = pd.read_pickle('../data/pandas/sentences_lemmas_mexican.pkl')

    # score sentences in the dataframe.
    #classes = classification.classify_sentences(model,dataframe)
    #dataframe['FF_class'] = classes

    # Write sentences dataframe to file
    con = mdb.connect('localhost', 'root', '', 'yelp_sentiment_db', 
                      use_unicode=True, charset="utf8")
    cur = con.cursor()
    try:
        cmd = "DROP TABLE {}".format(tablename)
        cur.execute(cmd)
    except:
        print 'No TABLE {} in the database'.format(tablename)


    cmd = "CREATE TABLE {0} (review_id text, sentence_id text,content text, lemmas text, stars float, FF_score float)".format(tablename)
    cur.execute(cmd)

    # Add one row at a time to the sentences table
    count = 0
    for index in dataframe.index:
        if count % 10000==0: print count
        count += 1

        a = dataframe.loc[index,:]
        if np.isnan(a['FF_score']):
            ffscore = "NULL"
        else:
            ffscore = a['FF_score']

        # Insert values into the dataframe
        cmd = u'INSERT INTO {0} VALUES ("{1}","{2}","{3}","{4}",{5},{6})'.format(tablename,a['review_id'].replace('"', ''),a['sentence_id'].replace('"',''),a['text'].replace('"','').replace('\n',' ').replace('\\','/'),' '.join(a['lemmas']),a['stars'],ffscore)
        try:
            cur.execute(cmd)
        except:
            print "Skipping index value {}".format(index)

    # Commit changes to the database
    con.commit()
    con.close()

    return True
