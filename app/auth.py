""" Handles authentication and account related functionalities """
from flask import (
    Blueprint, flash, redirect, render_template, request, url_for
)

from werkzeug.security import check_password_hash, generate_password_hash
from flask_login import login_user, login_required, logout_user, current_user
from datetime import datetime

from .models import User
from .forms import RegisterForm,  LoginForm
from .models import db
from .mail import send_msg

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/register', methods=('GET', 'POST'))
def register():
    """ Registers user to the system """
    form = RegisterForm(request.form)
    if form.validate_on_submit():
        check_user = db.session.query(User).filter(
            (User.username==form.username.data) | 
            (User.email==form.email.data)).first()
        
        if check_user is None:
            user = User(
                form.username.data,
                form.name.data,
                form.email.data, 
                generate_password_hash(form.password.data)
                )

            mail_html = '<p>Welcome! Thanks for signing up. </p>'

            send_msg(f'[VRRA] You\'ve succesfully been registered!', [form.email.data], mail_html)
                   
            db.session.add(user)
            db.session.commit()

            login_user(user)
            
            flash('Successfully registered!', 'success')
            return redirect(url_for('booking.home'))
        else:
            flash('Username and/or email is taken', 'error')
    return render_template('auth/register.html', form=form)

@auth_bp.route('/login', methods=('GET', 'POST'))
def login():
    """ Logs in user to the system """
    form = LoginForm(request.form)
    if form.validate_on_submit():
        user = User.query.filter(User.username==form.username.data).first()

        if user and check_password_hash(user.password, form.password.data):
            login_user(user)
            return redirect(url_for('booking.home'))
        else:
            flash('Failed to login', 'error')      
    return render_template('auth/login.html', form=form)

@auth_bp.route('/logout')
@login_required
def logout():
    """ Logs out user to the system """
    logout_user()
    return redirect(url_for('auth.login'))

@auth_bp.route('/<int:id>/delete')
@login_required
def delete(id):
    """ Deletes user account """
    deletion_time =  datetime.now().strftime('%H:%M:%S')
    
    delete_html = f'<p>You\'re account on the VRRA system has been successfully deleted on {deletion_time}.<br>Thank you for using our service.</p>'
    send_msg(f'[VRRA] You\'re account has been deleted', [current_user.email], delete_html)

    curr_user = db.session.query(User).filter(User.id == id).first()
    db.session.delete(curr_user)
    db.session.commit()

    return redirect(url_for('booking.home'))
