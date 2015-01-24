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
  #pull 'ID' from input field and store it
  input_term = request.args.get('ID')
  query_results = util.query_term(input_term)

  restaurants = []
  for result in query_results:
    restaurants.append(dict(name=result[0], nreviews=result[1], stars=result[2]))
  #pop_input = cities[0]['population']
  #the_result = ModelIt(city, pop_input)
  the_result = 5.00
  return render_template("output.html", restaurants = restaurants, the_result = the_result, input_term=input_term)
