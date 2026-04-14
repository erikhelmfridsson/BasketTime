"""
Auth helpers: current_user, login_required.
"""
import os
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


def admin_required(f):
    """
    Enkel admin-säkring: användarnamn måste finnas i env ADMIN_USERNAMES (komma-separerat).
    Ex: ADMIN_USERNAMES="erik,admin"
    """

    @wraps(f)
    def inner(*args, **kwargs):
        user = get_current_user()
        if user is None:
            return {"error": "Unauthorized"}, 401
        allowed = [x.strip() for x in (os.environ.get("ADMIN_USERNAMES") or "").split(",") if x.strip()]
        if allowed and (user.username not in allowed):
            return {"error": "Forbidden"}, 403
        return f(*args, **kwargs)

    return inner
