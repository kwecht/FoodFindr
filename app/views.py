#!/usr/bin/env python

"""
views.py
########################################################################
#
#        Kevin Wecht                22 January 2015
#
#    Insight Data Science Project:
#        Food Finder
#
########################################################################
#
#    views.py
#        - Contains python lines/functions to run when landing on given
#          web pages.
#        - for each page, run the function below the page name
#
########################################################################
"""

__author__      = "Kevin Wecht"

########################################################################

from flask import render_template, request
from app import app
from a_Model import ModelIt
import python_util as util

########################################################################

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

  # Check input for common input errors
  err_msg = util.handle_input(input_term)
  if err_msg!='':
    return render_template('input.html',err_msg=err_msg)

  # Query review data for sentence scores on the search term
  restaurants = util.query_term(input_term)

  # Return input error if no terms match
  if len(restaurants)==0:
    err_msg = 'No matches found. Please try another search term.'
    return render_template('input.html',err_msg=err_msg)

  # Query review data for sentences scores on various features of the top restaurants
  rest_ids = [r['ID'] for r in restaurants]  # list of business ID for each restaurant
  restaurant_details = []
  for r in restaurants:
    query_results = util.query_business(r['ID'],input_term)
    r['details'] = query_results


  # -------- Find the best ranked category for each restaurant --------
  # Build numpy array of FoodFindr scores for each restaurant and category. 
  categories = ['food','service','atmosphere','drinks']
  scores = np.zeros((len(restaurants),len(categories)))
  for ii in range(len(restaurants)):
    for jj in range(len(categories)):
      scores[ii,jj] = restaurants[ii]['details'][categories[jj]]['ffscore']

  # Calculate a numerical rank based on the scores in each category
  score_ranks = np.zeros(scores.shape)
  for jj in range(len(categories)):
    score_ranks[:,jj] = len(restaurants)-scores[:,jj].argsort().argsort()

  # Find the category of the lowest ranking (best) score for each restaurant
  for ii in range(len(restaurants)):
    restaurants[ii]['recommend_type'] = categories[score_ranks[ii,:].argmin()]

  # Find the rank of each category in restaurants
  for ii in range(len(restaurants)):
    for jj in range(len(categories)):
      restaurants[ii]['details'][categories[jj]]['rank'] = int(score_ranks[ii,jj])


  # Return top N restaurants to the webpage
  topN = 5
  total_evaluated = len(restaurants)
  restaurants = restaurants[0:topN]

  return render_template("output.html", input_term=input_term,
                         restaurants = restaurants, 
                         total_evaluated=total_evaluated,
                         restaurant_details=restaurant_details)

