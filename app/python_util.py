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

import pdb
import pymysql as db
import numpy as np

########################################################################


def order_output(output,ncutoff=50,nsigma=2):
    """
    Function for sorting output based on average foodfindr score 
    and the number of sentences from which the score was derived.

    ncutoff - number of samples necessary for sample standard deviation
              to be less than 1.
    nsigma - returned value is the lower end of the nsigma confidence
             interval. For example, if nsigma = 2, then the lower bound
             is approximately the edge of the 95% confidence interval.

    Sorting value is the lower bound on 95% confidence interval 
    of the estimate of the mean, approximated by:
       SE_mean = sigma / sqrt(n)
       sigma - standard deviation of sample
       n - number of samples
    If n < ncutoff and sigma < 1, set sigma=1. This is to prevent 
       the high ranking of a restaurant with a very low sigma
       that is caused by a small number of reviews.

    Returns sorted list output.
    """

    # Replace standard deviations that are too small with 1.
    #    output[ii][] = std
    if output[4] < ncutoff:
        output[3] = np.max([1.5,output[3]])

    # Calculate lower bound of 95% confidence interval
    nsigma = 2
    try:
        SE = output[3] / np.sqrt(output[4])
        lowerbound = output[2] - 2.*SE
    except:
        lowerbound = 0.  # because output[4] might be None


    return lowerbound




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
                 AVG(sent.FF_score) as FF_score, 
                 STD(sent.FF_score) as FF_std, COUNT(sent.FF_score) as num_sent,
                 rest.business_id, sent.content
          FROM Restaurant_mexican as rest, Review_mexican as rev, sentences_scored as sent
          WHERE rest.business_id=rev.business_id AND
                rev.review_id=sent.review_id AND
                sent.content LIKE '%{}%'
          GROUP BY rest.business_id;
          """.format(string)

    cur.execute(cmd)
    output = cur.fetchall()

    # Calculate value on which to sort results
    # This is the score that I'll call the FoodFindr results
    outlist = []
    for row in output:
        outlist.append(list(row))
    outlist = sorted( outlist, key=order_output, reverse=True)
    outlist = [v for v in outlist if v[2]!=None]

    # Calculate mean info for returning to calling function
    #weighted_scores = [v[2]*v[4] for v in outlist]
    #weights = [v[2] for v in outlist]
    #mean_info = sum(weighted_scores) / sum(weights)
    mean_info = []
    for ii in range(len(outlist)):
        mean_info.append(float(len(outlist)-ii)/len(outlist))

    outlist = outlist[0:5]
    mean_info = mean_info[0:5]


    cur.close()
    con.close()

    return outlist, mean_info



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

