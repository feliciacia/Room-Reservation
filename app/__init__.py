import os
from flask import Flask
from flask_login import LoginManager
from config import Config
from .models import db, User


app = Flask(__name__)

# ensure the instance folder exists
try:
    os.makedirs(app.instance_path)
except OSError:
    pass

app.config.from_object(Config)
app.config.from_pyfile('../account.cfg')

db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)

import manage
manage.init_app(app)

from . import auth
app.register_blueprint(auth.auth_bp)

from . import booking
app.register_blueprint(booking.booking_bp)
# app.add_url_rule('/', endpoint='home')

from . import mail
mail.mail.init_app(app)

login_manager.login_view = "auth.login"
login_manager.login_message_category = "error"

@login_manager.user_loader
def load_user(user_id):
    return User.query.filter(User.id == int(user_id)).first()