from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, RadioField
from wtforms.validators import DataRequired


class NameForm(FlaskForm):
    name = StringField('name', validators=[DataRequired()], render_kw={'maxlength': 20})
    submit = SubmitField('Login')


class CreateRoomForm(FlaskForm):
    name = StringField('name', validators=[DataRequired()], render_kw={'maxlength': 20}, id='c_room_name')
    players_amount = RadioField('name', validators=[DataRequired()],
                                choices=[('2', 'Two Players'),
                                         ('3', 'Three Players'),
                                         ('4', 'Four Players')
                                         ],
                                id='c_room_pa', default='2')

    room_type = RadioField('name', validators=[DataRequired()],
                           choices=[('public', 'Public Room'),
                                    ('private', 'Private Room')
                                    ],
                           default='public')

    submit = SubmitField('Create room', id='c_room')


class RoomCodeEnterForm(FlaskForm):
    code = StringField('room_code', validators=[DataRequired()])
    submit = SubmitField('Go to room')


class RoomLeaveForm(FlaskForm):
    submit = SubmitField('Leave room', id='leave-button')
