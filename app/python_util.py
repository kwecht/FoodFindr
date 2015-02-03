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


def score_lowerbound(output,ncutoff=20,nsigma=2):
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

    # Parameters to control
    minstd = 1.5
    nsigma = 2


    # Replace standard deviations that are too small with a minimum value
    if output[4] < ncutoff:
        output[3] = np.max([minstd,output[3]])

    # Calculate lower bound of 95% confidence interval
    try:
        SE = output[3] / np.sqrt(output[4])
        lowerbound = output[2] - nsigma*SE
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
          FROM Restaurant_mexican as rest, Review_mexican as rev, sentences_scored_400 as sent
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
    outlist = sorted( outlist, key=score_lowerbound, reverse=True)
    outlist = [v for v in outlist if v[2]!=None]

    # Calculate mean info for returning to calling function
    #weighted_scores = [v[2]*v[4] for v in outlist]
    #weights = [v[2] for v in outlist]
    #mean_info = sum(weighted_scores) / sum(weights)
    mean_info = []
    for ii in range(len(outlist)):
        mean_info.append(float(len(outlist)-ii)/len(outlist))

    outlist = outlist[0:20]
    mean_info = mean_info[0:20]


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
                     {'food':['food']},
                     {'service':['service','waiter','waitress']},
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
        SELECT bus.business_name, bus.business_stars, AVG(sent.FF_score) as FF_score, STD(sent.FF_score), COUNT(sent.FF_score)
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
            scores[category.keys()[0]] = [0,0,0,0,0]
        else:
            scores[category.keys()[0]] = [v for v in output[0]]

    cur.close()
    con.close()

    return scores



def find_outlier(query_results,input_term):
    """
    Return the name and decile (which 10% bin) in which some query results fall
    for the major hard-coded categories of food, atmosphere, drinks, and service.
    """

    # Maintain a list of decimal values corresponding to each bin.
    # This is not elegant, but it's inefficient to do the same queries each time
    #     someone uses the site.
    bins = {'food':[-2.0,0.37867965644,1.25,1.75,2.0,2.29101872004,2.50652466602,
                    2.75,2.98333705193,3.25, 4.24390350205],
            'service':[-2.0,-0.62132034356,0.267949192431,1.0,1.29467800954,1.66666666667,
                       2.0,2.125,2.45131670195,2.7964947398,3.67109874428],
            'atmosphere':[0 -2.0,0.0,0.171572875254,1.0,1.25,1.87867965644,2.0,
                          2.26794919243,2.72324943812,3.01410355182, 4.71730635364],
            'drinks':[-2.0,-0.12132034356,0.983930559977,1.14672783003,1.82273869354, 2.0,
                      2.30064126288,2.60858846194,2.87961601261,3.26794919243, 4.20804493973]}

    # Calculate lower bound of 95% confidence interval from query_results
    itemrank = {k:0 for k in query_results.keys() if k!=input_term}
    for item in itemrank:
        lowerbound = score_lowerbound(query_results[item])
        print input_term, item, lowerbound
        thisrank = np.digitize([lowerbound],np.array(bins[item]))-1
        itemrank[item] = thisrank


    # We now have a dictionary of the deciles in which each category falls
    # Find the highest/lowest one of them
    output = {'name':'', 'decile':-1}
    mindec = min(itemrank, key=itemrank.get) # returns key with lowest value
    maxdec = max(itemrank, key=itemrank.get) # returns key with highest value

    if (itemrank[maxdec] - 5) >= (4 - itemrank[mindec]):
        output['name'] = maxdec
        output['decile'] = np.float(itemrank[maxdec])
    else:
        output['name'] = mindec
        output['decile'] = np.float(itemrank[mindec])


    return output['name'], int(output['decile'])



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

