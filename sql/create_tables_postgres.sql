-- BasketTime – PostgreSQL schema
-- Används på Render med miljövariabeln DATABASE_URL.
-- Tabellen motsvarar SQLAlchemy-modellerna i backend/models.py.

CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(120) NOT NULL UNIQUE,
    password_hash VARCHAR(256) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS teams (
    id VARCHAR(64) PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(200) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_teams_user_id ON teams(user_id);

CREATE TABLE IF NOT EXISTS team_players (
    id SERIAL PRIMARY KEY,
    team_id VARCHAR(64) NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
    ord INTEGER NOT NULL DEFAULT 0,
    player_id VARCHAR(64) NOT NULL,
    name VARCHAR(200) NOT NULL
);

CREATE INDEX IF NOT EXISTS ix_team_players_team_id ON team_players(team_id);

CREATE TABLE IF NOT EXISTS matches (
    id VARCHAR(120) PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(200) NOT NULL,
    date_iso VARCHAR(64) NOT NULL,
    match_seconds INTEGER NOT NULL DEFAULT 0,
    team_id VARCHAR(64),
    team_name_at_time VARCHAR(200),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_matches_user_id ON matches(user_id);
CREATE INDEX IF NOT EXISTS ix_matches_created_at ON matches(created_at DESC);

CREATE TABLE IF NOT EXISTS match_players (
    id SERIAL PRIMARY KEY,
    match_id VARCHAR(120) NOT NULL REFERENCES matches(id) ON DELETE CASCADE,
    ord INTEGER NOT NULL DEFAULT 0,
    player_id VARCHAR(64) NOT NULL,
    player_name_at_time VARCHAR(200) NOT NULL,
    seconds_on_court INTEGER NOT NULL DEFAULT 0,
    assists INTEGER NOT NULL DEFAULT 0,
    fouls INTEGER NOT NULL DEFAULT 0,
    goals INTEGER NOT NULL DEFAULT 0,
    shots INTEGER NOT NULL DEFAULT 0,
    made_shots INTEGER NOT NULL DEFAULT 0
);

CREATE INDEX IF NOT EXISTS ix_match_players_match_id ON match_players(match_id);

