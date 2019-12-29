import pytest
import uuid
import json
from field_capture import socketio
from field_capture.models import Room, Player
from field_capture import create_app
from field_capture.main import game_objects
from field_capture.main.forms import NameForm, CreateRoomForm

@pytest.fixture
def app():
    return create_app(test_config=True)


@pytest.fixture
def test_client(app):
    flask_app = app
    flask_app.config.from_mapping(
            WTF_CSRF_ENABLED=False,
            TESTING=True,
    )
    testing_client = flask_app.test_client()

    ctx = flask_app.app_context()

    ctx.push()

    yield testing_client

    ctx.pop()

@pytest.fixture
def db(app):
    from field_capture import db
    with app.app_context():
        db.create_all()
        yield db
        db.session.commit()
        db.drop_all()


@pytest.fixture(scope="module")
def get_id():
    return str(uuid.uuid4())


@pytest.fixture
def new_room(get_id, db):
    room = Room(id=get_id, name='TestRoom', type='public', status='playing',
                global_score=340, field=json.dumps([]), number_of_moves=0
                )
    return room


@pytest.fixture
def room_manager(get_id, db):
    game_objects.RoomManager.create_room(get_id, 'test', 'public', 4)
    return game_objects.RoomManager(get_id)


@pytest.fixture
def player_manager(get_id, room_manager, db):
    p_id = str(uuid.uuid4())
    game_objects.PlayerManager.create_player(p_id, get_id, 'test')
    return game_objects.PlayerManager(p_id, get_id)


@pytest.fixture
def new_player(new_room):
    player = Player(id=str(uuid.uuid4()), order_of_turn=1, score=0,
                    token_presence=False, username='Victor',
                    ready=False, playing=False,
                    surrender=False, dice_has_rolled=False,
                    last_dice_values=json.dumps([0, 0]),
                    room_id=new_room.id)
    return player


@pytest.fixture
def make_socketio_test_client():
    def _make_socketio_test_client(app, test_client): 
        testing_client = socketio.test_client(app,
                                              flask_test_client=test_client)
        return testing_client
    return _make_socketio_test_client


@pytest.fixture
def make_players(get_id, db):
    def _make_players(amount=4):
        players = []
        for i in range(0, amount):
            player_id = str(uuid.uuid4())
            players.append(game_objects.PlayerManager
                           .create_player(player_id, get_id,
                                          'test_player' + str(i)))
        return players
    return _make_players


@pytest.fixture
def make_custom_player(get_id, db):
    def _make_custom_player(score=0, token_presence=False,
                            username="test", ready=False,
                            playing=False, surrender=False,
                            dice_has_rolled=False, last_dice_values=[0, 0],
                            order_of_turn=0, id=None):
        if id is None:
            id = str(uuid.uuid4())

        player = Player(id=id, order_of_turn=order_of_turn,
                        score=score, username=username, ready=ready,
                        playing=playing, surrender=surrender,
                        token_presence=token_presence, room_id=get_id,
                        dice_has_rolled=dice_has_rolled,
                        last_dice_values=last_dice_values)
        return player
    return _make_custom_player


@pytest.fixture
def score_table(get_id, db):
    return game_objects.ScoreTable()


@pytest.fixture
def game_field_class(new_room):
    return game_objects.GameField


@pytest.fixture
def game_field(new_room):
    return game_objects.GameField(new_room)
