import os

import requests
import datetime
from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required


#Configuring application
app = Flask(__name__)

#Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

#Configure session to use filesystem (intead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

db = SQL("sqlite:///todo.db")

@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/login", methods=["GET", "POST"])
def login():
    """Logs the user in"""
    #Forget the user
    session.clear()

    #User reached via POST
    if request.method == "POST":

        #Ensure username or password was submitted
        if not request.form.get("username") or not request.form.get("password"):
            return apology("You must be submit an username and a password", 403)

        #Queries database for username
        userrowlen = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        #Checks validity of username and password
        if len(userrowlen) != 1 or not check_password_hash(userrowlen[0]["password"], request.form.get("password")):
            return apology("Incorrect username or password", 403)

        #Remember the user that has logged in
        session["user_id"] = userrowlen[0]["id"]

        #Redirect to home page

        return redirect("/")

    #User reached via GET
    else:
        return render_template("login.html")


@app.route("/register", methods = ["GET", "POST"])
def register():

    #Forget the user
    session.clear()

    #REQUEST VIA POST
    if request.method == "POST":

        #Ensure username and password andd confirmation were filled in correctly
        if not request.form.get("username") or not request.form.get("password") or not request.form.get("confirmation"):
            return apology("You have to fill out every field", 400)

        #Checks password against confirmation
        if request.form.get("password") != request.form.get("confirmation"):
            return apology("Your password does not match the confirmation", 400)

        #Checks the database if the user already exists
        existcheck = db.execute("SELECT username FROM users WHERE username = ?", request.form.get("username"))
        if len(existcheck) == 1:
            return apology("Username already exists", 400)

        #Hashes the password
        hashpass = generate_password_hash(request.form.get("password"))

        #Inserts the user into the database
        db.execute("INSERT INTO users (username, password) VALUES (?,?)", request.form.get("username"), hashpass)

        #Remember the user that was registered
        usernew = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))
        session["user_id"] = usernew[0]["id"]

        #Redirects to homepage
        return redirect("/")

    #REQUEST VIA GET
    else:
        return render_template("register.html")


@app.route("/")
@login_required
def index():

    #grabs userid
    userid = session["user_id"]

    #queries SQL servr
    usertodo = db.execute("SELECT * FROM todo WHERE id = ?", userid)
    print(usertodo)


    return render_template("index.html", usertodo = usertodo)


@app.route("/add", methods = ["GET", "POST"])
@login_required
def add():

    #POST Request
    if request.method == "POST":

        #Make sure all fields are filled in
        if not request.form.get("category") or not request.form.get("description") or not request.form.get("date"):
            return apology("You must fill in all options", 400)

        #Operationalises variables from form
        category = request.form.get("category")
        description = request.form.get("description")
        date = request.form.get("date")

        #grabs userid
        userid = session["user_id"]

        #Checks first if it's a duplicate
        dupecheck = db.execute("SELECT * FROM todo WHERE id = ? AND categories = ? AND description = ? AND date = ?", userid, category, description, date)
        if len(dupecheck) == 1:
            return apology("Exactly the same entry has been added previously")

        #Inserts into SQL server
        else:
            db.execute("INSERT INTO todo (id, categories, description, date) VALUES (?,?,?,?)", userid, category, description, date)

        return redirect("/")

    #GET Request
    return render_template("add.html")

@app.route("/finished", methods = ["POST"])
@login_required
def finish():

    #POST Request
    if request.method == "POST":

        #Initializes variables
        userid = session["user_id"]
        data = request.form.get("finished")
        status = "Finished"
        time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        #SQL into history log
        query = db.execute("SELECT * FROM todo WHERE description = ? AND id = ?", data, userid)

        categories = query[0]["categories"]
        date = query[0]["date"]

        db.execute("INSERT INTO history (id, categories, description, date, dateefin, how) VALUES (?,?,?,?,?,?)", userid, categories, data, date, time, status)

        #SQL injection remove
        db.execute("DELETE FROM todo where id = ? AND description = ?", userid, data)

        #Redirects to homepage
        return redirect("/")



@app.route("/delete", methods = ["POST"])
@login_required
def delete():


    #POST Request
    if request.method == "POST":

        #Initializes variables
        userid = session["user_id"]
        data = request.form.get("deleted")
        status = "Deleted"
        time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        #SQL into history log
        query = db.execute("SELECT * FROM todo WHERE description = ? AND id = ?", data, userid)

        categories = query[0]["categories"]
        date = query[0]["date"]

        db.execute("INSERT INTO history (id, categories, description, date, dateefin, how) VALUES (?,?,?,?,?,?)", userid, categories, data, date, time, status)

        #SQL injection remove
        db.execute("DELETE FROM todo where id = ? AND description = ?", userid, data)

        #Redirects to homepage
        return redirect("/")


@app.route("/history", methods = ["GET"])
@login_required
def history():

    #Query SQL SERVER FOR HISTORY
    userid = session["user_id"]
    data = db.execute("SELECT * FROM history WHERE id = ?", userid)



    return render_template("history.html", data=data)

@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")



#CREATE TABLE users (id INTEGER PRIMARY KEY, username TEXT, password TEXT);
#CREATE TABLE todo (id INTEGER, categories TEXT, description TEXT, date TEXT, FOREIGN KEY (id) REFERENCES users (id));
#CREATE TABLE history (id INTEGER, categories TEXT, description TEXT, date TEXT, dateefin text, how TEXT, FOREIGN KEY (id) REFERENCES users (id));