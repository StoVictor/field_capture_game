from flask_socketio import SocketIO
from field_capture import celery
from field_capture.main import game_objects
from flask import current_app
import os


broker = os.environ.get('AMQP_BROKER')
socketio = SocketIO(message_queue=broker, async_mode='threading')


@celery.task(name="task.clock")
def game_clock(room_id, current_player_id, number_of_moves):
    app = current_app._get_current_object()
    with app.app_context():
        room_manager = game_objects.RoomManager(room_id)
        if room_manager.get_number_of_moves() == number_of_moves:
            socketio.emit('stop_game_clock', current_player_id, room=room_id)


@celery.task(name="task.message")
def async_board_message(room_id, message, color, number_of_moves):
    app = current_app._get_current_object()
    message_list = [{color:message}]
    with app.app_context():
        room_manager = game_objects.RoomManager(room_id)
        if room_manager.get_number_of_moves() == number_of_moves:
            socketio.emit('inf_board_message', message_list, room=room_id)
