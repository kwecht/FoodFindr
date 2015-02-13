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
#    There is some overlap between sentences2sql here and the sql functions
#        in initialize.py. Move relevant functions to one of the two files.
#        
#
########################################################################
"""

__author__      = "Kevin Wecht"

########################################################################

import numpy as np
import pandas as pd
import pymysql as db

########################################################################

def query_term(string):
    """
    Queries text of review database for a given string.

    Returns the number of reviews for each restaurant that contain the string.

    Returns list of tuples that are:
    (business_id, n_reviews)
    """

    # Start engine to connect to mysql
    con = db.connect('localhost', 'root', '', 'yelp_sentiment_db', 
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



def sentences2sql(dataframe,tablename):
    """
    Save pandas dataframe to mysql database as a table.
    """

    # Restore pandas dataframe from file
    #dataframe = pd.read_pickle('../data/pandas/sentences_lemmas_mexican.pkl')

    # score sentences in the dataframe.
    #classes = classification.classify_sentences(model,dataframe)
    #dataframe['FF_class'] = classes

    # Write sentences dataframe to file
    con = db.connect('localhost', 'root', '', 'yelp_sentiment_db', 
                      use_unicode=True, charset="utf8")
    cur = con.cursor()
    try:
        cmd = "DROP TABLE {}".format(tablename)
        cur.execute(cmd)
    except:
        print 'No TABLE {} in the database'.format(tablename)


    cmd = "CREATE TABLE {0} (review_id VARCHAR(22), sentence_id VARCHAR(6),content text, lemmas text, stars float, FF_score float, FULLTEXT idx (content), PRIMARY KEY (review_id, sentence_id)) ENGINE=InnoDB".format(tablename)
    cur.execute(cmd)

    # Add one row at a time to the sentences table
    count = 0
    print "processing ", len(dataframe),"documents"
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



def calc_ranges():
    """
    Calculates the 10% bin edges of lowerbounds for the major categories in my search.
    """


    # List of popular terms to query. Make this a function in the future.
    popular_terms = [{'guac':['guac']},
                     {'food':['food']},{'service':['service','waiter','waitress']},
                     {'atmosphere':['atmosphere','decor','environment']},
                     {'drinks':['drinks','alcohol','margarita','tequila','beer','wine']}]


    # Start engine to connect to mysql
    con = db.connect('localhost', 'root', '', 'yelp_sentiment_db', 
                      use_unicode=True, charset="utf8") #host, user, password, 
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
        SELECT bus.business_name, bus.business_stars, AVG(sent.FF_score) as FF_score, STD(sent.FF_score) as FF_std, COUNT(sent.FF_score)
        FROM Restaurant_mexican as bus,
            Review_mexican as rev,
            sentences_scored as sent
        WHERE bus.business_id=rev.business_id AND
            rev.review_id=sent.review_id AND 
            ({0})
        GROUP BY bus.business_id;
        """.format(like_string)

        cur.execute(cmd)
    
        output = cur.fetchall()

        outlist = []
        for row in output:
            outlist.append(list(row))
        outlist = sorted( outlist, key=score_lowerbound, reverse=False)
        outlist = [v for v in outlist if v[2]!=None]


        # Output list is now sorted by lowerbound score.
        # Print values at 0-100% by 10% bins
        print '-'*70
        print '-'*70
        print "Results for ", category
        print len(outlist), len(outlist[0])
        count = 0
        len10 = np.round(len(outlist)/10.)
        for ii in range(len(outlist)):
            if (ii==len(outlist)-1) | (ii%len10==0):
                print count, score_lowerbound(outlist[ii])
                count += 1


        if output==():
            scores[category.keys()[0]] = (0,0,0,0,0)
        else:
            scores[category.keys()[0]] = output[0]


    cur.close()
    con.close()
