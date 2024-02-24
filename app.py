import ast
import os
import re
import sqlite3
from random import randint
import json

from cs50 import SQL
from datetime import datetime
from flask import Flask, g, flash, redirect, render_template, request, session, url_for, abort
from flask_login import login_required, LoginManager
from flask_session import Session
from functools import wraps
from os import listdir
from os.path import isfile, join
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.wrappers.request import Request
from werkzeug.exceptions import HTTPException, NotFound
from functools import wraps



##### Configure application
app = Flask(__name__)


##### Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


##### Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)


##### LoginManager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)


##### Configure CS50 Library to use SQLite database
db = SQL("sqlite:///exercises.db")

##### Load gifs paths
gifsfolder = f'{os.getcwd()}/static/gifs'
gifspaths = [os.path.join(gifsfolder, f) for f in os.listdir(gifsfolder) if
os.path.isfile(os.path.join(gifsfolder, f))]

### groups of bodyParts
results = db.execute("SELECT DISTINCT bodyPart FROM exercises ORDER BY bodyPart")
bodyParts = []
for result in results:
    bodyParts.append(result['bodyPart'])
    ##['Back', 'Cardio', 'Chest', 'Lower Arms', 'Lower Legs', 'Neck', 'Shoulders', 'Upper Arms', 'Upper Legs', 'Waist']

### groups of muscle
results = db.execute("SELECT DISTINCT muscle FROM exercises ORDER BY muscle")
muscles = []
for result in results:
    muscles.append(result['muscle'])
    ##['Abductors', 'Abs', 'Adductors', 'Biceps', 'Calves', 'Cardiovascular System', 'Delts', 'Forearms', 'Glutes', 'Hamstrings', 'Lats', 'Levator Scapulae', 'Pectorals', 'Quads', 'Serratus Anterior', 'Spine', 'Traps', 'Triceps', 'Upper Back']

### group of equipments
results = db.execute("SELECT DISTINCT equipment FROM exercises ORDER BY equipment")
equipments = []
for result in results:
    equipments.append(result['equipment'])
    ##['Assisted', 'Band', 'Barbell', 'Body Weight', 'Bosu Ball', 'Cable', 'Dumbbell', 'Elliptical Machine', 'Ez Barbell', 'Hammer', 'Kettlebell', 'Leverage Machine', 'Medicine Ball', 'Olympic Barbell', 'Resistance Band', 'Roller', 'Rope', 'Skierg Machine', 'Sled Machine', 'Smith Machine', 'Stability Ball', 'Stationary Bike', 'Stepmill Machine', 'Tire', 'Trap Bar', 'Upper Body Ergometer', 'Weighted', 'Wheel Roller']



# Generate random numbers
def genNums(n):
    nums = []
    i = 0
    while i < n:
        num = randint(1,1314)
        if num < 10:
            num = '000'+str(num)
        elif num < 100:
            num = '00'+str(num)
        elif num < 1000:
            num = '0'+str(num)
        else:
            num = str(num)
        nums.append(num)
        i += 1
    return nums

##### Login_required
### More in: https://flask.palletsprojects.com/en/3.0.x/patterns/viewdecorators/#view-decorators
def login_required(f):
    if f is None:
        return redirect("/")
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            message = f"Login or Register!"
            flash(message)
            return render_template('login.html')
        else:
            return f(*args, **kwargs)
    return decorated_function

############################## CONTEXT PROCESSORS
##### Lists
@app.context_processor
def inject_lists():
    print(bodyParts)
    print("Lists injected")
    return {'bodyParts': bodyParts, 'muscles': muscles, 'equipments': equipments}

##### Exercises
@app.context_processor
def inject_exercises():
    exercises = db.execute("SELECT * FROM exercises")
    exercisesJson = json.dumps(exercises)
    print("Exercises injected")
    return {'exercises': exercises, 'exercisesJson': exercisesJson}

##### Favorites
@app.context_processor
def inject_favorites():
    if "user_id" in session:
        username = session["username"]
        favorites = db.execute("SELECT * FROM favorites JOIN exercises ON favorites.exercise = exercises.id WHERE favorites.user = ?", session["user_id"])

        favoritesId = []
        for favorite in favorites:
            favoritesId.append(favorite["exercise"])
        #favoritesJson = json.dumps(favorites)
        print("Favorites injected")
        return {'favorites': favorites, 'favoritesId': favoritesId, 'username': username}
    else:
        return {}


######################## ROUTES
##### INDEX
@app.route("/")
def index():
    nums = genNums(5)
    print(nums)
    return render_template("index.html", nums=nums)


##### SEARCH
@app.route("/search", methods=["GET", "POST"])
def search():
    # User reached route via GET (as by clicking a link or via redirect)
    if request.method == "GET":
        return render_template("search.html", exercises=[], request=request.method)

    # User reached route via POST (as by submitting a form via POST)
    elif request.method == "POST":
        input = request.form.get('searchInput')
        bodyPart = request.form.get('searchBodypart')
        equipment = request.form.get('searchEquipment')
        search= [input, bodyPart, equipment]
        results = db.execute("SELECT * FROM exercises WHERE bodyPart LIKE ? and equipment LIKE ? AND name LIKE ?", '%'+bodyPart+'%', '%'+equipment+'%','%'+str(input)+'%')
        return render_template("search.html", exercises=results, request=request.method, search=search)


##### RESULTS
@app.route("/results", methods=["GET", "POST"])
@login_required
def results():
    input = request.args.get('search')
    results = db.execute("SELECT * FROM exercises WHERE name LIKE ?", '%'+str(input)+'%')
    return render_template('results.html', search=input, exercises=results)


##### EXERCISE
@app.route("/exercise/<exerciseId>")
@login_required
def exercise(exerciseId):
    exercise = db.execute("SELECT * FROM exercises WHERE id = ?", exerciseId)
    try:
        return render_template('exercise.html', exercise=exercise)
    except Exception:
        return render_template('error.html', notfound='Exercise'), 400

##### PROFILE
@app.route("/favorites")
@login_required
def favorites():
    return render_template("favorites.html")


##### FAVORITE BUTTON SCRIPT
@app.route("/favorite", methods=["POST"])
@login_required
def favorite():
    data = request.get_json()
    exerciseId = data['exerciseId']
    isFavorited = data['isFavorited']

    if isFavorited == True:
        db.execute(
            "INSERT INTO favorites (user, exercise) VALUES (?,?)",
            session["user_id"],
            exerciseId
        )
        return render_template("favorites.html")
    elif isFavorited == False:
        db.execute(
            "DELETE FROM favorites WHERE user = ? and exercise = ?",
            session["user_id"],
            exerciseId
        )
        """Return with sucess message"""
        message = f"Unfavorited {exerciseId}!"
        flash(message)
        return render_template("favorites.html")


##### LOGIN
@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""
    # Forget any user_id
    session.clear()

    # User reached route via GET (as by clicking a link or via redirect)
    if request.method == "GET":
        return render_template("login.html")

    # User reached route via POST (as by submitting a form via POST)
    elif request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        # Ensure username was submitted
        if not username:
            message = f"Username not provided"
            flash(message)
            return render_template("login.html")

        # Ensure password was submitted
        elif not password:
            message = f"Password not provided"
            flash(message)
            return render_template("login.html")

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?", username)

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["pwhash"], password):
            message = f"Invalid username or password"
            flash(message)
            print("Login error")
            return render_template("login.html")

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]
        session["username"] = rows[0]["username"]

        # Redirect user to home page
        message = f"Hi, " + session["username"].capitalize() + "!"
        flash(message)
        print("Login successful")
        return redirect("/")


##### LOGOUT
@app.route("/logout", methods=["GET"])
@login_required
def logout():
    """Log user out"""
    # Forget any user_id
    session.clear()
    message = f"Logout realized!"
    flash(message)

    if request.method == "GET":
        # Redirect user to login form
        return redirect("/")


##### REGISTER
@app.route("/register", methods=["GET", "POST"])
def register():
    # Forget any user_id
    session.clear()

    # User reached route via GET (as by clicking a link or via redirect)
    if request.method == "GET":
        return render_template("register.html")

    # User reached route via POST (as by submitting a form via POST)
    elif request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")
        # Create list of speacial characters
        special_chars = r"[ !@#$%&*()]"

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?", username)

        # Ensure username was submitted
        if not username:
            message = f"Must provide username"
            flash(message)
            return render_template("register.html")

        # Ensure both password and confirmation were submitted
        elif not password and not confirmation:
            message = f"Must provide password and confirmation"
            flash(message)
            return render_template("register.html")

        # Ensure password was submitted
        elif not password:
            message = f"Must provide password"
            flash(message)
            return render_template("register.html")

        # Ensure confirmation was submitted
        elif not confirmation:
            message = f"Must provide password confirmation"
            flash(message)
            return render_template("register.html")

        # Ensure passwords provided matches
        elif confirmation != password:
            message = f"Password does not match confirmation"
            flash(message)
            return render_template("register.html")

        # Ensure password is 8 char long
        elif len(password) < 8:
            message = f"Password must be at least 8 characters long"
            flash(message)
            return render_template("register.html")

        # Ensure password is alphanum
        elif re.search('[0-9]',password) == None or re.search(special_chars, password) == None:
            message = f"Password must contain alphanumeric and special characters"
            flash(message)
            return render_template("register.html")

        # Ensure username is unique
        elif len(rows) != 0:
            message = f"Username {username} already in use"
            flash(message)
            return render_template("register.html"), 400


        # Save into database
        pwhash = generate_password_hash(password)
        type = "Free" # standard plan
        available = 4     # number of plans available (4 in the standard free plan)
        db.execute(
            "INSERT INTO users (username, pwhash, type, available) VALUES (?, ?, ?, ?)",
            username,
            pwhash,
            type,
            available
        )

        # Send message
        message = f"Registered!"
        flash(message)

        # Redirect user to home page
        login = db.execute("SELECT * FROM users WHERE username = ?", username)
        session["user_id"] = login[0]["id"]
        session["username"] = username
        return render_template("profile.html")


##### SUBSCRIPTION
@app.route("/subscription")
def subscription():
    return render_template("subscription.html")

##### CHECKOUT
@app.route("/checkout")
def checkout():
    return render_template("checkout.html")

##### CONTACT
# @app.route("/contact")
# def contact():
#     return render_template("contact.html")


################### Error handlers
### More at https://flask.palletsprojects.com/en/3.0.x/errorhandling/

@app.errorhandler(404)
def page_not_found(e):
    # note that we set the 404 status explicitly
    return render_template('error.html', notfound='Page'), 404

@app.errorhandler(405)
def page_not_found(e):
    # note that we set the 404 status explicitly
    return render_template('error500.html'), 405

@app.errorhandler(500)
def servererror(e):
    # note that we set the 500 status explicitly
    return render_template('error500.html'), 500

@app.route('/notfound')
def notfound():
    return render_template('error.html', notfound='Page')
