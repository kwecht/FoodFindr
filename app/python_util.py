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
          SELECT rest.business_name, rest.business_stars, 
                 AVG(sent.FF_score) as FF_score, COUNT(sent.FF_score) as num_sent,
                 rest.business_id
          FROM Restaurant_mexican as rest, Review_mexican as rev, sentences_scored as sent
          WHERE rest.business_id=rev.business_id AND
                rev.review_id=sent.review_id AND
                sent.content LIKE '%{}%'
          GROUP BY rest.business_id HAVING num_sent > 10
          ORDER BY FF_score DESC
          LIMIT 5;
          """.format(string)

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



def query_business(busID,query_term):
    """
    Queries text of reviews for a given business ID.

    Returns popular terms and associated scores in a dictionary.

    Always returns a single row.
    """

    # List of popular terms to query. Make this a function in the future.
    popular_terms = [{query_term:[query_term]},
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
        SELECT bus.business_name, bus.business_stars, AVG(sent.FF_score) as FF_score, COUNT(sent.FF_score)
        FROM Restaurant_mexican as bus,
            Review_mexican as rev,
            sentences_scored as sent
        WHERE bus.business_id=rev.business_id AND
            rev.review_id=sent.review_id AND 
            bus.business_id='{0}' AND 
            ({1})
        GROUP BY bus.business_id
        ORDER BY FF_score DESC;
        """.format(busID,like_string)

        cur.execute(cmd)
    
        output = cur.fetchall()
        if output==():
            scores[category.keys()[0]] = (0,0,0,0)
        else:
            scores[category.keys()[0]] = output[0]

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

