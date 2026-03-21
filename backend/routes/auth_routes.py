"""
Auth API: register, login, logout, me, profile (e-post), forgot/reset lösenord.
"""
import hashlib
import os
import re
import secrets
from datetime import datetime, timedelta

from flask import Blueprint, request, session

from backend.auth import get_current_user, login_required
from backend.mail import send_mail
from backend.models import User, db

bp = Blueprint("auth", __name__, url_prefix="/api/auth")

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _normalize_email(value):
    return (value or "").strip().lower()


def _email_ok(value):
    if not value or len(value) > 254:
        return False
    return bool(_EMAIL_RE.match(value))


def _hash_reset_token(raw_token):
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()


def _public_app_url():
    return (os.environ.get("PUBLIC_APP_URL") or os.environ.get("BASE_URL") or "").rstrip("/")


@bp.route("/register", methods=["POST"])
def register():
    data = request.get_json() or {}
    username = (data.get("username") or "").strip()
    email = _normalize_email(data.get("email"))
    password = data.get("password") or ""
    if not username or len(username) < 2:
        return {"error": "Username required (min 2 characters)"}, 400
    if not _email_ok(email):
        return {"error": "Valid email required"}, 400
    if not password or len(password) < 6:
        return {"error": "Password required (min 6 characters)"}, 400
    if User.query.filter_by(username=username).first():
        return {"error": "Username already taken"}, 409
    if User.query.filter_by(email=email).first():
        return {"error": "Email already registered"}, 409
    user = User(username=username, email=email)
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
    identifier = (data.get("username") or data.get("email") or "").strip()
    password = data.get("password") or ""
    if not identifier or not password:
        return {"error": "Username and password required"}, 400
    if "@" in identifier:
        user = User.query.filter_by(email=_normalize_email(identifier)).first()
    else:
        user = User.query.filter_by(username=identifier).first()
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
    user = get_current_user()
    if not user:
        return {"error": "Not logged in"}, 401
    return {"user": user.to_dict()}


@bp.route("/profile", methods=["PUT"])
@login_required
def update_profile():
    user = get_current_user()
    data = request.get_json() or {}
    email = _normalize_email(data.get("email"))
    if not email:
        return {"error": "Email required"}, 400
    if not _email_ok(email):
        return {"error": "Invalid email format"}, 400
    other = User.query.filter(User.email == email, User.id != user.id).first()
    if other:
        return {"error": "Email already in use"}, 409
    user.email = email
    db.session.commit()
    return {"user": user.to_dict()}


@bp.route("/forgot-password", methods=["POST"])
def forgot_password():
    data = request.get_json() or {}
    email = _normalize_email(data.get("email"))
    if not email:
        return {"error": "Email required"}, 400
    if not _email_ok(email):
        return {"error": "Invalid email format"}, 400
    user = User.query.filter_by(email=email).first()
    msg = (
        "Om det finns ett konto med denna e-postadress har vi skickat en länk "
        "för att återställa lösenordet."
    )
    if not user:
        return {"message": msg}, 200
    raw = secrets.token_urlsafe(32)
    user.password_reset_token_hash = _hash_reset_token(raw)
    user.password_reset_expires_at = datetime.utcnow() + timedelta(hours=1)
    db.session.commit()

    base = _public_app_url()
    if not base:
        base = request.url_root.rstrip("/")
    link = (
        base + "/reset-password.html?token=" + raw
    )
    body = (
        "Hej!\n\n"
        "Klicka på länken för att välja ett nytt lösenord för BasketTime:\n\n"
        + link
        + "\n\n"
        "Länken går ut om en timme."
    )
    ok = send_mail(
        email,
        "Återställ lösenord – BasketTime",
        body,
    )
    if not ok:
        user.password_reset_token_hash = None
        user.password_reset_expires_at = None
        db.session.commit()
        return {"error": "Could not send email. Try again later."}, 503
    return {"message": msg}, 200


@bp.route("/reset-password", methods=["POST"])
def reset_password():
    data = request.get_json() or {}
    raw_token = (data.get("token") or "").strip()
    password = data.get("password") or ""
    if not raw_token or len(raw_token) < 10:
        return {"error": "Invalid or missing token"}, 400
    if not password or len(password) < 6:
        return {"error": "Password required (min 6 characters)"}, 400
    th = _hash_reset_token(raw_token)
    user = User.query.filter_by(password_reset_token_hash=th).first()
    if not user or not user.password_reset_expires_at:
        return {"error": "Invalid or expired token"}, 400
    if user.password_reset_expires_at < datetime.utcnow():
        return {"error": "Invalid or expired token"}, 400
    user.set_password(password)
    user.password_reset_token_hash = None
    user.password_reset_expires_at = None
    db.session.commit()
    return {"message": "Password updated"}, 200
