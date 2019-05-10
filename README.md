# EvaLib: Book Evaluator :books:

Flask Web application allowing users to rate, comment on and search for books after creating an account. Users are given their own profile from which they can rate and comment on books, delete and edit their comments and ratings, read these books in addition to adding these books to a personal library. 

There are various permissions for the type of account.

Each registered user has a profile consisting of basic information, as well as their posts and comments.

Users of the site without an account are free to read books, comments, view ratings and the public profiles of other users but cannot post comments and reviews of their own.

A site administrator account can be created if the email contains the "admin" phrase.
It has all the privileges of a registered user, but can view all other registered users of the site, and has the ability to edit and delete the ratings and comments of other users. Other users can also be deleted.

The library functionality is enabled using the [Google Books API](https://developers.google.com/books).

### Technologies Used

- [Flask](http://flask.pocoo.org)
- [SQLite](https://www.sqlite.org/index.html)
- [Heroku](https://www.heroku.com)

### Usage
- `git clone https://github.com/Vukan-Markovic/Book-evaluator.git`
- `virtualenv -p python3 venv`
- `source venv/bin/activate`
- `pip install -r requirements.txt`
- `export FLASK_APP=app.py`
- `export FLASK_DEBUG=1`
- `flask run`

App can be access locally using http://127.0.0.1:5000 or at .
