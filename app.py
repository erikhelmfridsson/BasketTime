"""
BasketTime: Flask app – static frontend + API for users, teams, matches.
Serves static files and mounts /api for auth, teams, matches.
"""
import os
import sys
import threading
import time
from datetime import datetime, timedelta

from flask import Flask, request, send_from_directory
from werkzeug.middleware.proxy_fix import ProxyFix

from backend.models import db
from backend.models import ProfixioSyncConfig, ProfixioSyncState
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
from backend.profixio_sync import sync_tournament

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

    def _is_admin(user):
        allowed = [x.strip() for x in (os.environ.get("ADMIN_USERNAMES") or "").split(",") if x.strip()]
        return (not allowed) or (user and user.username in allowed)

    @app.route("/admin/profixio")
    def admin_profixio_page():
        # Skydda sidan utan att lägga till template-system.
        from backend.auth import get_current_user

        user = get_current_user()
        if not user:
            return send_from_directory(".", "index.html")
        if not _is_admin(user):
            return {"error": "Forbidden"}, 403
        return send_from_directory(".", "admin-profixio.html")

    def _daily_sync_loop():
        # Kör en gång per dygn. Förutsätter att turneringar konfigureras via admin-sidan.
        # För att undvika att flera processer kör samtidigt används ProfixioSyncState.running som enkel låsflagga.
        while True:
            try:
                with app.app_context():
                    state = db.session.get(ProfixioSyncState, 1)
                    now = datetime.utcnow()
                    if not state:
                        state = ProfixioSyncState(id=1, running=0, last_run_at=None, updated_at=now)
                        db.session.add(state)
                        db.session.commit()

                    # Kör om aldrig körd eller om det gått >= 24h
                    due = (state.last_run_at is None) or (now - state.last_run_at >= timedelta(hours=24))
                    if due and not state.running:
                        state.running = 1
                        state.updated_at = now
                        db.session.commit()
                        try:
                            cfgs = ProfixioSyncConfig.query.filter_by(enabled=1).all()
                            for cfg in cfgs:
                                sync_tournament(cfg.tournament_id, organisation_id=cfg.organisation_id or None)
                            db.session.commit()
                            state.last_run_at = datetime.utcnow()
                        except Exception:
                            db.session.rollback()
                            print("Daily Profixio sync failed", file=sys.stderr)
                        finally:
                            state.running = 0
                            state.updated_at = datetime.utcnow()
                            try:
                                db.session.commit()
                            except Exception:
                                db.session.rollback()
            except Exception:
                print("Daily Profixio sync loop crashed", file=sys.stderr)

            # Sov 10 minuter mellan checks (minskar load men ger <=10 min fördröjning efter 24h-gräns)
            time.sleep(600)

    # Starta bakgrundssynk om aktiverat och om API-nyckel finns
    if (os.environ.get("PROFIXIO_DAILY_SYNC", "true").lower() in ("1", "true", "yes")) and os.environ.get("PROFIXIO_API_SECRET"):
        t = threading.Thread(target=_daily_sync_loop, name="profixio-daily-sync", daemon=True)
        t.start()

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
