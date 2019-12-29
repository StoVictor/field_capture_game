from functools import wraps

from flask import session, redirect, url_for, flash


def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if 'pers_id' not in session:
            flash('You have been redirected to main page for automatic login')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return wrapper
