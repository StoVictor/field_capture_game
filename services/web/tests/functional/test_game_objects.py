import json
import random
import pytest
import uuid

from field_capture.models import Room, Player
from field_capture.main import game_objects

from field_capture.main.exceptions import (MissTokenError,
                                           TwiceRolledDiceError,
                                           MissTurnLastPersonError,
                                           GameDoesNotStartError)


class TestRoomManager:
    def test_create_room(self, get_id, db):
        result = Room.query.filter_by(id=get_id).first()
        assert result is None

        name = 'test'
        type = 'public'
        size = 2

        result = game_objects.RoomManager.create_room(get_id, name, type, size)

        result = Room.query.filter_by(id=get_id).first()
        assert result is not None

    def test_get_room_exist(self, get_id, db):
        room_existance = game_objects.RoomManager.get_room_exists('1111')
        assert room_existance is False

        name = 'test'
        type = 'public'
        size = 2

        game_objects.RoomManager.create_room(get_id, name, type, size)
        room_existance = game_objects.RoomManager.get_room_exists(get_id)
        assert room_existance is True

    def test_get_json_players_id_with_colors(self, get_id, db, room_manager):
        player1 = (game_objects.PlayerManager
                   .create_player(str(uuid.uuid4()), get_id, 'test_player1'))
        player2 = (game_objects.PlayerManager
                   .create_player(str(uuid.uuid4()), get_id, 'test_player2'))

        result = json.loads(room_manager.get_json_players_id_with_colors())

        assert player1.order_of_turn == result[0]['color']
        assert player1.id == result[0]['id']

        assert player2.order_of_turn == result[1]['color']
        assert player2.id == result[1]['id']

    def test_are_players_ready(self, db, room_manager, make_players):
        players = make_players()
        result = room_manager.are_players_ready()

        assert result is False

        for player in players:
            player.ready = True
        result = room_manager.are_players_ready()

        assert result is True

    def test_randomly_set_token(self, db, room_manager, make_players):
        token = False
        i = 0
        players = make_players()
        for player in players:
            if player.token_presence is True:
                token = True
                i += 1

        assert token is False
        assert i == 0

        room_manager.randomly_set_token()

        for player in players:
            if player.token_presence is True:
                token = True
                i += 1

        assert token is True
        assert i == 1

    def test_start_game(self, db, room_manager, make_players):
        players = make_players()
        someone_playing = 0

        assert room_manager.room.status == 'waiting'

        for player in players:
            if player.playing is True:
                someone_playing += 1

        assert someone_playing == 0

        room_manager.start_game()

        assert room_manager.room.status == 'playing'

        for player in players:
            if player.playing is True:
                someone_playing += 1

        assert someone_playing == room_manager.room.size

    def test_finish_game(self, get_id, db, make_custom_player, room_manager):
        custom_players = []
        custom_players.append(make_custom_player(score=20, order_of_turn=0,
                                                 ready=True, playing=True,
                                                 surrender=True,
                                                 token_presence=False,
                                                 dice_has_rolled=False,
                                                 last_dice_values=[0, 0],
                                                 username='cusom_p0'))

        custom_players.append(make_custom_player(score=11, order_of_turn=1,
                                                 ready=True, playing=False,
                                                 surrender=False,
                                                 token_presence=False,
                                                 dice_has_rolled=False,
                                                 last_dice_values=[0, 0],
                                                 username='cusom_p1'))

        custom_players.append(make_custom_player(score=42, order_of_turn=2,
                                                 ready=True, playing=True,
                                                 surrender=True,
                                                 token_presence=True,
                                                 dice_has_rolled=True,
                                                 last_dice_values=[5, 2],
                                                 username='cusom_p2'))

        custom_players.append(make_custom_player(score=37, order_of_turn=3,
                                                 ready=True, playing=True,
                                                 surrender=True,
                                                 token_presence=False,
                                                 dice_has_rolled=False,
                                                 last_dice_values=[0, 0],
                                                 username='cusom_p3'))
        for player in custom_players:
            db.session.add(player)
        db.session.commit()

        room_manager.room.status = 'playing'
        room_manager.room.global_score = 340-37-11-42-20
        numb_of_moves = room_manager.room.number_of_moves

        room_manager.finish_game()

        for player in room_manager.room.players:
            assert player.score == 0
            assert player.ready is False
            assert player.surrender is False
            assert player.dice_has_rolled is False
            assert player.playing is False
            assert player.token_presence is False
            assert json.loads(player.last_dice_values) == [0, 0]

        assert room_manager.room.status == 'waiting'
        assert room_manager.room.global_score == 340
        assert room_manager.room.number_of_moves == numb_of_moves+1

        def test_delet_room(get_id, room_manager):
            assert room_manager is not None

            player = make_custom_player(score=20, order_of_turn=0, ready=True,
                                        playing=True, surrender=True,
                                        token_presence=False,
                                        dice_has_rolled=False,
                                        last_dice_values=[0, 0],
                                        username='cusom_p0')
            room_manager.delete_room()

            assert room_manager is not None

            player_manager = game_objects.PlayerManager(player.id, get_id)
            player_manager.exit()

            room_manager.delete_room()

            assert room_manager is None


class TestPlayerManager:

    def test_create_player(self, get_id, room_manager, db):
        p_id = str(uuid.uuid4())

        player = Player.query.filter_by(id=p_id, room_id=get_id).first()
        assert player is None
        game_objects.PlayerManager.create_player(p_id, get_id, 'test')
        player = game_objects.PlayerManager(p_id, get_id).player
        assert player is not None

    class Decorator:
        def __init__(self, player_manager, room_manager=None):
            self.player_manager = player_manager
            if player_manager is not None:
                self.player = player_manager.player
            self.room_manager = room_manager

        @game_objects.PlayerManager.Decorator.player_has_token
        def player_has_token_decorated(self):
            return 'expected result'

        @game_objects.PlayerManager.Decorator.is_game_start
        def is_game_start_decorated(self):
            return 'expected result'

        @game_objects.PlayerManager.Decorator.player_roll_dice_status(True)
        def player_roll_dice_status_decorated(self):
            return 'expected result'

        @game_objects.PlayerManager.Decorator.is_player_win()
        def is_player_win_decorated(self):
            return 'expected result'

        @game_objects.PlayerManager.Decorator.is_player_win(False)
        def is_player_win_non_score_decorated(self):
            return 'expected result'

    def test_player_has_token(self, player_manager):
        test_decorators = self.Decorator(player_manager)

        with pytest.raises(MissTokenError) as info:
            test_decorators.player_has_token_decorated()
        assert 'Not your turn!' in str(info.value)

        test_decorators.player.token_presence = True
        assert (test_decorators
                .player_has_token_decorated() == 'expected result')
        test_decorators.player.token_presence = False

    def test_is_game_start(self, player_manager, room_manager):
        test_decorators = self.Decorator(player_manager,
                                         room_manager=room_manager)

        with pytest.raises(GameDoesNotStartError) as info:
            test_decorators.is_game_start_decorated()
        assert "Game doesn`t start yet!" in str(info.value)

        test_decorators.room_manager.set_status('playing')
        assert test_decorators.is_game_start_decorated() == 'expected result'

    def test_player_roll_dice_status(self, player_manager):
        test_decorators = self.Decorator(player_manager)

        test_decorators.player.dice_has_rolled = True
        assert (test_decorators
                .player_roll_dice_status_decorated() == 'expected result')

        test_decorators.player.dice_has_rolled = False
        with pytest.raises(TwiceRolledDiceError) as info:
            test_decorators.player_roll_dice_status_decorated()
        assert "You already rolled dice" in str(info.value)

    def test_is_player_win(self, db, player_manager,
                           room_manager, make_players):
        test_decorators = self.Decorator(player_manager,
                                         room_manager=room_manager)
        assert test_decorators.is_player_win_decorated() is False

        test_decorators.room_manager.room.global_score = 10
        test_decorators.player_manager.player.score = 20
        assert (test_decorators.is_player_win_decorated() ==
                test_decorators.player_manager.player)

        players = make_players(amount=3)
        assert test_decorators.is_player_win_non_score_decorated() is False

        for player in players:
            db.session.delete(player)
        db.session.commit()
        test_decorators.player_manager.player.playing = True
        assert (test_decorators.is_player_win_non_score_decorated() ==
                test_decorators.player_manager.player)

    def test_get_next_player(self, db, get_id, room_manager,
                             player_manager, make_custom_player):
        players = []
        for i in range(0, 3):
            players.append(make_custom_player(playing=True,
                                              username='test' + str(i),
                                              order_of_turn=i+2,
                                              ready=True))
        for player in players:
            db.session.add(player)
        db.session.commit()

        player_manager.player.playing = True
        player_manager.player.token_presence = True

        active_players = player_manager.get_active_players_in_room(get_id)
        next_player = player_manager.get_next_player(active_players)
        assert str(next_player.id) == str(players[0].id)

    def test_miss_turn(self, db, player_manager,
                       room_manager, make_custom_player):
        player_manager.player.playing = True
        player_manager.player.ready = True

        player_manager.player.dice_has_rolled = True
        player_manager.player.last_dice_values = json.dumps([5, 5])
        player_manager.player.token_presence = True
        moves_number = room_manager.room.number_of_moves
        custom_player = make_custom_player(playing=True,
                                           username='test2',
                                           order_of_turn=2,
                                           ready=True)
        db.session.add(custom_player)
        db.session.commit()
        player_manager.miss_turn()

        assert player_manager.player.dice_has_rolled is False
        assert json.loads(player_manager.player.last_dice_values) == [0, 0]
        assert player_manager.player.token_presence is False
        assert room_manager.room.number_of_moves == moves_number+1

        assert custom_player.token_presence is True

    def test_roll_dice(self, player_manager):
        player_manager.player.token_presence = True

        dice_values = player_manager.roll_dice()
        assert dice_values[0] < 7
        assert dice_values[0] > 0
        assert dice_values[1] < 7
        assert dice_values[1] > 0

    def test_set_figure(self, player_manager, new_player):
        player_manager.player.token_presence = True
        player_manager.player.dice_has_rolled = True
        player_manager.player.last_dice_values = json.dumps([1, 1])
        player_manager.set_figure(1, 1)
        assert player_manager.player.score == 1
    
    def test_exit(self, db, player_manager, make_players):
        player_manager.player.playing = True
        player_manager.exit()

        assert player_manager.player.playing is False

        players = make_players(3)
        
        for player in players:
            db.session.add(player)
        db.session.commit()

        player_manager.exit()

        for i in range(0, 3):
            assert players[i].order_of_turn == i+1

class TestScoreTable:
    @staticmethod
    def test_get_score_list(db, get_id, room_manager, 
                            make_players, score_table):
        players = make_players()
        i = 10
        for player in players:
            player.score = i
            i += 10
            db.session.add(player)

        db.session.commit()
        score_dicts, leader_player = (score_table.get_score_list(get_id))
        for i in range(0, 4):
            assert players[i].username == score_dicts[i]['username']
            assert players[i].score == score_dicts[i]['score']
            assert (players[i].token_presence
                    == score_dicts[i]['token_presence'])
            assert (players[i].order_of_turn
                    == score_dicts[i]['order_of_turn'])
            assert players[i].ready == score_dicts[i]['ready']
            assert players[i].surrender == score_dicts[i]['surrender']
            assert players[i].playing == score_dicts[i]['playing']

        assert players[3].username == leader_player['username']
        assert players[3].score == leader_player['score']
        assert players[3].order_of_turn == leader_player['order_of_turn']

class TestGameField:
    @staticmethod
    def test_create_empty_field(game_field_class):
        field = game_field_class.create_empty_field() 
        assert len(field) == 16
        assert len(field[0]) == 24

    def test_is_same_color_around(self, new_room, game_field):
        new_room.field = game_field.create_empty_field()
        game_field.field = new_room.field
        for i in range(5, 11):
            for k in range(5, 11):
                new_room.field[i][k] = 1
        for x in range(5, 11):
            assert game_field._is_same_color_around(x, 4, 1, 1, 1) is True
        for y in range(5, 11):
            assert game_field._is_same_color_around(4, y, 1, 1, 1) is True

    def test_is_figure_has_free_place(self, new_room, game_field):
        new_room.field = game_field.create_empty_field()
        game_field.field = new_room.field
        game_field.create_figure(10, 10, 1, 1, 1)
        assert game_field._is_figure_has_free_place(1, 1, 5, 5) is True
        assert game_field._is_figure_has_free_place(6, 6, 5, 5) is False

