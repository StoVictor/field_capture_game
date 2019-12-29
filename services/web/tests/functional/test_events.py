import pytest
import json
from sqlalchemy.orm import raiseload
from field_capture.main.exceptions import (MissTokenError,
                                           TwiceRolledDiceError,
                                           InappropriateActionError,
                                           GameDoesNotStartError)
from field_capture.main import game_objects
from field_capture.models import Room, Player


def test_join_handler(app, test_client,
                      make_socketio_test_client, player_manager,
                      db, get_id):
    test_client.get('/')
    test_client.get('/room?id=' + get_id)
    test_client_sockets = make_socketio_test_client(app, test_client)
    test_client_sockets.emit('join', (get_id))
    received = test_client_sockets.get_received()

    emit_names = []
    for emit in received:
        emit_names.append(emit['name'])

    assert 'set_local_init_data' in emit_names
    assert 'set_room_status' in emit_names


def test_disconnect_handler_first(app, db, test_client,
                                  make_socketio_test_client,
                                  room_manager, get_id, make_players):
    # 1) test when players don't plays and more then 1 player in room
    test_client.get('/')
    test_client.get('/room?id=' + get_id)
    test_client_sockets = make_socketio_test_client(app, test_client)
    test_client_sockets.emit('join', (get_id))
    players = make_players(1)

    for player in players:
        db.session.add(player)
    db.session.commit()
    test_client_sockets.emit('disconnect')
    assert Room.query.filter_by(id=get_id).first() is not None
    with test_client.session_transaction() as sess:
        assert Player.query.filter_by(id=sess['pers_id'],
                                      room_id=get_id).first() is None


def test_disconnect_handler_second(app, db, test_client,
                                   make_socketio_test_client,
                                   room_manager, get_id, make_players):
    # 2) test when game is not started and only one player in room
    test_client.get('/')
    test_client.get('/room?id=' + get_id)
    test_client_sockets = make_socketio_test_client(app, test_client)
    test_client_sockets.emit('join', (get_id))
    test_client_sockets.emit('disconnect')
    assert Room.query.filter_by(id=get_id).first() is None
    with test_client.session_transaction() as sess:
        assert Player.query.filter_by(id=sess['pers_id'],
                                      room_id=get_id).first() is None


def test_disconnect_handler_third(app, db, test_client,
                                  make_socketio_test_client,
                                  room_manager, get_id, make_players):
    # 3) test when game is started and in room 2 players
    test_client.get('/')
    test_client.get('/room?id=' + get_id)
    test_client_sockets = make_socketio_test_client(app, test_client)
    test_client_sockets.emit('join', (get_id))

    room_manager.room.status = 'playing'

    with test_client.session_transaction() as sess:
        player_manager = game_objects.PlayerManager(sess['pers_id'], get_id)
    player_manager.player.ready = True
    player_manager.player.playing = True

    players = make_players(1)
    p_id = players[0].id
    players[0].ready = True
    players[0].playing = True
    db.session.add(players[0])
    db.session.commit()

    test_client_sockets.emit('disconnect')

    received = test_client_sockets.get_received()
    event_names = []
    for el in received:
        event_names.append(el['name'])
    assert 'show_win_window' in event_names
    player = Player.query.filter_by(id=p_id).first()
    assert player.ready is False
    assert player.playing is False
    room = Room.query.filter_by(id=get_id).options(raiseload('*')).first()
    assert room.status == 'waiting'
    with test_client.session_transaction() as sess:
        client_player = (Player.query
                         .filter_by(id=sess['pers_id'], room_id=get_id)
                         .options(raiseload('*')).first())
    assert client_player is None


def test_disconnect_handler_fourth(app, db, test_client,
                                   make_socketio_test_client,
                                   room_manager, get_id, make_players):
    # 4) test when game is started and in room more then 2 players
    test_client.get('/')
    test_client.get('/room?id=' + get_id)
    test_client_sockets = make_socketio_test_client(app, test_client)
    test_client_sockets.emit('join', (get_id))

    room_manager.room.status = 'playing'

    with test_client.session_transaction() as sess:
        client_player = (Player.query
                         .filter_by(id=sess['pers_id'], room_id=get_id)
                         .options(raiseload('*')).first())
    client_player.ready = True
    client_player.playing = True

    players = make_players(3)
    for player in players:
        player.ready = True
        player.playing = True
        db.session.add(player)
    db.session.commit()

    test_client_sockets.emit('disconnect')

    received = test_client_sockets.get_received()
    event_names = []
    for el in received:
        event_names.append(el['name'])

    assert 'show_win_window' not in event_names
    for player in players:
        assert player.ready is True
        assert player.playing is True

    assert client_player.playing is False
    assert client_player.ready is True

    assert room_manager.room.status == 'playing'


def test_change_ready_status_handler(app, db, get_id, test_client,
                                     make_socketio_test_client):
    game_objects.RoomManager.create_room(get_id, 'TestRoom', 'public', 2)
    test_client.get('/')
    test_client.get('/room?id='+get_id)
    test_client_sockets = make_socketio_test_client(app, test_client)
    test_client_sockets.emit('join', (get_id))

    # 1) Game in room is already start
    room = Room.query.filter_by(id=get_id).first()
    room.status = 'playing'
    with pytest.raises(InappropriateActionError) as info:
        test_client_sockets.emit('change_ready_status')
    assert 'You can`t do this' in str(info.value)

    # 2) Game not start yet, player change status to ready
    room.status = 'waiting'
    test_client_sockets.emit('change_ready_status')
    received = test_client_sockets.get_received()
    inf_board_message = []
    for mess in received:
        if mess['name'] == 'inf_board_message':
            try:
                inf_board_message.append(mess['args'][0][0][1])
            except KeyError:
                pass
    assert 'Anonym is ready' in inf_board_message
    assert room.status == 'waiting'

    # 3) Game not start yet, player change status to not ready
    test_client_sockets.emit('change_ready_status')
    received = test_client_sockets.get_received()
    inf_board_message = []
    for mess in received:
        if mess['name'] == 'inf_board_message':
            try:
                inf_board_message.append(mess['args'][0][0][1])
            except KeyError:
                pass
    assert 'Anonym is not ready' in inf_board_message


def test_roll_dice_handler(app, db, get_id, test_client,
                           make_socketio_test_client):
    game_objects.RoomManager.create_room(get_id, 'TestRoom', 'public', 2)
    test_client.get('/')
    test_client.get('/room?id='+get_id)
    test_client_sockets = make_socketio_test_client(app, test_client)
    test_client_sockets.emit('join', (get_id))
    with test_client.session_transaction() as sess:
        player = Player.query.filter_by(id=sess['pers_id']).first()
    player.token_presence = True
    test_client_sockets.emit('roll_dice')
    received = test_client_sockets.get_received()
    emit_names = []
    for message in received:
        emit_names.append(message['name'])
    assert 'dice_rolled' in emit_names
    with pytest.raises(TwiceRolledDiceError) as info:
        test_client_sockets.emit('roll_dice')
    assert 'You already rolled dice' in str(info.value)


def test_surrender_handler_first(app, db, get_id, test_client,
                                 make_socketio_test_client):
    # 1) Game doesn't start yet
    game_objects.RoomManager.create_room(get_id, 'TestRoom', 'public', 2)
    test_client.get('/')
    test_client.get('/room?id='+get_id)
    test_client_sockets = make_socketio_test_client(app, test_client)
    test_client_sockets.emit('join', (get_id))
    with pytest.raises(GameDoesNotStartError) as info:
        test_client_sockets.emit('surrender')

    assert 'Game doesn`t start yet' in str(info.value)


def test_surrender_handler_second(app, db, get_id, test_client,
                                  make_socketio_test_client, make_players):
    # 2) Game start and room is full with 2 players
    game_objects.RoomManager.create_room(get_id, 'TestRoom', 'public', 2)
    test_client.get('/')
    test_client.get('/room?id='+get_id)
    test_client_sockets = make_socketio_test_client(app, test_client)
    test_client_sockets.emit('join', (get_id))
    with test_client.session_transaction() as sess:
        client_player = Player.query.filter_by(id=sess['pers_id'],
                                               room_id=get_id).first()
    client_player.ready = True
    client_player.playing = True

    room = Room.query.filter_by(id=get_id).first()
    room.status = 'playing'
    players = make_players(1)
    for player in players:
        player.ready = True
        player.playing = True
    db.session.commit()
    test_client_sockets.emit('surrender')
    received = test_client_sockets.get_received()
    emit_names = []
    for el in received:
        emit_names.append(el['name'])

    assert room.status == 'waiting'
    assert 'show_win_window' in emit_names


def test_surrender_handler_third(app, db, get_id, test_client,
                                 make_socketio_test_client, make_players):
    # 2) Game start and room is full with 3 players
    game_objects.RoomManager.create_room(get_id, 'TestRoom', 'public', 3)
    test_client.get('/')
    test_client.get('/room?id='+get_id)
    test_client_sockets = make_socketio_test_client(app, test_client)
    test_client_sockets.emit('join', (get_id))
    with test_client.session_transaction() as sess:
        client_player = Player.query.filter_by(id=sess['pers_id'],
                                               room_id=get_id).first()
    client_player.ready = True
    client_player.playing = True

    room = Room.query.filter_by(id=get_id).first()
    room.status = 'playing'
    players = make_players(2)
    for player in players:
        player.ready = True
        player.playing = True
    db.session.commit()
    test_client_sockets.emit('surrender')
    received = test_client_sockets.get_received()
    emit_names = []
    for el in received:
        emit_names.append(el['name'])

    assert 'show_win_winodw' not in emit_names
    assert client_player.surrender is True


def test_set_figure_check_exceptions(app, db, get_id, test_client,
                                     make_socketio_test_client, make_players):
    game_objects.RoomManager.create_room(get_id, 'TestRoom', 'public', 3)
    test_client.get('/')
    test_client.get('/room?id='+get_id)
    test_client_sockets = make_socketio_test_client(app, test_client)
    test_client_sockets.emit('join', (get_id))
    with test_client.session_transaction() as sess:
        client_player = Player.query.filter_by(id=sess['pers_id'],
                                               room_id=get_id).first()
    client_player.ready = True
    client_player.playing = True
    client_player.token_presence = True
    client_player.dice_has_rolled = True
    client_player.last_dice_values = json.dumps([5, 5])
    room = Room.query.filter_by(id=get_id).first()
    room.status = 'playing'
    players = make_players(1)
    for player in players:
        player.ready = True
        player.playing = True
    db.session.commit()
    with pytest.raises(ValueError) as info:
        test_client_sockets.emit('set_figure', 25, 25)

    assert "Figure out of field" in str(info.value)

    with test_client.session_transaction() as sess:
        client_player = Player.query.filter_by(id=sess['pers_id'],
                                               room_id=get_id).first()
    client_player.score = 20
    db.session.commit()

    with pytest.raises(ValueError) as info:
        test_client_sockets.emit('set_figure', 10, 10)
    assert ("You need build figure close "
            "to your previous figures") in str(info.value)
    room = Room.query.filter_by(id=get_id).first()
    field = game_objects.GameField.create_empty_field()
    for i in range(len(field[0])):
        for k in range(len(field)):
            field[k][i] = 1
    room.field = json.dumps(field)
    db.session.commit()
    with pytest.raises(ValueError) as info:
        test_client_sockets.emit('set_figure', 10, 10)
    assert "Figure has no free space" in str(info.value)


def test_set_figure_win_case(app, db, get_id, test_client,
                             make_socketio_test_client, make_players):
    game_objects.RoomManager.create_room(get_id, 'TestRoom', 'public', 2)
    test_client.get('/')
    test_client.get('/room?id='+get_id)
    test_client_sockets = make_socketio_test_client(app, test_client)
    test_client_sockets.emit('join', (get_id))
    with test_client.session_transaction() as sess:
        client_player = Player.query.filter_by(id=sess['pers_id'],
                                               room_id=get_id).first()
    client_player.ready = True
    client_player.playing = True
    client_player.token_presence = True
    client_player.dice_has_rolled = True
    client_player.last_dice_values = json.dumps([5, 5])
    client_player.score = 0
    room = Room.query.filter_by(id=get_id).first()
    room.status = 'playing'
    room.global_score = 1
    players = make_players(1)
    for player in players:
        player.ready = True
        player.playing = True
    db.session.commit()
    test_client_sockets.emit('set_figure', 10, 10)
    received = test_client_sockets.get_received()
    emit_names = []
    for message in received:
        emit_names.append(message['name'])
    assert 'show_win_window' in emit_names


def test_set_figure_not_win_case(app, db, get_id, test_client,
                                 make_socketio_test_client, make_players):
    game_objects.RoomManager.create_room(get_id, 'TestRoom', 'public', 3)
    test_client.get('/')
    test_client.get('/room?id='+get_id)
    test_client_sockets = make_socketio_test_client(app, test_client)
    test_client_sockets.emit('join', (get_id))
    with test_client.session_transaction() as sess:
        client_player = Player.query.filter_by(id=sess['pers_id'],
                                               room_id=get_id).first()
    client_player.ready = True
    client_player.playing = True
    client_player.token_presence = True
    client_player.dice_has_rolled = True
    client_player.last_dice_values = json.dumps([5, 5])
    room = Room.query.filter_by(id=get_id).first()
    room.status = 'playing'
    players = make_players(2)
    for player in players:
        player.ready = True
        player.playing = True
    db.session.commit()
    test_client_sockets.emit('set_figure', 10, 10)
    received = test_client_sockets.get_received()

    emit_names = []

    for message in received:
        emit_names.append(message['name'])

    assert 'show_win_window' not in emit_names

    with test_client.session_transaction() as sess:
        client_player = Player.query.filter_by(id=sess['pers_id'],
                                               room_id=get_id).first()
    assert client_player.score == 25
    assert client_player.token_presence is False


def test_miss_turn_handler(app, test_client, db, make_players,
                           make_socketio_test_client, get_id, room_manager,
                           make_custom_player):
    test_client.get('/')
    test_client.get('/room?id=' + get_id)
    test_client_sockets = make_socketio_test_client(app, test_client)
    test_client_sockets.emit('join', (get_id))

    with pytest.raises(MissTokenError) as info:
        test_client_sockets.emit('miss_turn')

    assert 'Not your turn!' in str(info.value)

    with test_client.session_transaction() as sess:
        player_manager = game_objects.PlayerManager(sess['pers_id'], get_id)

    players = make_players(3)
    for player in players:
        player.playing = True
        db.session.add(player)

    player_manager.player.token_presence = True
    player_manager.player.playing = True

    test_client_sockets.emit('miss_turn')

    with test_client.session_transaction() as sess:
        player_manager = game_objects.PlayerManager(sess['pers_id'], get_id)

    assert player_manager.player.token_presence is False
    assert players[0].token_presence is True
