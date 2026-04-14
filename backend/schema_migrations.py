"""Lägger till kolumner i befintlig SQLite/Postgres utan Alembic."""
import sys

from sqlalchemy import inspect, text


def ensure_user_email_and_reset_columns(db):
    """users: email, password_reset_token_hash, password_reset_expires_at"""
    try:
        insp = inspect(db.engine)
        cols = {c["name"] for c in insp.get_columns("users")}
    except Exception as e:
        print("schema_migrations: kunde inte läsa users: %s" % (e,), file=sys.stderr)
        return
    dialect = db.engine.dialect.name
    to_run = []
    if "email" not in cols:
        to_run.append("ALTER TABLE users ADD COLUMN email VARCHAR(255)")
    if "password_reset_token_hash" not in cols:
        to_run.append("ALTER TABLE users ADD COLUMN password_reset_token_hash VARCHAR(256)")
    if "password_reset_expires_at" not in cols:
        if dialect == "postgresql":
            to_run.append(
                "ALTER TABLE users ADD COLUMN password_reset_expires_at TIMESTAMP"
            )
        else:
            to_run.append(
                "ALTER TABLE users ADD COLUMN password_reset_expires_at DATETIME"
            )
    if not to_run:
        return
    try:
        with db.engine.begin() as conn:
            for stmt in to_run:
                conn.execute(text(stmt))
        print("schema_migrations: users uppdaterad (email/reset).", file=sys.stderr)
    except Exception as e:
        print("schema_migrations: ALTER misslyckades: %s" % (e,), file=sys.stderr)


def ensure_match_player_shots_columns(db):
    """match_players: shots, made_shots (äldre SQLite saknar dem efter modelländring)."""
    try:
        insp = inspect(db.engine)
        cols = {c["name"] for c in insp.get_columns("match_players")}
    except Exception as e:
        print("schema_migrations: kunde inte läsa match_players: %s" % (e,), file=sys.stderr)
        return
    dialect = db.engine.dialect.name
    to_run = []
    if "shots" not in cols:
        if dialect == "postgresql":
            to_run.append(
                "ALTER TABLE match_players ADD COLUMN shots INTEGER NOT NULL DEFAULT 0"
            )
        else:
            to_run.append("ALTER TABLE match_players ADD COLUMN shots INTEGER DEFAULT 0")
    if "made_shots" not in cols:
        if dialect == "postgresql":
            to_run.append(
                "ALTER TABLE match_players ADD COLUMN made_shots INTEGER NOT NULL DEFAULT 0"
            )
        else:
            to_run.append(
                "ALTER TABLE match_players ADD COLUMN made_shots INTEGER DEFAULT 0"
            )
    if not to_run:
        return
    try:
        with db.engine.begin() as conn:
            for stmt in to_run:
                conn.execute(text(stmt))
        print("schema_migrations: match_players uppdaterad (shots/made_shots).", file=sys.stderr)
    except Exception as e:
        print("schema_migrations: match_players ALTER misslyckades: %s" % (e,), file=sys.stderr)


def ensure_created_at_columns(db):
    """
    Äldre DB kan sakna created_at-kolumner trots att modellerna har dem.
    Utan dessa kan INSERT/SELECT (t.ex. order_by(created_at)) krascha i produktion.

    Tabellen kan redan finnas (create_all skapar inte nya kolumner), så vi kompletterar här.
    """
    dialect = db.engine.dialect.name
    targets = [
        ("users", "created_at"),
        ("teams", "created_at"),
        ("matches", "created_at"),
    ]
    try:
        insp = inspect(db.engine)
    except Exception as e:
        print("schema_migrations: kunde inte initiera inspector: %s" % (e,), file=sys.stderr)
        return

    altered_any = False
    for table, col in targets:
        try:
            cols = {c["name"] for c in insp.get_columns(table)}
        except Exception as e:
            print("schema_migrations: kunde inte läsa %s: %s" % (table, e), file=sys.stderr)
            continue
        if col in cols:
            continue
        # Postgres: TIMESTAMP, SQLite: DATETIME (båda funkar för SQLAlchemy DateTime)
        coltype = "TIMESTAMP" if dialect == "postgresql" else "DATETIME"
        stmt = f"ALTER TABLE {table} ADD COLUMN {col} {coltype}"
        try:
            with db.engine.begin() as conn:
                conn.execute(text(stmt))
            altered_any = True
            print("schema_migrations: %s uppdaterad (saknade %s)." % (table, col), file=sys.stderr)
        except Exception as e:
            print("schema_migrations: %s ALTER misslyckades: %s" % (table, e), file=sys.stderr)

    if altered_any:
        # Ingen data-migrering behövs; nya rader får värde från appens default.
        return
