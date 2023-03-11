""" Handles CLI commands """
from app.models import db, User
import click
from flask.cli import with_appcontext
from werkzeug.security import generate_password_hash

@click.command('drop-db')
@with_appcontext
def drop_db_command():
    """Drops db tables"""
    db.session.remove()
    db.drop_all()
    click.echo('Database dropped.')

@click.command('init-db')
@with_appcontext
def init_db_command():
    """Overwrite  db tables"""
    if db:
        db.drop_all()

    db.create_all()
    click.echo('Database initialized.')
    
@click.command('create-admin')
@with_appcontext
def create_admin_command():
    """Creates admin account"""

    admin_email = ''
    read_data= []
    with open('account.cfg') as f:
        read_data = f.read().replace('\n', ';')
        read_data = read_data.split(';')

    for d in read_data:
        if 'USERNAME' in d:
            admin_email = d[d.find('=')+1:-1].strip(" \'")

    # note: USERNAME is actually EMAIL
    db.session.add(User('admin','Admin', admin_email, generate_password_hash('admin'), admin=True))
    db.session.commit()
    click.echo('Created admin account.')

def init_app(app):
    app.cli.add_command(init_db_command)
    app.cli.add_command(drop_db_command)
    app.cli.add_command(create_admin_command)