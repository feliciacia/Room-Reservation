import os

OPEN_HOURS = (8,24)
NO_OF_ROOMS = 5

class Config(object):
    TESTING = False
    MAIL_SERVER = '127.0.0.1'
    MAIL_USERNAME = 'Reservation System Admin'
    MAIL_PORT = 465
    MAIL_USE_TLS = False
    MAIL_USE_SSL = True
    MAIL_SERVER='smtp.gmail.com'
    basedir = os.path.join(os.path.abspath(os.path.abspath(os.path.dirname(__file__))), 'instance')
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'project.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # SQLALCHEMY_ECHO=True
    SECRET_KEY = 'this_is_secret'