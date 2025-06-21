from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

db = SQLAlchemy()
login_manager = LoginManager()

def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = "change-this-key"
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///dear_diary.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "main.login"

    from dear_diary_app.routes import main        #  ← blueprint import
    app.register_blueprint(main)                  #  ← blueprint register

    return app
