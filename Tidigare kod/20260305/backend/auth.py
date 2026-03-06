"""
Auth helpers: current_user, login_required.
"""
from functools import wraps

from flask import g, session

from backend.models import User, db


def get_current_user():
    if hasattr(g, "current_user"):
        return g.current_user
    user_id = session.get("user_id")
    if not user_id:
        return None
    g.current_user = db.session.get(User, int(user_id))
    return g.current_user


def login_required(f):
    @wraps(f)
    def inner(*args, **kwargs):
        if get_current_user() is None:
            return {"error": "Unauthorized"}, 401
        return f(*args, **kwargs)

    return inner
