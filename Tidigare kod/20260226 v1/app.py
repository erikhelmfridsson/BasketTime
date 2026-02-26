"""
BasketTime: Flask app – static frontend + API for users, teams, matches.
Serves static files and mounts /api for auth, teams, matches.
"""
import os

from flask import Flask, send_from_directory

from backend.models import db
from backend.routes.auth_routes import bp as auth_bp
from backend.routes.matches_routes import bp as matches_bp
from backend.routes.teams_routes import bp as teams_bp


def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY") or "dev-secret-change-in-production"
    database_url = os.environ.get("DATABASE_URL")
    if database_url:
        if database_url.startswith("postgres://"):
            database_url = database_url.replace("postgres://", "postgresql://", 1)
        app.config["SQLALCHEMY_DATABASE_URI"] = database_url
    else:
        app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///baskettime.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SESSION_COOKIE_HTTPONLY"] = True
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
    app.config["PERMANENT_SESSION_LIFETIME"] = 86400 * 7  # 7 days

    db.init_app(app)
    app.register_blueprint(auth_bp)
    app.register_blueprint(teams_bp)
    app.register_blueprint(matches_bp)

    with app.app_context():
        db.create_all()

    @app.route("/")
    def index():
        return send_from_directory(".", "index.html")

    @app.route("/<path:path>")
    def static_file(path):
        return send_from_directory(".", path)

    return app


app = create_app()


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port, debug=False)
