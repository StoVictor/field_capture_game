import uuid

from field_capture.main.forms import NameForm, CreateRoomForm
from field_capture.main.forms import RoomCodeEnterForm
from field_capture.main.game_objects import RoomManager, PlayerManager


def send_name_form(test_client, name):
    name_form = NameForm(prefix='username', name=name, submit=True)
    response = test_client.post('/', data={name_form.name.name:
                                           name_form.name.data},
                                follow_redirects=True)
    return response


def send_create_room_form(test_client, redirects=False):
    """
    GIVEN test client,
    WHEN client try to create new room
    THEN check redirecting to new room, creating new room and
    player in database, room and player have valid ids, player
    are in created room.
    """
    create_room_form = CreateRoomForm(prefix='create_room')

    create_room_form.name.data = "TestRoom"
    create_room_form.submit.data = True
    response = test_client.post('/create_room',
                                data={create_room_form.name.name:
                                      create_room_form.name.data,
                                      create_room_form.players_amount.name:
                                      create_room_form.players_amount.data,
                                      create_room_form.room_type.name:
                                      create_room_form.room_type.data,
                                      create_room_form.submit.name:
                                      create_room_form.submit.data,
                                      },
                                follow_redirects=redirects)
    return response


def send_code_enter_form(test_client, room_id):
    room_code_enter_form = RoomCodeEnterForm(prefix='enter_code')
    room_code_enter_form.code.data = room_id
    response = test_client.post('/enter_private_room',
                                data={room_code_enter_form.code.name:
                                      room_code_enter_form.code.data,
                                      room_code_enter_form.submit.name:
                                      room_code_enter_form.submit.data,
                                      },
                                follow_redirects=False)

    return response


def test_index(test_client, db):
    response = test_client.get('/')
    assert response.status_code == 200
    with test_client.session_transaction() as sess:
        assert 'pers_id' in sess
        assert 'username' in sess
        assert sess['username'] == 'Anonym'

    test_name = 'TestName'
    response = send_name_form(test_client, test_name)
    assert response.status_code == 200
    with test_client.session_transaction() as sess:
        assert sess['username'] == test_name


def test_enter_private_room(test_client, db):
    # login user
    test_client.get('/')

    room_id = 'some_id'
    response = send_code_enter_form(test_client, room_id)
    assert response.status_code == 302

    response = test_client.post('/enter_private_room')
    assert response.status_code == 404


def create_room_and_wait_in_other_room(test_client):
    room_id = str(uuid.uuid4())
    room_size = 2
    RoomManager.create_room(room_id, 'TestRoom', 'public', room_size)
    # RoomManager(room_id)
    with test_client.session_transaction() as sess:
        PlayerManager.create_player(sess['pers_id'], room_id, sess['username'])
        player_manager = PlayerManager(sess['pers_id'], room_id)

    response = send_create_room_form(test_client, redirects=True)

    return response, player_manager


def create_room_and_play_in_other_room(test_client, player_manager):
    player_manager.restore()
    response = send_create_room_form(test_client, redirects=True)
    return response


def test_create_room(test_client, db):
    # login user
    test_client.get('/')

    response, player_manager = create_room_and_wait_in_other_room(test_client)

    assert response.status_code == 200
    assert b'You already wait in other room' in response.data

    response = create_room_and_play_in_other_room(test_client, player_manager)

    assert response.status_code == 200
    assert b'You already play' in response.data

    """
     First exit change playing status.
     Second exit delete player from database.
     This behaviour is unreachable in production,
     becuse to exit you need to join room.
    """
    player_manager.exit()
    player_manager.exit()

    response = send_create_room_form(test_client, redirects=False)
    assert response.status_code == 302

    room_id = response.location.split('?id=')[1]
    room_manager = RoomManager(room_id)
    assert room_manager.room is not None

    response = test_client.post('/create_room')
    assert response.status_code == 403


def enter_room_where_game_has_begun(test_client, room_manager):
    room_id = room_manager.room.id
    room_manager.set_status('playing')
    response = test_client.get('/room?id=%s' % room_id, follow_redirects=True)
    room_manager.set_status('waiting')

    return response


def enter_full_room(test_client, room_id, players_id):

    PlayerManager.create_player(players_id[0], room_id, 'dragon')
    PlayerManager.create_player(players_id[1], room_id, 'ghost')

    # Try enter to full room
    response = test_client.get('/room?id=%s' % room_id, follow_redirects=True)
    return response


def test_room(test_client, db):
    # login user
    test_client.get('/')

    response = test_client.get('/room')
    assert response.status_code == 404

    room_id = str(uuid.uuid4())
    room_size = 2
    RoomManager.create_room(room_id, 'TestRoom', 'public', room_size)
    room_manager = RoomManager(room_id)

    response = enter_room_where_game_has_begun(test_client, room_manager)

    assert response.status_code == 200
    assert b'Game session have started' in response.data

    players_id = [uuid.uuid4(), uuid.uuid4()]

    response = enter_full_room(test_client, room_id, players_id)

    assert response.status_code == 200
    assert b'Room is full' in response.data

    player_manager = PlayerManager(str(players_id[0]), room_id)
    player_manager.exit()

    response = test_client.get('/room?id=%s' % room_id)
    assert response.status_code == 200

    with test_client.session_transaction() as sess:
        PlayerManager(sess['pers_id'], room_id)

    """
     Set room status to playing while player is not play.
     It's mean player was in a room when game started but
     lately exit. Now we test case, when player try
     connect to room where he was previously
    """

    room_manager.set_status('playing')

    response = test_client.get('/room?id=%s' % room_id)
    assert response.status_code == 200
