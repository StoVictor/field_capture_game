import os
from flask import Flask
from flask_socketio import SocketIO
from .models import db, init_db_command, drop_db_command
from celery import Celery
import eventlet
eventlet.monkey_patch()

socketio = SocketIO()
broker=os.environ.get('AMQP_BROKER')
celery = Celery(__name__, broker=broker)


def create_app(test_config=None):
    """Create and configure app"""

    app = Flask(__name__, instance_relative_config=True)

    app.config.from_object("field_capture.config.Config")
    app.config['AMQP_BROKER'] = os.environ.get('AMQP_BROKER')
    if test_config is True:
        app.config['AMQP_BROKER']
    celery.conf.update(app.config)
    socketio.init_app(app, message_queue=app.config['AMQP_BROKER'],
                      logger=True, engineio_logger=True)

    from field_capture.errors import bp as errors_bp
    app.register_blueprint(errors_bp)

    from field_capture.main import main
    app.register_blueprint(main)

    db.init_app(app)
    app.cli.add_command(init_db_command)
    app.cli.add_command(drop_db_command)

    return app
