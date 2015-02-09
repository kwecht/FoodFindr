from flask import render_template, request
from app import app
import pymysql as mdb
from a_Model import ModelIt
import python_util as util

db = mdb.connect(user="root", host="localhost", db="world_innodb", charset='utf8')

#@app.route('/')
#@app.route('/index')
#def index():
#    return render_template("index.html",
#       title = 'Home', user = { 'nickname': 'Miguel' },
#       )


@app.route('/about')
def about_page():
  return render_template("about.html")

@app.route('/slides')
def slides_page():
  return render_template("slides.html")

@app.route('/')
@app.route('/index')
@app.route('/input')
def food_input():
  return render_template("input.html",error_string='')

@app.route('/output')
def food_output():
  import numpy as np

  # Pull ID from the input field and store it
  input_term = request.args.get('ID')
  input_term = input_term.lower()
  err_msg = util.handle_input(input_term)
  if err_msg!='':
    return render_template('input.html',err_msg=err_msg)

  # Query review data for sentence scores on the search term
  restaurants = util.query_term(input_term)


  # Query review data for sentences scores on various features of the top 5 restaurants
  rest_ids = [r['ID'] for r in restaurants]  # list of business ID for each restaurant
  restaurant_details = []
  for r in restaurants:
    query_results = util.query_business(r['ID'],input_term)
    r['details'] = query_results

  # Find the best ranked category for each restaurant
  categories = ['food','service','atmosphere','drinks']
  scores = np.zeros((len(restaurants),len(categories)))
  for ii in range(len(restaurants)):
    for jj in range(len(categories)):
      scores[ii,jj] = restaurants[ii]['details'][categories[jj]]['ffscore']

  # Replace each numerical value with an integer based on its rank in the column
  score_ranks = np.zeros(scores.shape)
  for jj in range(len(categories)):
    score_ranks[:,jj] = len(restaurants)-scores[:,jj].argsort().argsort()#[::-1]

  # Find the category of the lowest ranking (best) score for each restaurant
  for ii in range(len(restaurants)):
    restaurants[ii]['recommend_type'] = categories[score_ranks[ii,:].argmin()]

  # Find the rank of each category in restaurants
  for ii in range(len(restaurants)):
    for jj in range(len(categories)):
      restaurants[ii]['details'][categories[jj]]['rank'] = int(score_ranks[ii,jj])


  # Return top N restaurants
  topN = 5
  total_evaluated = len(restaurants)
  restaurants = restaurants[0:topN]


  return render_template("output.html", input_term=input_term,
                         restaurants = restaurants, 
                         total_evaluated=total_evaluated,
                         restaurant_details=restaurant_details)

