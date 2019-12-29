import uuid

from flask import (render_template, session,
                   abort, url_for, redirect, request, flash)

from field_capture.main import main
from .forms import NameForm, CreateRoomForm, RoomCodeEnterForm

from field_capture.main.game_objects import RoomManager, PlayerManager
from field_capture.main.auth import login_required


def set_username(name_form):
    if name_form.validate_on_submit():
        session['username'] = name_form.name.data
    if 'username' not in session:
        session['username'] = 'Anonym'


@main.route('/', methods=['GET', 'POST'])
def index():
    name_form = NameForm(prefix='username')
    create_room_form = CreateRoomForm(prefix='create_room')
    room_code_enter_form = RoomCodeEnterForm(prefix='enter_code')

    public_rooms = RoomManager.get_public_rooms()

    if 'pers_id' not in session:
        session['pers_id'] = str(uuid.uuid4())

    set_username(name_form)

    return render_template('index.html',
                           **{'name_form': name_form,
                              'create_room_form': create_room_form,
                              'room_code_enter_form': room_code_enter_form,
                              'public_rooms': public_rooms,
                              })


@main.route('/enter_private_room', methods=['POST'])
@login_required
def enter_private_room():
    room_code_enter_form = RoomCodeEnterForm(prefix='enter_code')
    if room_code_enter_form.validate_on_submit():
        room_id = room_code_enter_form.code.data
        return redirect(url_for('main.room') + '?id=%s' % room_id)
    abort(404)


@main.route('/create_room', methods=['POST'])
@login_required
def create_room():
    player_status = PlayerManager.get_player_status(session['pers_id'])

    message = PlayerManager.player_wait_or_play(player_status)
    if message is not None:
        flash(message)
        return redirect(url_for('main.index'))

    if player_status == 'free':
        create_room_form = CreateRoomForm(prefix='create_room')
        if (create_room_form.validate_on_submit()
                and create_room_form.submit.data):
            room_id = str(uuid.uuid4())
            room_name = create_room_form.name.data
            room_type = create_room_form.room_type.data
            room_size = create_room_form.players_amount.data
            RoomManager.create_room(room_id, room_name, room_type, room_size)
            return redirect(url_for('main.room') + '?id=%s' % room_id)
    abort(403)


@main.route('/room', methods=['GET', 'POST'])
@login_required
def room():
    room_id = request.args.get('id')
    is_room_exists = RoomManager.get_room_exists(room_id)
    if is_room_exists is False:
        abort(404)
    room_manager = RoomManager(room_id)
    player_status = PlayerManager.get_player_status(session['pers_id'],
                                                    room_id)

    message = PlayerManager.player_wait_or_play(player_status)
    if message is not None:
        flash(message)
        return redirect(url_for('main.index'))

    if player_status == 'restore':
        player_manager = PlayerManager(session['pers_id'], room_id)
        player_manager.restore()
    elif player_status == 'free':
        if room_manager.is_full():
            flash('Room is full')
            return redirect(url_for('main.index'))
        elif room_manager.is_playing():
            flash('Game session have started')
            return redirect(url_for('main.index'))

        PlayerManager.create_player(session['pers_id'],
                                    room_id, session['username'])

    return render_template('room.html', room_id=room_id)
