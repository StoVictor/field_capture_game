import json
import random

from field_capture import db
from field_capture.models import Room, Player
from .exceptions import (MissTokenError, TwiceRolledDiceError,
                         MissTurnLastPersonError, GameDoesNotStartError)


class RoomManager:
    def __init__(self, room_id=None):
        self.room = Room.query.filter_by(id=room_id).first()
        self.game_field = GameField(self.room)

    @staticmethod
    def get_room_exists(room_id):
        room = Room.query.filter_by(id=room_id).first()
        if room is None:
            return False
        return True

    @staticmethod
    def create_room(room_id, name, type, size):
        field = GameField.create_empty_field()
        field = json.dumps(field)
        room = Room(id=room_id, name=name, type=type, size=size,
                    status='waiting', global_score=340,
                    field=field, number_of_moves=0)
        db.session.add(room)
        db.session.commit()

    @staticmethod
    def get_public_rooms():
        public_rooms = Room.query.filter_by(type='public').all()
        return public_rooms

    @staticmethod
    def get_main_public_rooms_info_json():
        public_rooms = RoomManager.get_public_rooms()
        public_room_list = []
        for room in public_rooms:
            public_room_list.append({"id": room.id, "name": room.name,
                                     "size": room.size, "status": room.status,
                                     "players_amount": len(room.players)})
        return json.dumps(public_room_list)

    def get_json_players_id_with_colors(self):
        ids_and_colors = []
        for p in self.room.players:
            ids_and_colors.append({'color': p.order_of_turn, 'id': p.id})
        ids_and_colors = json.dumps(ids_and_colors)
        return ids_and_colors

    def is_full(self):
        if len(self.room.players) >= self.room.size:
            return True
        return False

    def is_playing(self):
        if self.room.status == 'playing':
            return True
        return False

    @staticmethod
    def get_rooms_list():
        rooms = Room.query.all()

    def are_players_ready(self):
        i = 0
        for player in self.room.players:
            if player.ready is True:
                i += 1

        if i == self.room.size:
            return True
        return False

    def get_engaged_place_number(self):
        return len(self.room.players)

    def get_number_of_moves(self):
        return self.room.number_of_moves

    def set_status(self, status):
        if (status == 'waiting') or (status == 'playing'):
            self.room.status = status
            db.session.commit()
            return True
        return False

    def randomly_set_token(self):
        p = random.randrange(1, self.room.size+1, 1)
        random_player_info = {}
        for player in self.room.players:
            if player.order_of_turn == p:
                player.token_presence = True
                random_player_info['id'] = player.id
                random_player_info['order_of_turn'] = p
                random_player_info['username'] = player.username
                db.session.commit()
                return random_player_info

    def start_game(self):
        self.set_status('playing')
        for player in self.room.players:
            player.playing = True
        db.session.commit()
        return True

    def finish_game(self):
        Player.query.filter_by(room_id=self.room.id, playing=False).delete()

        all_players_in_room = (Player.query
                               .filter_by(room_id=self.room.id)
                               .order_by(Player.order_of_turn).all())
        for player in all_players_in_room:
            player.surrender = False
            player.score = 0
            player.playing = False
            player.token_presence = False
            player.ready = False
            player.dice_has_rolled = False
            player.last_dice_values = json.dumps([0, 0])

        k = 1
        for player in all_players_in_room:
            player.order_of_turn = k
            k += 1

        field = GameField.create_empty_field()
        field = json.dumps(field)
        self.room.field = field
        self.room.status = 'waiting'
        self.room.global_score = 340

        # To avoide past game clock activity
        self.room.number_of_moves += 1

        db.session.commit()

    def delete_room(self):
        if len(self.room.players) == 0:
            db.session.delete(self.room)
            db.session.commit()


class PlayerManager:
    class Decorator:
        @classmethod
        def player_has_token(cls, func):
            def wrapper(self, *args):
                if self.player.token_presence is True:
                    return func(self, *args)
                raise MissTokenError("Not your turn!")
            return wrapper

        @classmethod
        def is_game_start(cls, func):
            def wrapper(self, *args):
                if self.room_manager.is_playing():
                    return func(self, *args)
                raise GameDoesNotStartError("Game doesn`t start yet!")
            return wrapper

        @classmethod
        def player_roll_dice_status(cls, rolled_dice):
            def wrap(func):
                def wrapped_f(self, *args):
                    if self.player.dice_has_rolled is rolled_dice:
                        return func(self, *args)
                    raise TwiceRolledDiceError("You already rolled dice")
                return wrapped_f
            return wrap

        @classmethod
        def is_player_win(cls, score_win=True):
            def wrap(func):
                def wrapped_f(self, *args):
                    func(self, *args)
                    if score_win:
                        global_score = self.room_manager.room.global_score
                        if (self.player.score > (global_score /
                                                 self.room_manager.room.size)):
                            return self.player
                    else:
                        i = 0
                        winner = None
                        for player in self.room_manager.room.players:
                            if (player.playing and (not player.surrender)):
                                i += 1
                                winner = player
                        if i == 1:
                            return winner
                    return False
                return wrapped_f
            return wrap

    def __init__(self, player_id, room_id):
        self.player = Player.query.filter_by(id=player_id,
                                             room_id=room_id).first()
        self.room_manager = RoomManager(room_id)

    @staticmethod
    def create_player(player_id, room_id, username):
        room_manager = RoomManager(room_id)
        engaged_place = len(room_manager.room.players)+1

        player = Player(id=player_id, room_id=room_id,
                        order_of_turn=engaged_place,
                        score=0, token_presence=False,
                        username=username, ready=False,
                        playing=False, surrender=False,
                        dice_has_rolled=False,
                        last_dice_values=json.dumps([0, 0]))

        db.session.add(player)
        db.session.commit()
        return player

    @staticmethod
    def get_player_in_room(player_id, room_id):
        player = Player.query.filter_by(id=player_id, room_id=room_id)
        return player

    @staticmethod
    def get_player_in_all_rooms(player_id):
        player_in_all_rooms = Player.query.filter_by(id=player_id).all()
        return player_in_all_rooms

    def get_active_players_in_room(self, room_id):
        active_players = (Player.query.
                          filter_by(surrender=False,
                                    playing=True, room_id=room_id).
                          order_by(Player.order_of_turn).all())
        return active_players

    @staticmethod
    def get_player_status(player_id, room_id=None):
        player_in_rooms = PlayerManager.get_player_in_all_rooms(player_id)
        for player in player_in_rooms:
            if player.playing is True:
                return 'playing'
            elif player.room.status == 'waiting':
                return 'waiting'
            elif room_id == player.room.id:
                return 'restore'
        return 'free'

    @staticmethod
    def player_wait_or_play(player_status):
        if player_status == 'waiting':
            return 'You already wait in other room'
        elif player_status == 'playing':
            return 'You already play'

    def change_ready_status(self):
        if not self.room_manager.is_playing():
            if self.player.ready is True:
                self.player.ready = False
            else:
                self.player.ready = True
            db.session.commit()
            if self.room_manager.are_players_ready():
                return True
            return False

    def change_score(self, points):
        self.player.score += points

    def set_playing(self, status):
        if type(status) == bool:
            self.player.playing = status
            return True
        return False

    def restore(self):
        self.player.playing = True
        db.session.commit()

    def get_next_player(self, active_players):
        order_of_turn = self.player.order_of_turn

        for player in active_players:
            if player.order_of_turn > order_of_turn:
                return player

        return active_players[0]

    @Decorator.player_has_token
    def miss_turn(self):
        self.room_manager.room.number_of_moves += 1
        number_of_moves = self.room_manager.room.number_of_moves

        self.player.token_presence = False
        self.player.dice_has_rolled = False
        self.player.last_dice_values = json.dumps([0, 0])

        room_id = self.room_manager.room.id

        active_players = self.get_active_players_in_room(room_id)

        if len(active_players) == 1:
            raise MissTurnLastPersonError()

        next_player = self.get_next_player(active_players)

        next_player.token_presence = True
        db.session.commit()

        return {'username': next_player.username,
                'order_of_turn': next_player.order_of_turn,
                'id': next_player.id,
                'number_of_moves': number_of_moves}

    @Decorator.player_roll_dice_status(False)
    @Decorator.player_has_token
    def roll_dice(self):
        width = random.randrange(1, 7)
        height = random.randrange(1, 7)
        self.player.dice_has_rolled = True

        self.player.last_dice_values = json.dumps([width, height])
        db.session.commit()

        return width, height

    @Decorator.is_player_win()
    @Decorator.player_roll_dice_status(True)
    @Decorator.player_has_token
    def set_figure(self, x, y):
        width, height = json.loads(self.player.last_dice_values)
        color = self.player.order_of_turn
        first_turn = False
        if self.player.score == 0:
            first_turn = True
        self.room_manager.game_field.is_possible_to_create_figure(x, y,
                                                                  width,
                                                                  height,
                                                                  color,
                                                                  first_turn)

        self.room_manager.game_field.create_figure(x, y, width, height, color)
        json_field = self.room_manager.game_field.get_json_field()
        self.room_manager.room.field = json_field
        self.change_score(width*height)
        db.session.commit()

    @Decorator.is_player_win(False)
    def exit(self):
        if self.player.playing is True:
            self.player.playing = False
        else:
            order_of_turn = self.player.order_of_turn
            db.session.delete(self.player)
            db.session.commit()
            for player in self.room_manager.room.players:
                if order_of_turn < player.order_of_turn:
                    player.order_of_turn -= 1

        db.session.commit()

        self.room_manager.delete_room()

    @Decorator.is_player_win(False)
    @Decorator.is_game_start
    def surrender(self):
        self.player.surrender = True
        db.session.commit()


class ScoreTable:
    @staticmethod
    def get_score_list(room_id):
        score_list = (Player.query.with_entities(Player.username,
                                                 Player.score,
                                                 Player.token_presence,
                                                 Player.order_of_turn,
                                                 Player.ready,
                                                 Player.surrender,
                                                 Player.playing)
                      .filter_by(room_id=room_id)
                      .order_by(Player.order_of_turn).all())

        leader_player = {"username": " ", "score": 0, "order_of_turn": 1}

        for player in score_list:
            if player.score >= leader_player['score']:
                leader_player['username'] = player.username
                leader_player['score'] = player.score
                leader_player['order_of_turn'] = player.order_of_turn

        score_dicts = []

        for player in score_list:
            score_dicts.append(player._asdict())

        return score_dicts, leader_player


class GameField:
    def __init__(self, room):
        self.room = room
        self.field = json.loads(room.field)

    @staticmethod
    def create_empty_field():
        field = []
        for i in range(0, 16):
            field.append([0 for i in range(0, 24)])
        return field

    def get_field(self):
        return self.field

    def get_json_field(self):
        return json.dumps(self.field)

    def _is_same_color_around(self, x, y, width, height, color):
        field_height = len(self.field)
        for temp_x in range(x, x+width):
            if y > 0:
                if self.field[y-1][temp_x] == color:
                    return True
            if y+height < field_height:
                if self.field[y+height][temp_x] == color:
                    return True

        field_width = len(self.field[0])
        for temp_y in range(y, y+height):
            if x > 0:
                if self.field[temp_y][x-1] == color:
                    return True
            if x+width < field_width:
                if self.field[temp_y][x+width] == color:
                    return True
        return False

    def _is_figure_out_of_field(self, x, y, width, height):
        if (x+width > len(self.field[0]) or
           (y+height > len(self.field) or
           (y < 0) or (x < 0))):
            return True

        return False

    def _is_figure_has_free_place(self, x, y, width, height):
        for temp_x in range(x, x+width):
            for temp_y in range(y, y+height):
                if self.field[temp_y][temp_x] != 0:
                    return False
        return True

    def is_possible_to_create_figure(self, x, y, width, height,
                                     color, first_turn):
        if self._is_figure_out_of_field(x, y, width, height):
            raise ValueError("Figure out of field")

        if first_turn is False:
            if not self._is_same_color_around(x, y, width, height, color):
                raise ValueError("You need build figure "
                                 "close to your previous figures")

        if not self._is_figure_has_free_place(x, y, width, height):
            raise ValueError("Figure has no free space")

        return True

    def create_figure(self, x, y, width, height, color):
        for temp_x in range(x, x+width):
            for temp_y in range(y, y+height):
                self.field[temp_y][temp_x] = color
