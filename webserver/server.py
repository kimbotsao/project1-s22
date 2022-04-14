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
import re
from sqlalchemy import *
from sqlalchemy.pool import NullPool
from flask import Flask, request, render_template, g, redirect, Response

tmpl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
app = Flask(__name__, template_folder=tmpl_dir, static_url_path='/static')



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
def home():
  return render_template("home.html")

@app.route('/createaccount')
def createaccount():
  return render_template("createaccount.html")

@app.route('/createaccountredirect',methods=['POST'])
def createaccountredirect():
  data={}
  data['username']=request.form['username']
  data['email']=request.form['email']
  data['birthday']=request.form['birthday']
  data['isadmin']=request.form['isadmin']
  insert1="""INSERT INTO Users(username,email,birthday) VALUES (:username, :email, :birthday)"""
  g.conn.execute(text(insert1),**data)
  if request.form.get('isadmin') == 1:
    insert2="""INSERT INTO Admins(username) VALUES (:username)"""
    g.conn.execute(text(insert2),**data)
  return redirect('/login')

@app.route('/login')
def login():
  return render_template("login.html")

@app.route('/loginredirect',methods=['POST'])
def loginredirect():
  username=request.form['username']
  # page=request.form['page']
  query="SELECT COUNT(*) FROM Users WHERE username='"+username+"'"
  cursor=g.conn.execute(query)
  for i in cursor:
    if (i[0]==1):
      return redirect('/allrecipes/'+username)
  return redirect('/login')

# Save recipe
@app.route('/saverecipe/<username>/<recipe_id>', methods=['POST'])
def saverecipe(username,recipe_id):
  select="SELECT COUNT(*) FROM Saves WHERE username=:username AND recipe_id=:recipe_id"
  cursor=g.conn.execute(text(select),username=username, recipe_id=recipe_id)
  for n in cursor:
    num=n[0]
    #print(num)
  if (num == 0):
    insert1="""INSERT INTO Saves VALUES (:username, :recipe_id)"""
    t=g.conn.execute(text(insert1), username=username, recipe_id=recipe_id)
    t.close()
  
  context={}
  context['username']=username
  context['recipe_id']=recipe_id 
  return render_template('saverecipe.html', **context)

# Form for posting recipe 
@app.route('/postrecipe/<username>')
def postrecipe(username):
  context=dict(data=username)
  return render_template("postrecipe.html",**context)

# Posts the recipe 
@app.route('/post',methods=['POST'])
def post():
  # Get the form fields 
  data={}
  data['username']=request.form['username']
  ingredients=request.form['ingredient']
  data['name']=request.form['name']
  data['instructions']=request.form['instructions']

  # Get the index of the last posted recipe, add 1 
  cursor = g.conn.execute("SELECT recipe_id FROM Post_Recipes ORDER BY recipe_id DESC LIMIT 1")
  for i in cursor:
    recipe_id=i[0]+1
  data['recipe_id']=recipe_id
  cursor.close()

  # Insert the recipe into Post_Recipes
  cmd = 'INSERT INTO Post_Recipes(username, recipe_id, name, instructions) VALUES (:username,:recipe_id,:name,:instructions)'
  t=g.conn.execute(text(cmd), **data)
  t.close()

  # Insert the ingredients into the Needs table 
  ingredients2=ingredients.split(';')
  for i in ingredients2:
    i_list=i.split(',')
    ing_dict={}
    ing_dict['measurement']=float(i_list[0])
    ing_dict['units']=i_list[1]
    ing=i_list[2]
    ing_dict['ingredient']=ing
    ing_dict['recipe_id']=recipe_id

    # Find out whether or not the ingredient already exists in the table 
    select="SELECT COUNT(*) FROM Ingredients WHERE ingredient=:ingredient"
    cursor=g.conn.execute(text(select),ingredient=ing)
    for n in cursor:
      num=n[0]
      #print(num)
    if (num == 0):
      insert1="""
        INSERT INTO Ingredients(ingredient) VALUES (:ingredient)"""
      t=g.conn.execute(text(insert1), ingredient=ing)
      t.close()
    insert2="""INSERT INTO Needs(recipe_id, ingredient, measurement, units) VALUES (:recipe_id, :ingredient, :measurement, :units)"""
    t=g.conn.execute(text(insert2), **ing_dict)
    t.close()
  return redirect('/recipeposted/'+str(data['username'])+'/'+str(recipe_id))

# Page for after recipe is posted 
@app.route('/recipeposted/<username>/<recipe_id>')
def recipeposted(username,recipe_id):
  cursor = g.conn.execute("SELECT * FROM Post_Recipes WHERE recipe_id="+recipe_id)
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

  return render_template("recipeposted.html", **context)

# View reviews for a certain recipe
@app.route('/reviews/<username>/<recipe_id>')
def reviews(username,recipe_id):

  cursor = g.conn.execute("SELECT * FROM Leaves_Review WHERE recipe_id="+recipe_id)
  reviews=[]
  for i in cursor: 
    r={}
    r['review_id']=i['review_id']
    r['body']=i['body']
    r['rating']=i['rating']
    r['username']=i['username']
    reviews.append(r)
  
  cursor.close() 
  context=dict(data=reviews)
  context['recipe_id']=recipe_id
  context['username']=username 
  return render_template("reviews.html",**context)

# Search by ingredient 
@app.route('/ingformpage/<username>')
def ingformpage(username):
  context=dict(data=username)
  
  return render_template("ingformpage.html",**context)

@app.route('/ingform',methods=['POST'])
def ingform():
  ing = request.form['ingredient']
  username=request.form['username']
  print(ing)
  return redirect('/searchbying/'+username+'/'+ing)

@app.route('/searchbying/<username>/<ingredient>')
def searchbying(username,ingredient):
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
  context['username']=username

  return render_template("reciperesults.html",**context)

# Search by name 
@app.route('/nameformpage/<username>')
def nameformpage(username):
  context=dict(data=username)
  return render_template("nameformpage.html",**context)

@app.route('/nameform',methods=['POST'])
def nameform():
  name = request.form['name']
  username=request.form['username']
  return redirect('/searchbyname/'+username+'/'+name)

@app.route('/searchbyname/<username>/<name>')
def searchbyname(username,name):
  cursor = g.conn.execute("SELECT * FROM Post_Recipes AS PR, Needs as N WHERE N.ingredient='"+name+"' AND PR.recipe_id=N.recipe_id")
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
  context['username']=username

  return render_template("reciperesults.html",**context)

@app.route('/leavereview',methods=['POST'])
def leavereview():
  data={}
  data['username']=request.form['username']
  data['recipe_id']=int(request.form['recipe_id'])
  data['rating']=int(request.form['rating'])
  data['body']=request.form['body']

  cursor = g.conn.execute("SELECT review_id FROM Leaves_Review ORDER BY review_id DESC LIMIT 1")
  for i in cursor:
    review_id=i[0]+1
    print(review_id)
  data['review_id']=review_id+1
  cursor.close()

  cmd = 'INSERT INTO Leaves_Review(review_id, rating, body, recipe_id, username) VALUES (:review_id, :rating, :body, :recipe_id, :username)'
  t=g.conn.execute(text(cmd), **data)
  t.close()

  context=data
  return render_template('reviewposted.html',**context)

# @app.route('/post')
# def
#  post():
#   name = request.form['name']
#   print(name)
#   cmd = 'INSERT INTO test(name) VALUES (:name1), (:name2)';
#   g.conn.execute(text(cmd), name1 = name, name2 = name);
#   return redirect('/')
  
@app.route('/allrecipes/<username>')
def allrecipes(username):
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
    
    label_cursor=g.conn.execute("SELECT * FROM Create_Labels AS CL, Labels AS L WHERE recipe_id="+str(recipe_id)+" AND CL.label_name=L.label_name")
    labels=[]
    for l in label_cursor: 
      label={}
      label['label_name']=l['label_name']
      label['color']=l['color']
      labels.append(label)
    label_cursor.close()
    recipe_dict['labels']=labels
  cursor.close()
  recipes.append
  context = dict(data = recipes)
  context['username']=username

  return render_template("allrecipes.html", **context)

@app.route('/user/<username>')
def user(username):
  context=dict(data=username)
  return render_template("user.html",**context)

@app.route('/myrecipes/<username>')
def myrecipes(username):
  recipes = []
  rec_cursor = g.conn.execute("SELECT * FROM Post_Recipes WHERE username='"+str(username)+"'")
  for recipe in rec_cursor:
    id=recipe['recipe_id']
    ing_cursor=g.conn.execute("SELECT * FROM Needs WHERE recipe_id="+str(id))
    recipe_dict={'name':recipe['name'],
      'recipe_id':recipe['recipe_id'],
      'username':recipe['username'],
      'instructions':recipe['instructions'],
      'ingredients':[]}
    for ing in ing_cursor:
      recipe_dict['ingredients'].append(str(ing['measurement'])+' '+ing['units']+' '+ing['ingredient'])
    recipes.append(recipe_dict)
    
  rec_cursor.close()
  context=dict(data=recipes)
  return render_template("myrecipes.html",**context)

@app.route('/mybooks/<username>')
def mybooks(username):
  # implement recipe books page
  books = []
  bk_cursor = g.conn.execute("SELECT * FROM Owns_RecipeBooks WHERE username='"+str(username)+"'")
  for book in bk_cursor:
    book_dict={'username':book['username'],
      'book_id':book['book_id'],
      'book_name':book['book_name'],
      'public':book['public']}
    books.append(book_dict)
  bk_cursor.close()
  context=dict(data=books)
  return render_template("mybooks.html",**context)

@app.route('/createlabel/<username>')
def createlabel(username):
  context=dict(data=username)
  return render_template("createlabel.html",**context)

@app.route('/labelform',methods=['POST'])
def labelform():
  data={}
  data['username']=request.form['username']
  data['label_name']=request.form['label_name']
  data['color']=request.form['color']
  insert1="""INSERT INTO Create_Labels(username,label_name,color) VALUES (:username, :label_name, :color)"""
  g.conn.execute(text(insert1),**data)
  return redirect('/allrecipes/<username>')

@app.route('/followusers/<username>')
def followusers(username):
  # to do add list of all users to context
  context=dict(data=username)
  return render_template("followuser.html",**context)

# can follow multiple people at once just iterate through and do a execute for each
@app.route('/followform',methods=['POST'])
def followform():
  data={}
  data['usernames']=request.form['usernames']
  for user in usernames:
    insert1="""INSERT INTO Create_Labels(username,label_name,color) VALUES (:username, :label_name, :color)"""
    g.conn.execute(text(insert1),**data)
  return redirect('/allrecipes/<username>')

# add my followers and my following functions for user page display

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
