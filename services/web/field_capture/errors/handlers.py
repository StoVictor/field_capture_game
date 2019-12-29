from flask import render_template
from field_capture.errors import bp
@bp.app_errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404


@bp.app_errorhandler(500)
def internal_error(error):
    return render_template('errors/500.html'), 500


@bp.app_errorhandler(403)
def forbidden_error(error):
    return render_template('errors/403.html'), 403


@bp.app_errorhandler(405)
def method_error(error):
    return render_template('errors/405.html'), 405
