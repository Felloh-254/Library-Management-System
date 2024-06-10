##Creating the __init__ file will help in making the my_app folder a pyhton package
from flask import Flask, Blueprint
import os
from flask_sqlalchemy import SQLAlchemy

#We use the SQLAlchemy for the operation of all our databases
from flask_login import LoginManager

#loginManager is used in the handling of all the login-related activities in our forms
#we need to make the flask applictaion know the path to follow when looking for our database, we then import the path attribute
from os import path

# For working with Mails
from flask_mail import Mail, Message
from my_app.my_binder import MyBinder


#We will then have our database object using SQLAlchemy then initialize it with the name of our database
db = SQLAlchemy()
DB_NAME = "library.db"
mail = Mail()

def create_app():
	app = Flask(__name__)
	#configuration of our database and specifying where to find our database configurations
	app.config["SQLALCHEMY_DATABASE_URI"]=f'sqlite:///{DB_NAME}'

	#generating and configuration of the secregt key
	secret_key = os.urandom(24)
	app.config["SECRET_KEY"] = secret_key

	# Configure Flask-Mail for Gmail (using app password if available)
	app.config['MAIL_SERVER'] = 'your_mail_server.com/IP Address'
	app.config['MAIL_PORT'] = 587
	app.config['MAIL_USE_TLS'] = True
	app.config['MAIL_USERNAME'] = 'your_email@your_mail_serve.com'
	app.config['MAIL_PASSWORD'] = 'mail_server_password'

	#initiating the db with the app
	db.init_app(app)
	mail.init_app(app)

	from my_app.auth import auth_blueprint
	from my_app.users.views import user_view_blueprint
	from my_app.admin.views import admin_blueprint


	auth_blueprint.injector = MyBinder(app)  # Bind MyBinder to the blueprint

	app.register_blueprint(admin_blueprint)
	app.register_blueprint(auth_blueprint)
	app.register_blueprint(user_view_blueprint)

	#Now we need to check evey time we run our program if we already have our database
	from my_app.models import User, Books
	#makes sure that the models.py file runs and defines the classes before we create the database
	create_database(app)

	#incase anyone is not logged in, they will be redirected by the following lines of codes.
	login_manager = LoginManager(app)
	login_manager.login_view = 'userView.homePage'
	login_manager.init_app(app)

	@login_manager.user_loader
	def load_user(id):
		return User.query.get(int(id))
	return app

def create_database(app):
    with app.app_context():
        try:
            if not path.exists('my_app/' +DB_NAME):
                print('Creating database')
                db.create_all()
                print('Created database')
        except Exception as e:
            print(f'Error creating database {e}')
