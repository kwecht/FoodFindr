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
#        - Contains functions for passing and manipulating information
#          passed through the web front-end.
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
          SELECT rest.business_name, rest.business_stars, AVG(sent.FF_score) as FF_score, 
                 AVG(sent.stars) as Star_score, COUNT(sent.FF_score) as num_sent
          FROM Restaurant_mexican as rest, Review_mexican as rev, sentences_scored as sent
          WHERE rest.business_id=rev.business_id AND
                rev.review_id=sent.review_id AND
                sent.content LIKE '%burrito%'
          GROUP BY rest.business_id HAVING num_sent > 10
          ORDER BY FF_score DESC
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



def query_business(busID):
    """
    Queries text of reviews for a given business ID.

    Returns popular terms and associated scores in a dictionary.

    Always returns a single row.
    """

    # List of popular terms to query. Make this a function in the future.
    popular_terms = [['salsa'],['taco'],['burrito'],['guacamole'],
                     ['service'],['price']]


    # Start engine to connect to mysql
    con = db.connect('localhost', 'root', '', 'yelp_sentiment_db', 
                      use_unicode=True, charset="utf8") #host, user, password, 
    cur = con.cursor()

    # Perform query for each popular term. Return a dictionary of 
    #     terms : scores
    scores = {}

    for category in popular_terms:
        query_term(category[0])
        thisterm = category[0]
        # Returns business name and number of reviews for each business
        cmd = """
        SELECT bus.business_name, bus.business_stars, AVG(sent.FF_score) as FF_score, AVG(sent.stars) as Star_score, COUNT(sent.FF_score)
        FROM Restaurant_mexican as bus,
            Review_mexican as rev,
            sentences_scored as sent
        WHERE bus.business_id=rev.business_id AND
            rev.review_id=sent.review_id AND
            sent.content LIKE '%burrito%'
        GROUP BY bus.business_id
        ORDER BY FF_score DESC;
        """.format(busID,category[0])
        cur.execute(cmd)
    
        output = cur.fetchall()
        scores[category[0]] = output

    cur.close()
    con.close()

    return scores





# To get average score of restaurants that contain burrito (using fulltext indices)
"""
SELECT bus.business_name, bus.business_stars, AVG(sent.FF_score) as FF_score, AVG(sent.stars) as Star_score, COUNT(sent.FF_score)
FROM Restaurant_mexican as bus,
     Review_mexican as rev,
     sentences_scored as sent
WHERE bus.business_id=rev.business_id AND
      rev.review_id=sent.review_id AND
      sent.content LIKE '%burrito%'
GROUP BY bus.business_id
ORDER BY FF_score DESC;
"""

