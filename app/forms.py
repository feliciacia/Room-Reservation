from flask_wtf import FlaskForm
from wtforms import  (
    StringField, PasswordField, RadioField, SelectMultipleField, SelectField, DateField,
)
from wtforms.validators import DataRequired, Email
from wtforms.widgets.core import ListWidget, CheckboxInput
from datetime import datetime
from config import OPEN_HOURS, NO_OF_ROOMS

class RegisterForm(FlaskForm):
    username = StringField(u'username', validators=[DataRequired()])
    name = StringField(u'name', validators=[DataRequired()])
    email = StringField(u'email', validators=[DataRequired(), Email()])
    password = PasswordField(u'password', validators=[DataRequired()])

class LoginForm(FlaskForm):
    username = StringField(u'username', validators=[DataRequired()])
    password = PasswordField(u'password', validators=[DataRequired()])

class ReservationForm(FlaskForm):
    start_hour_choices = [(i,str(i).zfill(2)+':00')for i in range(OPEN_HOURS[0], OPEN_HOURS [1])]
    end_hour_choices = [(i+1,str(i+1).zfill(2)+':00')for i in range(OPEN_HOURS[0], OPEN_HOURS [1])]

    check = [t[0] for t in end_hour_choices]
    if 24 in check:
        end_hour_choices[check.index(24)] = (24,'00:00')

    room_choices = [(i, 'R'+ str(i)) for i in range(1, NO_OF_ROOMS+1)]

    subject = StringField(u'subject', default='Meeting')
    room_id = RadioField(u'room', choices=room_choices, validators=[DataRequired()], widget=ListWidget())
    booked_date = DateField(u'current_date', default=datetime.today, validators=[DataRequired()])
    time_start = SelectField(u'start_time', choices=start_hour_choices, validators=[DataRequired()])
    time_end = SelectField(u'end_time', choices=end_hour_choices, validators=[DataRequired()])
    party = SelectMultipleField(u'party', widget=ListWidget(prefix_label=True), option_widget=CheckboxInput())
    message = StringField(u'message')
