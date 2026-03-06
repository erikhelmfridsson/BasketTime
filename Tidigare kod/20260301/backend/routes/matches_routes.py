"""
Matches API: list, create (save/update), get, delete.
"""
from flask import Blueprint, request

from backend.auth import get_current_user, login_required
from backend.models import Match, MatchPlayer, db

bp = Blueprint("matches", __name__, url_prefix="/api/matches")


def _match_to_response(m):
    return {
        "id": m.id,
        "name": m.name,
        "dateISO": m.date_iso,
        "matchSeconds": m.match_seconds,
        "teamId": m.team_id or "",
        "teamNameAtTime": m.team_name_at_time or "",
        "players": [
            {
                "playerId": p.player_id,
                "playerNameAtTime": p.player_name_at_time,
                "secondsOnCourt": p.seconds_on_court,
                "assists": p.assists,
                "fouls": p.fouls,
                "goals": p.goals,
            }
            for p in sorted(m.players, key=lambda x: x.ord)
        ],
    }


@bp.route("", methods=["GET"])
@login_required
def list_matches():
    user = get_current_user()
    matches = Match.query.filter_by(user_id=user.id).order_by(Match.created_at.desc()).all()
    return {"matches": [_match_to_response(m) for m in matches]}


@bp.route("", methods=["POST"])
@login_required
def save_match():
    user = get_current_user()
    data = request.get_json() or {}
    match_id = (data.get("id") or "").strip()
    if not match_id:
        return {"error": "Match id required"}, 400
    name = (data.get("name") or "").strip() or "Match"
    date_iso = data.get("dateISO") or data.get("date_iso") or ""
    match_seconds = int(data.get("matchSeconds") or data.get("match_seconds") or 0)
    team_id = data.get("teamId") or data.get("team_id") or ""
    team_name_at_time = data.get("teamNameAtTime") or data.get("team_name_at_time") or ""
    players_data = data.get("players") or []

    match = Match.query.filter_by(id=match_id, user_id=user.id).first()
    if match:
        match.name = name
        match.date_iso = date_iso
        match.match_seconds = match_seconds
        match.team_id = team_id
        match.team_name_at_time = team_name_at_time
        for mp in match.players:
            db.session.delete(mp)
    else:
        match = Match(
            id=match_id,
            user_id=user.id,
            name=name,
            date_iso=date_iso,
            match_seconds=match_seconds,
            team_id=team_id,
            team_name_at_time=team_name_at_time,
        )
        db.session.add(match)

    for i, entry in enumerate(players_data):
        if not isinstance(entry, dict):
            continue
        mp = MatchPlayer(
            match_id=match_id,
            ord=i,
            player_id=str(entry.get("playerId", "p" + str(i + 1))),
            player_name_at_time=str(entry.get("playerNameAtTime", "Spelare " + str(i + 1))),
            seconds_on_court=int(entry.get("secondsOnCourt", 0)),
            assists=int(entry.get("assists", 0)),
            fouls=int(entry.get("fouls", 0)),
            goals=int(entry.get("goals", 0)),
        )
        db.session.add(mp)
    db.session.commit()
    return _match_to_response(match), 201


@bp.route("/<match_id>", methods=["GET"])
@login_required
def get_match(match_id):
    user = get_current_user()
    match = Match.query.filter_by(id=match_id, user_id=user.id).first()
    if not match:
        return {"error": "Match not found"}, 404
    return _match_to_response(match)


@bp.route("/<match_id>", methods=["DELETE"])
@login_required
def delete_match(match_id):
    user = get_current_user()
    match = Match.query.filter_by(id=match_id, user_id=user.id).first()
    if not match:
        return {"error": "Match not found"}, 404
    db.session.delete(match)
    db.session.commit()
    return "", 204


@bp.route("/clear", methods=["POST"])
@login_required
def clear_all():
    user = get_current_user()
    Match.query.filter_by(user_id=user.id).delete()
    db.session.commit()
    return "", 204
