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
          SELECT business.name, review.nrev, business.stars
          FROM 
              (SELECT business_id, COUNT(review_id) AS nrev 
              FROM review_mexican 
              WHERE content LIKE '%{}%' 
              GROUP BY business_id) AS review 
            INNER JOIN
              (SELECT business_id, business_name as name, business_stars as stars
              FROM restaurant_mexican) AS business
            ON review.business_id=business.business_id
          ORDER BY review.nrev DESC
          LIMIT 5;
          """.format(string)
    print cmd
    cur.execute(cmd)

    # Create list of tuples with query results
    #output = []
    #for row in cur:
    #    output.append(row)

    # Save 
    output = cur.fetchall()

    cur.close()
    con.close()

    return output
