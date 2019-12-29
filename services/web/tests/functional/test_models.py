import uuid
import json


def test_new_room(new_room):
    """
    GIVEN a Room model
    WHEN a new Room is created
    THEN check name, type, engaged_place, status, global_score, field
    are defined correctly
    """
    try:
        uuid.UUID(str(new_room.id), version=4)
    except ValueError:
        raise ValueError('new_room id is not valid uuid4')
    assert new_room.name == 'TestRoom'
    assert new_room.type == 'public'
    assert new_room.status == 'playing'
    assert new_room.global_score == 340
    assert json.loads(new_room.field) == []
    assert new_room.number_of_moves == 0


def test_new_player(new_player, new_room):
    """
    GIVEN a Player model
    WHEN a new Player is created
    THEN check order_of_turn, score, token_presence, username, ready,
    playing, first_turn, surender are defined correctly
    """

    try:
        uuid.UUID(str(new_player.id), version=4)
    except ValueError:
        raise ValueError('new_player id is not valid uuid4')
    assert new_player.order_of_turn == 1
    assert new_player.score == 0
    assert new_player.token_presence is False
    assert new_player.username == 'Victor'
    assert new_player.ready is False
    assert new_player.playing is False
    assert new_player.surrender is False
    assert new_player.dice_has_rolled is False
    assert json.loads(new_player.last_dice_values) == [0, 0]
    assert new_player.room_id == new_room.id
