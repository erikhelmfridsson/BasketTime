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
