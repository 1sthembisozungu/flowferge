import os # allow you to interact with computer's operating system

from flask  import Flask #create flask web application
from flask_sqlalchemy import SQLAlchemy #allows you to work with databases using Python objects instead of raw SQL.
from dotenv import load_dotenv #loads environment variables from a .env file into your system environment so you can access them with os.getenv.
#from app.routes.test import test 

db = SQLAlchemy()

def create_app(): #instead of creating the app globally, you create it inside a function so you can configure it flexibly

    load_dotenv() # loads variabled from the .env file into environment

    app = Flask(__name__) #creates flask applications instance

    # __name__ tells Flask where to look for resources (like templates and static files).

    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY") # set up app's secret key from the environment variable

    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv(
        "DATABASE_URL"
    ) #set up db connection string from the environment variable
    
    app.config["SQLALCHEMY_TRCK_MODIFICATIONS"] = False #Disables SQLAlchemy’s event system that tracks object changes.

    # It’s not needed in most cases and consumes extra memory, so it’s best practice to set it to False.


    db.init_app(app) #links the db object to the flask app and it makes the database available inside the app context

    from app.models.user import User 
    from app.routes.test import test

    app.register_blueprint(test)

    return app #returns the fully configured flask app instance
