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
    restaurant_details.append(query_results)

  return render_template("output.html", input_term=input_term,
                         restaurants = restaurants, 
                         restaurant_details=restaurant_details)
