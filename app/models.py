""" Database models classes defined here """
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, unique=True, nullable=False)
    name = db.Column(db.String, nullable=False)
    email = db.Column(db.String, unique=True, nullable=False)
    password = db.Column(db.String, nullable=False)
    admin = db.Column(db.Boolean, nullable=False, default=False)

    def __init__(self, username, name, email, password, admin=False):
        self.username = username
        self.name = name
        self.email = email
        self.password = password
        self.admin = admin

    def is_authenticated(self):
        return True
    
    def is_admin(self):
        return self.admin

    # needed for flask login
    def is_active(self):
        return True
    
    # needed for flask login
    def get_id(self):
        return self.id

class Reservation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username  = db.Column(db.String, nullable=False)
    subject = db.Column(db.String, nullable=False)
    room_id = db.Column(db.Integer, nullable=False)
    booking_time = db.Column(db.DateTime, nullable=False)
    booked_date = db.Column(db.Date, nullable=False)
    time_start = db.Column(db.Time, nullable=False)
    time_end = db.Column(db.Time, nullable=False)
    _party = db.Column(db.String)
    message = db.Column(db.String)
    reminder = db.Column(db.Boolean, nullable=False)
    status = db.Column(db.Integer, nullable=False)

    def __init__(self, username, subject, room_id, booking_time, booked_date, time_start, time_end, party_list, message, reminder=False):
        self.username  = username 
        self.subject  = subject 
        self.room_id = room_id
        self.booking_time = booking_time
        self.booked_date = booked_date
        self.time_start = time_start
        self.time_end = time_end
        self._party = ';'.join(f'{name}'.replace("'", "").strip("() ") for name in party_list)
        self.message = message
        self.reminder = reminder
        self.status = 0     # 0: coming soon; 1: ongoing; 2: expired

    @property
    def party(self):
        return [name for name in self._party.split(';')]
    @party.setter
    def party(self, names):
        self._party = ';'.join(f'{n}'.replace("'", "").strip("() ") for n in names)

