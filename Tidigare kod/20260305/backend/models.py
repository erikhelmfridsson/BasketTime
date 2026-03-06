"""
SQLAlchemy models: User, Team, TeamPlayer, Match, MatchPlayer.
"""
import os
from datetime import datetime

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from werkzeug.security import check_password_hash, generate_password_hash

db = SQLAlchemy()


class User(db.Model):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(120), unique=True, nullable=False, index=True)
    password_hash = Column(String(256), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {"id": self.id, "username": self.username}


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

    def to_dict(self):
        return {
            "playerId": self.player_id,
            "playerNameAtTime": self.player_name_at_time,
            "secondsOnCourt": self.seconds_on_court,
            "assists": self.assists,
            "fouls": self.fouls,
            "goals": self.goals,
        }
