from flask import session
from flask_socketio import emit, join_room
from field_capture import socketio
from field_capture.main import game_objects
from field_capture.main.tasks import game_clock, async_board_message
from .exceptions import (MissTokenError, TwiceRolledDiceError,
                         InappropriateActionError, GameDoesNotStartError)


def miss_turn(player_manager, message_list=[]):
    room_id = session['room_id']
    next_player_info = player_manager.miss_turn()

    color = next_player_info['order_of_turn']
    message = next_player_info['username'] + ' is active'
    message_list.append({color: message})

    field = player_manager.room_manager.game_field.get_json_field()

    emit('update_token_inf', next_player_info['id'], room=room_id)
    emit('refresh_dice_rolled_status', room=room_id)
    emit('refresh_game_field', field)
    emit('refresh_game_clock', room=room_id)

    task_id = room_id + str(next_player_info['number_of_moves'])
    game_clock.apply_async((room_id, next_player_info['id'],
                           next_player_info['number_of_moves'], ),
                           countdown=20, task_id=task_id)

    return message_list


def send_board_message_and_refresh_score_table(room_manager, message_list):
    room_id = session['room_id']
    room_status = room_manager.is_playing()
    score_dicts, leader_player = (game_objects
                                  .ScoreTable.get_score_list(room_id))

    emit('refresh_score_table', (score_dicts, leader_player, room_status),
         room=room_id)
    emit('inf_board_message', message_list, room=room_id)


def player_win_event(player_manager, winner):
    color = winner.order_of_turn
    name = winner.username
    score = winner.score
    room_id = session['room_id']

    player_manager.room_manager.finish_game()

    emit('show_win_window', (name, score, color,), room=room_id)
    emit('refresh_players_data', room=room_id)
    emit('set_room_status', False, room=room_id)


def start_game_event(room_manager, message_list=[]):
    room_id = session['room_id']
    room_manager.start_game()
    first_player_info = room_manager.randomly_set_token()
    field = room_manager.game_field.get_json_field()

    players_id_and_colors = room_manager.get_json_players_id_with_colors()

    color = first_player_info['order_of_turn']
    message = first_player_info['username'] + ' is active'
    message_list.append({color: message})

    emit('refresh_game_field', field, room=room_id)
    emit('refresh_color', players_id_and_colors, room=room_id)
    emit('update_token_inf', first_player_info['id'], room=room_id)
    emit('refresh_game_clock', room=room_id)
    emit('set_room_status', True, room=room_id)

    number_of_moves = room_manager.get_number_of_moves()
    task_id = room_id + str(number_of_moves)
    game_clock.apply_async((room_id, first_player_info['id'],
                            number_of_moves, ),
                           countdown=20, task_id=task_id)
    return message_list


@socketio.on('join')
def join_handler(room_id):
    message_list = []
    session['room_id'] = room_id

    join_room(room_id)

    pm = game_objects.PlayerManager(session['pers_id'], room_id)

    color = pm.player.order_of_turn
    message_list.append({color: session['username'] + ' join room'})

    field = pm.room_manager.game_field.get_json_field()

    emit('set_local_init_data', (color, field, ))
    emit('set_room_status', pm.room_manager.is_playing(), room=room_id)

    send_board_message_and_refresh_score_table(pm.room_manager, message_list)


@socketio.on('disconnect')
def disconnect_handler():
    message_list = []
    room_id = session['room_id']
    winner = False

    pm = game_objects.PlayerManager(session['pers_id'], room_id)
    room_status = pm.room_manager.is_playing()

    color = pm.player.order_of_turn
    message_list.append({color: session['username'] + ' leave room'})
    if room_status:
        try:
            miss_turn(pm)
        except MissTokenError:
            pass

    winner = pm.exit()
    if winner is not False:
        player_win_event(pm, winner)

    send_board_message_and_refresh_score_table(pm.room_manager, message_list)


@socketio.on('change_ready_status')
def change_ready_status_handler():
    message_list = []
    room_id = session['room_id']

    pm = game_objects.PlayerManager(session['pers_id'], room_id)
    room_manager = game_objects.RoomManager(room_id)

    if room_manager.is_playing():
        message_list.append({-1: 'You cant do this'})
        emit('inf_board_message', message_list)
        raise InappropriateActionError('You can`t do this')

    all_ready = pm.change_ready_status()

    color = pm.player.order_of_turn
    if pm.player.ready is True:
        message_list.append({color: session['username'] + ' is ready'})
    else:
        message_list.append({color: session['username'] + ' is not ready'})

    if all_ready:
        message_list = start_game_event(room_manager, message_list)

    send_board_message_and_refresh_score_table(room_manager, message_list)


@socketio.on('miss_turn')
def miss_turn_handler():
    room_id = session['room_id']
    message_list = []
    pm = game_objects.PlayerManager(session['pers_id'], room_id)

    color = pm.player.order_of_turn
    message = session['username'] + ' miss turn'
    message_list.append({color: message})

    message_list = miss_turn(pm, message_list)

    send_board_message_and_refresh_score_table(pm.room_manager, message_list)


@socketio.on('roll_dice')
def roll_dice_handler():
    # dice_rolled
    room_id = session['room_id']
    pm = game_objects.PlayerManager(session['pers_id'], room_id)
    rm = game_objects.RoomManager(room_id)
    number_of_moves = rm.get_number_of_moves()
    width, height = pm.roll_dice()
    color = pm.player.order_of_turn

    message = (session['username'] + ' has figure with sides: ' +
               str(width) + ' and ' + str(height))

    async_board_message.apply_async((room_id, message, color,
                                     number_of_moves,),
                                    countdown=3)

    emit('dice_rolled', (width, height,))


@socketio.on('surrender')
def surrender_handler():
    pm = game_objects.PlayerManager(session['pers_id'], session['room_id'])

    message_list = []
    room_status = pm.room_manager.is_playing()

    if room_status:
        try:
            miss_turn(pm)
        except MissTokenError:
            pass

    try:
        winner = pm.surrender()
    except GameDoesNotStartError as e:
        message_list.append({-1: str(e)})
        emit("inf_board_message", message_list)
        raise GameDoesNotStartError('Game doesn`t start yet')

    if winner is not False:
        player_win_event(pm, winner)

    color = pm.player.order_of_turn
    message_list.append({color: pm.player.username + ' is surrendered'})

    send_board_message_and_refresh_score_table(pm.room_manager, message_list)


@socketio.on('set_figure')
def set_figure_handler(x, y):
    pm = game_objects.PlayerManager(session['pers_id'], session['room_id'])
    message_list = []
    winner = False

    try:
        winner = pm.set_figure(x, y)
    except ValueError as e:
        message_list = [{-1: str(e)}]
        emit('inf_board_message', message_list)
        raise ValueError(str(e))
    except MissTokenError as e:
        message_list = [{-1: str(e)}]
        emit('inf_board_message', message_list)
        raise MissTokenError(str(e))
    except TwiceRolledDiceError as e:
        message_list = [{-1: str(e)}]
        emit('inf_board_message', message_list)
        raise TwiceRolledDiceError(str(e))

    if winner is not False:
        player_win_event(pm, winner)
    else:
        color = pm.player.order_of_turn
        message_list.append({color: session['username'] + ' set figure'})
        message_list = miss_turn(pm, message_list)

    field = pm.room_manager.game_field.get_json_field()

    emit('refresh_game_field', field, room=session['room_id'])

    send_board_message_and_refresh_score_table(pm.room_manager, message_list)
