from flask import Flask, render_template, request, redirect, flash, url_for
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from tempfile import mkdtemp
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from functools import wraps
import requests
import sys
import logging

from settings import app, db
from models import *
from supports import lookup_general, lookup_specific, is_author


# Update login_required function to store the previous url 
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.is_anonymous:
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

# Ensure responses aren't cached
@app.after_request
def after_request(res):
    res.headers['Cache-Control'] = 'no-chace, no-store, must-revalidate'
    res.headers['Expires'] = 0
    res.headers['Pragma'] = 'no-chace'
    return res


# Login Manager Class
login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)


@login_manager.user_loader
def load_user(uid):
    return User.query.get(int(uid))

# Routes

# Homepage
@app.route('/')
def index():
    return render_template('index.html')

# Search
@app.route('/search', methods=['POST'])
def search():
    if request.method == 'POST':

        try:
            book = lookup_general(request.form.get('book_search_value'))
            counter = 0
            for row in book:
                counter += 1
            return render_template('search/search_results.html', book=book, search_term=request.form.get('book_search_value'), result_counter=counter)
        except:
            flash('No results found.', 'warning')
            return render_template('search/search.html')

# USER 

# Register
@app.route('/register', methods=['POST', 'GET'])
def register():
    if request.method == 'POST':

        # Catch the input
        username = request.form.get('username') 
        email = request.form.get('email')
        pw1 = request.form.get('password')
        pw2 = request.form.get('confirmation')

        # Check the input
        user_email = User.query.filter_by(email=email).first()
        user_username = User.query.filter_by(username=username).first()
        if user_email:
            flash('Email already registered.', 'warning')
            return redirect('/register')
        elif user_username:
            flash('Username already registered.', 'danger')
            return redirect('/register')
        elif pw1 != pw2:
            flash('Passwords must match.', 'danger')
            return redirect('/register')

        db.session.add(User(username=username, email=email, pwd=generate_password_hash(pw1)))
        db.session.commit()
        flash('Registration successful. You may now sign-in.', 'success')
        return redirect(url_for('login'))

    else:
        return render_template('register.html')

# User Account
@app.route('/user/<username>')
def account(username):

    # Query User
    user = User.query.filter_by(username=username).first()
    books = User_books.query.filter_by(user_id=user.id)
    written_summaries = []
    summaries = 0

    for row in books:
        summaries += 1

    for idx, book in enumerate(books):
        written_summaries.append(lookup_specific(book.book_id))
        written_summaries[idx]['id'] = book.book_id
        
    # Check user
    if user:
        return render_template('user_account/account.html', user=user, books=written_summaries, summaries=summaries)
    else:
        return redirect('/')

# User update profile
@app.route('/user/<username>/update/account', methods=['GET', 'POST'])
@login_required
def update_account_info(username):
    if request.method == 'POST':
        
        username = request.form.get('username')
        about_me = request.form.get('about_me')

        users = User.query.all()
        user = User.query.filter_by(id=current_user.id).first()

        try:

            if not username and not about_me:
                flash('Please specify which part would you like to update', 'danger')
                return redirect(url_for('update_account_info', username=current_user.username))

            if username:
                for row in users:
                    if username == row.username:
                        flash('This username is already taken, please choose another one.', 'danger')
                        return redirect(url_for('update_account_info', username=current_user.username))
                    else:
                        user.username = username
                        db.session.commit()
                        flash('Username successfully updated.', 'success')
                        return redirect(url_for('account', username=current_user.username))

            if about_me:
                user.about_me = about_me
                db.session.commit()
                flash('Account information successfully updated.', 'success')
                return redirect(url_for('account', username=current_user.username))   

        except:
            flash('Sorry something went wrong. Try again, please.', 'danger')
            return redirect(url_for('account', username=current_user.username))
    else:
        return render_template('user_account/update_account_info.html')

# User change password
@app.route('/user/<username>/update/password', methods=['GET', 'POST'])
@login_required
def update_account_pw(username):
    if request.method == 'POST':
        
        current_pw = request.form.get('current_pw')
        new_pw1 = request.form.get('new_password1')
        new_pw2 = request.form.get('new_password2')

        user = User.query.filter_by(id=current_user.id).first()
        
        try:
            if not current_pw or not new_pw1 or not new_pw2:
                flash('You must include all information.', 'danger')
                return redirect(url_for('update_account_pw', username=current_user.username))
            if not check_password_hash(user.pwd, current_pw):
                flash('Incorrect current password.', 'danger')
                return redirect(url_for('update_account_pw', username=current_user.username))
            elif new_pw1 != new_pw2:
                flash('Passwords must match.', 'danger')
                return redirect(url_for('update_account_pw', username=current_user.username))
            else:
                user.pwd = generate_password_hash(new_pw1)
                db.session.commit()
                flash('Password successfully changed.', 'success')
                return redirect(url_for('account', username=current_user.username))  
        except:
            flash('Sorry something went wrong. Try again, please.', 'danger')
            return redirect(url_for('account', username=current_user.username))

    else:
        return render_template('user_account/update_account_pw.html')

# User books
@app.route('/user/books/<username>')
@login_required
def user_books(username):

    # Query books, find book based on ID, append to list & send over to template
    books = User_books.query.filter_by(user_id=current_user.id).all()
    user_books = []
    
    for idx, book in enumerate(books):
        user_books.append(lookup_specific(book.book_id))
        user_books[idx]['id'] = book.book_id

    return render_template('user_account/account_books.html', books=user_books)

# Book summary

# Add summary
@app.route('/summary/add/<book_id>', methods=['GET', 'POST'])
@login_required
def add_summary(book_id):
    if request.method == 'GET':
        book_data = lookup_specific(book_id)
        user_data = User_books.query.filter_by(user_id=current_user.id)

        # Handle duplicate review ---- could be better, for now just redirect to the actual review
        for book in user_data:
            if book_id == book.book_id:
                flash('Looks like you have already written summary for this book!', 'info')
                return redirect(url_for('read_summary', book_id=book.book_id))

        return render_template('summaries/post_summary.html', book=book_data, bookID=book_id)
    else:
        summary = request.form.get('summary')
        rating = request.form.get('book_rating')

        try:
            new_summary = User_books(user_id=current_user.id, book_id=book_id, summary=summary, rating=rating)
            db.session.add(new_summary)
            db.session.commit()

            flash('Summary successfully added.', 'success')
            return redirect(url_for('user_books', username=current_user.username))
        except:
            flash('Sorry, something went wrong. Try again please.', 'danger')
            return redirect(url_for('search'))

# Update summary
@app.route('/summary/update/<book_id>', methods=['GET', 'POST'])
@login_required
def update_summary(book_id):
    if request.method == 'POST':

        try:
            updated_text = request.form.get('updated_text')
            book = User_books.query.filter_by(book_id=book_id, user_id=current_user.id).first()

            if updated_text:
                book.summary = updated_text
                db.session.commit()
                flash('Summary successfully updated', 'success')
                return redirect(url_for('read_summary', book_id=book_id, username=current_user.username))
        except:
            flash('Something went wrong.', 'danger')
            return redirect(url_for('read_summary', book_id=book_id, username=current_user.username))
    else:
        book = User_books.query.filter_by(book_id=book_id, user_id=current_user.id).first()
        actual_book = lookup_specific(book.book_id)

        return render_template('summaries/update_summary.html', book_id=book_id, book=actual_book)

# Read specific summary
@app.route('/summary/book/<book_id>/author/<username>')
def read_summary(book_id, username):
            
        author = User.query.filter_by(username=username).first()
        book_user_data = User_books.query.filter_by(book_id=book_id, user_id=author.id).first()
        book = lookup_specific(book_id)

        if current_user.is_authenticated:
            is_author_check = is_author(current_user.id, book_id)
        else:
            is_author_check = False

        return render_template('summaries/book_summary.html', book=book, book_user=book_user_data, book_id=book_id, is_author = is_author_check, summary_author=username)

@app.route('/summary/delete/<book_id>', methods=['POST'])
def summary_delete(book_id):
    book = User_books.query.filter_by(book_id=book_id, user_id=current_user.id).first()
    
    # Book found, delete it and redirect with success/failure message
    try:
        app.logger.info(book.book_id, book.user_id)
        db.session.delete(book)
        db.session.commit()

        flash('Book summary successfully deleted!', 'success')
        return redirect(url_for('user_books', username=current_user.username))
    except:
        flash('Couldn\'t delete book summary. Something went wrong. Please try again.', 'danger')
        return redirect(url_for('user_books', username=current_user.username))

# All summaries
@app.route('/summaries')
def summaries():
    books = User_books.query.all()
    books_all = []
    users = User.query.all()

    # Find, append each + find its summary author
    for idx, book in enumerate(books):
        books_all.append(lookup_specific(book.book_id))
        books_all[idx]['author_user'] = User.query.filter_by(id=book.user_id).first()
        books_all[idx]['id'] = book.book_id
        books_all[idx]['summary_rating'] = book.rating
        books_all[idx]['summary_date_added'] = book.date

    return render_template('summaries/summaries.html', books=books_all)

# Handle login/logout

# Log-in
@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        next_url = request.form.get("next_arg")
        
        # Query user from DB
        user = User.query.filter_by(email=email).first() 

        # Check input
        if not user or not check_password_hash(user.pwd, password):
            flash('Please check your login details and try again', 'warning')
            return redirect('/login')

        login_user(user)
        if next_url:
                return redirect(next_url)
        return redirect('/')
        
    else:
        return render_template('login.html')

# Log-out
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect('/')

# Reload APP when changed
if __name__ == '__main__':
    app.run(debug=True)