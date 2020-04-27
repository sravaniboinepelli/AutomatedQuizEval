from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

# Creates the application object 
app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///AQES.db'
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'

# Import Views from the app module. (DO NOT Confuse with app variable)
from app import views

# Import is at the end to avoid circular reference
