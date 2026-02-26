"""
Auth API: register, login, logout, me.
"""
from flask import Blueprint, request, session

from backend.models import User, db

bp = Blueprint("auth", __name__, url_prefix="/api/auth")


@bp.route("/register", methods=["POST"])
def register():
    data = request.get_json() or {}
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""
    if not username or len(username) < 2:
        return {"error": "Username required (min 2 characters)"}, 400
    if not password or len(password) < 6:
        return {"error": "Password required (min 6 characters)"}, 400
    if User.query.filter_by(username=username).first():
        return {"error": "Username already taken"}, 409
    user = User(username=username)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    session.clear()
    session["user_id"] = user.id
    session.permanent = True
    return {"user": user.to_dict()}, 201


@bp.route("/login", methods=["POST"])
def login():
    data = request.get_json() or {}
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""
    if not username or not password:
        return {"error": "Username and password required"}, 400
    user = User.query.filter_by(username=username).first()
    if not user or not user.check_password(password):
        return {"error": "Invalid username or password"}, 401
    session.clear()
    session["user_id"] = user.id
    session.permanent = True
    return {"user": user.to_dict()}


@bp.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return {}, 204


@bp.route("/me", methods=["GET"])
def me():
    from backend.auth import get_current_user

    user = get_current_user()
    if not user:
        return {"error": "Not logged in"}, 401
    return {"user": user.to_dict()}
