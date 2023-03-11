""" Handles reservation booking, editing, canceling and other booking utility functionalities """
from operator import and_
from flask import (
    Blueprint, flash, redirect, render_template, request, url_for, jsonify
)
from werkzeug.exceptions import abort
from datetime import datetime, time, date

from flask_login import login_required, current_user
from .forms import ReservationForm
from .models import db, Reservation, User
from config import NO_OF_ROOMS, OPEN_HOURS
from .mail import send_msg

booking_bp = Blueprint('booking', __name__)

@booking_bp.route('/')
def home():
    return render_template('booking/home.html')

@booking_bp.route('/profile')
@login_required
def profile():
    """ View user profile (reservation history) """
    update_records()
    send_reminder()

    records = {}
    reservations = db.session.query(Reservation).all()

    for r in reservations:
        if r.username == current_user.username:
            records.setdefault('own', []).append(r)
        elif str(f'{current_user.username}, {current_user.name}') in r.party:
            records.setdefault('partied', []).append(r)

    return render_template('booking/profile.html', records=records)

@booking_bp.route('/index')
@login_required
def index():
    """ Displays ongoing reservations """
    update_records()
    send_reminder()

    if current_user.is_authenticated and current_user.admin:
        reservations = db.session.query(Reservation).all()
    else:
        reservations = db.session.query(Reservation).filter(Reservation.status==0).all()

    return render_template('booking/index.html', records=reservations)

@booking_bp.route('/book', methods=('GET', 'POST'))
@login_required
def book():
    form = ReservationForm()

    # get party list to be listed out as choices, exclude current_user
    party_list = [p for p in get_party() if (p[0] != current_user.username)]
    form.party.choices = [(p[0], p[1]) for p in party_list]

    if request.method == 'POST' and form.validate_on_submit():
        party_list_form = []

        for party in form.party.data:
            party_list_form.append(party_list[[p[0] for p in party_list].index(party)])

        # include current_user back in reservation
        party_list_form.append((current_user.username, current_user.name))

        # If reservation happens today, no need reminders
        no_reminder = False
        if form.booked_date.data == date.today():
            no_reminder = True

        # parse time object from given hour integer
        time_start = time(int(form.time_start.data),0,0,0)
        time_end = time(int(form.time_end.data) if int(form.time_end.data)!=24 else 0,0,0,0)

        reservation = Reservation(
                current_user.username,
                form.subject.data,  
                form.room_id.data, 
                datetime.now(), 
                form.booked_date.data, 
                time_start, 
                time_end, 
                party_list_form,
                form.message.data,
                no_reminder
                )

        error = check_room_avail(int(form.room_id.data), form.booked_date.data, time_start, time_end)
        error = check_party_avail(form.booked_date.data, time_start, time_end, party_list_form)

        if error == '':
            db.session.add(reservation)
            db.session.commit()

            party_list_form.remove((current_user.username, current_user.name))
            emails = get_party_email(p[0] for p in party_list_form)

            info = {
                'date':form.booked_date.data,
                'time_start':form.time_start.data,
                'time_end':form.time_end.data,
                'party':party_list_form,
                'booking_time': datetime.now().strftime('%H:%M:%S'),
                'host': (current_user.name, current_user.username),
                'message': form.message.data
                }

            if party_list_form:
                party_msg_html = render_template('mail.html', message='You\'ve been invited to a meeting.', info=info)
                send_msg(f'[VRRA] Meeting Invitation on {info["date"]} at {info["time_start"]}:00 - {info["time_end"]}:00', emails, party_msg_html)

            user_msg_html = render_template('mail.html', message = 'You\'ve made a room reservation.', info=info)
            send_msg(f'[VRRA] You\'ve reserved a meeting room on {info["date"]} at {info["time_start"]}:00 - {info["time_end"]}:00', [current_user.email], user_msg_html)
            
            return redirect(url_for('booking.index'))
    
        flash(error, 'error')
    else:
        # Pre-populate form with current datetime
        form.time_start.default = datetime.now().hour
        form.time_end.default = datetime.now().hour + 1
        form.process()
    
    return render_template('booking/book.html', form=form, party=party_list, hours=OPEN_HOURS, no_of_rooms=NO_OF_ROOMS)

@booking_bp.route('/<int:id>/edit', methods=('GET', 'POST'))
@login_required
def edit(id):
    """ Edits reservation<id>"""
    prev_record = db.session.query(Reservation).filter(Reservation.id==id).first()
    form = ReservationForm()

    # Exclude current_user from choices
    party_list = [p for p in get_party() if (p[0] != current_user.username)]
    form.party.choices = [(p[0], p[1]) for p in party_list]
    
    prev_party = [p.split(',')[0] for p in prev_record.party]
    set_prev = set(prev_party)
    ts = prev_record.time_start.strftime('%H')
    te = prev_record.time_end.strftime('%H')
    if request.method == 'POST' and form.is_submitted():
        party_list_form = []

        # Indexes of party
        party_index = [p[0] for p in party_list]
        
        for party in form.party.data:
            party_list_form.append(party_list[party_index.index(party)])

        # include current_user in meeting
        party_list_form.append((current_user.username, current_user.name))

        # parse time object from given hour integer
        time_start = time(int(form.time_start.data),0,0,0)
        time_end = time(int(form.time_end.data),0,0,0)

        error = check_room_avail(form.room_id.data, form.booked_date.data,  time_start, time_end, id)
        error = check_party_avail(form.booked_date.data, time_start, time_end, party_list_form, id)

        if error == '':
            # Notify party about changes made to this reservation
            info = {
                        'subject':      form.subject.data,
                        'date':         form.booked_date.data,
                        'time_start':   form.time_start.data,
                        'time_end':     form.time_end.data,
                        'party':        party_list_form,
                        'booking_time': datetime.now().strftime('%H:%M:%S'),
                        'host':      (current_user.name, current_user.username),
                        'notes':        form.message.data
                    }

            # check if anyone is disinvited or newly added (contains usernames)
            prev_party.remove(current_user.username)
            party_disinvited = set(prev_party) - set(form.party.data)
            party_added = set(form.party.data) - set(prev_party)
            party_unchanged = set(prev_party) & set(form.party.data)
            
            prev_info = {
                        'subject':      prev_record.subject,
                        'date':         prev_record.booked_date,
                        'time_start':   prev_record.time_start,
                        'time_end':     prev_record.time_end,
                        'party':        prev_record.party,
                        'host':         (current_user.name, current_user.username),
                        'message':      prev_record.message
                }

            print(party_disinvited)
            print(party_added)
            print(party_unchanged)


            if party_disinvited:
                disinvite_html = render_template('mail.html', message= 'You\'ve been disinvited from a meeting.', info=prev_info)
                send_msg(f'[VRRA] Meeting Disinvitation: <{prev_info["subject"]}> .', get_party_email(party_disinvited), disinvite_html)

            if party_added:
                invite_html = render_template('mail.html', message='You\'ve been invited to a meeting.', info=info)
                send_msg(f'[VRRA] Meeting Invitation on {info["date"]} at {info["time_start"]}:00 - {info["time_end"]}:00', get_party_email(party_added), invite_html)

            if party_unchanged:
                modified_html = render_template('mail.html', message=f'The [{prev_info["subject"]}](previous) meeting has been modified.', info=info)
                send_msg(f'[VRRA] Meeting Modified: <{prev_info["subject"]}>', get_party_email(party_unchanged), modified_html)

            # Email to host
            user_msg_html = render_template('mail.html', message=f'The [{prev_info["subject"]}] has been modified.', info=info)
            send_msg(f'[VRRA] You\'ve modified a reservation', [current_user.email], user_msg_html)

            db.session.query(Reservation).filter(Reservation.id==id).update(
                dict(
                    subject=form.subject.data,
                    room_id=form.room_id.data,
                    booked_date=form.booked_date.data,
                    time_start=time_start,
                    time_end=time_end, 
                    _party= ';'.join(f'{name}'.replace("'", "").strip("() ") for name in party_list_form)
                    ))
            db.session.commit()

            return redirect(url_for('booking.index'))
        else:
            flash(error, 'error')
    else:
        # Pre-populate form with reservation's current data
        form.room_id.default = prev_record.room_id
        form.booked_date.default = prev_record.booked_date
        form.process()
        form.party.data = prev_party

    return render_template('booking/edit.html', record=prev_record, form=form, party=party_list, no_of_rooms=NO_OF_ROOMS, hours=OPEN_HOURS, te=te, ts=ts)

@booking_bp.route('/<int:id>/cancel', methods= ('POST','GET'))
@login_required
def cancel(id):
    """ Cancels reservation<id> """
    r = db.session.query(Reservation).filter(Reservation.id==id).first()

    party_emails = get_party_email([p.split(',')[0] for p in r.party])
    party_emails.append(current_user.email)

    info = {
        'subject': r.subject,
        'date':r.booked_date,
        'time_start':r.time_start,
        'time_end':r.time_end,
        'party':r.party,
        'cancel_time': datetime.now().strftime('%H:%M:%S'),
        'host': (current_user.name, current_user.username)
        }

    cancel_html = render_template('mail.html', message=f'The meeting you\'re in has been canceled.', info=info)
    send_msg(f'[VRRA] Meeting Canceled: <{info["subject"]}>', party_emails, cancel_html)

    db.session.query(Reservation).filter(Reservation.id==id).delete()
    db.session.commit()

    return redirect(url_for('booking.index'))

# Route used for updatinng schedule table
@booking_bp.route('/_get_status')
def get_status():
    date = request.args.get('date', datetime.today().strftime('%Y-%m-%d'))
    record = get_booked(date)
    return jsonify(record)

def get_booked(date):
    """ Gets all reserved time on given date. Utility for status table"""
    booked = {}
    for i in range(1,NO_OF_ROOMS+1):
        booked[i] = []
    for r in db.session.query(Reservation.room_id, Reservation.time_start, Reservation.time_end).filter(Reservation.booked_date==date).all():
        booked[r.room_id].append(
            (int(r.time_start.strftime('%H')), int(r.time_end.strftime('%H')))
        )
    return booked

@booking_bp.route('/status', methods=('GET','POST'))
def status():
    """ Displays all room status """
    update_records()
    send_reminder()
    return render_template('booking/status.html', hours=OPEN_HOURS, no_of_rooms=NO_OF_ROOMS)

# Functions to get data from DB
def get_party():
    """ Gets all participants/users in the system, excluding admin """
    party = db.session.query(User.username, User.name).filter(User.admin!=True).all()
    return party

def check_room_avail(room_id, booked_date, time_start,time_end, edit_id=None):
    """ Checks room availability """
    if db.session.query(Reservation).first():
        if edit_id != None:
            records = db.session.query(Reservation).filter(Reservation.id!=edit_id, Reservation.booked_date==booked_date).all()
        else:
            records = db.session.query(Reservation).filter(Reservation.booked_date==booked_date).all()

        time_end = time_end if time_end!=0 else 24

        for rec in records:
            # print(rec.room_id, room_id, '\n', rec.time_start,  rec.time_end, '\n', time_start, time_end)
            if rec.room_id == room_id \
                and (rec.time_start <= time_start and time_start <= rec.time_end) \
                and (rec.time_start <= time_end and time_end <= rec.time_end):
                return f'Room {room_id} is unavailable on {booked_date} at {time_start} - {time_end}'
    return ''

def check_party_avail(booked_date, time_start, time_end, party_list, id=None):
    """ Checks all participants availability """
    if db.session.query(Reservation).first():
        if id:
            records = db.session.query(Reservation._party, Reservation.time_start, Reservation.time_end).filter(Reservation.booked_date==booked_date, Reservation.id!=id).all()
        else:
            records = db.session.query(Reservation._party, Reservation.time_start, Reservation.time_end).filter(Reservation.booked_date==booked_date).all()

        time_end = time_end if time_end!=0 else 24

        for rec in records:
            for party in party_list:
                if (party[0] in rec._party) \
                    and (rec.time_start <= time_start and time_start <= rec.time_end) \
                    and (rec.time_start <= time_end and time_end <= rec.time_end):
                    
                    if party[0] is current_user.username:
                        return f'{current_user.name}(current) is unavailable on {booked_date} at {time_start} - {time_end}'
                    return f'{party[1]}({party[0]}) is unavailable on {booked_date} at {time_start} - {time_end}'
    return ''

def get_party_email(party_usernames):
    """ Get given participants' emails"""
    emails = db.session.query(User.username, User.email).filter(User.username.in_(party_usernames)).all()
    return emails
        
def check_time_passed(date, ts, te):
    """ Compares given datetime with current datetime """
    d1 = str(date).split('-')
    d2 = datetime.today().strftime('%Y-%m-%d').split('-')
    d1 = [int(i)for i in d1]
    d2 = [int(i)for i in d2]

    check = [i <= j for i, j in zip(d1, d2)]
    for c in check:
        if c is False:
            return 0

     # 0: coming soon; 1: ongoing; 2: expired
    if d1[2] == d2[2]:        
        hour_now = int(datetime.now().strftime('%H'))
        time_end = int(te.strftime('%H'))
        time_end = time_end if time_end != 0 else 24
        time_start = int(ts.strftime('%H'))
        if(time_end > hour_now):
            if(hour_now >= time_start):
                return 1
            return 0
    return 2

def check_time_diff(date):
    """ Calculates time difference between given date and today"""
    d1 = str(date).split('-')
    d1 = datetime(int(d1[0]), int(d1[1]), int(d1[2]))
    d2 = datetime.today()    
    return (d1-d2).days

def update_records():
    """ Updates all records' statuses """
    past_records = db.session.query(Reservation.id, Reservation.booked_date, Reservation.time_start, Reservation.time_end).filter(Reservation.status!=2).all()

    for r in past_records:
        curr_stat = check_time_passed(r.booked_date, r.time_start, r.time_end)

        # print(f'ID{r.id} Date: {r.booked_date}\t{r.time_end} stat:{curr_stat}')
        db.session.query(Reservation).filter(Reservation.id==r.id).update(
                dict(
                    status=curr_stat))
        db.session.commit()
    
def send_reminder():
    """ Sends reminders to participants with D-1"""
    reservations = db.session.query(Reservation).filter(and_(Reservation.reminder==False, Reservation.status==0)).all()
    
    for r in reservations:
        date = r.booked_date
        # 1 day before booked date
        if check_time_diff(date) <= 1:
            info = {
                'subject':r.subject,
                'date':r.booked_date,
                'time_start':r.time_start,
                'time_end':r.time_end,
                'party':r.party,
                'cancel_time': datetime.now().strftime('%H:%M:%S'),
                'host': (current_user.name, current_user.username),
                'message':r.message
                }

            party_emails = get_party_email([p.split(',')[0] for p in r.party])
            reminder_html = render_template('mail.html', message='The meeting you\'re in is coming soon.', info=info)
            send_msg(f'[VRRA] Meeting Reminder: <{info["subject"]}> ', party_emails, reminder_html)

            db.session.query(Reservation).filter(Reservation.id==r.id).update(
                dict(
                    reminder=True))
            db.session.commit()

