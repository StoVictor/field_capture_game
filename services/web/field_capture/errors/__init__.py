from flask import Blueprint

bp = Blueprint('errors', __name__)

from field_capture.errors import handlers
