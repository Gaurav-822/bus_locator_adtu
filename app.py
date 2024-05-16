import os

from sqlalchemy import create_engine, MetaData, Table, Column, Integer, Text, text, delete, insert
from sqlalchemy.sql.expression import update, select
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime
date_time = datetime.now()

from helpers import apology, login_required

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Making connection to the database
engine = create_engine("sqlite:///data.db", echo = False, connect_args={"check_same_thread": False})
conn = engine.connect()

# Make Tables:
meta = MetaData()
users = Table(
    'users', meta,
    Column('id', Integer, primary_key = True),
    Column('username', Text),
    Column('hash', Text),
    Column('additional', Text), # roll for student and phone no for driver
    Column('driver', Integer), # 0 for student and 1 for driver
    Column('start_p_lat', Integer), # to store the driver's gps and the user's stopage, i.e the start location
    Column('start_p_long', Integer),
)

meta.create_all(engine)

@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# Requires Change
@app.route("/", methods=['GET', 'POST'])
@login_required
def index():
    return render_template('index.html')

@app.route('/update_location', methods=['POST'])
def update_location():
    data = request.get_json()
    lat = data['latitude']
    long = data['longitude']
    session['latitude'] = lat
    session['longitude'] = long
    return render_template("index.html", lat=lat, long=long)

# Status: DONE
@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    # session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        user = text('SELECT username, hash, id, driver, start_p_lat, start_p_long FROM users')
        result = conn.execute(user)
        for row in result:
            if row[0] == request.form.get("username"):
                if check_password_hash(row[1], request.form.get("password")):
                    session['user_id'] = row[2]

                    driver = int(row[3])
                    if driver == 0:
                        lat = row[4]
                        long = row[5]

                        # data of all the buses
                        res = []
                        buses_q = text('SELECT username, start_p_lat, start_p_long FROM users WHERE driver = 1')
                        buses_q_res = conn.execute(buses_q)
                        for d in buses_q_res:
                            res.append([d[0], d[1], d[2]])
                        print(res)
                        return render_template("index.html", lat=lat, long=long, driver=driver, res=res)
                    else:

                        # my location
                        lat = session.get('latitude')
                        long = session.get('longitude')
                        return render_template("index.html", lat=lat, long=long, driver=driver, res=[["name", lat, long]])


        
        return apology('Sorry We cannot find you right now')
    
    else:
        return render_template("login.html")

# Status: DONE
@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")

# Status: Done
@app.route("/register_student", methods=["GET", "POST"])
def register_student():
    """Register user"""
    # Forget any user_id
    # session.clear()

    if request.method == "GET":
        return render_template("register_student.html")
    username = request.form.get('username')
    roll = request.form.get('roll')
    start_p = int(request.form['busStop'])
    locations = [[26.00, 91.86154], [26.2051, 91.861], [26.251, 91.8], [26.201, 91.86150]]
    start_p_lat = locations[start_p - 1][0]
    start_p_long = locations[start_p - 1][1]
    
    password = request.form.get('password')
    confirmation = request.form.get('confirmation')

    user = text('SELECT username, id FROM users GROUP BY id')
    result = conn.execute(user)
    u_l = []
    id = 0
    for row in result:
        u_l.append(row[0])
        id = row[1]
    if username == '' or username in u_l:
        return apology('input is blank or the username already exists.')
    u_l = []
    if password == '' or password != confirmation:
        return apology('Password input is blank or the passwords do not match.')
    
    ins = users.insert().values(username = username, hash = generate_password_hash(password), additional = roll, driver = 0, start_p_lat=start_p_lat, start_p_long=start_p_long)
    conn.execute(ins)


    return render_template("login.html")

# Status: Done
@app.route("/register_driver", methods=["GET", "POST"])
def register_driver():
    """Register user"""
    # Forget any user_id
    # session.clear()

    if request.method == "GET":
        return render_template("register_driver.html")
    username = request.form.get('username')
    phn = request.form.get('phn')
    password = request.form.get('password')
    confirmation = request.form.get('confirmation')

    start_p = int(request.form['busStop'])
    locations = [[26.00, 91.86154], [26.2051, 91.861], [26.251, 91.8], [26.201, 91.86150]]
    start_p_lat = locations[start_p - 1][0]
    start_p_long = locations[start_p - 1][1]

    user = text('SELECT username, id FROM users GROUP BY id')
    result = conn.execute(user)
    u_l = []
    id = 0
    for row in result:
        u_l.append(row[0])
        id = row[1]
    if username == '' or username in u_l:
        return apology('input is blank or the username already exists.')
    u_l = []
    if password == '' or password != confirmation:
        return apology('Password input is blank or the passwords do not match.')


    ins = users.insert().values(username = username, hash = generate_password_hash(password), additional = phn, driver = 1, start_p_lat=start_p_lat, start_p_long=start_p_long)
    conn.execute(ins)


    return render_template("login.html")

# Requires Change
@app.route("/location", methods=['GET', 'POST'])
@login_required
def location():
    return render_template("location.html")

@app.route("/bus_record", methods=['GET', 'POST'])
@login_required
def bus_record():
    return render_template("bus_record.html")

@app.route("/about", methods=['GET', 'POST'])
@login_required
def about():
    return render_template("about.html")

@app.route("/members", methods=['GET', 'POST'])
@login_required
def members():
    return render_template("members.html")