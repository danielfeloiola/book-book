import os
import requests

from flask import Flask, session, render_template, request, redirect, jsonify, flash
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True


# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)


# Set up database
uri = os.getenv("DATABASE_URL")
if not uri:
    raise RuntimeError("DATABASE_URL is not set")


engine = create_engine(uri)
db = scoped_session(sessionmaker(bind=engine))


@app.route("/")
def index():
    return render_template("index.html")

@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/login", methods=["GET", "POST"])
def login():

    # if user is looking for the login page
    if request.method == "GET":
        return render_template("login.html")

    # if user is loging in
    else:

        # Forget any user_id
        session.clear()

        # Ensure username was submitted
        if not request.form.get("email"):
            error = "must provide email"
            return render_template("login.html", error=error)

        # Ensure password was submitted
        elif not request.form.get("password"):
            error = "must provide password"
            return render_template("login.html", error=error)

        # Query database to get user data
        rows = db.execute("SELECT * FROM users WHERE email = :email",
                          {"email":request.form.get("email")}).fetchall()

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["password"], request.form.get("password")):
            error = "invalid username and/or password"
            return render_template("login.html", error=error)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]
        session["login"] = True

        # Redirect user to home page
        return redirect("/")


@app.route("/register", methods=["GET", "POST"])
def register():

    # Forget any user_id
    session.clear()

    # if looking for the form
    if request.method == "GET":
        return render_template("register.html")

    # if submitting data
    elif request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("email"):
            error = "must provide email"
            return render_template("register.html", error=error)

        # Ensure password was submitted
        elif not request.form.get("password"):
            error = "must provide password"
            return render_template("register.html", error=error)

         # Ensure passwords match
        if request.form.get("password") != request.form.get("confirm-password"):
            error = "Passwords don't match"
            return render_template("register.html", error=error)

        # encrypt passwprd
        hash_password = generate_password_hash(request.form.get("password"))

        # query to check if the username already exists
        query = db.execute("SELECT * FROM users WHERE email = :email", {"email":request.form.get("email")}).fetchone()

        # if its a unique username add user to database
        if not query:
            db.execute("INSERT INTO users (email, password) VALUES (:email, :password)",
                    {"email": request.form.get("email"), "password": hash_password})
            db.commit()

            # do the login proces as well
            rows = db.execute("SELECT * FROM users WHERE email = :email",
                              {"email":request.form.get("email")}).fetchall()

            # add user to session
            session["user_id"] = rows[0]["id"]
            session["login"] = True

            # Redirect user to home page
            return redirect("/")

        else:
            error = "username already exists"
            return render_template("register.html", error=error)


@app.route("/search", methods=["GET"])
def search():

    if request.method == "GET":

        # get the name of the bok from serchbar
        book = request.args.get("book")

        # query db for books
        query = f"SELECT * FROM books WHERE title ILIKE '%{book}%' OR author ILIKE '%{book}%' OR isbn ILIKE '%{book}%';"
        results = db.execute(query).fetchall()

        # lists for ratings
        ratings = []
        percentages = []

        # if no books matched query
        if not results:

            # make a variable
            no_results = True

            # Say no books matched the query
            return render_template("results.html", no_results=no_results)

        # else
        else:
            # iterate results to get ratings for each book
            for item in results:

                #get isbn
                isbn = item[1]

                # get rating from goodreads
                #req = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": os.getenv("API_KEY"), "isbns": isbn})
                #rate = req.json()

                # add to lists that will go to the html page
                #ratings.append(float(rate['books'][0]['average_rating']))
                #percentages.append(int(float(rate['books'][0]['average_rating']) * 20))

            return render_template("results.html", results=results, ratings=None, percentages=None)

@app.route("/book/<isbn>", methods=["GET", "POST"])
def book(isbn):

    # get the name of the book from serchbar
    book = isbn

    # query db for books
    query = f"SELECT * FROM books WHERE isbn = '{book}'"
    results = db.execute(query).fetchall()

    # iterate results to get ratings for each book
    for item in results:

        #get isbn
        isbn = item[1]

        # get rating from goodreads
        #req = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": os.getenv("API_KEY"), "isbns": isbn})
        #rate = req.json()

        # add to lists that will go to the html page
        #rating = float(rate['books'][0]['average_rating'])
        #review = int(rate['books'][0]['reviews_count'])

        # get book data
        title = results[0][2]
        author = results[0][3]
        year = results[0][4]
        isbn = isbn
        #review_count = review
        #average_score = rating

    # get reviews
    revs = db.execute(f"SELECT review FROM reviews WHERE isbn = '{book}'")

    #if looking for the page
    if request.method == "GET":

        # if user is logged in
        if session:

            #query to check if the username has already posted a review
            check_review = db.execute("SELECT review FROM reviews WHERE userid = :userid AND isbn = :isbn", {"userid":session["user_id"], "isbn": book}).fetchall()

            # set a variable if yes
            if len(check_review) == 0:
                already_posted = False
            else:
                already_posted = True

            return render_template('book.html', title=title, author=author, year=year, isbn=isbn,  revs=revs, already_posted=already_posted) # review_count=review_count, average_score=average_score,

        # if user is not logged in
        else:

            return render_template('book.html', title=title, author=author, year=year, isbn=isbn, revs=revs) #review_count=review_count, average_score=average_score,


    # IF POST!
    if request.method == "POST":

        # get the review
        review = request.form.get("review")

        #check if user already posted to aviod spammig
        check_review = db.execute("SELECT review FROM reviews WHERE userid = :userid AND isbn = :isbn", {"userid":session["user_id"], "isbn": book}).fetchall()

        # if not add to database
        if len(check_review) == 0:
            # add it to database
            db.execute("INSERT INTO reviews (isbn, review, userid) VALUES (:isbn, :review, :userid)",
                    {"isbn": book, "review": review, "userid": session["user_id"]})
            db.commit()

        # don't allow resending
        already_posted = True

        # then reload the page, this time with the new comment
        return render_template('book.html', title=title, author=author, year=year, isbn=isbn, revs=revs, already_posted=already_posted) #review_count=review_count, average_score=average_score,



@app.route("/api/<isbn>", methods=["GET", "POST"])
def api(isbn):
    ''' API: Returns data about the books in JSON format '''

    # get the name of the bok from serchbar
    book = isbn

    # query db for books
    query = f"SELECT * FROM books WHERE isbn ILIKE '%{book}%';"
    results = db.execute(query).fetchall()

    # if no books matched query
    if not results:

        # make a variable
        #no_results = True
        return jsonify({"error": "Book ISBN is not in database"}), 404
        # Say no books matched the query
        #return render_template("404.html")

    # else
    else:
        # iterate results to get ratings for each book
        for item in results:

            #get isbn
            isbn = item[1]

            # get rating from goodreads
            #req = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": os.getenv("API_KEY"), "isbns": isbn})
            #rate = req.json()

            # add to lists that will go to the html page
            #rating = float(rate['books'][0]['average_rating'])
            #review = int(rate['books'][0]['reviews_count'])

            return jsonify(
                title = results[0][2],
                author = results[0][3],
                year = results[0][4],
                isbn = isbn,
                #review_count = review,
                #average_score = rating
                )

