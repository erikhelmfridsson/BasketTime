"""
Teams API: list, create, get, update, delete.
"""
import time

from flask import Blueprint, request

from backend.auth import get_current_user, login_required
from backend.models import Team, TeamPlayer, db

bp = Blueprint("teams", __name__, url_prefix="/api/teams")


def _team_to_response(team):
    return {
        "id": team.id,
        "name": team.name,
        "players": [{"id": p.player_id, "name": p.name} for p in sorted(team.players, key=lambda x: x.ord)],
    }


@bp.route("", methods=["GET"])
@login_required
def list_teams():
    user = get_current_user()
    teams = Team.query.filter_by(user_id=user.id).order_by(Team.created_at).all()
    return {"teams": [_team_to_response(t) for t in teams]}


@bp.route("", methods=["POST"])
@login_required
def create_team():
    user = get_current_user()
    data = request.get_json() or {}
    name = (data.get("name") or "").strip() or "Lag"
    players = data.get("players") or []
    team_id = "t" + str(int(time.time() * 1000))
    team = Team(id=team_id, user_id=user.id, name=name)
    db.session.add(team)
    for i, p in enumerate(players[:20]):
        pid = (p.get("id") or "p" + str(i + 1)) if isinstance(p, dict) else "p" + str(i + 1)
        pname = (p.get("name") or "Spelare " + str(i + 1)) if isinstance(p, dict) else str(p)
        tp = TeamPlayer(team_id=team_id, ord=i, player_id=str(pid), name=str(pname).strip())
        db.session.add(tp)
    db.session.commit()
    return _team_to_response(team), 201


@bp.route("/<team_id>", methods=["GET"])
@login_required
def get_team(team_id):
    user = get_current_user()
    team = Team.query.filter_by(id=team_id, user_id=user.id).first()
    if not team:
        return {"error": "Team not found"}, 404
    return _team_to_response(team)


@bp.route("/<team_id>", methods=["PUT"])
@login_required
def update_team(team_id):
    user = get_current_user()
    team = Team.query.filter_by(id=team_id, user_id=user.id).first()
    if not team:
        return {"error": "Team not found"}, 404
    data = request.get_json() or {}
    if "name" in data:
        team.name = (data.get("name") or "").strip() or team.name
    if "players" in data:
        for tp in team.players:
            db.session.delete(tp)
        players = data.get("players") or []
        for i, p in enumerate(players[:20]):
            pid = (p.get("id") or "p" + str(i + 1)) if isinstance(p, dict) else "p" + str(i + 1)
            pname = (p.get("name") or "Spelare " + str(i + 1)) if isinstance(p, dict) else str(p)
            tp = TeamPlayer(team_id=team_id, ord=i, player_id=str(pid), name=str(pname).strip())
            db.session.add(tp)
    db.session.commit()
    return _team_to_response(team)


@bp.route("/<team_id>", methods=["DELETE"])
@login_required
def delete_team(team_id):
    user = get_current_user()
    team = Team.query.filter_by(id=team_id, user_id=user.id).first()
    if not team:
        return {"error": "Team not found"}, 404
    db.session.delete(team)
    db.session.commit()
    return "", 204
