import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

# App settings
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///main.db'
app.config['TEMPLATES_AUTO_RELOAD'] = True
# app.config['SECRET_KEY'] = b'_5#y2L"F4Q8z\n\xec]/'
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'Optional default value')
# DB Setup
db = SQLAlchemy(app)


