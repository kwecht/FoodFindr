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

@app.route('/db')
def cities_page():
    with db:
        cur = db.cursor()
        cur.execute("SELECT Name FROM City LIMIT 15;")
        query_results = cur.fetchall()
    cities = ""
    for result in query_results:
        cities += result[0]
        cities += "<br>"
    return cities


@app.route("/db_fancy")
def cities_page_fancy():
    with db:
        cur = db.cursor()
        cur.execute("SELECT Name, CountryCode, Population FROM City ORDER BY Population LIMIT 15;")

        query_results = cur.fetchall()
    cities = []
    for result in query_results:
        cities.append(dict(name=result[0], country=result[1], population=result[2]))
    return render_template('cities.html', cities=cities)

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
  query_results = util.query_term(input_term)
  restaurants = []
  for result in query_results:
    ffscore = np.round(100*result[2])/100.
    restaurants.append(dict(name=result[0], YelpRating=result[1], 
                            FoodFinder=ffscore, Nsentences=result[3]))

  # Query review data for sentences scores on various features of the top 5 restaurants
  rest_ids = [r[4] for r in query_results]  # list of business ID for each restaurant
  restaurant_details = []
  for RID in rest_ids:
    query_results = util.query_business(RID,input_term)
    restaurant_details.append(query_results)


  return render_template("output.html", restaurants = restaurants, 
                         input_term=input_term, restaurant_details=restaurant_details)
