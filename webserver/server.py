#!/usr/bin/env python2.7

"""
Columbia W4111 Intro to databases
Example webserver

To run locally

    python server.py

Go to http://localhost:8111 in your browser


A debugger such as "pdb" may be helpful for debugging.
Read about it online.
"""

import os
from sqlalchemy import *
from sqlalchemy.pool import NullPool
from flask import Flask, request, render_template, g, redirect, Response

tmpl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
app = Flask(__name__, template_folder=tmpl_dir)



# XXX: The Database URI should be in the format of: 
#
#     postgresql://USER:PASSWORD@<IP_OF_POSTGRE_SQL_SERVER>/<DB_NAME>
#
# For example, if you had username ewu2493, password foobar, then the following line would be:
#py
#     DATABASEURI = "postgresql://ewu2493:foobar@<IP_OF_POSTGRE_SQL_SERVER>/postgres"
#
# For your convenience, we already set it to the class database

# Use the DB credentials you received by e-mail
DB_USER = "jjs2295"
DB_PASSWORD = "Data123"

DB_SERVER = "w4111.cisxo09blonu.us-east-1.rds.amazonaws.com"

DATABASEURI = "postgresql://"+DB_USER+":"+DB_PASSWORD+"@"+DB_SERVER+"/proj1part2"


#
# This line creates a database engine that knows how to connect to the URI above
#
engine = create_engine(DATABASEURI)


# Here we create a test table and insert some values in it
#COMMENTED
# engine.execute("""DROP TABLE IF EXISTS test;""")
# engine.execute("""CREATE TABLE IF NOT EXISTS test (
#   id serial,
#   name text
# );""")
# engine.execute("""INSERT INTO test(name) VALUES ('grace hopper'), ('alan turing'), ('ada lovelace');""")



@app.before_request
def before_request():
  """
  This function is run at the beginning of every web request 
  (every time you enter an address in the web browser).
  We use it to setup a database connection that can be used throughout the request

  The variable g is globally accessible
  """
  try:
    g.conn = engine.connect()
  except:
    print("uh oh, problem connecting to database")
    import traceback; traceback.print_exc()
    g.conn = None

@app.teardown_request
def teardown_request(exception):
  """
  At the end of the web request, this makes sure to close the database connection.
  If you don't the database could run out of memory!
  """
  try:
    g.conn.close()
  except Exception as e:
    pass


#
# @app.route is a decorator around index() that means:
#   run index() whenever the user tries to access the "/" path using a GET request
#
# If you wanted the user to go to e.g., localhost:8111/foobar/ with POST or GET then you could use
#
#       @app.route("/foobar/", methods=["POST", "GET"])
#
# PROTIP: (the trailing / in the path is important)
# 
# see for routing: http://flask.pocoo.org/docs/0.10/quickstart/#routing
# see for decorators: http://simeonfranklin.com/blog/2012/jul/1/python-decorators-in-12-steps/
#
@app.route('/')
def index():
    print(request.args)
    return render_template("index.html")

@app.route('/postrecipe')
def postrecipe():
  return render_template("postrecipe.html")

@app.route('/ingformpage')
def ingformpage():
  return render_template("ingformpage.html")

@app.route('/ingform',methods=['POST'])
def ingform():
  ing = request.form['ingredient']
  print(ing)
  return redirect('/searchbying/'+ing)

@app.route('/searchbying/<ingredient>')
def searchbying(ingredient):
  cursor = g.conn.execute("SELECT * FROM Post_Recipes AS PR, Needs as N WHERE N.ingredient='"+ingredient+"' AND PR.recipe_id=N.recipe_id")
  recipes = []
  for result in cursor:
      # can also be accessed using result[0]
    recipe_id=result['recipe_id']
    ing_cursor=g.conn.execute("SELECT * FROM Needs WHERE recipe_id="+str(recipe_id))
    recipe_dict={'name':result['name'],
      'recipe_id':result['recipe_id'],
      'username':result['username'],
      'instructions':result['instructions'],
      'ingredients':[]}
    
    for ing in ing_cursor:
      recipe_dict['ingredients'].append(str(ing['measurement'])+' '+ing['units']+' '+ing['ingredient'])
    recipes.append(recipe_dict)

    ing_cursor.close()
  cursor.close()
  context = dict(data = recipes)

  return render_template("searchbying.html",**context)

# @app.route('/post')
# def
#  post():
#   name = request.form['name']
#   print(name)
#   cmd = 'INSERT INTO test(name) VALUES (:name1), (:name2)';
#   g.conn.execute(text(cmd), name1 = name, name2 = name);
#   return redirect('/')
  
@app.route('/allrecipes')
def allrecipes():
  cursor = g.conn.execute("SELECT * FROM Post_Recipes")
  recipes = []
  for result in cursor:
      # can also be accessed using result[0]
    recipe_id=result['recipe_id']
    ing_cursor=g.conn.execute("SELECT * FROM Needs WHERE recipe_id="+str(recipe_id))
    recipe_dict={'name':result['name'],
      'recipe_id':result['recipe_id'],
      'username':result['username'],
      'instructions':result['instructions'],
      'ingredients':[]}
    
    for ing in ing_cursor:
      recipe_dict['ingredients'].append(str(ing['measurement'])+' '+ing['units']+' '+ing['ingredient'])
    recipes.append(recipe_dict)

    ing_cursor.close()
  cursor.close()
  context = dict(data = recipes)

  return render_template("allrecipes.html", **context)

# @app.route('/post-recipe', method=['POST'])
# def post_recipe():
#   username=request.form['']

@app.route('/login')
def login():
    abort(401)
    this_is_never_executed()

if __name__ == "__main__":
  import click

  @click.command()
  @click.option('--debug', is_flag=True)
  @click.option('--threaded', is_flag=True)
  @click.argument('HOST', default='0.0.0.0')
  @click.argument('PORT', default=8111, type=int)
  def run(debug, threaded, host, port):
    """
    This function handles command line parameters.
    Run the server using

        python server.py

    Show the help text using

        python server.py --help

    """

    HOST, PORT = host, port
    print("running on %s:%d" % (HOST, PORT))
    app.run(host=HOST, port=PORT, debug=debug, threaded=threaded)


  run()
