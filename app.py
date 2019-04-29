# import libraries
from flask import \
    Flask, \
    flash, \
    render_template, \
    request, \
    url_for, \
    redirect, \
    session
from flask_mail import \
    Mail, \
    Message
from flask_session import Session
from cs50 import SQL
from passlib.apps import custom_app_context as pwd_context
from flask_sslify import SSLify
from util import *
import datetime
import requests
import random
import re
import os

app = Flask(__name__)
mail = Mail(app)

if 'DYNO' in os.environ:
    sslify = SSLify(app)

app.secret_key = os.urandom(24)

if app.config["DEBUG"]:
    @app.after_request
    def after_request(response):
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Expires"] = 0
        response.headers["Pragma"] = "no-cache"
        return response

API_KEY = "&key=AIzaSyBfdmZZVzkHwhbl-DVouoG7M8OZKBLQUUw"
app.config["SESSION_PERMANENT"] = True
app.config["SESSION_TYPE"] = "filesystem"
app.config["PERMANENT_SESSION_LIFETIME"] = 10800
app.config["SESSION_COOKIE_HTTPONLY"] = False
app.config["SESSION_COOKIE_SECURE"] = True
Session(app)

app.config['MAIL_SERVER']='smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = 'test@mail.com'
app.config['MAIL_PASSWORD'] = 'qwerty'
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
mail = Mail(app)

database = SQL("sqlite:///evaLib.db")

# index route
@app.route("/")
def index():
    return render_template("index.html",
                           books = requests.get("https://www.googleapis.com/books/v1/volumes?q=" +
                            random.choice('abcdefghijklmnopqrstuvwxzy') +
                            "&maxResults=40" + API_KEY).json())

@app.errorhandler(404)
def page_not_found(e):
    return render_template("pageNotFound.html")


@app.route("/about")
def about():
    return render_template("about.html")


# blog route
@app.route("/blog")
def blog():

    posts = database.execute("SELECT * FROM posts")
    usersPosts = list()

    for post in posts:
        user = database.execute("SELECT * FROM users WHERE id = :id", id = post["user_id"])
        usersPosts.append({"id": post["id"], "title": post["title"], "username": user[0]["username"]})

    return render_template("blog.html", posts = usersPosts)


@app.route("/search", methods = ["POST", "GET"])
def search():

    if request.method == "POST":

        if not request.form.get("title"):
            return promptUser("title")

        # If user entered author
        if request.form.get("author"):
            return render_template("searchResults.html",
                                   books = requests.get("https://www.googleapis.com/books/v1/volumes?q=" +
                                                        request.form.get("title") +
                                                        "+inauthor:" +
                                                        request.form.get("author") +
                                                        API_KEY).json())

        # If user entered publisher
        if request.form.get("publisher"):
            return render_template("searchResults.html",
                                   books = requests.get("https://www.googleapis.com/books/v1/volumes?q=" +
                                                        request.form.get("title") +
                                                        "+inpublisher:" +
                                                        request.form.get("publisher") +
                                                        API_KEY).json())

        # If user entered author and publisher
        if request.form.get("author") and request.form.get("publisher"):
            return render_template("searchResults.html", books = requests.get("https://www.googleapis.com/books/v1/volumes?q=" +
                                                                              request.form.get("title") +
                                                                              "+inauthor:" +
                                                                              request.form.get("author") +
                                                                              "+inpublisher:" +
                                                                              request.form.get("publisher") +
                                                                              API_KEY).json())

        return render_template("searchResults.html",
                               books = requests.get("https://www.googleapis.com/books/v1/volumes?q=" +
                                                    request.form.get("title") +
                                                    API_KEY).json())

    else:
        return render_template("search.html")

@app.route("/profile")
@loginRequired
def profile():

    # Query database to obtain user information
    user = database.execute("SELECT * FROM users WHERE id = :id", id = session["user_id"])

    # Query to obtain read books
    books = database.execute("SELECT * FROM books WHERE user_id = :user_id", user_id = session["user_id"])

    readBooks = list()

    #  HTTP Query to obtain all books read by user
    for book in books:
        readBooks.append(requests.get("https://www.googleapis.com/books/v1/volumes?q=" +
                                        book["book_id"] +
                                        API_KEY).json()["items"][0])

    # Query database to obtain all comments made by user
    comments = database.execute("SELECT * FROM comments WHERE user_id = :user_id", user_id = session["user_id"])

    usersComments = list()

    # Obtain all books user has commented on
    for comment in comments:
        book = requests.get("https://www.googleapis.com/books/v1/volumes?q=" +
                            comment["book_id"] +
                            API_KEY).json()
        usersComments.append({"id": comment["id"],
                              "comment": comment["comment"],
                              "dateOfPublish": comment["dateOfPublish"],
                              "book": book["items"][0]})

    grades = database.execute("SELECT * FROM grades WHERE user_id = :user_id",
                              user_id = session["user_id"])

    usersGrades = list()

    for grade in grades:
        book = requests.get("https://www.googleapis.com/books/v1/volumes?q=" +
                            grade["book_id"] +
                            API_KEY).json()
        usersGrades.append({"id": grade["id"],
                            "grade": grade["grade"],
                            "dateOfEvaluation": grade["dateOfEvaluation"],
                            "book": book["items"][0]})

    posts = database.execute("SELECT * FROM posts WHERE user_id = :user_id",
                             user_id = session["user_id"])

    return render_template("profile.html",
                           user = user[0],
                           books = readBooks,
                           comments = usersComments,
                           grades = usersGrades,
                            posts = posts)


@app.route("/bookDetails/<book_id>")
def bookDetails(book_id):

    books = database.execute("SELECT * FROM books WHERE book_id = :book_id",
                             book_id = book_id)

    grades = database.execute("SELECT * FROM grades WHERE book_id = :book_id",
                              book_id = book_id)

    comments = database.execute("SELECT * FROM comments WHERE book_id = :book_id",
                                book_id = book_id)

    usersComments = list()

    for comment in comments:
        user = database.execute("SELECT * FROM users WHERE id = :id",
                                id = comment["user_id"])
        if user:
            usersComments.append({"id": comment["id"],
                                  "comment": comment["comment"],
                                  "dateOfPublish": comment["dateOfPublish"],
                                  "username": user[0]["username"],
                                  "user_id": comment["user_id"]})

    usersGrades = list()

    for grade in grades:
        user = database.execute("SELECT * FROM users WHERE id = :id",
                                id = grade["user_id"])
        if user:
            usersGrades.append({"id": grade["id"], "grade": grade["grade"],
                                "dateOfEvaluation": grade["dateOfEvaluation"],
                                "username": user[0]["username"],
                                "user_id": grade["user_id"]})

    # Count times book has been read
    if len(books) > 0:
        numberOfReadings = len(books)
    else:
        numberOfReadings = 0

    # Calc average rating of book
    gradesSum = 0

    for grade in grades:
        gradesSum += grade["grade"]

    if len(grades) > 0:
        averageGrade = gradesSum / len(grades)
    else:
        averageGrade = 0
    
    graded = False
    read = False
    
    # Check if user is logged in
    if session.get("user_id") != None:
        
        # Check if user has already graded book
        for grade in grades:
            if grade["user_id"] == session["user_id"] and grade["book_id"] == book_id:
                graded = True
                break

        # Check if book is already in bookmarks
        for book in books:
            if book["book_id"] == book_id and book["user_id"] == session["user_id"]:
                read = True
                break

    # Obtain book information as JSON that user clicks
    book = requests.get("https://www.googleapis.com/books/v1/volumes?q=" + book_id + API_KEY).json()

    return render_template("bookDetails.html", book = book["items"][0], numberOfReadings = numberOfReadings,
                            averageGrade = averageGrade, grades = usersGrades, comments = usersComments, graded = graded,
                            read = read)


# page to allow user to add comment (user must be authenticated)
@app.route("/addComment/<book_id>", methods = ["GET", "POST"])
@loginRequired
def addComment(book_id):

    if request.method == "POST":

        if not request.form.get("comment"):
            return promptUser("comment")

        database.execute("""INSERT INTO comments (comment, dateOfPublish, user_id, book_id)
                            VALUES(:comment, :dateOfPublish, :user_id, :book_id)""", comment = request.form.get("comment"),
                            dateOfPublish = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), user_id = session["user_id"],
                            book_id = book_id)

        flash("Comment Successful!")
        return redirect(url_for("bookDetails", book_id = book_id))

    else:
        return render_template("addComment.html", book_id = book_id)


# Page to allow user to update a comment (user must be authenticated)
@app.route("/updateComment/<int:comment_id>", methods = ["POST", "GET"])
@loginRequired
def updateComment(comment_id):

    if request.method == "POST":
        if not request.form.get("updatedComment"):
            return promptUser("updatedComment")

        database.execute("UPDATE comments SET comment = :comment, dateOfPublish = :dateOfPublish WHERE id = :id",
                          comment = request.form.get("updatedComment"),
                          dateOfPublish = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), id = comment_id)

        flash("Update Successful!")

        return redirect(url_for("profile"))

    else:
        comment = database.execute("SELECT * FROM comments WHERE id = :id", id = comment_id)

        return render_template("updateComment.html", comment = comment[0])


# Delete comment page
# TODO: Add confirmation for delete
@app.route("/deleteComment/<int:comment_id>", methods = ["GET", "POST"])
@loginRequired
def deleteComment(comment_id):

    database.execute("DELETE FROM comments WHERE id = :id",
                     id = comment_id)
    flash("Delete Successful!")
    return redirect(url_for("profile"))

@app.route("/addGrade/<book_id>", methods = ["GET", "POST"])
@loginRequired
def addGrade(book_id):
    if request.method == "POST":
        if not request.form.get("grade"):
            return promptUser("grade")
        database.execute("""INSERT INTO grades (grade, dateOfEvaluation, user_id, book_id)
                            VALUES(:grade, :dateOfEvaluation, :user_id, :book_id)""", grade = int(request.form.get("grade")),
                            dateOfEvaluation = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), user_id = session["user_id"],
                            book_id = book_id)
        flash("Grading Successful!")
        return redirect(url_for("bookDetails", book_id = book_id))
    else:
        return render_template("addGrade.html", book_id = book_id)


@app.route("/updateGrade/<int:grade_id>", methods = ["POST", "GET"])
@loginRequired
def updateGrade(grade_id):
    if request.method == "POST":
        if not request.form.get("updatedGrade"):
            return promptUser("grade")
        database.execute("UPDATE grades SET grade = :grade, dateOfEvaluation = :dateOfEvaluation WHERE id = :id",
                         grade = request.form.get("updatedGrade"),
                         dateOfEvaluation = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                         id = grade_id)
        flash("Update Successful!")
        return redirect(url_for("profile"))
    else:
        grade = database.execute("SELECT * FROM grades WHERE id = :id", id = grade_id)
        return render_template("updateGrade.html", grade = grade[0])


@app.route("/deleteGrade/<int:grade_id>", methods = ["GET", "POST"])
@loginRequired
def deleteGrade(grade_id):
    database.execute("DELETE FROM grades WHERE id = :id", id = grade_id)
    flash("Grade deleted!")
    return redirect(url_for("profile"))


@app.route("/postDetails/<int:post_id>")
def postDetails(post_id):
    post = database.execute("SELECT * FROM posts WHERE id = :id", id = post_id)
    user = database.execute("SELECT * FROM users WHERE id = :id", id = post[0]["user_id"])
    return render_template("postDetails.html", post = post[0], user = user[0])


@app.route("/publish", methods = ["POST", "GET"])
@loginRequired
def publish():
    if request.method == "POST":
        if not request.form.get("title"):
            return promptUser("title")
        if not request.form.get("content"):
            return promptUser("content")
        database.execute("""INSERT INTO posts (title, content, dateOfPublish, user_id)
                            VALUES(:title, :content, :dateOfPublish, :user_id)""", title = request.form.get("title"),
                            content = request.form.get("content"),
                            dateOfPublish = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), user_id = session["user_id"])
        flash("Published!")
        return redirect(url_for("blog"))
    else:
        return render_template("publish.html")


@app.route("/updatePost/<int:post_id>", methods = ["POST", "GET"])
@loginRequired
def updatePost(post_id):
    if request.method == "POST":
        if not request.form.get("updatedTitle"):
            return promptUser("title")
        if not request.form.get("updatedContent"):
            return promptUser("content")
        database.execute("UPDATE posts SET title = :title, content = :content, dateOfPublish = :dateOfPublish WHERE id = :id",
                          title = request.form.get("updatedTitle"), content = request.form.get("updatedContent"),
                          dateOfPublish = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), id = post_id)
        flash("Updated!")
        return redirect(url_for("profile"))
    else:
        post = database.execute("SELECT * FROM posts WHERE id = :id", id = post_id)
        return render_template("updatePost.html", post = post[0])


@app.route("/deletePost/<int:post_id>", methods = ["GET", "POST"])
@loginRequired
def deletePost(post_id):
    database.execute("DELETE FROM posts WHERE id = :id", id = post_id)
    flash("Delete Successful!")
    return redirect(url_for("profile"))


@app.route("/addBook/<book_id>", methods = ["POST", "GET"])
@loginRequired
def addBook(book_id):
    database.execute("INSERT INTO books (book_id, user_id) VALUES(:book_id, :user_id)", book_id = book_id,
                      user_id = session["user_id"])
    flash("Book Bookmarked!")
    return redirect(url_for("bookDetails", book_id = book_id))


@app.route("/deleteBook/<book_id>", methods = ["GET", "POST"])
@loginRequired
def deleteBook(book_id):
    database.execute("DELETE FROM books WHERE book_id = :book_id", book_id = book_id)
    flash("Delete Successful!")
    return redirect(url_for("profile"))


# register route
@app.route("/register", methods = ["GET", "POST"])
@loggedIn
def register():
    if request.method == "POST":

        if not request.form.get("username"):
            return promptUser("Username cannot be blank.")

        if not re.match(r'^(?=.{2,20}$)(?![_.])(?!.*[_.]{2})[a-zA-Z0-9._]+(?<![_.])$', request.form.get("username")):
            return promptUser("Invalid Username.")

        if not request.form.get("firstName"):
            return promptUser("First Name cannot be blank.")

        if not re.match(r'^(?=.{2,20}$)(?![_.])(?!.*[_.]{2})[A-Za-z]+(?<![_.])$', request.form.get("firstName")):
            return promptUser("First Name must be valid. Only letters are allowed.")

        if not request.form.get("lastName"):
            return promptUser("Last Name cannot be blank.")

        if not re.match(r'^(?=.{2,20}$)(?![_.])(?!.*[_.]{2})[A-Za-z]+(?<![_.])$', request.form.get("lastName")):
            return promptUser("Last Name is Invalid. Only letters are allowed.")

        if not request.form.get("email"):
            return promptUser("Email cannot be blank.")

        # Mitigate XSS
        if '/''' in request.form.get("email") or ';' in request.form.get("email"):
            return promptUser("Invalid characters.")

        if not request.form.get("password"):
            return promptUser("Password cannot be blank.")

        if not re.match(r'(?=.*\d)(?=.*[a-z])(?=.*[A-Z]).{8,}', request.form.get("password")):
            return promptUser("Invalid Password")

        # ensure that password was confirmed
        if not request.form.get("confirmPassword"):
            return promptUser("Password does not match.")

        # ensure that passwords matched
        if request.form.get("password") != request.form.get("confirmPassword"):
            return promptUser("Password does not match.")

        # Insert user into DB
        users = database.execute("""INSERT INTO users (username, hash, firstName, lastName, email)
                                    VALUES(:username, :hash, :firstName, :lastName, :email)""",
                                    username = request.form.get("username"), hash = pwd_context.hash(request.form.get("password")),
                                    firstName = request.form.get("firstName"),
                                    lastName = request.form.get("lastName"), email = request.form.get("email"))

        # Ensure information is unique and user does not already exist.
        if not users:
            return promptUser("Username or email already in use.")

        users = database.execute("SELECT * FROM users WHERE username = :username", username = request.form.get("username"))
        session["user_id"] = users[0]["id"]

        flash("Account Created!")
        return redirect(url_for("index"))
    else:
        return render_template("register.html")


@app.route("/login", methods = ["GET", "POST"])
@loggedIn
def login():

    # Delete any previous login session
    session.clear()

    if request.method == "POST":

        if not request.form.get("email"):
            return promptUser("Email cannot be blank.")

        if not request.form.get("password"):
            return promptUser("Password cannot be blank.")

        if not re.match(r'(?=.*\d)(?=.*[a-z])(?=.*[A-Z]).{8,}', request.form.get("password")):
            return promptUser("Password invalid.")

        users = database.execute("SELECT * FROM users WHERE email = :email", email = request.form.get("email"))

        if len(users) != 1 or not pwd_context.verify(request.form.get("password"), users[0]["hash"]):
            return promptUser("Invalid Username and/or Password")

        session["user_id"] = users[0]["id"]

        # Check if user is admin, save email to enable admin privileges
        if request.form.get("email") == "admin@mail.com":
            session["email"] = request.form.get("email")

        flash("Login Successful!")

        return redirect(url_for("index"))
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out!")
    return redirect(url_for("login"))


@app.route("/changePassword", methods = ["GET", "POST"])
@loginRequired
def changePassword():
    if request.method == "POST":

        if not request.form.get("newPassword"):
            return promptUser("Field cannot be blank.")

        if not re.match(r'(?=.*\d)(?=.*[a-z])(?=.*[A-Z]).{8,}', request.form.get("newPassword")):
            return promptUser("Invalid Password.")

        database.execute("UPDATE users SET hash = :hash WHERE id = :id", hash = pwd_context.hash(request.form.get("newPassword")),
                          id = session["user_id"])

        flash("Password changed!")
        return redirect(url_for("profile"))
    else:
        return render_template("changePassword.html")


@app.route("/changeUsername", methods = ["GET", "POST"])
@loginRequired
def changeUsername():
    if request.method == "POST":

        if not request.form.get("newUsername"):
            return promptUser("Field cannot be blank.")

        if not re.match(r'^(?=.{2,20}$)(?![_.])(?!.*[_.]{2})[a-zA-Z0-9._]+(?<![_.])$', request.form.get("newUsername")):
            return promptUser("Username Invalid.")
        users = database.execute("UPDATE users SET username = :username WHERE id = :id", username = request.form.get("newUsername")
                                  , id = session["user_id"])

        if not users:
            return promptUser("Username Already In Use")

        flash("Username changed!")

        return redirect(url_for("profile"))
    else:
        return render_template("changeUsername.html")


@app.route("/changeProfilePicture", methods = ["POST", "GET"])
@loginRequired
def changeProfilePicture():
    if request.method == "POST":

        if not request.form.get("profilePicture"):
            return promptUser("profile picture")

        database.execute("UPDATE users SET profilePicture = :profilePicture WHERE id=:id",
                    profilePicture = request.form.get("profilePicture"), id=session["user_id"])

        flash("Updated!")
        return redirect(url_for("profile"))
    else:
        return render_template("changeProfilePicture.html")



@app.route("/changeEmail", methods = ["GET", "POST"])
@loginRequired
def changeEmail():

    if request.method == "POST":

        if not request.form.get("newEmail"):
            return promptUser("Field cannot be blank.")

        if '/''' in request.form.get("newEmail")  or ';' in request.form.get("newEmail"):
            return promptUser("Illegal characters.")

        users = database.execute("UPDATE users SET email = :email WHERE id = :id", email = request.form.get("newEmail")
                                  , id = session["user_id"])

        if not users:
            return promptUser("Email already in use")
        flash("Email changed!")
        return redirect(url_for("profile"))
    else:
        return render_template("changeEmail.html")


# Obtains the information of a user that can be publicly viewed by another user
@app.route("/user/<username>")
def user(username):

    # Query to obtain public information of user
    user = database.execute("SELECT * FROM users WHERE username = :username", username = username)

    # Obtain read books of user
    books = database.execute("SELECT * FROM books WHERE user_id = :user_id", user_id = user[0]["id"])

    readBooks = list()

    # Obtain all books user has read and add to list
    for book in books:
        readBooks.append(requests.get("https://www.googleapis.com/books/v1/volumes?q=" + book["book_id"] +
                           API_KEY).json()["items"][0])

    # Obtain public comments
    comments = database.execute("SELECT * FROM comments WHERE user_id = :user_id", user_id = user[0]["id"])

    usersComments = list()

    for comment in comments:
        book = requests.get("https://www.googleapis.com/books/v1/volumes?q=" + comment["book_id"] +
                            API_KEY).json()
        usersComments.append({"id": comment["id"], "comment": comment["comment"], "dateOfPublish": comment["dateOfPublish"], 
                              "book": book["items"][0]})

    grades = database.execute("SELECT * FROM grades WHERE user_id = :user_id", user_id = user[0]["id"])

    usersGrades = list()

    for grade in grades:
        book = requests.get("https://www.googleapis.com/books/v1/volumes?q=" + grade["book_id"] +
                            API_KEY).json()
        usersGrades.append({"id": grade["id"], "grade": grade["grade"], "dateOfEvaluation": grade["dateOfEvaluation"], 
                            "book": book["items"][0]})

    posts = database.execute("SELECT * FROM posts WHERE user_id = :user_id", user_id = user[0]["id"])

    return render_template("user.html", user = user[0], books = readBooks, comments = usersComments, grades = usersGrades,
                            posts = posts)


# Admin Page to view all registered users
@app.route("/users")
@loginRequired
def users():

    # Query to obtain all users
    users = database.execute("SELECT * from users")

    return render_template("users.html", users = users)


# Admin functionality to delete users
@app.route("/deleteUser/<user_id>", methods = ["GET", "POST"])
@loginRequired
def deleteUser(user_id):

    # Query database to delete user
    database.execute("DELETE FROM users WHERE id = :id", id = user_id)

    # Following queries delete all evidence of user
    database.execute("DELETE FROM books WHERE user_id = :user_id", user_id = user_id)
    database.execute("DELETE FROM comments WHERE user_id = :user_id", user_id = user_id)
    database.execute("DELETE FROM grades WHERE user_id = :user_id", user_id = user_id)
    database.execute("DELETE FROM posts WHERE user_id = :user_id", user_id = user_id)
    users = database.execute("SELECT * FROM users")

    # return rendered users.html page with all users
    return render_template("users.html", users = users)