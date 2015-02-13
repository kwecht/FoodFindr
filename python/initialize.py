#!/usr/bin/env python

"""
initialize.py
########################################################################
#
#        Kevin Wecht                21 January 2015
#
#    Insight Data Science Project:
#        Food Finder
#
########################################################################
#
#    initialize.py
#        - Reads yelp data in json format and puts into pandas 
#              dataframes for restaurants and reviews.
#        - Saves pandas dataframes of all information as pickles.
#        - Saves tokenized, segmented text to a pandas dataframe to build 
#              traning labels.
#
#    FUNCTIONS
#        main     - primary function in this file. main reads yelp
#                   data from json and creates tables in a mysql database
#                   of business, review, and sentence information.
#        other functions called by main. These are involved in cleaning 
#        data, pickling pandas dataframes, and generating a mysql database.
#        Enumerate the functions and their purposes here.
#
#    EXAMPLE
#        $ python initialize.py
#
########################################################################
"""

__author__      = "Kevin Wecht"

########################################################################

import pandas as pd

########################################################################

def process_adhoc(data,filetype):
    """perform ad-hoc filtering and correction of values in the restaurant and review data."""

    if filetype=='business':

        # Correct some city names
        data['city'] = data.city.str.lower()
        to_replace = ['glendale az','pheonix','phoenix sky harbor center','higley']
        value = ['glendale','phoenix','phoenix','gilbert']
        data['city'].replace(to_replace=to_replace,value=value,inplace=True)

    if filetype=='review':

        # Remove reviews with less than 2 characters
        data = data[data['text'].map(lambda x: len(x) > 2)]

        # Remove reviews that cannot be converted to utf-8
        # Hand-written list obtained by error message in py2mysql
        badIDs = [45062,46284,82878,161853,440669,559193,590483,621772,
                  663255,684140,720458,723694,731942,738358,800360,873680,
                  910421,927878,1078645,1100278]
        data = data[-data.index.isin(badIDs)]

    return data



def read_yelp(filetype,**kwargs):
    """Read json formatted data from yelp download and return pandas dataframe."""

    import json

    print "Reading Yelp data for "+filetype

    # Open file and read one json object at a time
    data = []
    json_data = open('../data/yelp/yelp_academic_dataset_'+filetype+'.json')
    for line in json_data:
        data.append(json.loads(line))

    json_data.close()
    
    data = pd.DataFrame(data)

    # Apply optional filters
    for key,value in kwargs.iteritems():
        if key=='categories':
            data = data[data[key].map(lambda x: value in [cat.lower() for cat in x])]
        else:
            data = data[data[key].isin(value)]

    # Add-hoc filtering and processing of reviews. 
    data = process_adhoc(data,filetype)

    return data

def save2pickle(restaurant_data,review_data,append_string=''):
    """save restaurant and review data to pickles with option
       to append a string to each filename."""

    print "Saving dataframes to pickle "+append_string

    restaurant_data.to_pickle('../data/pandas/business'+append_string+'.pkl')
    review_data.to_pickle('../data/pandas/review'+append_string+'.pkl')

    return None


def py2mysql(restaurant_data,review_data,append_string=''):
    """
    Saves restaurant and review data to MySQL database.
    Adapted from function written by Mei.

    Clean and modularize when I have time.
    """

    import pymysql as mdb

    print "Saving MySQL databases "+append_string

    # Start engine to connect to mysql
    con = mdb.connect('localhost', 'root', '', 'yelp_sentiment_db', use_unicode=True, charset="utf8") #host, user, password, 
    con.set_charset('utf8')

    # -----------------------------------------------------------------------------
    # Set up Restaurants data table
    cur = con.cursor()
    table_name = "Restaurant"+append_string
    try:
        cmd = "DROP TABLE {}".format(table_name)
        cur.execute(cmd)
    except:
        print 'No TABLE {} in the database'.format(table_name)

    cmd = "CREATE TABLE {} (ID int NOT NULL AUTO_INCREMENT PRIMARY KEY, business_id VARCHAR(22), business_name text,city text, latitude float, longitude float, business_stars float, review_count int, status text, takeout float, noise float, reservations float, wifi float,parking float, creditcard float, goodforgroup float)".format(table_name)
    cur.execute(cmd)

    # Add one row at a time to the Restaurants table
    for index in restaurant_data.index:
        a = restaurant_data.loc[index]
        b=str(a.business_id)
        d=a['attributes']
        a1=0
        a2=0
        a3=0
        a4=0
        a5=0
        a6=0
        a7=0
        if 'Take-out' in d.keys():
            if d['Take-out']==True:
                a1=1
            else:
                a1=-1
        if 'Noise Level' in d.keys():
            if d['Noise Level']=='quite':
                a2=1
            elif d['Noise Level']=='average':
                a2=2
            elif d['Noise Level']=='loud':
                a2=3
            else:
                a2=4
        if 'Takes Reservations' in d.keys():
            if d['Takes Reservations']==True:
                a3=1
            else:
                a3=-1
        if 'Wi-Fi' in d.keys():
            if d['Wi-Fi']=="free":
                a4=1
            else:
                a4=-1
        if 'Parking' in d.keys():
            if True in d['Parking'].values():
                a5=1
            else:
                a5=-1
        if 'Accepts Credit Cards' in d.keys():
            if d['Accepts Credit Cards']==True:
                a6=1
            else:
                a6=-1
        if 'Good For Groups' in d.keys():
            if d['Good For Groups']==True:
                a7=1
            else:
                a7=-1
    
        # Insert values into the dataframe
        cmd = u'INSERT INTO {15} VALUES ("{0}","{1}","{2}",{3},{4},{5},{6},"{7}",{8},{9},{10},{11},{12},{13},{14})'.format(a['business_id'].replace('"', ''),a['name'].replace('"',''),a['city'],a['latitude'],a['longitude'],a['stars'],a['review_count'],a['open'],a1,a2,a3,a4,a5,a6,a7,table_name)
        cur.execute(cmd)

    # Commit changes to the database
    con.commit()


    # -----------------------------------------------------------------------------
    # Set up Reviews data table
    cur = con.cursor()
    table_name = "Review"+append_string
    try:
        cmd = "DROP TABLE {}".format(table_name)
        cur.execute(cmd)
    except:
        print 'No TABLE {} in the database'.format(table_name)


    # Replace business ID with primary key from restaurant table above
    cmd = "SELECT ID, business_id FROM Restaurant_mexican"
    cur.execute(cmd)
    output = cur.fetchall()  # tuple of rows in reviews
    primary_key = [out[0] for out in output]
    busid = [out[1] for out in output]
    primary_key = pd.Series(primary_key,index=busid)
    review_data['business_primary_key'] = -1
    for bid, key in output:
        review_data[review_data['business_id']==bid]['business_primary_key'] = key



    cmd = "CREATE TABLE {} (ID int NOT NULL AUTO_INCREMENT PRIMARY KEY, business_primary_key int, business_id VARCHAR(22), review_id text, user_id text, stars float, ymd DATE, content text)".format(table_name)
    cur.execute(cmd)

    # Add one row at a time to the Restaurants table
    for index in review_data.index:

        a = review_data.loc[index]
    
        # Insert values into the dataframe
        cmd = u'INSERT INTO {7} VALUES ({0},"{1}","{2}","{3}",{4},"{5}","{6}")'.format(a['business_primary_key'],a['business_id'].replace('"', ''),a['review_id'].replace('"',''),a['user_id'].replace('"',''),a['stars'],a['date'],a['text'].replace('"','').replace('\n',' ').replace('\\','/'),table_name)
        try:
            cur.execute(cmd)
        except:
            print "Skipping index value {}".format(index)

    # Commit changes to the database
    con.commit()



def sentence2mysql(sentences,append_string=''):
    """
    create sentence database in mysql database for yelp_sentiment_db
    Adapted from py2mysql function defined above.

    Clean and modularize when I have time. This shares many operations
    with py2msql above.
    """

    cur = con.cursor()
    table_name = "Sentences"+append_string
    try:
        cmd = "DROP TABLE {}".format(table_name)
        cur.execute(cmd)
    except:
        print 'No TABLE {} in the database'.format(table_name)

    cmd = "CREATE TABLE {} (review_id text, sentence_id, stars float, handlabel float, content text)".format(table_name)
    cur.execute(cmd)

    # Add one row at a time to the Restaurants table
    for index in sentences.index:

        a = sentences.loc[index]
    
        # Insert values into the dataframe
        cmd = u'INSERT INTO {5} VALUES ("{0}","{1}",{2},{3},"{4}")'.format(a['review_id'].replace('"',''),a['sentence_id'],a['stars'],a['hand_label'],a['text'].replace('"','').replace('\n',' ').replace('\\','/'),table_name)
        try:
            cur.execute(cmd)
        except:
            print "Skipping index value {}".format(index)

    # Commit changes to the database
    con.commit()


def build_lemma_vocab(append_string=''):
    """
    Builds entire vocabulary from a dataframe of reviews.
    """
    import process_text

    # Restore data from file
    reviews = pd.read_pickle('../data/pandas/review'+append_string+'.pkl')

    vocab = {}
    print len(reviews)
    count = 0
    for index,row in reviews.iterrows():
        lemmas = process_text.text2lemmas(row.text)
        for lemma in vocab:
            try:
                vocab[lemma] += 1
            except:
                vocab[lemma] = 1
        count += 1
        if count % 100==0: print count

    # Save vocabulary to file
    vocab = pd.Series(vocab)
    vocab.to_pickle('../data/pandas/vocab'+append_string+'.pkl')

    return True


def add_lemmas2pandas(type_string='', append_string=''):
    """
    Adds lemmatized text as an extra column in the reviews and/or sentences
    databases.

    type_string = {'review'|'sentences'}  determines whether to lemmatize
                  text in pandas dataframe of reviews or sentences
    """
    import process_text

    # Error handling
    if type_string not in ['review','sentences']:
        print "Error in add_lemmas2pandas:"
        print "    type_string must be either 'review' or 'sentences'"
        print "    please try again"
        return None

    # Lemmatize each row in the dataframe
    dataframe = pd.read_pickle('../data/pandas/'+type_string+append_string+'.pkl')
    lemmatized_text = []
    count = 0
    for item in dataframe.index:
        #if count<63400: 
        #    count += 1
        #    continue
        if count%1000==0: print count
        thisitem = dataframe.loc[item]
        lemmatized_text.append( process_text.text2lemmas(thisitem.text) )
        count += 1

    # Add lemmatized text back as a column in the dataframe
    lemmatized_text = pd.Series(lemmatized_text,index=dataframe.index)
    dataframe['lemmas'] = lemmatized_text

    # Save dataframe to file
    dataframe.to_pickle('../data/pandas/'+type_string+'_lemmas'+append_string+'.pkl')

    return True



def main():
    """Main function to initialize databases to analysize Yelp data."""
    import random

    # ------------ Save Yelp Data as Pandas DataFrames to pickle ------------
    # Save all Yelp restaurant data in Arizona (Phoenix area)
    #restaurant_data = read_yelp('business',state=['AZ'],open=[True],categories='restaurants')
    #review_data = read_yelp('review',business_id=restaurant_data.business_id.unique())
    restaurant_data = pd.read_pickle('../data/pandas/business.pkl')
    review_data = pd.read_pickle('../data/pandas/review.pkl')
    result = save2pickle(restaurant_data,review_data)
    result = py2mysql(restaurant_data,review_data)

    # Save information for mexican restaurants only
    restaurant_data = restaurant_data[restaurant_data['categories'].map(lambda x: 'mexican' in [cat.lower() for cat in x])]
    review_data = review_data[review_data['business_id'].isin(restaurant_data.business_id.unique())]
    result = save2pickle(restaurant_data,review_data,append_string='_mexican')
    result = py2mysql(restaurant_data,review_data,append_string='_mexican')

    # Segment some data for training
    random.seed(1234)
    trainids = random.sample(restaurant_data.business_id,20)
    restaurant_data = restaurant_data[restaurant_data['business_id'].isin(trainids)]
    review_data = review_data[review_data['business_id'].isin(trainids)]
    result = save2pickle(restaurant_data,review_data,append_string='_mexican_train')

    # Make database of individual sentences from review data
    sentences = process_text.reviews_to_sentences(review_data)
    sentences = process_text.add_training_label(sentences,review_data)
    sentences.to_pickle('../data/pandas/sentences_mexican.pkl')
    result = sentence2mysql(sentences,review_data,append_string='_mexican')


if __name__=='__main__':
    main()
