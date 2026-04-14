"""
BasketTime: Flask app – static frontend + API for users, teams, matches.
Serves static files and mounts /api for auth, teams, matches.
"""
import os
import sys

from flask import Flask, request, send_from_directory
from werkzeug.middleware.proxy_fix import ProxyFix

from backend.models import db
from backend.schema_migrations import (
    ensure_created_at_columns,
    ensure_match_player_shots_columns,
    ensure_user_email_and_reset_columns,
)

# Domäner som ska visa landningssidan istället för appen (resten får index/app)
LANDING_HOSTS = {"baskettime.se", "www.baskettime.se"}
from backend.routes.auth_routes import bp as auth_bp
from backend.routes.matches_routes import bp as matches_bp
from backend.routes.profixio_routes import bp as profixio_bp
from backend.routes.public_routes import bp as public_bp
from backend.routes.teams_routes import bp as teams_bp

DEV_SECRET = "dev-secret-change-in-production"


def create_app():
    app = Flask(__name__)
    secret = os.environ.get("SECRET_KEY") or DEV_SECRET
    app.config["SECRET_KEY"] = secret
    if secret == DEV_SECRET and os.environ.get("PORT"):
        print("VARNING: SECRET_KEY är inte satt. Sätt miljövariabeln SECRET_KEY i produktion.", file=sys.stderr)
    database_url = os.environ.get("DATABASE_URL")
    if database_url:
        if database_url.startswith("postgres://"):
            database_url = database_url.replace("postgres://", "postgresql://", 1)
        # Tvinga SSL för PostgreSQL (t.ex. Render) om inte redan angivet
        if database_url.startswith("postgresql://") and "sslmode=" not in database_url:
            database_url += "?sslmode=require" if "?" not in database_url else "&sslmode=require"
        app.config["SQLALCHEMY_DATABASE_URI"] = database_url
    else:
        app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///baskettime.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SESSION_COOKIE_HTTPONLY"] = True
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
    app.config["PERMANENT_SESSION_LIFETIME"] = 86400 * 7  # 7 days
    # Render (och liknande) terminierar TLS framför appen; utan detta kan sessioncookies
    # med Secure-flagga eller is_secure bli fel. Lokalt utan DATABASE_URL används HTTP.
    if database_url:
        app.wsgi_app = ProxyFix(
            app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_port=1, x_prefix=1
        )
        # Secure-session kräver HTTPS i webbläsaren. Lokalt med http:// + DATABASE_URL
        # måste cookien kunna sättas: sätt SESSION_COOKIE_SECURE=false, annars 401 på alla /api.
        # På Render (HTTPS) används standard True via miljövariabeln RENDER.
        _sec = os.environ.get("SESSION_COOKIE_SECURE")
        if _sec is not None:
            app.config["SESSION_COOKIE_SECURE"] = _sec.lower() in ("1", "true", "yes")
        else:
            app.config["SESSION_COOKIE_SECURE"] = os.environ.get("RENDER") == "true"
        app.config["PREFERRED_URL_SCHEME"] = "https"

    db.init_app(app)
    app.register_blueprint(auth_bp)
    app.register_blueprint(teams_bp)
    app.register_blueprint(matches_bp)
    app.register_blueprint(profixio_bp)
    app.register_blueprint(public_bp)

    with app.app_context():
        db.create_all()
        ensure_user_email_and_reset_columns(db)
        ensure_created_at_columns(db)
        ensure_match_player_shots_columns(db)

    @app.route("/")
    def index():
        host = (request.host or "").split(":")[0].lower()
        if host in LANDING_HOSTS:
            return send_from_directory(".", "landing.html")
        return send_from_directory(".", "index.html")

    @app.route("/landing")
    def landing():
        return send_from_directory(".", "landing.html")

    @app.route("/landing/matcher")
    def landing_matcher():
        return send_from_directory(".", "landing/matcher.html")

    @app.route("/<path:path>")
    def static_file(path):
        return send_from_directory(".", path)

    return app


app = create_app()


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port, debug=False)
