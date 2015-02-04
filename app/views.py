from flask import render_template, request
from app import app
import pymysql as mdb
from a_Model import ModelIt
import python_util as util

db = mdb.connect(user="root", host="localhost", db="world_innodb", charset='utf8')

@app.route('/')
@app.route('/index')
def index():
    return render_template("index.html",
       title = 'Home', user = { 'nickname': 'Miguel' },
       )


@app.route('/about')
def about_page():
  return render_template("about.html")

@app.route('/input')
def food_input():
  return render_template("input.html")

@app.route('/output')
def food_output():
  import numpy as np

  # Pull ID from the input field and store it
  input_term = request.args.get('ID')

  # Query review data for sentence scores on the search term
  restaurants = util.query_term(input_term)



  # Start here, transforming info into that which can be more easily
  #   be shown on the 5 point scale





  # Query review data for sentences scores on various features of the top 5 restaurants
  rest_ids = [r[5] for r in query_results]  # list of business ID for each restaurant
  restaurant_details = []
  for RID in rest_ids:
    query_results = util.query_business(RID,input_term)
    #query_results['also_name'], query_results['also_score'] = util.find_outlier(query_results,input_term)
    ## Place results in restaurant dictionary
    #for d in restaurants:
    #    if RID==d['busid']:
    #        d['also_name'] = query_results['also_name']
    #        d['also_score'] = query_results['also_score']
    restaurant_details.append(query_results)


  # Find the category (food, service, atmosphere, drinks) in which 
  #    each restaurant ranks highest compared to its competitors
  # nRestaurant x nFeatures array to hold scores
  categories = ['food','service','atmosphere','drinks']
  scores = np.zeros((len(restaurants),len(categories)))
  print scores.shape
  for ii in range(len(restaurants)):
    for jj in range(len(categories)):
      scores[ii,jj] = util.score_lowerbound(restaurant_details[ii][categories[jj]])

  # Replace each numerical value with an integer based on its rank in the column
  for jj in range(len(categories)):
    print 70*'-'
    print scores[:,jj]
    scores[:,jj] = scores[:,jj].argsort().argsort()#[::-1]
    print scores[:,jj]

  # For each row, find the lowest value in the row, and add that category name 
  #     to the dictionary in the list of restaurant details dicts
  for ii in range(len(restaurant_details)):
    restaurants[ii]['recommend_type'] = categories[scores[ii,:].argmax()]


  # Only send the top 5 results to be rendered on the page.
  restaurants_long = restaurants
  restaurants = restaurants[0:5]
  restaurant_details_long = restaurant_details
  restaurant_details = restaurant_details[0:5]

  # Use the top N scores to calculate relative ranks for
  #   service, food, atmosphere, and drinks
  decimals = np.zeros(scores.shape)
  for ii in range(len(restaurants_long)):
    for jj in range(len(categories)):
      decimals[ii,jj] = int( 10.* scores[ii,jj] / float(len(restaurants_long)) )
    
    #print ii, scores[ii,:], decimals[ii,:]

  # Add decimal info to the restaurant_details data
  for ii in range(len(restaurant_details)):
    for jj in range(len(categories)):
      restaurant_details[ii][categories[jj]].append(int(decimals[ii,jj]))

  # Make each restaurant details dictionary a dictionary in restaurants
  for ii in range(len(restaurant_details)):
    print '='*70
    print type(restaurant_details[ii])
    print restaurant_details[ii]
    print type(restaurants[ii])
    print restaurants[ii]
    restaurants[ii]['details'] = restaurant_details[ii]
    print '-'*70
    print type(restaurant_details[ii])
    print restaurant_details[ii]
    print type(restaurants[ii])
    print restaurants[ii]
    print '='*70


  return render_template("output.html", input_term=input_term,
                         restaurants = restaurants, 
                         restaurant_details=restaurant_details)

