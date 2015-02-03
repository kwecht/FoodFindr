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
  # mean_info contains quantile ranking of food-findr scores
  # for a given restaurant compared to all mexican restaurants.
  query_results, mean_info = util.query_term(input_term)
  restaurants = []
  count = 1
  for result,mi in zip(query_results,mean_info):
    ffscore = np.round(100*result[2])/100.

    # Get 
    #if mi>0.67:
    #    arrow_type = 'up_arrow'
    #elif mi<0.33:
    #    arrow_type = 'down_arrow'
    #else:
    #    arrow_type = 'side_arrow'

    # Determine which type of circle image to create
    mi_real = mi
    mi_img = int(np.min([np.floor(mi*10),9]))
    restaurants.append(dict(name=result[0], YelpRating=result[1],
                            busid=result[5],
                            FoodFinder=ffscore, Nsentences=result[4],
                            quantile=np.round(1000.*mi_real)/10.,
                            rank=count, decimal=mi_img,
                            text=result[6]))
    count += 1


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
    scores[:,jj] = scores[:,jj].argsort()

  # For each row, find the lowest value in the row, and add that category name 
  #     to the dictionary in the list of restaurant details dicts
  for ii in range(len(restaurant_details)):
    restaurants[ii]['recommend_type'] = categories[scores[ii,:].argmin()]


  return render_template("output.html", input_term=input_term,
                         restaurants = restaurants, 
                         restaurant_details=restaurant_details)
