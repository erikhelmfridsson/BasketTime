"""
SQLAlchemy models: User, Team, TeamPlayer, Match, MatchPlayer + Profixio cache/linking.
"""
import os
from datetime import datetime

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from werkzeug.security import check_password_hash, generate_password_hash

db = SQLAlchemy()


class User(db.Model):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(120), unique=True, nullable=False, index=True)
    password_hash = Column(String(256), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    # Valfri e-post: befintliga konton kan vara utan; krävs för lösenordsåterställning
    email = Column(String(255), unique=True, nullable=True, index=True)
    password_reset_token_hash = Column(String(256), nullable=True)
    password_reset_expires_at = Column(DateTime, nullable=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email or "",
        }


class Team(db.Model):
    __tablename__ = "teams"
    id = Column(String(64), primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(200), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    players = db.relationship("TeamPlayer", backref="team", cascade="all, delete-orphan", order_by="TeamPlayer.ord")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "players": [p.to_dict() for p in self.players],
        }


class TeamPlayer(db.Model):
    __tablename__ = "team_players"
    id = Column(Integer, primary_key=True, autoincrement=True)
    team_id = Column(String(64), ForeignKey("teams.id", ondelete="CASCADE"), nullable=False, index=True)
    ord = Column(Integer, nullable=False, default=0)
    player_id = Column(String(64), nullable=False)
    name = Column(String(200), nullable=False)

    def to_dict(self):
        return {"id": self.player_id, "name": self.name}


class Match(db.Model):
    __tablename__ = "matches"
    id = Column(String(120), primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(200), nullable=False)
    date_iso = Column(String(64), nullable=False)
    match_seconds = Column(Integer, nullable=False, default=0)
    team_id = Column(String(64), nullable=True)
    team_name_at_time = Column(String(200), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    players = db.relationship("MatchPlayer", backref="match", cascade="all, delete-orphan", order_by="MatchPlayer.ord")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "dateISO": self.date_iso,
            "matchSeconds": self.match_seconds,
            "teamId": self.team_id or "",
            "teamNameAtTime": self.team_name_at_time or "",
            "players": [p.to_dict() for p in self.players],
        }


class MatchPlayer(db.Model):
    __tablename__ = "match_players"
    id = Column(Integer, primary_key=True, autoincrement=True)
    match_id = Column(String(120), ForeignKey("matches.id", ondelete="CASCADE"), nullable=False, index=True)
    ord = Column(Integer, nullable=False, default=0)
    player_id = Column(String(64), nullable=False)
    player_name_at_time = Column(String(200), nullable=False)
    seconds_on_court = Column(Integer, nullable=False, default=0)
    assists = Column(Integer, nullable=False, default=0)
    fouls = Column(Integer, nullable=False, default=0)
    goals = Column(Integer, nullable=False, default=0)
    shots = Column(Integer, nullable=False, default=0)
    made_shots = Column(Integer, nullable=False, default=0)

    def to_dict(self):
        return {
            "playerId": self.player_id,
            "playerNameAtTime": self.player_name_at_time,
            "secondsOnCourt": self.seconds_on_court,
            "assists": self.assists,
            "fouls": self.fouls,
            "goals": self.goals,
            "shots": self.shots,
            "madeShots": self.made_shots,
        }


class ProfixioTournament(db.Model):
    __tablename__ = "profixio_tournaments"
    id = Column(Integer, primary_key=True, autoincrement=False)
    organisation_id = Column(String(64), nullable=True, index=True)
    name = Column(String(255), nullable=True)
    raw_json = Column(Text, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, index=True)


class ProfixioTeam(db.Model):
    __tablename__ = "profixio_teams"
    id = Column(Integer, primary_key=True, autoincrement=False)
    tournament_id = Column(Integer, nullable=False, index=True)
    name = Column(String(255), nullable=True, index=True)
    club_name = Column(String(255), nullable=True, index=True)
    raw_json = Column(Text, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, index=True)
    __table_args__ = (UniqueConstraint("id", "tournament_id", name="uq_profixio_team_id_tournament"),)


class ProfixioPlayer(db.Model):
    __tablename__ = "profixio_players"
    id = Column(Integer, primary_key=True, autoincrement=False)
    tournament_id = Column(Integer, nullable=False, index=True)
    team_id = Column(Integer, nullable=True, index=True)
    name = Column(String(255), nullable=True, index=True)
    jersey_number = Column(String(32), nullable=True)
    birth_date = Column(String(32), nullable=True)
    raw_json = Column(Text, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, index=True)
    __table_args__ = (UniqueConstraint("id", "tournament_id", name="uq_profixio_player_id_tournament"),)


class ProfixioMatch(db.Model):
    __tablename__ = "profixio_matches"
    id = Column(Integer, primary_key=True, autoincrement=False)
    tournament_id = Column(Integer, nullable=False, index=True)
    start_time = Column(String(64), nullable=True, index=True)
    home_team_id = Column(Integer, nullable=True, index=True)
    away_team_id = Column(Integer, nullable=True, index=True)
    raw_json = Column(Text, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, index=True)
    __table_args__ = (UniqueConstraint("id", "tournament_id", name="uq_profixio_match_id_tournament"),)


class UserProfixioTeamLink(db.Model):
    __tablename__ = "user_profixio_team_links"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    local_team_id = Column(String(64), nullable=False, index=True)
    profixio_team_id = Column(Integer, nullable=False, index=True)
    tournament_id = Column(Integer, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    __table_args__ = (UniqueConstraint("user_id", "local_team_id", name="uq_user_local_team"),)


class UserProfixioPlayerLink(db.Model):
    __tablename__ = "user_profixio_player_links"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    local_team_id = Column(String(64), nullable=False, index=True)
    local_player_id = Column(String(64), nullable=False, index=True)
    profixio_player_id = Column(Integer, nullable=False, index=True)
    tournament_id = Column(Integer, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    __table_args__ = (UniqueConstraint("user_id", "local_team_id", "local_player_id", name="uq_user_local_player"),)


class ProfixioSyncConfig(db.Model):
    """
    Admin-konfig för återkommande synk (en gång per dygn) av en specifik turnering.
    """

    __tablename__ = "profixio_sync_configs"
    id = Column(Integer, primary_key=True, autoincrement=True)
    tournament_id = Column(Integer, nullable=False, index=True)
    organisation_id = Column(String(64), nullable=True, index=True)
    enabled = Column(Integer, nullable=False, default=1)  # 1/0 (för enkel cross-db)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, index=True)
    __table_args__ = (UniqueConstraint("tournament_id", name="uq_profixio_sync_tournament"),)


class ProfixioSyncState(db.Model):
    """
    Körstatus för daglig synk (för att undvika parallella körningar mellan processer).
    """

    __tablename__ = "profixio_sync_state"
    id = Column(Integer, primary_key=True, autoincrement=False, default=1)
    last_run_at = Column(DateTime, nullable=True, index=True)
    running = Column(Integer, nullable=False, default=0)  # 1/0
    updated_at = Column(DateTime, default=datetime.utcnow, index=True)
