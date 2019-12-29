import click
from flask.cli import with_appcontext
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def init_db():
    db.create_all()
    # guest = User(username='guest', email='guest@example.com')
    # db.session.add(guest)
    db.session.commit()


@click.command('init-db')
@with_appcontext
def init_db_command():
    init_db()
    click.echo('Initalized the database.')


@click.command('drop-db')
@with_appcontext
def drop_db_command():
    db.drop_all()
    click.echo('Droped the database.')


class Room(db.Model):
    __tablename__ = 'rooms'
    id = db.Column(db.String(200), primary_key=True)
    name = db.Column(db.String(20), nullable=False)
    type = db.Column(db.String(10), nullable=False)
    size = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(10), nullable=False)
    global_score = db.Column(db.Integer, nullable=False)
    field = db.Column(db.JSON, nullable=False)
    number_of_moves = db.Column(db.Integer, nullable=False)


class Player(db.Model):
    __tablename__ = 'players'
    id = db.Column(db.String(200), primary_key=True)
    room_id = db.Column(db.String(200), db.ForeignKey('rooms.id'),
                        primary_key=True)

    __table_args__ = (db.PrimaryKeyConstraint('id', 'room_id'), {},)

    order_of_turn = db.Column(db.Integer, nullable=False)
    score = db.Column(db.Integer, nullable=False)
    token_presence = db.Column(db.Boolean, nullable=False)
    username = db.Column(db.String(20), nullable=False)
    ready = db.Column(db.Boolean, nullable=False)
    playing = db.Column(db.Boolean, nullable=False)
    surrender = db.Column(db.Boolean, nullable=False)
    dice_has_rolled = db.Column(db.Boolean, nullable=False)
    last_dice_values = db.Column(db.JSON, nullable=False)

    room = db.relationship('Room',
                           backref=db.
                           backref('players',
                                   lazy=True,
                                   cascade="all, delete, delete-orphan"))
