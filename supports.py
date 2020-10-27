from flask import jsonify
import requests
import urllib.parse

from models import User_books

# Look General up function
def lookup_general(book):

    # Contact API
    try:
        response = requests.get(f'https://www.googleapis.com/books/v1/volumes?q={urllib.parse.quote_plus(book)}&key=AIzaSyCdjm_QYo4osDiS8MJkjyLNx1PhoObkC5M&maxResults=40')
        response.raise_for_status()
    except requests.RequestException:
        return None

   # Parse response
    try:
        books = response.json()
        return books['items']

    except (KeyError, TypeError, ValueError):
        return None

# Look up Specific function - Specific book by its ID
def lookup_specific(book_id):

    # Contact API
    try:
        response = requests.get(f'https://www.googleapis.com/books/v1/volumes/{urllib.parse.quote_plus(book_id)}?key=AIzaSyCdjm_QYo4osDiS8MJkjyLNx1PhoObkC5M')
        response.raise_for_status()
    except requests.RequestException:
        return None

   # Parse response
    try:
        book = response.json()
        return book['volumeInfo']
    
        # return {
        #     "id": book["id"],
        #     "title": book["volumeInfo"]["title"],
        #     "subtitle": book["volumeInfo"]["subtitle"],
        #     "authors": book["volumeInfo"]["authors"],
        #     "publishedDate": book["volumeInfo"]["publishedDate"],
        #     "description": book["volumeInfo"]["description"],
        #     "imageLinks": book["volumeInfo"]["imageLinks"]["thumbnail"]
        # }
        

    except:
        return jsonify({'error': 'Book not found - msg from lookup_specific()'})

# Check if current_user is author of the summary
def is_author(user_id, book_id):
    
    # known bug here - will find all users that have written summary for this book, but update will update only the actual user's summary
    book = User_books.query.filter_by(user_id=user_id, book_id=book_id).first()

    if book:
        return True
        

    return False

