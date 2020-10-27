# from app import db
from settings import db
from flask_login import UserMixin
from sqlalchemy import DateTime, Date
import datetime

# User model
class User(UserMixin, db.Model):
    """Main User class for the DB"""

    id = db.Column(db.Integer, primary_key = True)
    email = db.Column(db.String(64), unique=True)
    username = db.Column(db.String(24), unique=True)
    pwd = db.Column(db.Text())
    about_me = db.Column(db.Text())
    date = db.Column(Date, default=datetime.datetime.now)

    # Constructor
    def __init__(self, username, email, pwd, about_me=None):
        self.username = username
        self.email = email
        self.pwd = pwd
        self.about_me = about_me

# Books model
class User_books(db.Model):
    """User_books DB Class that connects user and the book based on user ID"""
    
    id = db.Column(db.Integer, primary_key = True)
    user_id = db.Column(db.Integer)
    book_id = db.Column(db.Integer)
    date = db.Column(Date, default=datetime.datetime.now)
    summary = db.Column(db.String)
    rating = db.Column(db.Integer)

    # Constructor
    def __init__(self, user_id, book_id, summary, rating):
        self.user_id = user_id
        self.book_id = book_id
        self.summary = summary
        self.rating = rating


